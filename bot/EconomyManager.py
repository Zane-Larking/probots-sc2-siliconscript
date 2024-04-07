from sc2.bot_ai import BotAI
import BuildOrder
import WallManager
from sc2.unit import Unit
import numpy as np

from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from typing import TYPE_CHECKING, Any, Dict, Generator, Iterable, List, Optional, Set, Tuple, Union

SUPPLY_CONST = 8

def radial_offset(pos: Union[Unit, Point2, Tuple[float, float]], center: Union[Unit, Point2, Tuple[float, float]], radius: float):
    vector = pos - center
    angle = np.arctan(vector) 
    return Point2({
        "x": center.x + radius * np.cos(angle), 
        "y": center[1] + radius * np.sin(angle)
        })

def behind_minerals(bot_object: BotAI, townhall: Unit):

    mineral_fields = bot_object.mineral_field.closer_than(8, townhall)
    return radial_offset(mineral_fields.center, townhall.position, 2)
    

class EconomyManager:
    def __init__(self, bot_object, game_plan):
        self._bot_object: BotAI = bot_object
        self.townhalls = [] # townhalls at mineralfields
        self.macro_orbitals = [] # additional macro townhalls

        self.wall_manager: WallManager
        self.build_order: BuildOrder = game_plan.build_order


        # self.focus

    
    def assign_wall_manager(self, wall_manager: WallManager):
        self.wall_manager = wall_manager

        
    def init_townhall(self, townhall: Unit):
        self.townhalls.append(townhall)

    def operate(self):

        if not(self.build_order.is_overiding()):
            # ensure not supply blocked
            townhalls = self._bot_object.units.tags_in(self.townhalls)
            if self._bot_object.supply_left < SUPPLY_CONST * townhalls:
                if self._bot_object.can_afford(UnitTypeId.SUPPLYDEPOT):
                    needed_structure = self.wall_manager.structure_needed()
                    if (needed_structure == None):
                        building_location = self.wall_manager.vacant_spaces().peak()
                    else:
                        building_location = self._bot_object.find_placement(UnitTypeId.SUPPLYDEPOT, behind_minerals(self._bot_object, self.townhalls[0]))
                    
                    builder = self._bot_object.workers.gathering.closest_to(building_location)

                    self._bot_object.build(UnitTypeId.SUPPLYDEPOT, building_location, build_worker=builder, random_alternative=False)
            # produce production
            # expand
            # produce units
            # carry out build order
        self.build_order.execute()


    def set_alert_level(self, level):
        pass