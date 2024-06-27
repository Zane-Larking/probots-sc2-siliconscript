from sc2.bot_ai import BotAI
from bot.build_order import BuildOrder
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from bot.typeHelper import is_production_structure
from bot.economy_manager import WorkerManager

from typing import TYPE_CHECKING, Any, Dict, Generator, Iterable, List, Optional, Set, Tuple, Union

class ConstructionManager:
    def __init__(self, bot_ai: BotAI, build_order: BuildOrder) -> None:
        self.bot_ai = bot_ai
        self.build_order = build_order
        self.production_potential = 0
        self.worker_manager: WorkerManager = WorkerManager()

    def update_production_potential(self):
        #  calculates the amount of supply that can be used in the next 20
        #  seconds if every capable production structure were to be producing
        production_structures = self.bot_ai.structures.filter(is_production_structure)



    

    def produce(self):

        if (self.bot_ai.supply_used + self.production_potential > self.bot_ai.supply_cap):
            self.build_supply()

        if self.build_order.has_pending(self.bot_ai.supply_used):
            self.service_build_order()
            self.update_production_potential()

    def service_build_order(self, structure, placement_position):
        pass

    async def build_supply(self, priority: int):
        # request worker
        worker = self.worker_manager.request_worker(priority)
        
        if worker:
            map_center = self.bot_ai.game_info.map_center
            position_towards_map_center = self.bot_ai.start_location.towards(map_center, distance=5)
            placement_position = await self.bot_ai.find_placement(UnitTypeId.SPAWNINGPOOL, near=position_towards_map_center, placement_step=1)
            # Placement_position can be None
            if placement_position:
                build_worker = worker.closest_to(placement_position)
                build_worker.build(UnitTypeId.SPAWNINGPOOL, placement_position)
        