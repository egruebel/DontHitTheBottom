from console_controller import RoundRobinConsole
from enum import Enum
from datetime import datetime

class MessageType(Enum):
    INFO = 0
    WARNING = 1
    ERROR = 2
    DEBUG = 3

def init():
    global dhtb_console
    dhtb_console = RoundRobinConsole()
    dhtb_console.start_console()

