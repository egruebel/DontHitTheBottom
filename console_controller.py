from app_settings import AppSettings
from datetime import datetime
import threading
import time
#from enum import Enum

#class MessageType(Enum):
#    INFO = 0
#    WARNING = 1
#    ERROR = 2

class RoundRobinConsole:

    def __init__(self):
        self.message_queue = []

    def add_message(self, message):
        #[message text, message type, timestamp]
        self.message_queue.append([message, 0, datetime.now()])

    def add_warning(self, message):
        self.message_queue.append([message, 1, datetime.now()])

    def add_error(self, message, details):
        self.message_queue.append([message, 2, datetime.now()])

    def console_loop(self):
        while(True):
            #this needs to be done in 2 parts since you cant iterate an array that youre deleting from
            delete_list = []
            for m in range(len(self.message_queue)):
                if((datetime.now() - self.message_queue[m][2]).seconds > AppSettings.console_display_time):
                    delete_list.append(m)

            delete_list.reverse()

            for i in delete_list:
                self.message_queue.pop(i)

            time.sleep(AppSettings.console_display_time)

    def start_console(self):
        r = threading.Thread(target = self.console_loop)
        r.start()



