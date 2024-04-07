from sc2.unit import Unit
from sc2.units import Units
from sc2.ids.unit_typeid import UnitTypeId


military_unit_types = set(
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
)

static_defence_types = set(
    UnitTypeId.PLANETARYFORTRESS,
    UnitTypeId.MISSILETURRET,
    UnitTypeId.BUNKER,
    UnitTypeId.PHOTONCANNON,
    UnitTypeId.SHIELDBATTERY,
    UnitTypeId.SPINECRAWLER,
    UnitTypeId.SPORECRAWLER,
    UnitTypeId.NYDUSNETWORK,
    UnitTypeId.NYDUSCANAL
)


economy_unit_types = set(
    UnitTypeId.SCV, 
    UnitTypeId.PROBE, 
    UnitTypeId.DRONE
    )

def filter_economy_units(units: Units) -> Units:
    return (unit for unit in units.same_unit(economy_unit_types))

def filter_military_units(units: Units) -> Units:
    return (unit for unit in units.same_unit(military_unit_types))

def filter_static_defence(units: Units) -> Units:
    return (unit for unit in units.same_unit(static_defence_types))
