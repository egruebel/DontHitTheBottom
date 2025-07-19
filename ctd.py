import pygame
import statistics
from enum import Enum
from app_settings import AppSettings

#class WaterColumn(Enum):
    #FULL = 1
    #MID = 2
    #LOW = 3

class CTD:
    
    def __init__(self):
        self.depth = 0
        self.history = []
        self.altimeter_history = []
        self.average_sound_velocity = AppSettings.altimeter_default_sv
        self.instantaneous_sound_velocity = AppSettings.altimeter_default_sv
        self.pressure = 0
        self.altitude = 0
        self.altimeter_max_range = AppSettings.altimeter_max_range_m
        #self.altimeter_hit_count = 0
        self.altimeter_active = False
        self.height_px = AppSettings.ctd_min_height_px
        self.width_px = self.height_px * .6
        self.angle = 0.0
        self.rotate = True
        self.altimeter_default_sound_velocity = AppSettings.altimeter_default_sv
        #self.altimeter_valid = False
        self.altimeter_correction = AppSettings.altimeter_sv_correction
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

    def remove_highest_deviation(self, vals, avg):
        highest_index = 0
        highest_dev = 0
        for i, v in enumerate(vals):
            dev = abs(v-avg)
            if(dev > highest_dev):
                highest_dev = dev
                highest_index = i
        vals.pop(highest_index)



    def set_altimeter(self, altitude):

        #self.altitude = altitude
        self.altimeter_active = False

        #adjust the sliding window of altimeter data
        self.altimeter_history.append(altitude)
        while(len(self.altimeter_history) > AppSettings.altimeter_filtering_window):
            self.altimeter_history.pop(0)

        num = int(AppSettings.altimeter_filtering_window * .25)
        ms = AppSettings.altimeter_filtering_window - num
        max_std = 3

        size = len(self.altimeter_history)
        std = 0
        avg = 0
        if (size > 4):
            std = statistics.stdev(self.altimeter_history)
            std = int(std)
            avg = statistics.median(self.altimeter_history)

        #track passes and fails
        passes = 0
        fails = 0

        use_altimeter = False
        if(size >= ms) and (std < 3) and (avg > AppSettings.altimeter_minimum_viable_m) and (avg < AppSettings.altimeter_max_range_m):
            passes += 1
            use_altimeter = True
        else:
            fails -= 1

        if(use_altimeter):
            #if you're here it means that the altimeter is good-to-go as a depth source
            if(AppSettings.altimeter_averaging):
                self.altitude = avg
            else:
                self.altitude = altitude
            self.altimeter_active = True

    def set_depth(self, depth_m):
        self.depth = depth_m
        self.history.append(depth_m)
        

    










