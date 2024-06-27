
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Callable, Dict, TypeVar

from sc2.bot_ai import BotAI

T = TypeVar("T")

DELAY = 2.0

class Cacheable(ABC):
    
    def __init__(self) -> None:
        super().__init__()
        self.cache: Dict[Callable[[Cacheable], T], T] = dict()
        

    @property 
    @abstractmethod
    def _frame(self) -> int:
        ...



class property_generic_cache_once_per_frame(property):
    """This decorator caches the return value for one game loop,
    then clears it if it is accessed in a different game loop.
    Only works on properties of the bot object, because it requires
    access to self.state.game_loop

    This decorator compared to the above runs a little faster, however you should only use this decorator if you are sure that you do not modify the mutable once it is calculated and cached.

    Copied and modified from https://tedboy.github.io/flask/_modules/werkzeug/utils.html#cached_property
    # """

    def __init__(self, func: Callable[[Cacheable], T], name=None):
        # pylint: disable=W0231
        self.__name__ = name or func.__name__
        self.__frame__ = f"__frame__{self.__name__}"
        self.func = func

    def __set__(self, obj: Cacheable, value: T):
        obj.cache[self.__name__] = value
        obj.cache[self.__frame__] = obj._frame

    def __get__(self, obj: Cacheable, _type=None) -> T:
        value = obj.cache.get(self.__name__, None)
        obj_frame = obj._frame
        if value is None or obj.cache[self.__frame__] < obj_frame:
            value = self.func(obj)
            obj.cache[self.__name__] = value
            obj.cache[self.__frame__] = obj_frame
        return value

