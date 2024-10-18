from re import M
import pygame
from app_settings import AppSettings
from ctd import CTD
from enum import Enum
import threading
import time
import math

class DepthSource(Enum):
    NONE = 0
    ECHO = 1
    ALTIMETER = 2

class ViewWindow:

    def __init__(self, window_size_px):
        self.height_px = window_size_px[1]
        self.width_px = window_size_px[0]
        self.horizontal_center = self.width_px * AppSettings.horizontal_center
        self.bg_image = pygame.image.load(AppSettings.bg_image).convert()
        self.sky_image = pygame.image.load(AppSettings.sky_image).convert()
        self.ship_image = pygame.image.load(AppSettings.ship_image).convert_alpha()
        
    def resize(self, window_size_px): #called when the pygame window is resized by user
        self.height_px = window_size_px[1]
        self.width_px = window_size_px[0]
        self.horizontal_center = self.width_px * AppSettings.horizontal_center

class Seabed:

    def __init__(self, initial_depth_m, initial_ceiling_m, on_padding_changed = None):
        self.water_depth = initial_depth_m 
        self._on_padding_changed = on_padding_changed
        self.depth_padding = self._get_water_depth_padding(initial_ceiling_m)
        self.water_depth_upper_threshold = 0
        self.water_depth_lower_threshold = 0
        self._set_water_depth_thresholds()
        self.history = []
        self.sound_velocity_m_s = AppSettings.echosounder_default_sv
        self.depth_source = DepthSource.NONE
        self.depth_corrected = False

    def set_water_depth(self, depth_m, view_window_ceiling_m):
        self.water_depth = depth_m
        self.history.append([self.depth_source.value, self.depth_corrected, depth_m])
        if (self.water_depth > self.water_depth_lower_threshold) or (self.water_depth < self.water_depth_upper_threshold):
            self.adjust_padding(view_window_ceiling_m)
            if self._on_padding_changed: self._on_padding_changed(self.water_depth_lower_threshold, self.water_depth_upper_threshold)
            
    def adjust_padding(self, view_window_ceiling_m):
        self.depth_padding = self._get_water_depth_padding(view_window_ceiling_m)
        self._set_water_depth_thresholds()

    def _set_water_depth_thresholds(self):
        self.water_depth_upper_threshold = int(self.water_depth - self.depth_padding)
        self.water_depth_lower_threshold = int(self.water_depth + (self.depth_padding))

    def _get_water_depth_padding(self, view_window_ceiling_m):
        return (self.water_depth - view_window_ceiling_m) * AppSettings.bottom_padding_coefficient
        

class ViewPort:

    px_per_meter = 1.0

    def __init__(self, parent_window, instrument, initial_top, initial_bottom):
        self.window = parent_window
        self.screen_top_meters = initial_top
        self.screen_bottom_meters = initial_bottom
        self.bg_image = self.window.bg_image
        self.sky_image = self.window.sky_image
        self.ship_image = self.window.ship_image
        self.height_meters = initial_bottom - initial_top
        self.instrument = instrument
        self.thread_lock = False
        self.thread_kill = False
        self._redraw

    def resize(self):
        #called when window is resized by user
        self._redraw()

    def set_top_and_bottom_meters(self, top, bottom, animate = True):
        if (AppSettings.animate_transitions and animate):
            if(self.thread_lock):
                #animation in progress, tell it to kill itself
                self.thread_kill = True
                #wait for it to die
                while(self.thread_lock):
                      next
            #reset the kill switch
            self.kill = False
            x = threading.Thread(target=self.start_animate, args = (self.screen_top_meters, top, self.screen_bottom_meters, bottom,))
            x.start()
        else:
            self.screen_top_meters = top
            self.screen_bottom_meters = bottom
        self._redraw()

    def start_animate(self, old_top, new_top, old_bottom, new_bottom):
        self.lock = True
        top_dif = new_top - old_top
        bottom_dif = new_bottom - old_bottom
        frame_count = 6
        for this_frame in range(frame_count):
            if self.kill:
                print("animation killed")
                break
            self.screen_top_meters = self._ease_out_cubic(this_frame, old_top, top_dif, frame_count)
            self.screen_bottom_meters = self._ease_out_cubic(this_frame, old_bottom, bottom_dif, frame_count)
            self._redraw()
            time.sleep(.05)
        self.lock = False

    def _ease_cubic(self, this_frame, last_val, val_dif, total_frames):
        frame = this_frame / (total_frames / 2)
        if(frame < 1):
            return val_dif / 2 * frame * frame * frame + last_val
        frame = frame - 2
        return val_dif / 2 * ((frame) * frame * frame + 2) + last_val

    def _ease_out_cubic(self, this_frame, last_val, val_dif, total_frames):
        frame = this_frame / total_frames - 1
        return val_dif * (frame * frame * frame + 1) + last_val

    def _redraw(self):
        self.height_meters = self.screen_bottom_meters - self.screen_top_meters
        self.px_per_meter = self.window.height_px / self.height_meters 
        self.instrument.resize(self.px_per_meter)
        self._scale_background_images()

    def _scale_background_images(self):
        top_m = self.screen_top_meters
        if(self.screen_top_meters < 0):
            top_m = 0
        #calc the window px per meter which is different than the current viewport px per meter depending on ceiling
        window_px_per_meter = self.window.height_px / self.screen_bottom_meters
        top_px = top_m * window_px_per_meter
        height = self.window.height_px - top_px
        #copy and scale the raw background image to the window size before manipulating
        self.bg_image = pygame.transform.scale(self.window.bg_image, (self.window.width_px, self.window.height_px))
        #crop the background image as we get deeper and cross triplines, rectangle is left, top, width, height
        self.bg_image = self.bg_image.subsurface(0, top_px, self.window.width_px, height)
        #stretch the newly cropped image to the window size
        self.bg_image = pygame.transform.scale(self.bg_image, (self.window.width_px, self.window.height_px))
        #copy and scale the raw sky image to the surface padding area (meters at the top of the screen)
        if(self.screen_top_meters <= 0):
            self.sky_image = pygame.transform.scale(self.window.sky_image, (self.window.width_px, window_px_per_meter * abs(self.screen_top_meters)))
        #scale the ship image
        if(self.screen_top_meters <= 0):
            sw = self.px_per_meter * self.window.ship_image.get_width() * .07
            self.ship_image = pygame.transform.scale(self.window.ship_image, (sw, sw * .6))

    def get_background_padding(self):
        if (self.screen_top_meters <= 0):
            return abs(self.screen_top_meters) * self.px_per_meter
        return 0
        
    def get_ypos_px(self, depth):
        return self.px_per_meter * (depth - self.screen_top_meters)

class ViewEngine:

    def __init__(self, vw):
        self.instrument = CTD()
        self.seabed = Seabed(AppSettings.initial_water_depth, Triplines.get_surface_padding(AppSettings.initial_water_depth))
        self.seabed._on_padding_changed = self.on_seabed_padding_changed
        self.triplines = Triplines(self.seabed.water_depth, self.instrument.depth)
        self.triplines._on_tripline_changed = self.on_tripline_changed
        self.viewport = ViewPort(vw, self.instrument, self.triplines.active_tripline, self.seabed.water_depth_lower_threshold)
        
    def set_water_depth(self, water_depth_m):
        self.seabed.depth_source = DepthSource.ECHO
        self.seabed.depth_corrected = False

        #check if altimeter is active and valid
        if(self.instrument.altimeter_active):
            self.seabed.depth_source = DepthSource.ALTIMETER
            if(self.instrument.altimeter_correction):
                self.seabed.depth_corrected = True
                self.instrument.altitude = (self.instrument.altitude / self.instrument.altimeter_default_sound_velocity) * self.instrument.instantaneous_sound_velocity
            water_depth_m = self.instrument.depth + self.instrument.altitude
        else:
            #altimeter is not active use echosounder
            if(AppSettings.echosounder_sv_correction and self.instrument.depth > water_depth_m / 2):
                water_depth_m = (water_depth_m / self.seabed.sound_velocity_m_s) * self.instrument.average_sound_velocity
                self.seabed.depth_corrected = True

        self.seabed.set_water_depth(water_depth_m, self.viewport.screen_top_meters)

    def set_altimeter(self, altitude):
        self.instrument.set_altimeter(altitude)

    def set_instrument_depth(self, depth_m):
        self.instrument.set_depth(depth_m)
        #get the tripline at or above the current instrument depth
        new_tripline = self.triplines.get_last_tripline_depth(depth_m)
        tripline_changed = False
        #check if new tripline is different than the active tripline
        if(new_tripline != self.triplines.active_tripline):
            print('hit tripline')
            tripline_changed = True
        
        #redraw the screen if changed
        if(tripline_changed):
            #need to adjust both the triplines and the padding
            #first approximate the new window height #todo is there a more precise way to do this?
            self.seabed.adjust_padding(new_tripline)

            #this will trigger a redraw
            #self.triplines.set_triplines(self.seabed.water_depth_upper_threshold, self.instrument.depth)
            self.triplines.set_triplines(self.seabed.water_depth, self.instrument.depth)
            #self.viewport.set_top_meters(self.triplines.active_tripline)
            self.viewport.set_top_and_bottom_meters(self.triplines.active_tripline, self.seabed.water_depth_lower_threshold)


    def on_seabed_padding_changed(self, lower_threshold, upper_threshold):
        print("seabed padding has changed")
        self.viewport.set_top_and_bottom_meters(self.viewport.screen_top_meters, lower_threshold)
        self.triplines.set_triplines(self.seabed.water_depth, self.instrument.depth)
        #self.triplines.set_triplines(upper_threshold, self.instrument.depth)

    def on_tripline_changed(self, new_ceiling):
        print("Active Tripline is now: " + str(new_ceiling))
        self.viewport.set_top_and_bottom_meters(new_ceiling, self.seabed.water_depth_lower_threshold)

class Triplines:
    
    def __init__(self, initial_water_depth_m, initial_instrument_depth_m, on_tripline_changed = None):
        self._on_tripline_changed = on_tripline_changed
        #self._surface_padding = self.get_surface_padding(initial_instrument_depth_m)
        #self.depth_triplines = self.altitude_triplines.copy()
        #self.depth_triplines.insert(0,self._surface_padding)
        #self.active_tripline = self.depth_triplines[0]
        #self.water_depth_last_calc = initial_water_depth_m
        self.set_triplines(initial_water_depth_m, initial_instrument_depth_m)

    def set_triplines(self, water_depth_m, instrument_depth_m):
        #get the jitter offset (prevents flapping when instrument is sitting right at the tripline)
        jitter_offset = AppSettings.tripline_jitter_m
        self.depth_triplines = []
        #the working depth is the full water column minus the defined "bottom window" where the display will be in full zoom
        #this is the area we will generate triplines for
        working_depth = water_depth_m - AppSettings.bottom_window_m

        #todo fix bug where working depth is less than or close to the surface

        #insert a tripline right near the bottom for "bottoming ops"
        if(working_depth > AppSettings.bottom_window_m + 20):
            self.depth_triplines.insert(1, int(working_depth))
        window_height = working_depth
        last_window_top = 0
        while(window_height > 80): #todo fix magic number 80
            window_height = int((working_depth - last_window_top) / 2) #1500
            trip = int(last_window_top + window_height) #3k
            self.depth_triplines.append(trip)
            last_window_top = trip
        self.depth_triplines.sort()
        #add a surface tripline that floats above the surface
        self._surface_padding = self.get_surface_padding(water_depth_m)
        self.depth_triplines.insert(0, self._surface_padding)
        #subtract offset for triplines above us (shift lines up)
        for i, val in enumerate(self.depth_triplines):
            if ((val - jitter_offset) < instrument_depth_m):
                self.depth_triplines[i] -= jitter_offset
        self.active_tripline = self.get_last_tripline_depth(instrument_depth_m)
        #save the water depth for the next time we calculate triplines todo why are we doing this?
        self.water_depth_last_calc = water_depth_m
        #call the event
        if self._on_tripline_changed: self._on_tripline_changed(self.active_tripline)
   
    @staticmethod
    def get_surface_padding(water_depth_m):
        return int(water_depth_m * AppSettings.surface_padding_coefficient * -1)

    def get_last_tripline_depth(self, instrument_depth_m):
        trip = 0
        for tl in self.depth_triplines:
            if(instrument_depth_m > tl):
                trip = tl
        return int(trip)

    def get_next_tripline_depth(self, depth_m):
        #see if another tripline exists after and return it
        index = self.depth_triplines.index(self.get_last_tripline_depth(depth_m))
        if (index + 1 < len(self.depth_triplines)):
            return self.depth_triplines[index + 1]
        return 0

        
    

