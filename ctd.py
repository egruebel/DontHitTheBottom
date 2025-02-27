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


    def set_altimeter(self, altitude):
        #self.altitude = altitude
        self.altimeter_active = False
        if(altitude < self.altimeter_max_range) and (altitude > AppSettings.altimeter_minimum_viable_m):
            #we have an altimeter reading within the valid range, add it to the hit count
           while(len(self.altimeter_history) >= AppSettings.altimeter_hit_count):
               self.altimeter_history.pop(0)
               #dont want the hit count to get too big (int.max...though very unlikely it would ever get that high)
           self.altimeter_history.append(altitude)
        else:
            self.altimeter_history.clear()
        if(len(self.altimeter_history) >= AppSettings.altimeter_hit_count):
            #if you're here it means that the altimeter is good-to-go as a depth source
            if(AppSettings.altimeter_averaging):
                self.altitude = statistics.median(self.altimeter_history)
            else:
                self.altitude = altitude
            self.altimeter_active = True

    def set_depth(self, depth_m):
        self.depth = depth_m
        self.history.append(depth_m)
        

    










