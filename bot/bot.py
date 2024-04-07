from sc2.bot_ai import BotAI, Race
from sc2.data import Result


from bot import OpponentPredictor, EconomyManager, MilitaryManager


from enum import Enum

class Goals(Enum):
    BALANCED = 1
    ECO = 2
    TECH = 3
    MILITARY = 4

class CompetitiveBot(BotAI):
    NAME: str = "SiliConscript"
    """This bot's name"""

    RACE: Race = Race.Terran
    """This bot's Starcraft 2 race.
    Options are:
        Race.Terran
        Race.Zerg
        Race.Protoss
        Race.Random
    """

    async def on_start(self):
        """
        This code runs once at the start of the game
        Do things here before the game starts
        """
        print("Game started")

        self.units
        self.OP = OpponentPredictor(self)

        if (self.OP.military):
            pass

        self.EM = EconomyManager(self, game_plan)
        self.MM = MilitaryManager(self, game_plan)

        self.EM.init_base(self.townhalls[0])


    async def on_step(self, iteration: int):
        """
        This code runs continually throughout the game
        Populate this function with whatever your bot should do!
        """
        self.EM.operate()
        self.MM.operate()

    async def on_end(self, result: Result):
        """
        This code runs once at the end of the game
        Do things here after the game ends
        """
        print("Game ended.")
