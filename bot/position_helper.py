from typing import TYPE_CHECKING, Any, Dict, Generator, Iterable, List, Optional, Set, Tuple, Union
from sc2.unit import Unit
from sc2.position import Point2
from sc2.bot_ai import BotAI

import math

def radial_offset(pos: Union[Unit, Point2, Tuple[float, float]], center: Union[Unit, Point2, Tuple[float, float]], radius: float):
    vector: Point2 = pos - center
    angle = math.atan(vector.y/ vector.x) 
    return Point2((center.x + radius * math.cos(angle),  center.y + radius * math.sin(angle)))

def behind_minerals(bot_object: BotAI, townhall: Unit):

    mineral_fields = bot_object.mineral_field.closer_than(8, townhall)
    return radial_offset(mineral_fields.center, townhall.position, 9)