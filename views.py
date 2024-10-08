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
        self.horizontal_center = self.width_px * AppSettings.horizontal_center
        self.bg_image = pygame.image.load(AppSettings.bg_image).convert()
        self.sky_image = pygame.image.load(AppSettings.sky_image).convert()
        
    def resize(self, window_size_px): #called when the pygame window is resized by user
        self.height_px = window_size_px[1]
        self.width_px = window_size_px[0]
        self.horizontal_center = self.width_px * AppSettings.horizontal_center


class Seabed:

    def __init__(self, depth_m):
        self.water_depth = depth_m 
        self.depth_padding = self._get_water_depth_padding(depth_m)
        self.water_depth_upper_threshold = 0
        self.water_depth_lower_threshold = 0
        self._set_water_depth_thresholds()
        self.padding_changed = False
        self.history = []
        self.sound_velocity_m_s = AppSettings.echosounder_default_sv
        self.depth_source = DepthSource.NONE
        self.depth_corrected = False

    def set_water_depth(self, depth_m, view_window_height_m):
        self.water_depth = depth_m
        self.history.append([self.depth_source.value,self.depth_corrected,depth_m])
        if (self.water_depth > self.water_depth_lower_threshold) or (self.water_depth < self.water_depth_upper_threshold):
            self.adjust_padding(view_window_height_m)

    def adjust_padding(self, view_window_height_m):
        self.depth_padding = self._get_water_depth_padding(view_window_height_m)
        self._set_water_depth_thresholds()
            
    def _set_water_depth_thresholds(self):
        self.water_depth_upper_threshold = self.water_depth - self.depth_padding
        self.water_depth_lower_threshold = self.water_depth + (self.depth_padding * 2)

    def _get_water_depth_padding(self, view_window_height_m):
        self.padding_changed = True
        return view_window_height_m * AppSettings.bottom_padding_coefficient
        

class ViewPort:

    px_per_meter = 1.0

    def __init__(self, parent_window):
        self.window = parent_window
        #self._seabed = Seabed(AppSettings.initial_water_depth)
        #self._ctd = CTD()
        #self._triplines = Triplines(self.seabed.water_depth, self.ctd.depth)
        self.top_meters = 0
        self.bottom_meters = 0
        self.bg_image = self.window.bg_image
        self.height_meters = 0
        self.ctd = CTD()

    def resize(self):
        #called when window is resized by user
        self.redraw()

    def set_bottom_meters(self, m):
        self.bottom_meters = m
        self._redraw()

    def set_top_meters(self, m):
        self.top_meters = m
        self._redraw()

    def _redraw(self):
        self.height_meters = self.bottom_meters - self.top_meters
        self.px_per_meter = self.window.height_px / self.height_meters 
        self.ctd.resize_ctd(self.px_per_meter)
        self._scale_background_image()

    def _scale_background_image(self):
        #load the raw image scale the raw background image to the window size
        #self.bg_image = pygame.transform.scale(self.window.bg_image, (self.window.width_px, self.window.height_px))
        #crop the image to the ctd cast zoom level
        #rect is left, top, width, height
        top_m = self.top_meters
        if(self.top_meters < 0):
            top_m = 0
        window_px_per_meter = self.window.height_px / self.bottom_meters
        top_px = abs(top_m) * window_px_per_meter #top_px needs to be scaled window height meters
        height = self.window.height_px - top_px
        #cut the background image as we get deeper and cross triplines
        self.bg_image = self.window.bg_image.subsurface(0, top_px, self.window.width_px, height)
        #stretch the cropped image to the window size
        self.bg_image = pygame.transform.scale(self.bg_image, (self.window.width_px, self.window.height_px))

    def get_background_padding(self):
        if (self.top_meters <= 0):
            return abs(self.top_meters) * self.px_per_meter
        return 0
        
    def get_ypos_px(self, depth):
        return self.px_per_meter * (depth - self.top_meters)

class ViewEngine:

    def __init__(self, vp):
        self.ctd = CTD()
        self.seabed = Seabed(AppSettings.initial_water_depth)
        self.triplines = Triplines(self.seabed.water_depth, self.ctd.depth)
        self.viewport = vp
        vp.ctd = self.ctd

    def set_water_depth(self, water_depth_m):
        self.seabed.depth_source = DepthSource.ECHO
        self.seabed.depth_corrected = False

        if(self.ctd.altimeter_active):
            self.seabed.depth_source = DepthSource.ALTIMETER
            if(self.ctd.altimeter_correction):
                self.seabed.depth_corrected = True
                self.ctd.altitude = (self.ctd.altitude / self.ctd.altimeter_default_sound_velocity) * self.ctd.instantaneous_sound_velocity
            water_depth_m = self.ctd.depth + self.ctd.altitude
        else:
            #altimeter is not active use echosounder
            if(AppSettings.echosounder_sv_correction):
                water_depth_m = (water_depth_m / self.seabed.sound_velocity_m_s) * self.ctd.average_sound_velocity
                self.seabed.depth_corrected = True

        self.seabed.set_water_depth(water_depth_m, self.viewport.height_meters)
        if(self.seabed.padding_changed):
            self.viewport.set_bottom_meters(self.seabed.water_depth_lower_threshold)
            #reset the sentinel todo make this feature a callback function
            self.seabed.padding_changed = False
            self.triplines.set_triplines(self.seabed.water_depth_upper_threshold, self.ctd.depth)
            #self.viewport.redraw()

    def set_altimeter(self, altitude):
        self.ctd.set_altimeter(altitude)

    def set_ctd_depth(self, depth_m):
        self.ctd.set_depth(depth_m)
        #get the tripline at or above the current CTD depth
        new_tripline = self.triplines.get_last_tripline_depth(depth_m)
        tripline_changed = False
        #check if new tripline is different than the active tripline
        if(new_tripline != self.triplines.active_tripline):
            print('hit tripline')
            tripline_changed = True
        #self.triplines.active_tripline = new_tripline
        
        #redraw the screen if changed
        if(tripline_changed):
            self.triplines.set_triplines(self.seabed.water_depth_upper_threshold, self.ctd.depth)
            self.viewport.set_top_meters(self.triplines.active_tripline)
            #self.viewport.redraw()

class Triplines:
    
    def __init__(self, initial_depth_m, initial_ctd_depth_m):
        self._surface_padding = int(initial_depth_m * AppSettings.surface_padding * -1)
        self.altitude_triplines = AppSettings.altitude_triplines.copy()
        self.depth_triplines = self.altitude_triplines.copy()
        self.depth_triplines.insert(0,self._surface_padding)
        self.active_tripline = self.depth_triplines[0]
        self.set_triplines(initial_depth_m, initial_ctd_depth_m)

    def set_triplines(self, water_depth_m, ctd_depth_m):
        #get the jitter offset (prevents flapping when CTD is sitting right at the tripline)
        jitter_offset = AppSettings.tripline_jitter_m
        if(False):
            
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
            #this is what's actually used in the display
            self.depth_triplines = self.altitude_triplines.copy()
            #calculate the depth of the line from the altitude
            for i, val in enumerate(self.altitude_triplines):
                self.depth_triplines[i] = int(water_depth_m - val)
            #add a surface tripline that floats above the surface
            self._surface_padding = int(water_depth_m * AppSettings.surface_padding) * -1
            self.depth_triplines.insert(0,self._surface_padding)
            self.active_tripline = self.get_last_tripline_depth(ctd_depth_m)
        else:
            self.depth_triplines = []
            self.altitude_triplines = []
            #the working depth is the full water column minus the defined "bottom window" where the display will be in full zoom
            working_depth = water_depth_m - AppSettings.bottom_window_m
            self.depth_triplines.insert(1, int(working_depth))
            window_height = working_depth
            last_window_top = 0
            while(window_height > 80): 
                window_height = int((working_depth - last_window_top) / 2) #1500
                trip = int(last_window_top + window_height) #3k
                self.depth_triplines.append(trip)
                last_window_top = trip
            self.depth_triplines.sort()
            #add a surface tripline that floats above the surface
            self._surface_padding = int(water_depth_m * AppSettings.surface_padding * -1)
            self.depth_triplines.insert(0, self._surface_padding)
            #subtract offset for triplines above us (shift lines up)
            for i, val in enumerate(self.depth_triplines):
                if ((val - jitter_offset) < ctd_depth_m):
                    self.depth_triplines[i] -= jitter_offset
            self.active_tripline = self.get_last_tripline_depth(ctd_depth_m)

    def __depth_to_altitude(self, depth_m, bottom_depth_m):
        return int(bottom_depth_m - depth_m)

    def __altitude_to_depth(self, altitude_m, bottom_depth_m):
        return 
        

    def get_last_tripline_depth(self, ctd_depth_m):
        trip = 0
        for tl in self.depth_triplines:
            if(ctd_depth_m > tl):
                trip = tl
        return int(trip)

    def get_next_tripline_depth(self, depth_m):
        #see if another tripline exists after and return it
        index = self.depth_triplines.index(self.get_last_tripline_depth(depth_m))
        if (index + 1 < len(self.depth_triplines)):
            return self.depth_triplines[index + 1]
        return 0

        
    

