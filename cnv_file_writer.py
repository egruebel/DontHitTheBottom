from app_settings import AppSettings
import time
import threading
import console
import datetime 

class CnvFileWriter:

    def __init__(self):
        self.folder = AppSettings.filepath
        self.active_file = ""
        self.file_time = datetime.datetime.now()
        self.scanline = 0

    def start_new(self):
        self.file_time = datetime.datetime.now()
        self.active_file = 'dhtb_' + filetime.strftime('%Y%m%d%H%M%S') + '.cnv'
        try:
            with open(self.folder + self.active_file, "x") as f:
                header = f"""* Don't Hit The Bottom Data File
                * {self.file_time}
                * https://github.com/egruebel/donthitthebottom
                # name 0 = scan: Scan Count
                # name 1 = timeS: Time, Elapsed [seconds]
                # name 2 = depSM: {AppSettings.seasave_depth_qualifier}
                # name 3 = prDM: {AppSettings.seasave_pressure_qualifier}
                # name 4 = altM: {AppSettings.seasave_altimeter_qualifier}
                # name 5 = svCM: {AppSettings.seasave_sv_qualifier}
                # name 6 = avgsvCM: {AppSettings.seasave_sv_avg_qualifier}
                # name 7 = echoDM: echosounder depth [m]
                # name 8 = echoSV: echosounder sound velocity [m/s]
                *END*
                """
                f.write(header)
        except Exception as e:
            console.dhtb_console.add_error('File IO error while starting a new data file')
            console.dhtb_console.add_error(e)

    def add_line(self, depth, pressure, altitude, sv, sv_avg, echo, echo_sv):

        try:
            with open(self.folder + self.active_file, 'a') as f:
                self.scanline += 1
                seconds = (datetime.datetime.now() - self.file_time).total_seconds
                f.write(f'\n{self.scanline}\t{seconds}\t{depth}\t{altitude}\t{sv}\t{sv_avg}\t{echo}\t{echo_sv}')
        except Exception as e:
            console.dhtb_console.add_error('File IO error while writing line to data file')
            console.dhtb_console.add_error(e)

