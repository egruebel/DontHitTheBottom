from app_settings import AppSettings
from datetime import datetime
import threading
import time
import primitives
#from enum import Enum

#class MessageType(Enum):
#    INFO = 0
#    WARNING = 1
#    ERROR = 2
#    DEBUG = 3

class ConsoleMessage:

    def __init__(self, text, type):
        self.text = text
        self.type = type
        self.timestamp = datetime.now()

    @property
    def color(self):
        if(self.type == 1):
            return primitives.Color.YELLOW
        elif(self.type == 2):
            return primitives.Color.RED
        else:
            return primitives.Color.WHITE

class RoundRobinConsole:

    def __init__(self):
        self.message_queue = []

    def add_message(self, message):
        #[message text, message type, timestamp]
        self.message_queue.append(ConsoleMessage(message, 0))
        #self.message_queue.append([message, 0, datetime.now()])

    def add_warning(self, message):
        self.message_queue.append(ConsoleMessage(message, 1))
        #self.message_queue.append([message, 1, datetime.now()])

    def add_error(self, message, details):
        self.message_queue.append(ConsoleMessage(message, 2))
        #self.message_queue.append([message, 2, datetime.now()])

    def add_debug(self, message):
        self.message_queue.append(ConsoleMessage(message, 3))
        #self.message_queue.append([message, 3, datetime.now()])

    def console_loop(self):
        while(True):
            now = datetime.now()
            self.message_queue = [x for x in self.message_queue if ((now - x.timestamp).seconds < AppSettings.console_display_time)]
            time.sleep(AppSettings.console_display_time)

    def start_console(self):
        r = threading.Thread(target = self.console_loop)
        r.start()



