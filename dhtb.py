import pygame
pygame.init()
from app_settings import AppSettings
from primitives import *
from views import *
import console
from io_controller import *

#constants
default_size = AppSettings.default_screen_size
screen = pygame.display.set_mode(default_size, pygame.RESIZABLE)
clock = pygame.time.Clock()
done = False

#setup the window
dhtb_icon = pygame.image.load('images/dhtb_icon_trans_2.png')
pygame.display.set_icon(dhtb_icon)
pygame.display.set_caption(AppSettings.title)

scroll_speed = AppSettings.scroll_speed

#these three little guys are the main objects that control the application
window = ViewWindow(default_size)
viewengine = ViewEngine(window)
viewport = viewengine.viewport

#calling this resize event on startup makes sure that images are scaled and placed correctly before data acquisition
viewport.resize()

def draw_cast_history():
    if not viewengine.instrument.history:
        return
    #make sure we're only storing enough history to fill the screen and not leaking memory
    while (window.horizontal_center / scroll_speed) < len(viewengine.instrument.history):
      viewengine.instrument.history.pop(0)
    h_length = len(viewengine.instrument.history)
    x = window.horizontal_center - ( scroll_speed * h_length)
    for i in range(h_length):
        depth = viewengine.instrument.history[i]
        y = viewport.get_ypos_px(depth)
        x += scroll_speed
        #don't draw if zero (instrument not acquiring)
        if(depth != 0):
            pygame.draw.circle(screen, Color.BLUE, (x,y), 1)

def draw_raw_altimeter_history():
    #reference to the altimeter history because that's a lot to type 5 times
    raw_history = viewengine.instrument.altimeter.raw_altitude_history
    if not raw_history:
        return
    #make sure we're only storing enough history to fill the screen and not leaking memory
    while (window.horizontal_center / scroll_speed) < len(raw_history):
      raw_history.pop(0)
    h_length = len(raw_history)
    x = window.horizontal_center - ( scroll_speed * h_length)
    for i in range(h_length):
        alt = raw_history[i]
        if(alt == None):
            return
        depth = viewengine.instrument.history[i]
        y = viewport.get_ypos_px(alt + depth)
        x += scroll_speed
        #don't draw if zero (instrument not acquiring)
        if(alt > viewengine.instrument.altimeter.blanking_range and alt < viewengine.instrument.altimeter.max_range):
            pygame.draw.circle(screen, Color.YELLOW, (x,y), 1)

def draw_bathy_history():
    if not viewengine.seabed.history:
        return
    #make sure we're only storing enough history to fill the screen and not leaking memory
    while (window.horizontal_center / scroll_speed) < len(viewengine.seabed.history):
      viewengine.seabed.history.pop(0)
    #plot the history
    h_length = len(viewengine.seabed.history)
    x = window.horizontal_center - ( scroll_speed * h_length)
    for i in range(h_length):
        #depth history is a 2D array of [depth source, depth corrected, depth in meters]
        h_src = viewengine.seabed.history[i][0] #depth source
        h_corr = viewengine.seabed.history[i][1] #depth corrected?
        h_val = viewengine.seabed.history[i][2] # depth value
        x += scroll_speed
        if(h_val != None):
            y = viewport.get_ypos_px(h_val)
            thk = 3 if h_corr else 2 #fatter circle if corrected
            col = AppSettings.echosounder_color if (h_src == 1) else AppSettings.altimeter_color
            pygame.draw.circle(screen, col, (x,y), thk)

def draw_threaded_surface(surface, position_x_y):
    #since animations run in another thread we need to make sure the surface isn't locked
    while surface.get_locked():
        next
    #if you're here the surface isn't locked so blit to the screen
    #todo there's a rare bug where this throws an exception, probably a thread thing
    screen.blit(surface, position_x_y)
    
#the console is used throughout the application for user display and logging
console.init()

#the acq device is the io class to accomodate many different types of sensors
acq_device = IOController()

#declare playback buttons even if we're not in playback mode
speed_button = Button(200,200,'images/faster_icon.png', .3)
slow_button = Button(150,200,'images/slower_icon.png', .3)
reset_button = Button(100,200,'images/reset_icon.png', .3)

#main program loop
while not done:
    #listen for window resizing event
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
        elif event.type == pygame.VIDEORESIZE:
            window.resize(event.size)
            viewport.resize()
            screen = pygame.display.set_mode((window.width_px, window.height_px), pygame.RESIZABLE)

    viewengine.set_instrument(acq_device.instrument_depth, 
                              acq_device.instrument_pressure, 
                              acq_device.instrument_altitude, 
                              acq_device.instrument_sv, 
                              acq_device.instrument_sv_average)
    viewengine.set_water_depth(acq_device.echosounder_depth, acq_device.echosounder_sv)

    #screen background, draw this first so everything else is on top
    #draw the sky image
    draw_threaded_surface(viewport.sky_image, (0,0))
    #draw the background image
    draw_threaded_surface(viewport.bg_image,(0, viewport.get_background_padding()))
    #draw the ship image
    shx = viewport.ship_image.get_width() / 2
    shy = viewport.ship_image.get_height()
    draw_threaded_surface(viewport.ship_image,(window.horizontal_center - shx, viewport.get_background_padding() - shy))

    if(AppSettings.playback_mode):
        if(speed_button.draw(screen)):
            if(acq_device.io_device.playback_speed >= .002):
                acq_device.io_device.playback_speed -= .001
            console.dhtb_console.add_message('playback speed = ' + str(int(1 / acq_device.io_device.playback_speed)) + ' scans per second')
        if(slow_button.draw(screen)):
            acq_device.io_device.playback_speed += .001
            console.dhtb_console.add_message('playback speed = ' + str(int(1 / acq_device.io_device.playback_speed)) + ' scans per second')
        if(reset_button.draw(screen)):
            #first kill the file reader thread
            acq_device.io_device.kill()
            #then refresh the IOController
            #acq_device = IOController()
            console.dhtb_console.add_message('Restarting file playback')

    ctd_ypos = viewport.get_ypos_px(viewengine.instrument.depth) - viewengine.instrument.height_px
   
    #draw transition triplines
    if AppSettings.draw_triplines:
        for tl in viewengine.triplines.depth_triplines:
            if(tl > viewengine.instrument.depth):

                tripline_y_pos = viewport.get_ypos_px(tl)
                draw_horizontal_line(screen, tripline_y_pos, Color.YELLOW, 60)
                #next_depth = viewport.triplines.get_next_tripline_depth(viewport.instrument.depth)
                trip_label_a = ''
                if(viewengine.seabed.water_depth != None):
                    trip_label_a = str(int(viewengine.seabed.water_depth - tl)) + "m from bottom"
                trip_label_b = str(tl) + "m deep"
                render_text([trip_label_a, trip_label_b], 0, tripline_y_pos, Color.YELLOW, screen, -20)
    
    #draw history
    draw_cast_history()
    draw_bathy_history()
    draw_raw_altimeter_history()

    #draw the instrument if it's acquiring
    if(acq_device.io_device._acquiring):
        screen.blit(viewengine.instrument.image_scaled, ((window.horizontal_center) - (viewengine.instrument.width_px / 2),ctd_ypos, viewengine.instrument.width_px, viewengine.instrument.height_px))
        #draw instrument depth value
        wd = render_text(float2str(viewengine.instrument.depth) + 'm', (window.horizontal_center) + viewengine.instrument.width_px, ctd_ypos, Color.LIGHTBLUE, screen, 20)

    #draw the depth source and value if it's acquiring or not timed out "None"
    #todo depth source should be its own class eventually since this is a mess
    if(not viewengine.seabed.water_depth == None):
        depth_source_text_color = Color.ORANGE
        depth_source_text = ""
        #depth_source_subtext = ""
        if (viewengine.seabed.depth_source == DepthSource.ECHO):
            depth_source_text =  "Echosounder"
            depth_source_text_color = AppSettings.echosounder_color
        elif (viewengine.seabed.depth_source == DepthSource.ALTIMETER):
            depth_source_text = "Altimeter"
            depth_source_text_color = AppSettings.altimeter_color
        
        str_depth_val = float2str(viewengine.seabed.water_depth) + "m " 
    
        depth_text_ypos = viewport.get_ypos_px(viewengine.seabed.water_depth_upper_threshold + (viewengine.seabed.depth_padding/2))
        depth_text_xpos = (window.horizontal_center) + viewengine.instrument.width_px
        depth_text_offset = render_text(str_depth_val, depth_text_xpos, depth_text_ypos, depth_source_text_color, screen, 20)
        depth_text_offset = render_text(depth_source_text, depth_text_xpos, depth_text_ypos + (depth_text_offset[1]), depth_source_text_color, screen, -5)
        if(viewengine.seabed.depth_corrected):
            render_text("corrected for svl=" + str(int(viewengine.seabed.sound_velocity)) + "m/s", depth_text_xpos, depth_text_offset[3] + (depth_text_offset[1]), depth_source_text_color, screen, -18)

    #draw countdown
    #if greater than 5m from the bottom display integer, if very close display decimal for precision
    #draw this last so it displays on top of all of the other stuff
    if(viewengine.seabed.water_depth != None):
        meters_to_go = round(viewengine.seabed.water_depth - viewengine.instrument.depth,1)
        if(meters_to_go >= 5):
            meters_to_go = int(meters_to_go)
        if(meters_to_go <= AppSettings.countdown_distance_m and meters_to_go >= 0):
            hugefont_size = int(AppSettings.font_size * 4)
            hugefont_adjust = hugefont_size - AppSettings.font_size
            render_text(str(meters_to_go) + 'm', 50, window.height_px - (hugefont_size * 2), Color.WHITE, screen, hugefont_adjust )
            render_text(' To the Bottom', 50, window.height_px - (hugefont_size), Color.WHITE, screen, 0 )

    #draw the seabed window
    if AppSettings.draw_seabed_window:
        # show the bottom depth window
        yt = viewport.get_ypos_px(viewengine.seabed.water_depth_upper_threshold)
        yb = viewport.get_ypos_px(viewengine.seabed.water_depth_lower_threshold) - 2
        render_text(str(viewengine.seabed.water_depth_upper_threshold) + 'm', 0, yt, Color.WHITE, screen, -18)
        render_text(str(viewengine.seabed.water_depth_lower_threshold) + 'm', 0, yb -18, Color.WHITE, screen, -18)
        pygame.draw.line(screen, Color.WHITE, (0, yt), (window.width_px, yt), 1)
        pygame.draw.line(screen, Color.WHITE, (0, yb), (window.width_px, yb), 1)

    #draw the console messages
    #start y position 35px from the screen top
    cyp = 80
    for message in console.dhtb_console.message_queue:
        line_offset = render_text(message[0], 5, cyp, Color.WHITE, screen, -18)
        cyp += line_offset[1]

    if AppSettings.draw_screen_top:
        v = float2str
        yt = viewport.get_ypos_px(viewengine.viewport.screen_top_meters)
        render_text((float2str(viewengine.viewport.screen_top_meters)) + 'm', 0, yt, Color.WHITE, screen, -18)
        testval = viewengine.viewport.screen_bottom_meters - viewengine.viewport.screen_top_meters
        render_text((float2str(testval)) + 'm', 0, yt + 18, Color.WHITE, screen, -18)

    if AppSettings.draw_params:
        yp = viewengine.viewport.window.height_px/2
        values = [
            'ctd_sv ' + (float2str(viewengine.instrument.sound_velocity)) + 'm/s',
            'ctd_sv_avg ' + (float2str(viewengine.instrument.average_sound_velocity)) + 'm/s',
            'echosounder_sv ' + (float2str(acq_device.echosounder_sv)) + 'm/s',
            'applied_sv ' + (float2str(viewengine.seabed.sound_velocity)) + 'm/s',
            'inst_depth ' + (float2str(acq_device.instrument_depth)),
            'inst_pressure ' + (float2str(acq_device.instrument_pressure)),
            'inst_altitude ' + (float2str(acq_device.instrument_altitude)),
            'acquiring ' + str(acq_device.io_device._acquiring)
        ]
        render_text(values, 0, yp, Color.WHITE,screen, -20)


    pygame.display.flip()
    clock.tick(AppSettings.frame_rate)
pygame.quit()


