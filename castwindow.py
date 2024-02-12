import pygame
from enum import Enum
 
class WaterColumn(Enum):
    FULL = 1
    MID = 2
    LOW = 3

class CastWindow:

    #total_depth = 100
    px_per_meter = 1
    depth_padding = 1 #meters

    def __init__(self):
        self.ctd = CTD()
        self.water_depth = 0
        self.window_width_px = 0
        self.window_height_px = 0
        self.depth_padding = 0
        self.full_water_column_meters = 0 #meters of the entire cast plus padding
        self.horizontal_center = 0
        self.depth_at_top = 0 #meters at the top of screen
        self.current_view_meters = 0 #meters currently shown on screen
        self.water_depth_upper_threshold = 0
        self.water_depth_lower_threshold = 0
        #self.set_water_depth_thresholds()
        self.background_image_raw = pygame.image.load("deepsea_bg.png").convert()
        self.background_image = self.background_image_raw
        #self.ctd_depth = 0
        #self.ctd_altitude = 0
        self.mid_altitude_tripline = 0
        self.low_altitude_tripline = 0
        self.water_column_display = WaterColumn.FULL
        #self.set_zoom_level()

    def set_water_depth_thresholds(self):
        self.water_depth_upper_threshold = self.water_depth - self.depth_padding
        self.water_depth_lower_threshold = self.water_depth + self.depth_padding

    def set_background_image(self):
        #scale the background image to the window size
        self.background_image = pygame.transform.scale(self.background_image_raw, (self.window_width_px, self.window_height_px))
        full_window_px_per_meter = self.window_height_px / self.full_water_column_meters
        #crop the image to the ctd cast zoom level
        #rect is left, top, width, height
        top = self.depth_at_top * full_window_px_per_meter #top needs to be scaled window height meters?? maybe??
        height = self.window_height_px - (top)
        self.background_image = self.background_image.subsurface(0, top, self.window_width_px, height)
        #stretch the cropped image to the window size
        self.background_image = pygame.transform.scale(self.background_image, (self.window_width_px, self.window_height_px))

    def get_current_window_depth(self):
        if(self.water_column_display == WaterColumn.FULL):
            return 0
        elif(self.water_column_display == WaterColumn.MID):
            return self.mid_altitude_tripline
        elif(self.water_column_display == WaterColumn.LOW):
            return self.low_altitude_tripline

    def get_next_tripline_depth(self):
        if(self.water_column_display == WaterColumn.FULL):
            return self.mid_altitude_tripline
        elif(self.water_column_display == WaterColumn.MID):
            return self.low_altitude_tripline
        elif(self.water_column_display == WaterColumn.LOW):
            return 0

    def set_zoom_level(self):
        self.depth_at_top = self.get_current_window_depth()
        self.full_water_column_meters = self.water_depth + self.depth_padding
        self.current_view_meters = self.full_water_column_meters - self.depth_at_top
        self.set_depth_padding()
        self.px_per_meter = self.window_height_px / (self.current_view_meters)
        self.set_background_image()

    def set_depth_padding(self):
        self.depth_padding = self.current_view_meters * .05

    def reset_window(self, window_size_px, water_depth_m, ctd_depth_m):
        self.window_width_px = window_size_px[0]
        self.window_height_px = window_size_px[1]
        self.horizontal_center = self.window_width_px *.75
        self.water_depth = water_depth_m
        self.mid_altitude_tripline = water_depth_m - 300
        self.low_altitude_tripline = water_depth_m - 150
        #self.set_ctd_depth(ctd_depth_m, False) #also evaluates position in water column
        #self.set_depth_padding()
        #self.full_water_column_meters = self.water_depth + self.depth_padding
        #self.set_water_depth_thresholds()
        self.set_zoom_level()

    def get_ypos_px(self, depth):
       return self.px_per_meter * (depth - self.depth_at_top)

    def set_ctd_depth(self, depth, reset_window = True):
        self.ctd.depth = depth
        #altitude can be negative if ctd is below estimated bottom (sound speed error or something)
        self.ctd.altitude = self.water_depth - self.ctd_depth
        #check if CTD has crossed a tripline
        current_water_column = WaterColumn.FULL
        if depth > self.mid_altitude_tripline:
            current_water_column = WaterColumn.MID
        if depth > self.low_altitude_tripline:
            current_water_column = WaterColumn.LOW
        if current_water_column != self.water_column_display:
            #ctd has moved into another zoom window
            self.water_column_display = current_water_column
            if reset_window:
                self.reset_window((self.window_width_px, self.window_height_px), self.water_depth, depth)

    def set_bottom_depth(self, depth):
        self.water_depth = depth
        #check if we need to adjust the window due to water depth 
        if (self.water_depth > self.water_depth_lower_threshold):
            #water depth has sank below the window...expand it by the padding size
            self.full_water_column_meters += self.depth_padding
            self.set_water_depth_thresholds()
            self.set_zoom_level()
        elif self.water_depth < self.water_depth_upper_threshold:
            #water depth has shallowed above our threshold...shrink the screen
            self.full_water_column_meters = self.water_depth + self.depth_padding
            self.set_water_depth_thresholds()
            self.set_zoom_level()
            


