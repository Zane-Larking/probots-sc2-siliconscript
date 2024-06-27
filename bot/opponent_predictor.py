


from sc2.game_data import Cost
from sc2.units import Units
from sc2.bot_ai import BotAI
from bot.typeHelper import filter_economy_units, filter_military_units , filter_static_defence

# import enum

# MANIFEST_COMMAND = enum.Enum("Manifest_command", [("KILL": 0), ("DISCOVER":
# 1), ("PREDICT": 2)])


class OpponentPredictor():


    def __init__(self, bot_object: BotAI):
        self._bot_object: BotAI = bot_object
        self.opponents_units: Units = Units([], bot_object)
        self.opponents_upgrades = set()

    def update_manifest(self, units: Units):
        self.opponents_units |= units

    def update_upgrades(self):
        """
        add to list of upgrades
        """
        # self.opponents_upgrades 

    def appraise(self, units: Units):
        """
        This function returns a heuristic for the worth of a subset  of the
        opponents units
        returns the mineral and vespene costs for known units

        Further improvements can be made:
        - extrapolate with covariance
        """
        appraisal = 0
        for cost in (self._bot_object.calculate_unit_value(unit) for unit in units):
            appraisal += cost
        return appraisal
    
    def appraise_economy(self):
        """
        This function returns a heuristic for the worth of the opponents economy

        Further improvements can be made:
        - Consider gold mineral fields
        - factoring in available mineral field and their proximity to the
            opponents townhalls
        - extrapolate with covariance
        """
        economy_units = filter_economy_units(self.opponents_units)
        appraisal = self.appraise(economy_units)
        return appraisal
    
    def appraise_army(self):

        military_units = filter_military_units(self.opponents_units)
        appraisal = self.appraise(military_units)
        return appraisal
    
    def appraise_static_defence(self):

        static_defence = filter_static_defence(self.opponents_units)
        appraisal = self.appraise(static_defence)
        return appraisal
    

    # TODO
    # def appraise_infrastructure(self, units: Units):
    #     pass
    
