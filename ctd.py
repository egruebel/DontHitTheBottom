import pygame
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
        self.average_sound_velocity = AppSettings.altimeter_default_sv
        self.instantaneous_sound_velocity = AppSettings.altimeter_default_sv
        self.pressure = 0
        self.altitude = 0
        self.altimeter_max_range = AppSettings.altimeter_max_range_m
        self.altimeter_hit_count = 0
        self.altimeter_active = False
        self.height_px = AppSettings.ctd_min_height_px
        self.width_px = self.height_px * .6
        self.altimeter_default_sound_velocity = AppSettings.altimeter_default_sv
        self.altimeter_valid = False
        self.altimeter_correction = AppSettings.altimeter_sv_correction
        self.image_file = pygame.image.load(AppSettings.ctd_image).convert_alpha()

    def resize_ctd(self, viewport_height_m):
        new_height = (1/viewport_height_m) * AppSettings.ctd_size_scaling_coeff
        if(new_height < AppSettings.ctd_min_height_px):
            new_height = AppSettings.ctd_min_height_px
        self.height_px = new_height
        self.width_px = self.height_px *.6

    def set_altimeter(self, altitude):
        self.altitude = altitude
        self.altimeter_active = False
        if(altitude < self.altimeter_max_range) and (altitude > AppSettings.altimeter_minimum_viable_m) and (self.altimeter_hit_count < AppSettings.altimeter_hit_count):
            self.altimeter_hit_count += 1 #in a row
        else:
            if(self.altimeter_hit_count >= 1):
                self.altimeter_hit_count -= 1
        if(self.altimeter_hit_count >= AppSettings.altimeter_hit_count / 2):
            self.altimeter_active = True

    def set_depth(self, depth_m):
        self.depth = depth_m
        self.history.append(depth_m)
        

    










