from typing import Any, List, Self

from sc2.units import Units


class UnitUpdater(dict):
    __instance__ = None

    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        if cls.__instance__ == None:
            return super().__new__(*args, **kwargs)
        return cls.__instance__
    
    def __init__(self) -> None:
        super().__init__()

        subscribers: List[Units] = []

    def __setitem__(self, key: Any, value: Any) -> None:
        return super().__setitem__(key, value)
    
    def __getitem__(self, key: Any) -> Any:
        return super().__getitem__(key)
    
    def subscribe():
