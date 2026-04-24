
from cnv_file_writer import CnvFileWriter
from echosounder import EchoSounder
from app_settings import AppSettings
from echosounder import EchoSounder
from seasave_tcp import SeasaveApi
from cnv_file_interface import CnvFilePlayback
from io_device import IODevice
import threading
import console

class IOController():

    #callback functions from data acquisition sources
    def echo_receive_callback(self, depth, keeldepth, sv):
        #keeldepth not used
        self.echosounder_depth = depth
        self.echosounder_sv = sv

    def io_device_receive_callback(self, depth, pressure, altitude, sv, sv_avg):
        self.instrument_depth = depth
        self.instrument_pressure = pressure
        self.instrument_altitude = altitude
        self.instrument_sv = sv
        self.instrument_sv_average = sv_avg

    def echo_connect_callback(self, connected):
        console.dhtb_console.add_message('echosounder connected ' + str(connected))

    def io_device_connect_callback(self, connected):
        console.dhtb_console.add_message('io device connected ' + str(connected))
        
    def __init__(self):
        self.echosounder = EchoSounder(AppSettings.echosounder_udp_port, self.echo_receive_callback, self.echo_connect_callback)
        #self.io_device
        self._watchdog_thread = threading.Thread()
        self.echosounder_depth = AppSettings.initial_water_depth
        self.echosounder_sv = AppSettings.echosounder_default_sv
        self.instrument_depth = 0
        self.instrument_pressure = 0
        self.instrument_altitude = 0
        self.instrument_sv = 1500
        self.instrument_sv_average = 1500
        if(AppSettings.playback_mode):
            self.io_device = CnvFilePlayback(AppSettings.playback_file, AppSettings.playback_speed, self.io_device_receive_callback, self.io_device_connect_callback)
            self.io_device.validate_file()
            if(self.io_device.simulate_echosounder):
                self.echosounder.start_simulate(self.io_device.simulate_max_depth_of_cast, .5, 1.5)
            self.io_device.begin_receive()
        else:
            self.io_device = SeasaveApi(AppSettings.seasave_ip, AppSettings.seasave_port, self.io_device_callback)
            self.echosounder.begin_receive()
            self.io_device.begin_receive()

    
