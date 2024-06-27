from typing import List, Union
from sc2.bot_ai import BotAI
from sc2.unit import Unit
from sc2.units import Units


class WorkerManager():
    def __init__(self, bot_object: BotAI, workers: Union[List[Unit], Units]) -> None:
        self._bot_object = bot_object
        self.workers: Units = Units(workers, self._bot_object) 
        self.idle_workers: Units = Units([], self._bot_object)