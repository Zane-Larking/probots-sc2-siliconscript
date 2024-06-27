import enum
from typing import Dict, Set, Tuple, TypedDict, Union
from sc2.bot_ai import BotAI
from sc2.client import Client
from sc2.position import Point2, Point3

class DebugMsg(TypedDict):
    text: str 
    pos: Point2
    color: Point2 
    size: int

class DebugTopic(enum.Enum):
    DEFAULT = 1
    ECONOMY_EVENTS = 2
    UNIT_PERSISTANCE_TEST = 3
    BUILD_ORDER_STATE = 4
    BALANCE = 5

class Debug():
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Debug, cls).__new__(cls)
        return cls.instance
  
    def __init__(self, bot: Union[BotAI, None]) -> None:
        self.bot_object = bot
        self.client: Client = bot.client
        self.debug_msgs: Dict[str, Dict[str, DebugMsg]] = dict()

        self.debug_screen_pos = Point2((0, 0.2))
        self.enabled_topics: Set[DebugTopic] = {DebugTopic.DEFAULT}

    def log_cond(self, *values: object, topic: DebugTopic = DebugTopic.DEFAULT, sep: Union[str, None] = " ", end: Union[str, None] = "\n") -> None:

        assert isinstance(topic, DebugTopic)

        if topic in self.enabled_topics:
            print(*values, sep = sep, end = end)

    def enable_topic(self, topic):
        self.enabled_topics.add(topic)

    def disable_topic(self, topic):
        if topic in self.enabled_topics:
            self.enabled_topics.remove(topic)

    def set_text(self, msg_name: str, text: str, pos: Point2 = None, color: Point3 = None, size: int = 8):
       if pos == None:
           pos = self.debug_screen_pos

       self.debug_msgs.update({msg_name: {'text': text, 'pos': pos, 'color': color, 'size': size}})

    def draw_text(self):
        pos: Point2 = Point2((0,0.3))
        msg: Dict[str, DebugMsg]
        for key, msg in self.debug_msgs.items():
            if (msg.get("pos")):
               pos = msg.get("pos")
            self.client.debug_text_screen(text=key+": "+msg.get("text"), pos=msg.get("pos"), color=msg.get("color"), size=msg.get("size"))
            pos = Point2((pos.x, pos.y + msg.get("size") + 2))