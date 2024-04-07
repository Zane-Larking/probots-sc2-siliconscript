from sc2.bot_ai import BotAI, Race
from sc2.unit import Unit
from sc2.units import Units

class BaseEconomySupervisor():
    def __init__(self, bot_object: BotAI, townhall):
        self._bot_object: BotAI = bot_object
        self.townhall: Unit = townhall
        self.workers: Units = Units()
    
    def add_worker(self, workers):
        self.workers += workers

    def remove_workers(self, workers: Units):
        self.workers -= workers

    def get_workers(self, workers: Units):
        return self.workers.__and__(workers)

    def get_worker_count(self) -> int:
        self.workers.amount()
    
        
    def needs_workers(self) -> bool:
        return self.get_worker_count() <= 2 * self._bot_object.mineral_field.closer_than(6, self.townhall)
    
    #TODO
    def request_worker(self):
        pass