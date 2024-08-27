import socket
import threading
import time
import random

class EchoSounder:

    def __init__(self, broadcast_port, receive_callback):
        self.port = broadcast_port
        self.callback = receive_callback
        self.depth = 0
        self.sound_velocity = 0
        self.keel_depth = 0
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) # UDP
        #self.client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        # Enable broadcasting mode
        self.client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def sim(self, rand_coeff):
        while True:
            time.sleep(1.0)
            self.depth = self.depth + random.uniform((-1 * rand_coeff), rand_coeff)
            self.keel_depth = 5
            self.sound_velocity = 1500
            self.callback("echosounder simulation: " + str(self.depth))
        return
            
    def start_simulate(self, start_depth_m, start_sv, rand_coeff):
        self.depth = start_depth_m
        self.sound_velocity = start_sv
        x = threading.Thread(target=self.sim, args = (rand_coeff,))
        x.start()
        
    def connect(self):
        self.client.bind(("", self.port))
        self.client.setblocking(0)
        data =''
        address = ''
        while True:
            try:
                data,address = self.client.recvfrom(10000)
            except socket.error:
                pass
            else:
                try:
                    s = str(data).split(',')
                    self.depth = float(s[6])
                    self.keel_depth = float(s[8])
                    self.sound_velocity = int(s[9].replace('\\r\\n\'',''))
                    self.callback(data)
                except:
                    print("Exception in echosounder.py")
                    for a in e.args:
                        print(a)
            time.sleep(1)

    def start_receive(self):
        x = threading.Thread(target=self.connect)
        x.start()