from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId

class BuildOrder():
    def __init__(self, bot_object: BotAI):
        self._bot_object: BotAI = bot_object
        self.queue = [
            UnitTypeId.SCV, 
            UnitTypeId.SUPPLYDEPOT,
            UnitTypeId.SCV,
            UnitTypeId.SCV,
            UnitTypeId.BARRACKS
            ]

    #TODO
    def transition_condition_met(self):
        return False
        
    def next_building(self):
        return self.queue[0]