import socket
import threading
import time
import random
from app_settings import AppSettings
import console
from io_device import IODevice

class EchoSounder(IODevice):

    def __init__(self, broadcast_port, receive_callback):
        self.port = broadcast_port
        self.callback = receive_callback
        self._acquiring = False
        self.depth = None
        self.sound_velocity = AppSettings.echosounder_default_sv
        self.keel_depth = 5
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) # UDP
        self.client.settimeout(8)
        # Enable broadcasting mode
        self.client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    @property
    def acquiring(self):
        return self._acquiring

    def sim(self, rand_coeff, sounding_interval_s):
        while True:
            self._acquiring = True
            #add a random value between -X and +X to make the bottom change
            self.depth = self.depth + random.uniform((-1 * rand_coeff), rand_coeff)
            self.callback(self.depth, self.keel_depth, self.sound_velocity)
            time.sleep(sounding_interval_s)
        self._acquiring = False
        return
            
    def start_simulate(self, start_depth_m, rand_coeff, sounding_interval_s):
        self.depth = start_depth_m
        x = threading.Thread(target=self.sim, args = (rand_coeff, sounding_interval_s))
        x.start()

    def connect(self):
        self.client.bind(("", self.port))
        #self.client.setblocking(0)
        data =''
        address = ''
        while True:
            try:
                data,address = self.client.recvfrom(4000)
            except socket.timeout as e:
                self.depth = None
                self.callback(self.depth, self.keel_depth, self.sound_velocity)
                console.dhtb_console.add_message('echosounder timeout')
            except Exception as e:
                self.depth = None
                self.callback(self.depth, self.keel_depth, self.sound_velocity)
                console.dhtb_console.add_error("exception in echosounder", e)
            else:
                try: #todo put these NMEA string indices into app settings
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
                    self._acquiring = True
                    self.callback(self.depth, self.keel_depth, self.sound_velocity)
                except Exception as e:
                    self._acquiring = False
                    console.dhtb_console.add_error("exception in echosounder", e)
            time.sleep(.2)

    def begin_receive(self):
        x = threading.Thread(target=self.connect)
        x.start()