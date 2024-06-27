from typing import Dict, Union
from sc2.data import Race
from sc2.unit import Unit
from sc2.units import Units
from sc2.ids.unit_typeid import UnitTypeId


military_unit_types = set([
    UnitTypeId.MARINE,
    UnitTypeId.MARAUDER,
    UnitTypeId.REAPER,
    UnitTypeId.GHOST,
    UnitTypeId.HELLION,
    UnitTypeId.SIEGETANK,
    UnitTypeId.CYCLONE,
    UnitTypeId.WIDOWMINE,
    UnitTypeId.THOR,
    UnitTypeId.VIKING,
    UnitTypeId.MEDIVAC,
    UnitTypeId.LIBERATOR,
    UnitTypeId.RAVEN,
    UnitTypeId.BANSHEE,
    UnitTypeId.BATTLECRUISER,
    UnitTypeId.ZEALOT,
    UnitTypeId.STALKER,
    UnitTypeId.SENTRY,
    UnitTypeId.ADEPT,
    UnitTypeId.HIGHTEMPLAR,
    UnitTypeId.DARKTEMPLAR,
    UnitTypeId.IMMORTAL,
    UnitTypeId.COLOSSUS,
    UnitTypeId.DISRUPTOR,
    UnitTypeId.OBSERVER,
    UnitTypeId.WARPPRISM,
    UnitTypeId.PHOENIX,
    UnitTypeId.VOIDRAY,
    UnitTypeId.ORACLE,
    UnitTypeId.CARRIER,
    UnitTypeId.TEMPEST,
    UnitTypeId.MOTHERSHIP,
    UnitTypeId.QUEEN,
    UnitTypeId.ZERGLING,
    UnitTypeId.BANELING,
    UnitTypeId.ROACH,
    UnitTypeId.RAVAGER,
    UnitTypeId.HYDRALISK,
    UnitTypeId.LURKER,
    UnitTypeId.INFESTOR,
    UnitTypeId.SWARMHOSTMP,
    UnitTypeId.ULTRALISK,
    UnitTypeId.OVERSEER,
    UnitTypeId.MUTALISK,
    UnitTypeId.CORRUPTOR,
    UnitTypeId.BROODLORD,
    UnitTypeId.VIPER
]
)

static_defence_types = set([
    UnitTypeId.PLANETARYFORTRESS,
    UnitTypeId.MISSILETURRET,
    UnitTypeId.BUNKER,
    UnitTypeId.PHOTONCANNON,
    UnitTypeId.SHIELDBATTERY,
    UnitTypeId.SPINECRAWLER,
    UnitTypeId.SPORECRAWLER,
    UnitTypeId.NYDUSNETWORK,
    UnitTypeId.NYDUSCANAL
]
)

#  TODO add Zerg and Protoss
production_structures = set([
    UnitTypeId.PLANETARYFORTRESS,
    UnitTypeId.COMMANDCENTER,
    UnitTypeId.ORBITALCOMMAND,
    UnitTypeId.BARRACKS,
    UnitTypeId.FACTORY,
    UnitTypeId.STARPORT,
])

HAVERSTER_FOR_RACE: Dict[Race, UnitTypeId] = {
    Race.Terran: UnitTypeId.SCV, 
    Race.Protoss:UnitTypeId.PROBE, 
    Race.Zerg: UnitTypeId.DRONE
}

RACE_TOWNHALL = {
    Race.Protoss: UnitTypeId.NEXUS,
    Race.Terran: UnitTypeId.COMMANDCENTER,
    Race.Zerg: UnitTypeId.HATCHERY,
}

def filter_economy_units(units: Units) -> Units:
    return (unit for unit in units.of_type(HAVERSTER_FOR_RACE))

def filter_military_units(units: Units) -> Units:
    return (unit for unit in units.of_type(military_unit_types))

def filter_static_defence(units: Units) -> Units:
    return (unit for unit in units.of_type(static_defence_types))

def is_production_structure(structure: Unit):
    return structure.type_id in production_structures


UnitTag = int

def get_tag(unit: Union[Unit, UnitTag]) -> Union[UnitTag, None]:
    if isinstance(unit, Unit):
        return unit.tag
    if isinstance(unit, UnitTag):
        return unit  

def get_structure(building: Union[Unit, UnitTag]) -> Union[Unit, None]:
    """
    This is a helper function used by remove_building and has building
    Returns 'building' if it is apart of the wall or None otherwise.
    
    If 'building' is a unit_tag it will return the corresponding building
    Unit instance if it is apart of the wall or None otherwise.
    """
    
    assert isinstance(building, (Unit, UnitTag))

    if isinstance(building, Unit):
        return building
    elif isinstance(building, UnitTag):
        building_tag: UnitTag = building
        return self.structures.find_by_tag(building_tag)