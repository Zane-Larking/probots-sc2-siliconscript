from sc2 import maps
from sc2.player import Bot, Computer
from sc2.main import run_game
from sc2.data import Race, Difficulty


from bot import CompetitiveBot


OpponentId = "siliconscript"

def load_bot():
    # Load bot
    competitive_bot = CompetitiveBot()
    # Add opponent_id to the bot class (accessed through self.opponent_id)
    competitive_bot.opponent_id = OpponentId

    return Bot(CompetitiveBot.RACE, competitive_bot)


run_game(maps.get("Abyssal Reef LE"), [
    load_bot(),
    Computer(Race.Protoss, Difficulty.Medium)
], realtime=True)