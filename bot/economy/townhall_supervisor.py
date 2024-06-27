from sc2.bot_ai import BotAI, Race
from sc2.unit import Unit
from sc2.units import Units

class TownhallSupervisor():
    def __init__(self, bot_object: BotAI, townhall: Unit, workers: Units):
        self._bot_object: BotAI = bot_object
        self.townhall: Unit = townhall
        self.workers: Units = workers or Units([], self._bot_object)

        # self.economy_mediator: EconomyMediator = EconomyMediator()

    def manage_harvesting():
        pass


    
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

class MacroTownhallSupervisor(TownhallSupervisor):
    def __init__(self, bot_object: BotAI, townhall: Unit, workers: Units):
        super().__init__(bot_object, townhall, workers)

class ExpansionTownhallSupervisor(TownhallSupervisor):
    def __init__(self, bot_object: BotAI, townhall: Unit, workers: Units):
        super().__init__(bot_object, townhall, workers)