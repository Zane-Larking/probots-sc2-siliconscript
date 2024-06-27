from sc2 import maps
from sc2.player import Bot, Computer
from sc2.main import run_game
from sc2.data import Race, Difficulty


from bot.bot import SiliConscriptBot


OpponentId = "siliconscript"

def load_bot():
    # Load bot
    competitive_bot = SiliConscriptBot()
    # Add opponent_id to the bot class (accessed through self.opponent_id)
    competitive_bot.opponent_id = OpponentId

    return Bot(SiliConscriptBot.RACE, competitive_bot)


run_game(maps.get("Abyssal Reef LE"), [
    load_bot(),
    Computer(Race.Protoss, Difficulty.Medium)
], realtime=True)