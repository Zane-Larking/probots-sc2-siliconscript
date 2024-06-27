
from bot.interfaces.mediator import Mediator
from bot.enums.game_focus import Focus
from bot.build_order import Builds


from enum import Enum




class GamePlanEvent(Enum):
    REQUEST_REDICISION = 1
    BUILD_ORDER_COMPLETE = 2
    TRANSITION = 3


class GamePlan(Mediator):
    def __init__(self, starting_focus: Focus) -> None:
        self.goal: Focus = starting_focus
        self._decision_is_pending = False
        self.build_order = Builds.default()


    def notify(self, sender, event):
        if event == "reconsider":
            self.reconsider()

    def decision_is_pending(self):
        return self._decision_is_pending

    # TODO
    def reconsider(self):
        """
        re-evaluate the focus and/or build order when new information is revealed
        about the opponent or when damage is sustained. 
        """
        pass
