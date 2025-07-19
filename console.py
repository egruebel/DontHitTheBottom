from console_controller import RoundRobinConsole
from enum import Enum

class MessageType(Enum):
    INFO = 0
    WARNING = 1
    ERROR = 2

def init():
    global dhtb_console
    dhtb_console = RoundRobinConsole()
    dhtb_console.start_console()

