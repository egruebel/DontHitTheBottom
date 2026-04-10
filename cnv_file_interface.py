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

        self.depth = CnvFileParameter('depth', AppSettings.seasave_depth_qualifier)
        self.pressure = CnvFileParameter('pressure', AppSettings.seasave_pressure_qualifier)
        self.altitude = CnvFileParameter('altitude', AppSettings.seasave_altimeter_qualifier)
        self.sv = CnvFileParameter('sv', AppSettings.seasave_sv_qualifier)
        self.sv_avg = CnvFileParameter('sv_avg', AppSettings.seasave_sv_avg_qualifier)
        self.bottom_depth = CnvFileParameter('bottom_depth', AppSettings.seasave_bottom_depth_qualifier)
        self.bottom_depth_sv = CnvFileParameter('bottom_depth_sv', AppSettings.seasave_bottom_depth_sv_qualifier)

        #these fields are only for calculating sv if there's enough data to do so
        self._temp = CnvFileParameter('temp', 'Temperature [ITS-90, deg C]')
        self._salinity = CnvFileParameter('salinity', 'Salinity, Practical [PSU]')
        
        self.fields = {
            'depth': self.depth,
            'pressure': self.pressure,
            'altitude': self.altitude,
            'sv': self.sv,
            'sv_avg': self.sv_avg,
            'temp': self._temp,
            'salinity': self._salinity,
            'bottom_depth': self.bottom_depth,
            'bottom_depth_sv': self.bottom_depth_sv
        }
     
    @property
    def acquiring(self):
        return self._acquiring

    def initialize_field(self, line):
        #Sea-bird cnv files name their variables in the header like so: "# name 3 = prDM: Pressure, Digiquartz [db]"
        name_array = line.split(': ')
        #Now get the part after the colon like " Pressure, Digiquartz [db]" and strip the preceding whitespace
        col_name = name_array[1].strip()
        #Now get the tab delimeted column integer for this variable from "# name 3 = prDM"
        #a blank split() argument separates by any whitespace
        col_index = int(name_array[0].split()[2])

        #see if the cnv field is one that we need
        for key, field in self.fields.items():
            if field.qualifier == col_name:
                field.exists_in_file = True
                field.column_index = col_index

    def playback_loop(self):
        with open(self.filepath, 'rt', encoding='latin-1') as f:
            #row_context = 0
            begin_reading = False

            read_row = 0
            sv_sum = 0
            sv_count = 0
            #header = []
            for line in f:
                if(line == '*END*\n'):
                    begin_reading = True
                    continue
                if(begin_reading):
                    self._acquiring = True
                    read_row += 1
                    dat = line.split()
                    self.depth.value = float(dat[self.depth.column_index])
                    self.pressure.value = float(dat[self.pressure.column_index])
                    self.altitude.value = float(dat[self.altitude.column_index])
                    
                    if(self.sv.exists_in_file):
                        self.sv.value = float(dat[self.sv.column_index])
                    elif(self._simulate_sv):
                        self._temp.value = float(dat[self._temp.column_index])
                        self._salinity.value = float(dat[self._salinity.column_index])
                        #this algorithm gives wacky sv. Todo figure out why. 
                        #self.sv = self.chenmillero(self.pressure, self._temp, self._salinity)
                        self.sv.value = self.chenmillero_seabird(self.pressure.value, self._temp.value, self._salinity.value)
                    else:
                        #sv not present, use constant
                        self.sv.value = 1500
                    
                    if(self.sv_avg.exists_in_file):
                        self.sv_avg.value = float(dat[self.sv_avg.column_index])
                    elif(self._simulate_sv_avg):
                        #keep track of row so we only calculate sv average on the downcast
                        if(read_row <= self._row_of_max_depth):
                            sv_sum += self.sv.value
                            sv_count += 1
                            self.sv_avg.value = sv_sum / sv_count
                    else:
                        self.sv_avg.value = 1500

                    self.callback(self.depth.value, self.pressure.value, self.altitude.value, self.sv.value, self.sv_avg.value)
                    time.sleep(self.playback_speed)

            else:
                # No more lines to be read from file
                self._acquiring = False

        return
                
    def validate_file(self):
        with open(self.filepath, 'rt', encoding='latin-1') as f:
            begin_reading = False
            #read the header and figure out which data is in which rows
            max_cast_depth = 0
            altitude_at_max = AppSettings.altimeter_max_range_m
            read_row = 0
            for line in f:

                if line.startswith('# name'):
                    #ingest this cnv file parameter from the header
                    self.initialize_field(line)

                if(line == '*END*\n'):
                    #we've read past the file header
                    #set the flag to begin reading data
                    begin_reading = True
                    #check the file contains needed fields
                    if self.depth.exists_in_file == False:
                        #todo gracefully let the user know instead of crashing the application
                        raise Exception(".cnv file is missing the depth field specified in the AppSettings")
                    if self.pressure.exists_in_file == False:
                        console.dhtb_console.add_warning(".cnv file is missing the pressure field specified in the AppSettings")
                    if self.altitude.exists_in_file == False:
                        raise Exception(".cnv file is missing the altimeter field specified in the AppSettings") 
                    if self.sv.exists_in_file == False:
                        #sound velocity is missing from the file. If Temp and Salinity exist we can calculate it. 
                        if self._temp.exists_in_file and self._salinity.exists_in_file and self.pressure.exists_in_file:
                            #the file has the T, S, and P needed to calculate SV on the fly
                            self._simulate_sv = True
                            console.dhtb_console.add_message("calculating sound velocity")
                        else:
                            #use constant sound velocity
                            console.dhtb_console.add_warning("cnv file is missing the sound velocity field specified in the AppSettings")
                            console.dhtb_console.add_warning("using a fixed sound velocity of 1500 m/s")
                    if self.sv_avg.exists_in_file == False:
                        #average sound velocity is missing
                        #if sv is present in the file or we have enough data to calculate sv then that's ok
                        if self._simulate_sv or self.sv.exists_in_file:
                            self._simulate_sv_avg = True
                            console.dhtb_console.add_message("calculating average sound velocity")
                        else:
                            #use constant average sv
                            console.dhtb_console.add_warning("cnv file is missing the average sound velocity field specified in AppSettings")
                            console.dhtb_console.add_warning("using a fixed average sound velocity of 1500 m/s")
                    if self.bottom_depth.exists_in_file == False:
                        self.simulate_echosounder = True
                        console.dhtb_console.add_warning(".cnv file is missing the echosounder field specified in AppSettings")
                        console.dhtb_console.add_warning("simulating echosounder data")
                    continue
                
                if begin_reading and self.simulate_echosounder:
                    #find max depth of cast
                    #split the tab delimited row into array
                    dat = line.split()
                    #get the data from the column
                    dep = float(dat[self.fields['depth'].column_index])
                    alt = float(dat[self.fields['altitude'].column_index])
                    read_row += 1
                    if dep > self.simulate_max_depth_of_cast:
                        #new deep world record
                        self.simulate_max_depth_of_cast = dep + alt
                        #keep track of row so we're only averaging sound velocity on the downcast
                        self._row_of_max_depth = read_row

            
    def begin_receive(self):
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


        
