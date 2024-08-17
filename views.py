import pygame
from app_settings import AppSettings
from ctd import CTD
from enum import Enum

class DepthSource(Enum):
    NONE = 0
    ECHO = 1
    ALTIMETER = 2

class ViewWindow:

    #px_per_meter = 0

    def __init__(self, window_size_px):
        self.height_px = window_size_px[1]
        self.width_px = window_size_px[0]
        #self.height_m = 0
        self.horizontal_center = self.width_px * AppSettings.horizontal_center
        self.bg_image = pygame.image.load(AppSettings.bg_image).convert()
        self.sky_image = pygame.image.load(AppSettings.sky_image).convert()
        
    def resize(self, window_size_px): #called when the pygame window is resized by user
        self.height_px = window_size_px[1]
        self.width_px = window_size_px[0]
        self.horizontal_center = self.width_px * AppSettings.horizontal_center

        #self.adjust(self.height_m)

    #def adjust(self, height_m):
        #self.height_m = height_m
        #self.px_per_meter = self.height_px / self.height_m

class Seabed:

    def __init__(self, depth_m):
        self.water_depth = depth_m #AppSettings.initial_water_depth
        self.depth_padding = self.get_water_depth_padding()
        self.water_depth_upper_threshold = 0
        self.water_depth_lower_threshold = 0
        self.set_water_depth_thresholds()
        self.padding_changed = False
        self.history = []
        self.sound_velocity_m_s = AppSettings.echosounder_default_sv
        self.depth_source = DepthSource.NONE
        self.depth_corrected = False

    def set_water_depth(self, depth_m):
        self.water_depth = depth_m
        self.history.append([self.depth_source.value,self.depth_corrected,depth_m])
        if (self.water_depth > self.water_depth_lower_threshold) or (self.water_depth < self.water_depth_upper_threshold):
            self.depth_padding = self.get_water_depth_padding()
            self.set_water_depth_thresholds()
            
    def set_water_depth_thresholds(self):
        self.water_depth_upper_threshold = self.water_depth - self.depth_padding
        self.water_depth_lower_threshold = self.water_depth + (self.depth_padding * 2)

    def get_water_depth_padding(self):
        self.padding_changed = True
        return self.water_depth * AppSettings.bottom_padding_coefficient
        

class ViewPort:

    px_per_meter = 1.0

    def __init__(self, parent_window):
        self.window = parent_window
        self.seabed = Seabed(AppSettings.initial_water_depth)
        self.ctd = CTD()
        self.triplines = Triplines(self.seabed.water_depth, self.ctd.depth)
        self.top_meters = self.triplines.get_past_tripline_depth(0)
        self.bg_image = self.window.bg_image #pygame.image.load(AppSettings.bg_image).convert()
        #self.bg_image = pygame.image.load(AppSettings.bg_image).convert()
        #self.height_px = self.window.height_px
        #self.width_px = self.window.width_px
        self.height_meters = 0
        #self.set_water_depth(AppSettings.initial_water_depth)
        self.redraw()#self.top_meters)
        #self.triplines.set_triplines(self.seabed.water_depth, self.ctd.depth)

    def resize(self):
        #called when window is resized by user
        self.redraw()

    def redraw(self):
        #top_m = top_m #- AppSettings.viewport_padding_top
        #self.top_meters = top_m
        #self.seabed.set_water_depth_padding((self.seabed.water_depth - top_m) * AppSettings.bottom_padding_coefficient)
        self.height_meters = self.seabed.water_depth_lower_threshold - self.top_meters
        self.px_per_meter = self.window.height_px / self.height_meters #todo this method needs to be called when the user resizes the window
        self.ctd.resize_ctd(self.px_per_meter)
        self.scale_background_image()

    def scale_background_image(self):
        #scale the raw background image to the window size
        self.bg_image = pygame.transform.scale(self.window.bg_image, (self.window.width_px, self.window.height_px))
        #crop the image to the ctd cast zoom level
        #rect is left, top, width, height
        top_m = self.top_meters
        if(self.top_meters < 0):
            top_m = 0
        window_px_per_meter = self.window.height_px / self.seabed.water_depth_lower_threshold
        top_px = abs(top_m) * window_px_per_meter #top_px needs to be scaled window height meters
        #top = abs(self.top_meters) * self.window.px_per_meter #top needs to be scaled window height meters
        height = self.window.height_px - top_px
        self.bg_image = self.bg_image.subsurface(0, top_px, self.window.width_px, height)
        #stretch the cropped image to the window size
        self.bg_image = pygame.transform.scale(self.bg_image, (self.window.width_px, self.window.height_px))

    def set_altimeter(self, altitude):
        self.ctd.set_altimeter(altitude)

    def get_background_padding(self):
        if (self.top_meters <= 0):
            return abs(self.top_meters) * self.px_per_meter
        return 0
        

    def get_ypos_px(self, depth):
        return self.px_per_meter * (depth - self.top_meters)

    def set_ctd_depth(self, depth_m):
        self.ctd.set_depth(depth_m)
        #get the tripline at or above the current CTD depth
        new_tripline = self.triplines.get_past_tripline_depth(depth_m)
        tripline_changed = False
        #check if new tripline is different than the active tripline
        if(new_tripline != self.triplines.active_tripline):
            tripline_changed = True
            #self.triplines.set_triplines(self.seabed.water_depth, self.ctd.depth)
            #self.top_meters = self.triplines.active_tripline
            #self.redraw()#self.triplines.active_tripline)
        #set new to active for the next go-around
        self.triplines.active_tripline = new_tripline
        #redraw the screen if changed
        if(tripline_changed):
            self.triplines.set_triplines(self.seabed.water_depth, self.ctd.depth)
            self.top_meters = self.triplines.active_tripline
            self.redraw()#self.triplines.active_tripline)
     
    def set_water_depth(self, water_depth_m):
        self.seabed.depth_source = DepthSource.ECHO
        self.seabed.depth_corrected = False

        if(water_depth_m > 0) and (self.ctd.depth / self.seabed.water_depth_upper_threshold > .75):
            #correct sound velocity Todo fix the flapping issue when ctd is sitting right at the .75 mark
            water_depth_m = (water_depth_m / self.seabed.sound_velocity_m_s) * self.ctd.average_sound_velocity
            self.seabed.depth_corrected = True
        if(self.ctd.altimeter_active):
            #altimeter can be noisy, only plot the good hits
            self.seabed.depth_source = DepthSource.ALTIMETER
            if (self.ctd.altitude > AppSettings.altimeter_minimum_viable_m):
                if(self.ctd.altimeter_correction):
                    self.seabed.depth_corrected = True
                    self.ctd.altitude = (self.ctd.altitude / self.ctd.altimeter_default_sound_velocity) * self.ctd.instantaneous_sound_velocity
                water_depth_m = self.ctd.depth + self.ctd.altitude
            else:
                return

        self.seabed.set_water_depth(water_depth_m)
        if(self.seabed.padding_changed):
            self.seabed.padding_changed = False
            self.triplines.set_triplines(self.seabed.water_depth, self.ctd.depth)
            #self.window.adjust(self.seabed.water_depth_lower_threshold)
            self.redraw()#self.top_meters)

class Triplines:
    
    def __init__(self, initial_depth_m, initial_ctd_depth_m):
        self._surface_padding = int(initial_depth_m * .10) * -1
        self.altitude_triplines = AppSettings.altitude_triplines.copy()
        self.depth_triplines = self.altitude_triplines.copy()
        self.depth_triplines.insert(0,self._surface_padding)
        self.active_tripline = self.depth_triplines[0]
        self.set_triplines(initial_depth_m, initial_ctd_depth_m)

    def set_triplines(self, water_depth_m, ctd_depth_m):
        #get the jitter offset (prevents flapping when CTD is sitting right at the tripline)
        jitter_offset = AppSettings.tripline_jitter_m
        #rebuild the tripline list from defaults
        self.altitude_triplines = AppSettings.altitude_triplines.copy()
        #add the jitter to triplines (moves them up in the water column since they are altitude)
        for i, val in enumerate(self.altitude_triplines):
            self.altitude_triplines[i] += jitter_offset
        #remove any triplines that are greater than the current water depth (triplines that would be in the sky)
        while (len(self.altitude_triplines) > 0 and self.altitude_triplines[0] > water_depth_m):
            self.altitude_triplines.pop(0)
        #remove the offset only for lines still below us
        for i, val in enumerate(self.altitude_triplines):
            if ((val - jitter_offset) > ctd_depth_m):
                self.altitude_triplines[i] -= jitter_offset
        #build a list for depths instead of altitudes
        self.depth_triplines = self.altitude_triplines.copy()
        #calculate the depth of the line from the altitude
        for i, val in enumerate(self.altitude_triplines):
            self.depth_triplines[i] = int(water_depth_m - val)
        #add a zero depth
        self._surface_padding = int(water_depth_m * .10) * -1
        self.depth_triplines.insert(0,self._surface_padding)

    def get_past_tripline_depth(self, ctd_depth_m):
        trip = 0
        for tl in self.depth_triplines:
            if(ctd_depth_m > tl):
                trip = tl
        return int(trip)

    def get_next_tripline_depth(self, depth_m):
        #see if another tripline exists after and return it
        index = self.depth_triplines.index(self.get_past_tripline_depth(depth_m))
        if (index + 1 < len(self.depth_triplines)):
            return self.depth_triplines[index + 1]
        return 0

        
    

