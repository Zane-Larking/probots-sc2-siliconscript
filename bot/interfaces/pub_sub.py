from abc import ABC, abstractmethod

from typing import TYPE_CHECKING, Any, Dict, Generator, Iterable, List, Optional, Set, Tuple, Union


class Subscriber(ABC):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def update(self, context):
        pass

class publisher():
    
    def __init__(self) -> None:
        super().__init__()
        self.subscribers: List[Subscriber] = []

    def subscribe(self, s: Subscriber):
        self.subscribers.append(s)
    
    def subscribe(self, s: Subscriber):
        self.subscribers.remove(s)

    def notify_subscribers(self, context):
        for s in self.subscribers:
            s.update(context)