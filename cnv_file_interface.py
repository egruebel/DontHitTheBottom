from app_settings import AppSettings
import time
import threading
import console
import math
from io_device import IODevice

class CnvFileParameter():

    def __init__(self, name, qualifier):
        self.name = name
        self.qualifier = qualifier
        self.exists_in_file = False
        self.column_index = int
        self.value = float

    def __str__(self):
        return self.name


class CnvFilePlayback(IODevice):

    def __init__(self, filepath, playback_speed, callback):
        self.filepath = filepath
        self.callback = callback
        self.playback_speed = playback_speed

        self.simulate_echosounder = False
        self.simulate_max_depth_of_cast = 0
        self._row_of_max_depth = 0
        self._simulate_sv = False
        self._simulate_sv_avg = False

        self._acquiring = False

        self.depth = 0
        self.pressure = 0
        self.altitude = 0
        self.sv = 0
        self.sv_avg = 0

        #these fields are only for calculating sv if there's enough data to do so
        self._temp = 0
        self._salinity = 0
        
        #collection for tracking fields in the cnv [qualifier, exists in file, col index, current value]
        #todo make this a class
        self.fields = [[AppSettings.seasave_depth_qualifier,False,-1,-99],
                  [AppSettings.seasave_altimeter_qualifier, False,-1,-99],
                  [AppSettings.seasave_sv_qualifier, False,-1,-99],
                  [AppSettings.seasave_pressure_qualifier, False,-1,-99],
                  [AppSettings.seasave_sv_avg_qualifier, False,-1,-99],
                  [AppSettings.seasave_bottom_depth_qualifier, False,-1,-99],
                  ['Temperature [ITS-90, deg C]', False, -1,-99],
                  ['Salinity, Practical [PSU]', False, -1, -99]]
     
    @property
    def acquiring(self):
        return self._acquiring

    def initialize_field(self, line):
        #Sea-bird cnv files name their variables in the header like so: "# name 3 = prDM: Pressure, Digiquartz [db]"
        name_array = line.split(': ')
        #Now get the part equal to " Pressure, Digiquartz [db]" and strip the preceding whitespace
        col_name = name_array[1].strip()
        #Now get the tab delimeted row number for this variable from "# name 3 = prDM"
        #a blank split() argument separates by any whitespace
        col_index = int(name_array[0].split()[2])
        for field in self.fields:
            if field[0] == col_name:
                field[1] = True
                field[2] = col_index

    def playback_loop(self):
        with open(self.filepath, 'rt', encoding='latin-1') as f:
            #row_context = 0
            begin_reading = False

            #get column idices of required data to run this app
            depth_index = self.fields[0][2] 
            altitude_index = self.fields[1][2]
            sv_index = self.fields[2][2]
            sv_exists = self.fields[2][1]
            sv_avg_index = self.fields[4][2]
            sv_avg_exists = self.fields[4][1]
            pressure_index = self.fields[3][2]
            temp_index = self.fields[6][2]
            salinity_index = self.fields[7][2]
            read_row = 0
            sv_sum = 0
            sv_count = 0
            header = []
            for line in f:
                if(line == '*END*\n'):
                    begin_reading = True
                    continue
                if(begin_reading):
                    self._acquiring = True
                    dat = line.split()
                    self.depth = float(dat[depth_index])
                    self.altitude = float(dat[altitude_index])
                    self.pressure = float(dat[pressure_index])
                    read_row += 1
                    if(self._simulate_sv):
                        self._temp = float(dat[temp_index])
                        self._salinity = float(dat[salinity_index])
                        #this algorithm gives wacky sv. Todo figure out why. 
                        #self.sv = self.chenmillero(self.pressure, self._temp, self._salinity)
                        self.sv = self.chenmillero_seabird(self.pressure, self._temp, self._salinity)
                    elif(sv_exists):
                        self.sv = float(dat[sv_index])
                    else:
                        self.sv = 1500
                    
                    if(self._simulate_sv_avg):
                        #keep track of row so we only calculate sv average on the downcast
                        if(read_row <= self._row_of_max_depth):
                            sv_sum += self.sv
                            sv_count += 1
                            self.sv_average = sv_sum / sv_count
                    elif(sv_avg_exists):
                        self.sv_average = float(dat[sv_avg_index])
                    else:
                        self.sv_average = 1500
                    #row += 1
                    self.callback(self.depth, self.pressure, self.altitude, self.sv, self.sv_average)
                    time.sleep(self.playback_speed)

            else:
                # No more lines to be read from file
                self._acquiring = False

        return
                
            
    def begin_receive(self):
        with open(self.filepath, 'rt', encoding='latin-1') as f:
            #row_context = 0
            begin_reading = False
            header = []

            #read the header and figure out which data is in which rows
            max_cast_depth = 0
            altitude_at_max = AppSettings.altimeter_max_range_m
            read_row = 0
            for line in f:
                if line.startswith('# name'):
                    #name_data = line.split(': ')
                    self.initialize_field(line)

                if(line == '*END*\n'):
                    #we've read past the file header, check the file contains needed fields
                    if self.fields[0][1] == False:
                        #todo gracefully let the user know instead of crashing the application
                        raise Exception(".cnv file is missing the depth field specified in the AppSettings")
                    if self.fields[1][1] == False:
                        raise Exception(".cnv file is missing the altimeter field specified in the AppSettings") 
                    if self.fields[2][1] == False:
                        #sound velocity is missing from the file. If Temp and Salinity exist we can calculate it. 
                        if self.fields[6][1] == True and self.fields[7][1] == True and self.fields[3][1] == True:
                            #the file has the T, S, and P needed to calculate SV on the fly
                            self._simulate_sv = True
                            console.dhtb_console.add_message("calculating sound velocity")
                        else:
                            #use constant sound velocity
                            self.sv = 1500
                            console.dhtb_console.add_warning("cnv file is missing the sound velocity field specified in the AppSettings")
                            console.dhtb_console.add_warning("using a fixed sound velocity of 1500 m/s")
                        #raise Exception(".cnv file is missing the sound velocity field specified in the AppSettings")
                    if self.fields[3][1] == False:
                        console.dhtb_console.add_warning(".cnv file is missing the pressure field specified in the AppSettings")
                    if self.fields[4][1] == False:
                        #average sound velocity is missing
                        #if sv is present in the file or we have enough data to calculate it then that's ok
                        if self._simulate_sv or self.fields[2][1]:
                            self._simulate_sv_avg = True
                            console.dhtb_console.add_message("calculating average sound velocity")
                        else:
                            #use constant average sv
                            self.sv_average = 1500
                            console.dhtb_console.add_warning("cnv file is missing the average sound velocity field specified in AppSettings")
                            console.dhtb_console.add_warning("using a fixed average sound velocity of 1500 m/s")
                    if self.fields[5][1] == False:
                        self.simulate_echosounder = True
                        console.dhtb_console.add_warning(".cnv file is missing the echosounder field specified in AppSettings")
                        console.dhtb_console.add_warning("simulating echosounder data")

                    begin_reading = True
                    continue
                
                if begin_reading and self.simulate_echosounder:
                    #find max depth of cast
                    dat = line.split()
                    dep = float(dat[self.fields[0][2]])
                    alt = float(dat[self.fields[1][2]])
                    read_row += 1
                    if dep > self.simulate_max_depth_of_cast:
                        max_cast_depth = dep
                        altitude_at_max = alt
                        self.simulate_max_depth_of_cast = dep + alt
                        #keep track of row so we're only averaging sound velocity on the downcast
                        self._row_of_max_depth = read_row
                    #row += 1
        #start a new thread and pump out data to the callback
        x = threading.Thread(target=self.playback_loop, args = ())
        x.start()

    @staticmethod
    def chenmillero_seabird(p0, t, s):
        #straight from the SBE data processing manual
        #ported to Python
        a, a0, a1, a2, a3 = 0, 0, 0, 0, 0
        b, b0, b1 = 0, 0, 0
        c, c0, c1, c2, c3 = 0, 0, 0, 0, 0
        p, sr, d, sv = 0, 0, 0, 0
        p = p0 / 10.0 #scale pressure to bars
        if (s < 0.0): s = 0.0
        sr = math.sqrt(s)
        d = 1.727e-3 - 7.9836e-6 * p
        b1 = 7.3637e-5 + 1.7945e-7 * t
        b0 = -1.922e-2 - 4.42e-5 * t
        b = b0 + b1 * p
        a3 = (-3.389e-13 * t + 6.649e-12) * t + 1.100e-10
        a2 = ((7.988e-12 * t - 1.6002e-10) * t + 9.1041e-9) * t - 3.9064e-7
        a1 = (((-2.0122e-10 * t + 1.0507e-8) * t - 6.4885e-8) * t - 1.2580e-5) * t + 9.4742e-5
        a0 = (((-3.21e-8 * t + 2.006e-6) * t + 7.164e-5) * t -1.262e-2) * t + 1.389
        a = ((a3 * p + a2) * p + a1) * p + a0
        c3 = (-2.3643e-12 * t + 3.8504e-10) * t - 9.7729e-9
        c2 = (((1.0405e-12 * t -2.5335e-10) * t + 2.5974e-8) * t - 1.7107e-6) * t + 3.1260e-5
        c1 = (((-6.1185e-10 * t + 1.3621e-7) * t - 8.1788e-6) * t + 6.8982e-4) * t + 0.153563
        c0 = ((((3.1464e-9 * t - 1.47800e-6) * t + 3.3420e-4) * t - 5.80852e-2) * t + 5.03711) * t + 1402.388
        c = ((c3 * p + c2) * p + c1) * p + c0
        sv = c + (a + b * sr + d * s) * s
        return sv
    
    @staticmethod
    def chenmillero( P=None, T=None, S=None ): 

    #CHENMILLERO: Converts Pressure, Temperature and Salinity to Sound Velocity in Sea Water
    #through Chen and Millero's formula. 
    #
    # Usage:    sound_speed_in_sea_water = chenmillero( pressure , temperature , salinity ) ; 
    #
    #           Range of validity: temperature 0 to 40 Celsius degrees, 
    #           salinity 0 to 40 parts per thousand and pressure 0 to 1000 bar. 
    #
    #


    #Max error using Apel data for validation: 0.07 m/s. 

    #***************************************************************************************
    # Faro, ter 11 jun 2024 21:01:23 
    # 
    # Contact: orodrig@ualg.pt
    # 
    # Don't like it? Don't use it. 
    # 
    # Reference: C-T. Chen and F.J. Millero, "Speed of sound in seawater at high pressures" 
    #                 J. Acoust. Soc. Am. 62(5) pp 1129-1135, 1977. 
    #
    #***************************************************************************************

        c00 =  1402.388  ; c01 =  5.03830    ; c02 = -5.81090e-2 ; c03 =  3.3432e-4  ; c04 = -1.47797e-6 ; c05 = 3.1419e-9 
        c10 =  0.153563  ; c11 =  6.8999e-4  ; c12 = -8.1829e-6  ; c13 =  1.3632e-7  ; c14 = -6.1260e-10
        c20 =  3.1260e-5 ; c21 = -1.7111e-6  ; c22 =  2.5986e-8  ; c23 = -2.5353e-10 ; c24 =  1.0415e-12 
        c30 = -9.7729e-9 ; c31 =  3.8513e-10 ; c32 = -2.3654e-12
        a00 =  1.389     ; a01 = -1.262e-2   ; a02 =  7.166e-5   ; a03 =  2.008e-6   ; a04 = -3.21e-8 
        a10 =  9.4742e-5 ; a11 = -1.2583e-5  ; a12 = -6.4928e-8  ; a13 = 1.0515e-8   ; a14 = -2.0142e-10 
        a20 = -3.9064e-7 ; a21 =  9.1061e-9  ; a22 = -1.6009e-10 ; a23 = 7.994e-12 
        a30 =  1.100e-10 ; a31 =  6.651e-12  ; a32 = -3.391e-13
        b00 = -1.922e-2  ; b01 = -4.42e-5    ; b10 =  7.3637e-5  ; b11 = 1.7950e-7 
        d00 =  1.727e-3  ; d10 = -7.9836e-6  ; 

        PP  =    P*P
        PPP =   P*PP
        TT  =    T*T
        TTT =   TT*T
        TIV =  TTT*T
        TV  =  TIV*T

        cw = (c00 + c01*T + c02*TT + c03*TTT + c04*TIV + c05*TV) \
        + (c10 + c11*T + c12*TT + c13*TTT + c14*TIV )*P       \
        + (c20 + c21*T + c22*TT + c23*TTT + c24*TIV )*( PP )  \
        + (c30 + c31*T + c32*TT)*( PPP )
            
        a  = (a00 + a01*T + a02*TT + a03*TTT + a04*TIV)   \
        + (a10 + a11*T + a12*TT + a13*TTT + a14*TIV)*P \
        + (a20 + a21*T + a22*TT + a23*TTT)*( PP )      \
        + (a30 + a31*T + a32*TT)*( PPP )
            
        b  =  b00 + b01*T + ( b10 + b11*T )*P 

        d  =  d00 + d10*P
    
        c = cw + a*S + b*( S**(1.5) ) + d*( S*S )

        return c


        
