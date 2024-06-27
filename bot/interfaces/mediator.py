from abc import ABC, abstractmethod

class Mediator(ABC):
    @abstractmethod
    def notify(self, sender, event):
        pass

class Component(ABC):
    def __init__(self, mediator: Mediator) -> None:
        super().__init__()
        self.mediator = mediator
