import socket
import threading
import time
import random
from app_settings import AppSettings
import console
from io_device import IODevice

class EchoSounder(IODevice):

    def __init__(self, broadcast_port, receive_callback, connection_callback):
        self.port = broadcast_port
        self.receive_callback = receive_callback
        self.connection_callback = connection_callback
        self._acquiring = False
        self._kill = threading.Event()
        self._reader = threading.Thread()

        self.depth: float
        self.sound_velocity: float
        self.keel_depth: int
        self.set_defaults()

        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) # UDP
        self.client.settimeout(8)
        # Enable broadcasting mode
        self.client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def acquiring(self, status = True):
        if(self._acquiring != status):
            #the state of the IO has changed
            self._acquiring = status
            #there's been a disconnect set all of the output params to their defaults
            if(status == False):
                self.set_defaults()
                self.receive_callback(self.depth, self.keel_depth, self.sound_velocity)
            self.connection_callback(status)
        return self._acquiring
    
    def kill(self):
        #this will kill the read thread so we can dispose of the object
        self._kill.set()
        #this will block until the thread is released
        self._reader.join()
        self.acquiring(False)

    def set_defaults(self):
        self.depth = None
        self.sound_velocity = AppSettings.echosounder_default_sv
        self.keel_depth = 5

    def sim(self, rand_coeff, sounding_interval_s):
        while not self._kill.is_set():
            self.acquiring(True)
            #add a random value between -X and +X to make the bottom change
            self.depth = self.depth + random.uniform((-1 * rand_coeff), rand_coeff)
            self.receive_callback(self.depth, self.keel_depth, self.sound_velocity)
            time.sleep(sounding_interval_s)
        self.acquiring(False)
        return
            
    def start_simulate(self, start_depth_m, rand_coeff, sounding_interval_s):
        self.depth = start_depth_m
        self._reader = threading.Thread(target=self.sim, args = (rand_coeff, sounding_interval_s))
        self._reader.start()

    def connect(self):
        #open the UDP port and begin collecting bits
        self.client.bind(("", self.port))
        data =''
        #run continuously until the thread is killed by some external call
        while not self._kill.is_set():
            try:
                data,address = self.client.recvfrom(4000)
            except socket.timeout as e:
                self.acquiring(False)
                console.dhtb_console.add_message('echosounder timeout')
            except Exception as e:
                self.acquiring(False)
                console.dhtb_console.add_error("exception in echosounder", e)
            else:
                try:
                    if(len(data) < 8): #todo check this more gracefully. SounderSuite still transmits empty strings when not running.
                        self.depth = None
                        self.callback(self.depth, self.keel_depth, self.sound_velocity)
                        continue
                    nmea = str(data).split(',')
                    self.depth = nmea[AppSettings.echosounder_nmea_depth_index].strip()
                    self.keel_depth = nmea[AppSettings.echosounder_nmea_keeldepth_index].strip()
                    self.sound_velocity = nmea[AppSettings.echosounder_nmea_sv_index].replace('\\r\\n\'','').strip()

                    if(self.depth == '' or self.depth == '0.00'):
                        self.depth = None
                    else:
                        self.depth = float(self.depth)
                    self.keel_depth = float(self.keel_depth)
                    self.sound_velocity = int(self.sound_velocity)
                    #if you're here the data looks good, send it
                    self.acquiring()
                    self.receive_callback(self.depth, self.keel_depth, self.sound_velocity)
                except Exception as e:
                    self.acquiring(False)
                    console.dhtb_console.add_error("exception in echosounder", e)
            time.sleep(.2)

    def begin_receive(self):
        self._reader = threading.Thread(target=self.connect)
        self._reader.start()