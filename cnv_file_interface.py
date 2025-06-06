from app_settings import AppSettings
import time
import threading

class CnvFilePlayback:

    def __init__(self, filepath, playback_speed, callback):
        self.filepath = filepath
        self.callback = callback
        self.playback_speed = playback_speed

        self.simulate_echosounder = False
        self.simulate_max_depth_of_cast = 0
        self.simulate_sv_avg = False

        self.acquiring = False

        self.depth = 0
        self.pressure = 0
        self.altitude = 0
        self.sv = 0
        self.sv_avg = 0
        
        #[qualifier, exists in file, col index, current value]
        self.fields = [[AppSettings.seasave_depth_qualifier,False,0,-99],
                  [AppSettings.seasave_altimeter_qualifier, False,0,-99],
                  [AppSettings.seasave_sv_qualifier, False,0,-99],
                  [AppSettings.seasave_pressure_qualifier, False,0,-99],
                  [AppSettings.seasave_sv_avg_qualifier, False,0,-99],
                  [AppSettings.seasave_bottom_depth_qualifier, False,0,-99]]

    def initialize_field(self, line):
        name_array = line.split(': ')
        col_name = name_array[1].strip()
        col_index = int(name_array[0].split()[2])
        for field in self.fields:
            if field[0] == col_name:
                field[1] = True
                field[2] = col_index

    def playback_loop(self):
        with open(self.filepath, 'rt') as f:
            #row_context = 0
            begin_reading = False

            #get column idices of required data to run this app
            depth_index = self.fields[0][2] 
            altitude_index = self.fields[1][2]
            sv_index = self.fields[2][2]
            sv_sum = 0
            sv_count = 0
            header = []
            for line in f:
                if(line == '*END*\n'):
                    begin_reading = True
                    continue
                if(begin_reading):
                    self.acquiring = True
                    dat = line.split()
                    self.depth = float(dat[depth_index])
                    self.altitude = float(dat[altitude_index])
                    self.sv_instantaneous = float(dat[sv_index])
                    sv_sum += self.sv_instantaneous
                    sv_count += 1
                    self.sv_average = sv_sum / sv_count
                    #row += 1
                    self.callback(self)
                    time.sleep(self.playback_speed)

            else:
                # No more lines to be read from file
                self.acquiring = False
                return
            
    def begin_playback(self):
        with open(self.filepath, 'rt') as f:
            #row_context = 0
            begin_reading = False
            header = []

            #read the header and figure out which data is in which rows
            for line in f:
                if line.startswith('# name'):
                    #name_data = line.split(': ')
                    self.initialize_field(line)

                if(line == '*END*\n'):
                    #we're past the header, check the file contains needed fields
                    if self.fields[0][1] == False:
                        raise Exception(".cnv file is missing the depth field specified in the AppSettings")
                    if self.fields[1][1] == False:
                        raise Exception(".cnv file is missing the altimeter field specified in the AppSettings")
                    if self.fields[2][1] == False:
                        raise Exception(".cnv file is missing the sound velocity field specified in the AppSettings")
                    if self.fields[4][1] == False:
                        self.simulate_sv_avg = True
                    if self.fields[5][1] == False:
                        self.simulate_echosounder = True

                    begin_reading = True
                    continue
                if begin_reading and self.simulate_echosounder:
                    #find max depth of cast
                    dat = line.split()
                    dep = float(dat[self.fields[0][2]])
                    if dep > self.simulate_max_depth_of_cast:
                        self.simulate_max_depth_of_cast = dep
                    #row += 1
        #start a new thread and pump out data to the callback
        x = threading.Thread(target=self.playback_loop, args = ())
        x.start()


        
