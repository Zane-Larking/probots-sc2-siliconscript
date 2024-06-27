import warnings
from typing import Any, Callable, Dict, FrozenSet, List, Set, Tuple, TypeVar, Union

from sc2.bot_ai import BotAI
from sc2.dicts.generic_redirect_abilities import GENERIC_REDIRECT_ABILITIES
from sc2.dicts.unit_abilities import UNIT_ABILITIES
from sc2.game_info import Ramp
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

from bot.worker_manager import WorkerManager
from bot.general_cache import Cacheable, property_generic_cache_once_per_frame
from bot.typeHelper import get_structure, get_tag, UnitTag


# Note Only Works For Terran ATM
# Turrets and sensor towers omitted as there is a chance I fully block of the wall. 
SMALL_BUILDINGS: Set[UnitTypeId] = {
    UnitTypeId.SUPPLYDEPOT
    # , UnitTypeId.MISSILETURRET
}

# 
MEDIUM_BUILDINGS: Set[UnitTypeId] = {
    UnitTypeId.BARRACKS,
    UnitTypeId.FACTORY,
    UnitTypeId.STARPORT,
    UnitTypeId.ENGINEERINGBAY,
    UnitTypeId.ARMORY,
    UnitTypeId.GHOSTACADEMY,
}

T = TypeVar("T")

class Wall(Cacheable):
    """
    A wall stores positions for where structures and units (WIP) should be along
    with the tags for existing units and structures.

    It establishes a proxy to the BotAI.all_units Units attribute utilising a
    cache implementation.
    """
    def __init__(self, bot_object: BotAI, start_point, end_point, ramp: Ramp = None) -> None:
        super().__init__()
        self._unit_tags: List[UnitTag] = []
        self._structure_tags: List[int] = []
        self._bot_object: BotAI = bot_object
        self.ramp = ramp
        self.start_point = start_point
        self.end_point = end_point

        self.repair_squad: WorkerManager
        self.structure_from_position: Dict[Point2, UnitTag] = dict()
        self.depot_placement_positions: FrozenSet[Point2]
        self.barracks_placement_positions: FrozenSet[Point2]



        assert ramp, "Non-ramp walls are not implemented"

        if ramp:
            self.depot_placement_positions = ramp.corner_depots
            self.barracks_placement_positions = {ramp.barracks_in_middle}

        else:
            # TODO
            self.determine_placements()
  
    @property 
    def _frame(self) -> int:
        return self._bot_object.state.game_loop
          
    @property_generic_cache_once_per_frame
    def units(self):
        return self._bot_object.units.tags_in(self._unit_tags)

    @property_generic_cache_once_per_frame
    def structures(self):
        return self._bot_object.structures.tags_in(self._structure_tags)

    @property
    def all_units(self):
        return self.units + self.structures
    
    @property
    def depots(self) -> Units:
        """
        returns all depots in the wall
        """
        # Note I may change depot_placement_positions to include turrets
        return self.structures.same_tech({UnitTypeId.SUPPLYDEPOT})
    
    @property
    def medium_structures(self) -> Units:
        """
        returns all medium sized buildings in the wall (see SMALL_BUILDINGS in wall_managers.py).
        """
        return self.structures.same_tech(MEDIUM_BUILDINGS)

    
    @property
    def structure_positions(self) -> Set[Point2]:
        """
        returns a set of all building positions in the wall
        """
        return self.depot_placement_positions | self.barracks_placement_positions

    
    @property
    def filled_structure_positions(self) -> Set[Point2]:
        """
        returns a set of all positions in the wall filled by a correct building
        """
        return self.structure_from_position.keys()
    
    @property
    def empty_structure_positions(self) -> Set[Point2]:
        """
        returns a set of all positions in the wall not filled by a correct building
        this is kind of useless as it takes a lot to determine what building
        goes in these positions.
        Example:
        wall_supervisor: WallSupervisor
        empty_positions = wall_supervisor.empty_building_positions()
        [empty_postion for empty_potion in empty_positions if empty_position in wall_supervisor.barracks_placement_position]
        

        """
        return self.structure_positions - self.filled_structure_positions
    

        

        

    def add_structure(self, structure: Union[Unit, UnitTag]) -> None:
        structure_tag: UnitTag = get_tag(structure)
        structure_unit: Unit = get_structure(structure)

        if not (structure_tag in self._structure_tags):
            self._structure_tags.append(structure_tag)

        self.structure_from_position[structure_unit.position] = structure_tag

    def remove_structure(self, structure: Union[Unit, UnitTag]) -> None:
        """
        """
        structure_tag: UnitTag = get_tag(structure)

        if structure_tag in self._structure_tags:
            self._structure_tags.remove(structure_tag)

        for pos, tag in self.structure_from_position.items():
            if tag == structure_tag:
                del self.structure_from_position[pos]
                return

        
    def has_building(self, structure: Union[Unit, UnitTag]) -> bool:
        """
        Returns True if the wall contains 'structure' or False otherwise.

        Does not refresh Unit lists (Unit could have been destroyed/died; this
        method does not care)
        """
        # return get_structure(structure) != None
        return get_tag(structure) in self._structure_tags

      
    # TODO
    def determine_placements(self):
        """
        # Unimplemented
        # """
        pass

    def is_complete(self) -> bool:
        """
        Returns True if all buildings positions have been filled or False otherwise.
        
        To be accurate this WallSupervisor needs to remove buildings that have either flown away or
        have been distroyed. 
        """
        # The following method is not robust to enemy obstructions
        # return not (any([
        #     ...(self._bot_object.can_place(UnitTypeId.SUPPLYDEPOT, self.depot_placement_positions)),
        #         self._bot_object.can_place_single(UnitTypeId.BARRACKS, self.barracks_placement_position)
        #     ])) 

        return len(set(self.structure_positions) - set(self.filled_structure_positions)) == 0
    
    def position_filled(self, pos: Point2) -> bool:
        """
        Returns true if the position is filled by a building added by this
        WallSupervisor or False otherwise.

        The position could still have been filled/blocked by the opponent or
        poor building placement.
        """
        return pos in self.structure_from_position.keys()

    def missing_buildings(self) -> Dict[UnitTypeId, List[Point2]]:

        position_dict: Dict[UnitTypeId , List[Point2]] = dict()

        medium_list = [pos for pos in self.barracks_placement_positions if not(self.position_filled(pos))]

        for building_type_id in MEDIUM_BUILDINGS:
            position_dict[building_type_id] = medium_list

        small_list = [pos for pos in self.depot_placement_positions if not(self.position_filled(pos))]

        for building_type_id in SMALL_BUILDINGS:
            position_dict[building_type_id] = small_list

        return position_dict


    def where_structure_is_needed(self, type_id: UnitTypeId) -> List[Point2]:
        """
        Returns True if a building with the UnitTypeId 'type_id' is needed to
        finish the wall.  
        """
        for key, value in self.missing_buildings().items():
            if type_id == key:
                return value
        return []
    
    def is_structure_needed(self, type_id: UnitTypeId) -> bool:
        """
        Returns True if a building with the UnitTypeId 'type_id' is needed to
        finish the wall.  
        """

        return len(self.where_structure_is_needed(type_id)) > 0

    # only applicable to Terran structures
    def lift_structure(self, unit: Unit):
        """
        Remove from position dict and issue a Ability.LIFT command 
        """
        
        assert unit.is_structure, "Unit is not a structure"
        assert unit.type_id in {UnitTypeId.BARRACKS, UnitTypeId.FACTORY, UnitTypeId.STARPORT, UnitTypeId.COMMANDCENTER, UnitTypeId.ORBITALCOMMAND}, f"{unit.type_id.name} can not be lifted"
        # Equivalent to above
        # assert AbilityId.LIFT in list(map(lambda x:
        # GENERIC_REDIRECT_ABILITIES.get(x, None),
        # UNIT_ABILITIES(unit.type_id)))

        self.structure_from_position.pop(unit.position)

        unit(AbilityId.LIFT)





    

class WallManager():
    def __init__(self, bot_object: BotAI):
        self._bot_object: BotAI = bot_object
        self.walls: List[Wall] = []
        bot_object.main_base_ramp = self._bot_object.main_base_ramp


        self.wall_for_position: Dict[Point2, Wall] = dict()

    @property
    def depots(self):
        depots: Units = Units([], self._bot_object)
        for wall in self.walls:
            depots.extend(wall.depots)
        return depots
    
    @property
    def structures(self):
        structures = []
        for wall in self.walls:
            structures += wall.structures
        return structures

    def add_wall(self, start_position, end_position, ramp = None):
        wall = Wall(self._bot_object, start_position, end_position, ramp)
        for pos in wall.structure_positions:
            self.wall_for_position[pos] = wall
        self.walls.append(wall)
    
    def remove_wall(self, wall):
        self.walls.remove(wall)
    
    
    # External facing methods

    def is_structure_needed(self, type_id: UnitTypeId):
        return any([wall.is_structure_needed(type_id) for wall in self.walls])
            
    def where_structure_is_needed(self, type_id: UnitTypeId) -> List[Point2]:
        positions = []
        for wall in self.walls:
            positions += wall.where_structure_is_needed(type_id)
        return positions
    
    def perform_border_patrol(self):
        # Raise depos when enemies are nearby
        for depot in self.depots.ready:
            for unit in self._bot_object.enemy_units:
                if unit.distance_to(depot) < 15:
                    break
            else:
                depot(AbilityId.MORPH_SUPPLYDEPOT_LOWER)

        # Lower depos when no enemies are nearby
        for depot in self._bot_object.structures(UnitTypeId.SUPPLYDEPOTLOWERED).ready:
            for unit in self._bot_object.enemy_units:
                if unit.distance_to(depot) < 10:
                    depot(AbilityId.MORPH_SUPPLYDEPOT_RAISE)
                    break

    def handle_structure_detroyed(self, unit_tag: UnitTag):
        for wall in self.walls:
            if wall.has_building(unit_tag):
                wall.remove_structure(unit_tag)
