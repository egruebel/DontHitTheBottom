import pygame
import statistics
from enum import Enum
from app_settings import AppSettings
import console

#class WaterColumn(Enum):
    #FULL = 1
    #MID = 2
    #LOW = 3

class Altimeter:

    def __init__(self):
        self.altitude = 0.0
        self.filtered_altitude = 0.0
        self.quality = 0
        self.is_tracking = False
        self.raw_altitude_history = []
        self._raw_window = []
        self._filtered_window = []
        self._quality_window = []
        self.blanking_range = AppSettings.altimeter_blanking_range_m
        self.max_range = AppSettings.altimeter_max_range_m
        self.default_sound_velocity = AppSettings.altimeter_default_sv

        #todo logic to decide when to display vs when to use altimeter
        #two or three complete flushes of the averaging buffer

    def set_altitude(self, altitude):

        self._raw_window.append(altitude)
        self.raw_altitude_history.append(altitude) #todo dont forget to trim this when it's not displayed
        self.altitude = altitude

        filter_window_full = False
        if(len(self._raw_window) >= AppSettings.altimeter_filtering_window):
            filter_window_full = True
        
        #calculate the Mean Average Distance using the median of the dataset
        median = statistics.median(self._raw_window)
        distances = [abs(x-median) for x in self._raw_window]
        mad = statistics.mean(distances)
        
        #if dataset is tight, use it. Otherwise correct up to n values and see if the messiness improves.
        corrections = 1
        raw_copy = self._raw_window.copy()
        filtered = False
        while(filter_window_full and mad > 10 and corrections > 0):
            #find the altitude with the highest error
            max_distance = max(distances)
            max_index = distances.index(max_distance)
            #remove it
            raw_copy.pop(max_index)
            distances.pop(max_index)
            #recalculate mad
            mad = statistics.mean(distances)
            filtered = True
            corrections -= 1

        self.filtered_altitude = statistics.median(raw_copy)
        self._filtered_window.append(self.filtered_altitude)

        altitude_within_range = False
        if(self.filtered_altitude <= self.max_range and self.filtered_altitude >= self.blanking_range):
            altitude_within_range = True

        #determine quality
        if(mad < 10 and not filtered and altitude_within_range):
            #best
            self.quality = 3
        elif(mad <= 10 and filtered and altitude_within_range):
            #data was filtered and brought into specification
            self.quality = 2
        else:
            #data is messy or not in range
            self.quality = 1

        self._quality_window.append(self.quality)
        if(1 not in self._quality_window):
            if(not self.is_tracking):
                console.dhtb_console.add_message('altimeter tracking on')
                self.is_tracking = True
            if(self.filtered_altitude <= AppSettings.altimeter_reliable_range_m):
                self.blanking_range = 0
                #console.dhtb_console.add_message('minumum altimeter range is now 0m')
            else:
                self.blanking_range = AppSettings.altimeter_blanking_range_m
                #console.dhtb_console.add_message('minumum altimeter range is now ' + str(self.blanking_range))
        else:
            if(self.is_tracking):
                console.dhtb_console.add_message('altimeter tracking off')
                self.is_tracking = False
            

        #shrink the sliding window(s) to the filter size setting.
        while(len(self._raw_window) > AppSettings.altimeter_filtering_window):
            self._raw_window.pop(0)
            self._filtered_window.pop(0)
            self._quality_window.pop(0)
    

class CTD:
    
    def __init__(self):
        self.depth = 0
        self.history = []
        self.average_sound_velocity = AppSettings.altimeter_default_sv
        self.instantaneous_sound_velocity = AppSettings.altimeter_default_sv
        self.pressure = 0
        self.altimeter = Altimeter()
        self.height_px = AppSettings.ctd_min_height_px
        self.width_px = self.height_px * .6
        self.angle = 0.0
        self.rotate = True
        self.altimeter_correction = False
        #self.altimeter_default_sound_velocity = AppSettings.altimeter_default_sv
        #self.altimeter_correction = AppSettings.altimeter_sv_correction
        self.image = pygame.image.load(AppSettings.ctd_image).convert_alpha()
        self.image_scaled = pygame.image.load(AppSettings.ctd_image).convert_alpha()
        
    def resize(self, px_per_meter):
        #img_height_px = self.ctd_image.get_height()
        #assume ctd is 2m/6ft because that's what they usually are
        ctd_height_m = 3
        ih = px_per_meter * ctd_height_m
        if (ih < AppSettings.ctd_min_height_px):
            ih = AppSettings.ctd_min_height_px
        #img_height_px_corrected = img_height_px / ctd_height_m
        self.height_px = ih
        self.width_px = ih * .6
        self.image_scaled = pygame.transform.scale(self.image, (self.width_px, self.height_px))
        #self.ctd_image_scaled = pygame.transform.rotate(self.ctd_image_scaled, 20)

    def set_depth(self, depth_m):
        self.depth = depth_m
        self.history.append(depth_m)

        

    










