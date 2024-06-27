from itertools import chain
import warnings
from bot.debug import Debug, DebugTopic
from sc2.bot_ai import BotAI
from sc2.constants import IS_CONSTRUCTING_SCV, TERRAN_STRUCTURES_REQUIRE_SCV, ABILITYID_TO_UNITTYPEID
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from enum import Enum

from typing import List, Union

from sc2.ids.upgrade_id import UpgradeId

debug: Debug
def is_production_ability(ability_id: AbilityId) -> bool:
    # Note Only works for Terran
    if ability_id in IS_CONSTRUCTING_SCV or ability_id in ABILITYID_TO_UNITTYPEID:
        return True
    return False

class BuildCommand():
    def __init__(self, bot_object: BotAI, type_id: Union[UnitTypeId, UpgradeId, AbilityId], supply: int, global_total: int, override_production: bool = False) -> None:
        self._bot_object = bot_object
        self.type_id: Union[UnitTypeId, UpgradeId, AbilityId] = type_id
        self.supply = supply
        self.global_total = global_total
        self.override_production = override_production

    @property
    def quota_is_met(self) -> bool:
        return self._bot_object.already_pending(self.type_id) + self._bot_object.structures.filter(lambda structure: structure.type_id == self.type_id).amount >= self.global_total

    @property
    def can_afford(self) -> bool:
        return self._bot_object.can_afford(self.type_id)
    
    @property
    def amount_left_to_produce(self):
        if isinstance(self.type_id, UnitTypeId):
            items = self._bot_object.structures.same_tech({self.type_id})
            return self.global_total - items.amount 
        if isinstance(self.type_id, UpgradeId):
            if self._bot_object.already_pending_upgrade(self.type_id) == 0:
                return 1
            return 0
        if isinstance(self.type_id, AbilityId):
            if is_production_ability(self.type_id):
                return self.amount_left_to_produce(ABILITYID_TO_UNITTYPEID[self.type_id])
            warnings.warn(f"AbilityId: {self.type_id.name} does not produce anything)")
            return 0
    
    @property
    def is_pending(self) -> bool:
        return self.supply <= self._bot_object.supply_workers and not self.quota_is_met

class BuildOrder():
    def __init__(self):
        # self._bot_object: BotAI = bot_object
        # should just be buildings
        self.build_queue: List[BuildCommand] = [
            # (UnitTypeId.SUPPLYDEPOT, 13),
            # (UnitTypeId.BARRACKS, 15)
            ]
        self.is_overiding = True
        self.progress = 0
    
    def _add_build_command(self, build_command: BuildCommand):
        self.build_queue.append(build_command)
    
    def add_building(self, type_id: UnitTypeId, supply: int, global_total: int, override_production: bool = False):
        self._add_build_command(BuildCommand(Builds._bot_object, 
            type_id, supply, global_total, override_production))
    
    def add_prerequisit_for_current_build_command(self, prerequisite_type_id):
        self.build_queue.insert(self.progress, BuildCommand(Builds._bot_object, prerequisite_type_id, self.build_queue[self.progress].supply, 1, self.build_queue[self.progress].override_production))

    def update(self) -> bool:
        if self.is_finished:
            # NOTE: I'm not sure what the return value is best suited for this case
            
            debug.set_text("Build Order", "Finished")
            return False
            #  From this point on, once a build command is added it will
            #  corespond to the present value of progress 
        debug.set_text("Build Order", f"{self.current_build_command.type_id}")
        if self.build_queue[self.progress].quota_is_met:
            self.advance_build()
            return True
        return False

    @property
    def current_build_command(self) -> Union[BuildCommand, None]:
        return self.build_queue[self.progress]

    def advance_build(self):
        self.progress += 1
        
        if self.is_finished:
            self.is_overiding = False
            return
        self.is_overiding = self.build_queue[self.progress].override_production
    
    @property
    def is_finished(self) -> bool:
        return self.progress >= len(self.build_queue) 
    
    @property
    def has_pending(self) -> bool:
        if self.is_finished:
            return False
        
        build_command = self.build_queue[self.progress]
        if build_command.supply <= Builds._bot_object.supply_workers:
            debug.log_cond(f"Build order Supply condition met supply condition ({self.current_build_command.supply} <= worker supply({Builds._bot_object.supply_workers})", topic=DebugTopic.BUILD_ORDER_STATE)
            return True
        
        return False
    
    @property
    def pending_build_command_type_ids(self) -> List[Union[UnitTypeId, UpgradeId, AbilityId]]:
        remaining_build_commands: List[BuildCommand] = self.build_queue[self.progress:]
        print(remaining_build_commands)
        return list(chain(*[[bc.type_id]*bc.amount_left_to_produce for bc in remaining_build_commands if bc.is_pending]))

class Builds():
    """
    builds are based on worker supply
    """
    _bot_object:BotAI = None

    @staticmethod
    def set_bot_ai(_bot_object):
        global debug
        debug = Debug(_bot_object)
        Builds._bot_object = _bot_object

    @staticmethod
    def default() -> BuildOrder:
        build_order = BuildOrder()

        build_order.add_building( 
            UnitTypeId.SUPPLYDEPOT, 13, 1, True)
        build_order.add_building(
            UnitTypeId.BARRACKS, 15, 1, True)
        build_order.add_building(
            UnitTypeId.REFINERY, 16, 1, True)
        build_order.add_building(
            UnitTypeId.ORBITALCOMMAND, 19, 1, True)
        build_order.add_building(
            UnitTypeId.COMMANDCENTER, 19, 2)
        
        return build_order

    # Add a Builder creational pattern