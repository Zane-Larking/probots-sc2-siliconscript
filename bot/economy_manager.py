from functools import reduce
from itertools import chain
import warnings
from bot.debug import Debug, DebugTopic
from bot.game_plan import GamePlan
from bot.general_cache import Cacheable, property_generic_cache_once_per_frame
from sc2.bot_ai import BotAI
from sc2.constants import IS_CONSTRUCTING_SCV, TERRAN_STRUCTURES_REQUIRE_SCV, ABILITYID_TO_UNITTYPEID
from sc2.data import Race, race_gas
from sc2.dicts.unit_abilities import UNIT_ABILITIES
from sc2.dicts.unit_train_build_abilities import TRAIN_INFO
from sc2.dicts.unit_trained_from import UNIT_TRAINED_FROM
from bot.build_order import BuildOrder, BuildCommand
from bot.wall_manager import WallManager
from bot.economy.townhall_supervisor import ExpansionTownhallSupervisor, TownhallSupervisor
from bot.military.base_military_supervisor import BaseMilitarySupervisor
from sc2.ids.ability_id import AbilityId
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units
import numpy as np
from sc2.ids.unit_typeid import UnitTypeId
from typing import TYPE_CHECKING, Any, Dict, Generator, Iterable, List, Optional, Set, Tuple, Union

from bot.typeHelper import HAVERSTER_FOR_RACE, RACE_TOWNHALL
from bot.interfaces.mediator import Mediator
from abc import ABC, abstractmethod
from bot.interfaces.pub_sub import Subscriber
from sc2.game_data import Cost, UnitTypeData

from bot.position_helper import behind_minerals
from bot.worker_manager import WorkerManager

from bot.typeHelper import get_structure, get_tag, UnitTag

# the amount of excess supply per expansion that should be maintained to not be supply blocked 
SUPPLY_BUFFER = 5

debug: Debug

class WorkerDonationSubscriber(Subscriber, WorkerManager):
    def __init__(self) -> None:
        super().__init__()

    #returns a worker
    def update(self, context) -> List[Unit]:
        # context urgency
        # context should contain information about where the worker is needed
        # NOTE won't work for zerg

        bids: List[Unit] = []
        
        idle_worker_donations = self.idle_workers.closest_n_units(context.position, context.quantity)
        worker_speed = 3.94
        for worker in idle_worker_donations:
            # This does not take into account path finding
            eta = worker.position.distance_to(context.position) / worker_speed
            bids.append(WorkerDonationBid(worker, eta))
        if idle_worker_donations.amount < context.quantity:
            for i in range(0, context.quantity-idle_worker_donations.amount):
                build_time = self._bot_object.game_data.units[UnitTypeId.SCV].cost.time * (i+1)
                eta = worker.position.distance_to(context.position) / worker_speed + build_time 
                bids.append(WorkerDonationBid(worker, eta))

        return bids
    


class EconomyManager(Cacheable):
    def __init__(self, bot_object, game_plan: GamePlan, wall_manager: WallManager):
        super().__init__()
        global debug
        debug = Debug(bot_object)

        self._bot_object: BotAI = bot_object
        self._expansion_townhall_tags: List[UnitTag] = [] # townhalls at mineralfields
        self._macro_townhall_tags: List[UnitTag] = [] # additional macro townhalls


        self.BESs: List[TownhallSupervisor] = [self.init_first_eco_supervisor()]
        self.wall_manager: WallManager = wall_manager
        self.build_order: BuildOrder = game_plan.build_order

        self.current_building: BuildCommand = self.build_order.build_queue[0]

    @property 
    def _frame(self) -> int:
        return self._bot_object.state.game_loop
    
    @property_generic_cache_once_per_frame
    def expansion_townhalls(self) -> Units:
        return self._bot_object.structures.filter(lambda th: th.tag in self._expansion_townhall_tags)

    @property_generic_cache_once_per_frame
    def macro_townhalls(self) -> Units:
        return self._bot_object.structures.filter(lambda th: th.tag in self._macro_townhall_tags)
    
    @property
    def townhalls(self) -> Units:
        return self.expansion_townhalls + self.macro_townhalls
    
    @property
    def orbitals_with_energy(self):
        orbitals_with_energy = self._bot_object.structures.filter(lambda structure: structure.type_id == UnitTypeId.ORBITALCOMMAND and structure.energy >= 50)
        return orbitals_with_energy
    
    # TODO make this better
    def return_to_work(self, worker: Unit):
        """
        returns a worker to the main townhalls mineral line
        ### THIS SHOULD BE UPDATED
        """
        assert worker.type_id == HAVERSTER_FOR_RACE[self._bot_object.race]

        # the Units stored in a class instance are old representations of the
        # game units
        townhall_reps = self.expansion_townhalls
        # there might not be any townhalls
        if townhall_reps.amount > 0:
            townhall = self._bot_object.structures.find_by_tag(townhall_reps.first.tag)
            
            mineral_fields = self._bot_object.mineral_field.closer_than(8, townhall)

            if mineral_fields.amount > 0:
                worker(AbilityId.HARVEST_GATHER, mineral_fields.first, queue = True)


    def init_first_eco_supervisor(self) -> TownhallSupervisor:
        first_townhall = self._bot_object.townhalls.first
        starting_workers = self._bot_object.workers
        self.add_expansion_townhall(first_townhall)
        return ExpansionTownhallSupervisor(self._bot_object, first_townhall, starting_workers)


    def add_expansion_townhall(self, townhall: Union[Unit, UnitTag]):
        townhall_tag = get_tag(townhall)
        townhall_struct = get_structure(townhall)

        debug.log_cond(f"adding expansion townhall at position: {townhall_struct.position}", topic=DebugTopic.ECONOMY_EVENTS)
        self._expansion_townhall_tags.append(townhall_tag)

    def add_macro_townhall(self, townhall: Union[Unit, UnitTag]):
        townhall_tag = get_tag(townhall)
        debug.log_cond(f"adding macro townhall at position: {townhall.position}", topic=DebugTopic.ECONOMY_EVENTS)
        self._macro_townhall_tags.append(get_tag(townhall_tag))

        
    async def operate(self):
        if (self.build_order.has_pending):

            build_successful = True
            while (build_successful and not self.build_order.current_build_command.quota_is_met):
                debug.log_cond("Build order supply Quota not yet met", topic=DebugTopic.DEFAULT)
                
                # carry out build order
                build_successful = await self.build(self.build_order.current_build_command.type_id)

        if (self.build_order.is_overiding and self.build_order.has_pending):
            # Subtract the cost of the current build command to save up for
            # build order
            # self.type_id = type_id
            # self.supply = supply
            # self.global_total = global_total
            print("reserve resources")
            
            reserved_item_ids: List[Union[UnitTypeId, UpgradeId, AbilityId]] = self.build_order.pending_build_command_type_ids
            
            print(f"reserving resources for {reserved_item_ids}")
            self.reserve_resources_for(reserved_item_ids) 
            print(f"minerals: {self._bot_object.minerals}")
            print(f"vespene: {self._bot_object.vespene}")
            
        townhalls = self._bot_object.structures.same_tech({UnitTypeId.COMMANDCENTER})

        # ensure there is a townhall
        if townhalls.amount == 0:
            debug.log_cond("no townhalls", topic=DebugTopic.BUILD_ORDER_STATE)
            return
        
        # produce workers
        for townhall in townhalls:
            if not (townhall.is_active):
                harvester_type_id = HAVERSTER_FOR_RACE[self._bot_object.race]
                if self._bot_object.supply_workers + self._bot_object.already_pending(harvester_type_id) < self._bot_object.WORKER_MAX and self._bot_object.can_afford(harvester_type_id):
                    
                    townhall.train(harvester_type_id)



        # ensure not supply blocked

        if self._bot_object.supply_cap != 200 and self._bot_object.supply_left + 8 * self._bot_object.already_pending(UnitTypeId.SUPPLYDEPOT) < SUPPLY_BUFFER * townhalls.amount:
            print("supply depot needed")
            await self.build_with_worker(UnitTypeId.SUPPLYDEPOT)

        # produce units
        build_successful = True
        while (build_successful and self._bot_object.can_afford(UnitTypeId.MARINE)):
            build_successful = await self.build(UnitTypeId.MARINE)

        # expand condition
        if self._bot_object.workers.amount >= self.scv_threshhold:
            print(f"expand threshhold: {self.scv_threshhold}, scv count: {self._bot_object.workers.amount}")
            await self.build_with_worker(UnitTypeId.COMMANDCENTER)

        # add production condition
        if self._bot_object.minerals >= 500:
            await self.build(UnitTypeId.BARRACKS)

        debug.log_cond(f"I think I have\n\tminerals: {self._bot_object.minerals}\n\tvespene: {self._bot_object.vespene}\n", topic=DebugTopic.BALANCE)


    @property
    def scv_threshhold(self):

        amount_of_gas_structures = self._bot_object.structures.tags_in({race_gas[self._bot_object.race]}).filter(lambda geyser: geyser.has_vespene).amount

        production_compensation = 6 # you can make 6 scvs in the time the CC builds
        safety_offset = 6 # can be tuned to be more greedy or safe
        scv_threshhold = amount_of_gas_structures + safety_offset
        
        vespene_geysers = self._bot_object.vespene_geyser.filter(lambda geyser: geyser.has_vespene)

        for townhall in self.expansion_townhalls:
            if townhall.is_ready:
                # Find all vespene geysers that are closer than range 10 to this townhall
                vespene_harvesters = vespene_geysers.closer_than(10, townhall).amount
                
                scv_threshhold += (townhall.ideal_harvesters + vespene_harvesters*3 - production_compensation)
            else:
                scv_threshhold += 22
        return scv_threshhold

    def notify_construction_started(self, unit: Unit):
        debug.log_cond(f"Construction of building {unit} started at {unit.position}.", topic=DebugTopic.ECONOMY_EVENTS)

        # if 'unit' is assigned to a wall
        for wall in self.wall_manager.walls:
            if unit.position in wall.where_structure_is_needed(unit.type_id):
                wall.add_structure(unit)

        # if building under construction is from the build order
        build_order_advanced:bool = self.build_order.update()
        if build_order_advanced:
            debug.log_cond(f"Build order progressed by building: {self.current_building.type_id}", topic=DebugTopic.ECONOMY_EVENTS)

        # Add new Townhalls
        if (unit.type_id == UnitTypeId.COMMANDCENTER):
            if (unit.position in self._bot_object.expansion_locations_list):
                print("expansion tag added")
                self.add_expansion_townhall(unit)
            else:
                self.add_macro_townhall(unit)


        # Take care of rallies
        if unit.tag == RACE_TOWNHALL[self._bot_object.race]:
            minerals = self._bot_object.mineral_field.closer_than(7, unit)
            if minerals:
                print(f"Setting rally point of {unit.name} to {minerals.first.position}")
                unit(AbilityId.RALLY_BUILDING, minerals.first)


    def subtract_cost(self, item_id: Union[UnitTypeId, UpgradeId, AbilityId]):
        #  subtracts the cost even if it can not be afforded
        cost: Cost = self._bot_object.calculate_cost(item_id)
        self._bot_object.minerals -= cost.minerals
        self._bot_object.vespene -= cost.vespene
        
    def subtract_costs(self, item_ids: List[Union[UnitTypeId, UpgradeId, AbilityId]]):
        for item_id in item_ids:
            self.subtract_cost(item_id)

    def reserve_resources_for(self, item_ids: List[Union[UnitTypeId, UpgradeId, AbilityId]]):
        debug.log_cond(f"Reserving resources for {item_ids}", topic=DebugTopic.DEFAULT)
        self.subtract_costs(item_ids)

    # TODO improve by adding a quantity to make
    async def build(self, type_id: UnitTypeId) -> bool:
        # ==================================
        # Control flow
        """
        Attempts to build the corresponding unit or structure and returns True
        if successful, otherwise reurn False.

        determine if tech requirements are satisfied
            if not available append tech to build queue
        determine if workers/production structures are available
            if not purchased append ^ to build queue 
            if construction not complete skip
            (if not idle consider if more production is needed)  
        determine if addon requirements are satisfied
            if not satisfied append addon to build queue    
        
        determine the position to build
        determine the worker to build with
        """
        # ==================================

        assert isinstance(type_id, UnitTypeId)
        
        # determine if tech requirements are met  
        if not(self.ensure_tech_requirements(type_id)):
            return False
            # if still contructing, wait
                
        if self.is_produced_by_worker(type_id):
            return await self.build_with_worker(type_id)
        elif (False):
            # edge cases
            pass
        else:
            return self.build_from_structure(type_id)

    def build_from_structure(self, type_id) -> bool:
        """
        Attempts to make with the appropriate structure. Returns True if
        successful, otherwise return False. 
        """
        # TODO This method should handle the filtering as well            
        trainers = self.get_structures_as_trainer_candidates(type_id)
        
        if trainers.amount == 0:
            # no trainers available
            debug.log_cond(f"trainer_type_ids: {UNIT_TRAINED_FROM[type_id]}", topic=DebugTopic.BUILD_ORDER_STATE)
            debug.log_cond(f"No {UNIT_TRAINED_FROM[type_id]}s available", topic=DebugTopic.BUILD_ORDER_STATE)

        debug.log_cond(f"Production structures for {type_id.name}: {trainers}", topic=DebugTopic.BUILD_ORDER_STATE)

        if trainers.amount == 0:
            return False
        
        trainer = trainers.prefer_idle.first
        train_ability = self.train_ability(type_id)
        if self._bot_object.can_afford(train_ability) and trainer.is_idle and len(trainer.orders) == 0:
            if trainer(train_ability, subtract_cost=True, subtract_supply=True):
                self.build_order.update()
                return True
        return False
    
    def train_ability(self, type_id: UnitTypeId):
        train_info = self.get_train_info(type_id)
        return train_info.get('ability')
            
    async def build_with_worker(self, type_id: UnitTypeId) -> bool:
        worker_candidates = self.get_worker_candidates()
        if worker_candidates.amount == 0:
            # no workers
            return False
        # Gas Geysers are built differently
        if type_id == race_gas[self._bot_object.race]:
            return self.build_on_gas()
        
        if type_id == RACE_TOWNHALL[self._bot_object.race]:
            print("Wanting to expand now")
            if self._bot_object.can_afford(type_id):
                print("EXPANDING!!!")

                placement_position = await self._bot_object.get_next_expansion()
                build_worker = worker_candidates.prefer_idle.closest_to(placement_position)
                if not placement_position:
                    # All expansions are used up or mined out
                    warnings.warn("Trying to expand_now() but bot is out of locations to expand to")
                    return False
                
                return build_worker.build(type_id, placement_position)
        
        debug.log_cond(f"Worker Candidates: {worker_candidates}", topic=DebugTopic.BUILD_ORDER_STATE)
        placement_position = await self.get_construction_position(type_id)
        # Placement_position can be None
        if placement_position:
            debug.log_cond(f"Position: {placement_position}", topic=DebugTopic.BUILD_ORDER_STATE)
            build_worker = worker_candidates.prefer_idle.closest_to(placement_position)
            if self._bot_object.can_afford(type_id):
                if build_worker.build(type_id, placement_position):
                    # build command successfully issued

                    # TODO create a call back event system for when orders are
                    # removed (ie completed)
                    # HOTFIX this behaviour should be integrated with a worker_manager
                    self.return_to_work(build_worker)
                    return True
            return False

    def build_on_gas(self) -> bool:
        # find geysers
        target_geyser = self.get_vespene_geyser()

        if target_geyser:
            debug.log_cond(f"Geyser: {target_geyser} at Position: {target_geyser.position}", topic=DebugTopic.BUILD_ORDER_STATE)
            build_worker = self.get_worker_candidates().prefer_idle.closest_to(target_geyser.position)
            return build_worker.build_gas(target_geyser)
        
        # No geyser. Skipping in build order
        debug.log_cond("unable to find appropriate geyser. Skipping build command", topic=DebugTopic.ECONOMY_EVENTS)
        self.increment_build()
        return False

    def get_vespene_geyser(self) -> Union[Unit, None]:
        townhalls = self.townhalls
        
        vespene_geysers: Units = Units([], self._bot_object)

        for th in townhalls:
        # Find all vespene geysers that are closer than range 10 to this townhall
            vespene_geysers.extend(self._bot_object.vespene_geyser.closer_than(10, th).filter(lambda geyser: geyser.has_vespene))
            debug.log_cond(f"vespene geysers: {self._bot_object.vespene_geyser.closer_than(10, th)}", topic=DebugTopic.BUILD_ORDER_STATE)
            debug.log_cond(f"filtered vespene geysers: {self._bot_object.vespene_geyser.closer_than(10, th).filter(lambda geyser: geyser.has_vespene)}", topic=DebugTopic.BUILD_ORDER_STATE)

        # TODO determine optimal geyser

        debug.log_cond(f"all appropriate vespene geysers: {vespene_geysers}", topic=DebugTopic.BUILD_ORDER_STATE)

        # might not have found a geyser
        if vespene_geysers.amount > 0:
            return vespene_geysers.first
        return None

    def get_train_info(self, type_id: UnitTypeId) -> Dict[str, Union[AbilityId, bool, UnitTypeId]]:
        trainer_type_id: UnitTypeId = list(UNIT_TRAINED_FROM[type_id])[0]
        return TRAIN_INFO[trainer_type_id][type_id]

    def is_produced_by_worker(self, type_id: UnitTypeId) -> bool:
        trainer_type_ids = UNIT_TRAINED_FROM[type_id]
        harvester_type_id = HAVERSTER_FOR_RACE[self._bot_object.race]
        return harvester_type_id in trainer_type_ids

    def get_structures_as_trainer_candidates(self, type_id: UnitTypeId) -> Union[Units, None]:
        if self.is_produced_by_worker(type_id):
            warnings.warn(f"{type_id.name} is made using workers")
            return None
        
        # provides an empty Unit list if type_id can't be produced
        try:
            trainer_type_ids = UNIT_TRAINED_FROM[type_id]
        except KeyError:
            print(f"{type_id} can't be produced")
            return None

        trainers = self._bot_object.structures.of_type(trainer_type_ids)

        # TODO more filtering here
            
        return trainers
        
    def ensure_tech_requirements(self, type_id: UnitTypeId) -> bool:
        train_info = self.get_train_info(type_id)
        trainning_prerequisite_type_id: UnitTypeId = train_info.get('required_building')
        if self._bot_object.tech_requirement_progress(type_id) < 1:
            debug.log_cond(f"Tech Requirements not met to build {type_id.name}", topic=DebugTopic.BUILD_ORDER_STATE)
            if trainning_prerequisite_type_id:
                if self._bot_object.structures.same_tech({trainning_prerequisite_type_id}).amount == 0:
                    debug.log_cond(f"Issue: a {trainning_prerequisite_type_id} is required to build a {type_id}", DebugTopic.BUILD_ORDER_STATE)

                    # prepend the build order and wait for next step
                    self.build_order.add_prerequisit_for_current_build_command(trainning_prerequisite_type_id)
                    return False
        return True
    
    def get_worker_candidates(self) -> Units:
        return self._bot_object.workers.filter(lambda worker: (worker.is_collecting or worker.is_idle) and worker.tag not in self._bot_object.unit_tags_received_action)
    
    async def get_construction_position(self, type_id: UnitTypeId) -> Point2:
        # select building location
        if (self.wall_manager.is_structure_needed(type_id)):
            #  Assuming the first position is the highest chronological priority
            debug.log_cond(f"{type_id.name} needed")
            locations = self.wall_manager.where_structure_is_needed(type_id)
            location_checks = await self._bot_object.can_place(type_id, locations)
            for i in range(len(location_checks)):
                if location_checks[i]:
                    return locations[i]
            # All postions are blocked

        # find placement position based on type of structure
        if (type_id == UnitTypeId.SUPPLYDEPOT):
            near = behind_minerals(self._bot_object, self.expansion_townhalls[0])
            return await self._bot_object.find_placement(building = UnitTypeId.SUPPLYDEPOT, near = near)
        else:
            # WIP
            # everything else is built in the center of the base for now
            map_center = self._bot_object.game_info.map_center
            position_towards_map_center = self._bot_object.start_location.towards(map_center, distance=5)
            return await self._bot_object.find_placement(type_id, near=position_towards_map_center, placement_step=2)


    def premove_worker(self, position):
        # TODO
        pass

# TODO ===================================
"""
All of the rest of this file is in a sort of deprecated state. ie A lot of WIPs
to be completed
"""
class EconomyMediator(Mediator):
    def __init__(self, supervisors, townhalls) -> None:
        super().__init__()
        # leasable 
        self.supervisors = supervisors
        self.townhalls = townhalls

    # able to produce more and holds onto execess workers
    def add_townhall(self, townhall) -> None:
        self.townhalls.append(townhall)

    # Includes: Repair squads, Militia, Scout Manager, Production Manager, 
    def add_supervisor(self, supervisor) -> None:
        self.supervisors.append(supervisor)

    def request_workers() -> None:
        pass

class WorkerExchangeMediator(Mediator):
    #implements a mix of the mediator, command and observer design pattern
    def __init__(self, supervisors: List, townhalls: List) -> None:
        super().__init__()
        # leasable 
        self.supervisors = supervisors
        self.townhalls = townhalls
        
        # donators
        self.donators = set(supervisors + townhalls)
        self.pending_commands = []



    def notify(self, sender, command):
        # responds to 
        pass
            
    def add_townhall(self, townhall) -> None:
        self.townhalls.append(townhall)

    def add_supervisor(self, supervisor) -> None:
        self.supervisors.append(supervisor)

        
    def react_on():
        pass

    def promptDonators(self):
        best_bid: Union[Unit, int] = {"worker": None, "eta": None}
        bidder = None
        for donator in self.donators:
            bid = donator.update()

            if (best_bid == None or bid > best_bid):
                best_bid = bid
                bidder = donator

        bidder.donate_worker(bid.worker)


    def subscribe(self, s: WorkerDonationSubscriber):
        self.donators.add(s)

    def unsubscribe(self, s: WorkerDonationSubscriber):
        self.donators.remove(s)

class WorkerExchangeClient(WorkerDonationSubscriber):
    def __init__(self, bot_object: BotAI, worker_mediator: WorkerExchangeMediator) -> None:
        self.bot_object = bot_object
        self.worker_mediator = worker_mediator
        self.requests = []
    
    def request_worker(self, priority):
        command = RequestWorkerCommand(self.bot_object, self, self.worker_mediator, 10)
        self.worker_mediator.notify(self, command)

    def request_leased_worker(self):
        command = "request leased worker"
        self.worker_mediator.notify(self, command)

    def donate_worker(self, worker) -> Unit:
        return 
    
    def conscript_worker(self, PromisedWorker):
        pass
    
    def lease_worker(self, worker):
        command = "lease worker"
        self.worker_mediator.notify(self, command)
    
    def offer_worker(self, worker):
        command = "offer worker"
        self.worker_mediator.notify(self, command)


#TODO implement
class PromisedWorker():
    def __init__(self) -> None:
        pass

class WorkerDonationBid():
    def __init__(self, worker: Union[Unit, PromisedWorker], eta: float) -> None:
        self.worker: Union[Unit, PromisedWorker] = worker
        self.eta: float = eta 


class Subscriber(ABC):
    @abstractmethod
    def update(self, context):
        pass


class WorkerProducer(WorkerManager):
    pass

class WorkerCommand(ABC): 
    def __init__(self, bot_object: BotAI, invoker, exchange, priority) -> None:
        self._bot = bot_object
        self.invoker = invoker
        self.exchange = exchange
        self.priority = priority

    def set_priority(self, priority: int):
        self.priority = priority
    
    def place_command(self):
        self.exchange.enqueue_command(self)
    
    @abstractmethod
    def execute_command(self):
        pass

class RequestWorkerCommand(WorkerCommand):
    def __init__(self, bot_object: BotAI, invoker, exchange, priority) -> None:
        super().__init__(bot_object, invoker, exchange, priority)
    
    def execute_command(self):
        pass













