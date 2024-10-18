
import pygame
pygame.init()
import random
from echosounder import EchoSounder
from seasave_serial import SeaSaveSerial
from app_settings import AppSettings
from primitives import *
from views import *

#constants
DEBUG = False
debug_water_depth = 1000
default_size = AppSettings.default_screen_size
screen = pygame.display.set_mode(default_size, pygame.RESIZABLE)
pygame.display.set_caption(AppSettings.title)
clock = pygame.time.Clock()
done = False

#set the icon
dhtb_icon = pygame.image.load('images/dhtb_icon_trans_2.png')
pygame.display.set_icon(dhtb_icon)

ctd_depth = 0
upcast = False
scroll_speed = AppSettings.scroll_speed
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
        y = viewport.get_ypos_px(viewengine.instrument.history[i])
        x += scroll_speed
        pygame.draw.circle(screen, Color.BLUE, (x,y), 1)

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
        y = viewport.get_ypos_px(h_val)
        x += scroll_speed
        thk = 3 if h_corr else 2 #fatter circle if corrected
        col = Color.ORANGE if (h_src == 1) else Color.ORANGE3
        pygame.draw.circle(screen, col, (x,y), thk)

def draw_threaded_surface(surface, position_x_y):
    #since animations run in another thread we need to make sure the surface isn't locked
    while surface.get_locked():
        next
    #if you're here the surface isn't locked so blit to the screen
    #todo there's an occasional exception that the surface is locked sorry if if happens
    screen.blit(surface, position_x_y)
    
#setup echosounder
def echo_callback(message):
    return
def seasave_callback(object):
    return
    #if(random.uniform(0,10) > 9):
        #print(object.depth, object.altitude, object.sv_average)
echo = EchoSounder(AppSettings.echosounder_udp_port, echo_callback)
seasave = SeaSaveSerial("COM5", 9600, seasave_callback)


if AppSettings.playback_mode:
    #001 hit the bottom (for real)
    #005 is deep with altim issue
    #008 shallow with tripline adjustment issue on upcast
    #003 is nice medium case demo
    #004 has tripline adjustment issue
    seasave.start_simulate(AppSettings.playback_file)
    echo.start_simulate(seasave.debug_max_depth_of_cast + 10, 1500, .4)
    
else:
    next
    #echo.start_receive()
    #seasave.start_receive()

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

    #screen background, draw first so everything else is on top
    #draw the sky image
    draw_threaded_surface(viewport.sky_image, (0,0))
    #draw the background image
    draw_threaded_surface(viewport.bg_image,(0, viewport.get_background_padding()))
    #draw the ship image
    shx = viewport.ship_image.get_width() / 2
    shy = viewport.ship_image.get_height()
    draw_threaded_surface(viewport.ship_image,(window.horizontal_center - shx, viewport.get_background_padding() - shy))

    #for testing only
    if DEBUG:
        #debug mode the ctd depth is the mouse position on the screen
        mouse_x, mouse_y = pygame.mouse.get_pos()
        #scale the instrument depth to the screen
        debug_instrument_depth = (viewengine.seabed.water_depth_lower_threshold / window.height_px) * mouse_x
        debug_water_depth = debug_water_depth + [-1,1][random.randrange(2)]
        viewengine.set_instrument_depth(debug_instrument_depth)
        viewengine.set_altimeter(debug_water_depth - debug_instrument_depth)
        viewengine.instrument.average_sound_velocity = 1500
        viewengine.instrument.instantaneous_sound_velocity = 1500
        viewengine.seabed.sound_velocity_m_s = 1500
        viewengine.set_water_depth(debug_water_depth)
        ctd_ypos = viewport.get_ypos_px(viewengine.instrument.depth) - viewengine.instrument.height_px
    else:
        #normal mode use the inputs or the file playback values
        viewengine.set_instrument_depth(seasave.depth)
        viewengine.set_altimeter(seasave.altitude)
        viewengine.instrument.average_sound_velocity = seasave.sv_average
        viewengine.instrument.instantaneous_sound_velocity = seasave.sv_instantaneous
        viewengine.seabed.sound_velocity_m_s = echo.sound_velocity
        viewengine.set_water_depth(echo.depth)
        ctd_ypos = viewport.get_ypos_px(viewengine.instrument.depth) - viewengine.instrument.height_px
   
    #draw transition triplines
    if AppSettings.draw_triplines:
        for tl in viewengine.triplines.depth_triplines:
            if(tl > viewengine.instrument.depth):

                tripline_y_pos = viewport.get_ypos_px(tl)
                draw_horizontal_line(screen, tripline_y_pos, Color.YELLOW, 60)
                #next_depth = viewport.triplines.get_next_tripline_depth(viewport.instrument.depth)
                trip_label_a = str(int(viewengine.seabed.water_depth - tl)) + "m from bottom"
                trip_label_b = str(tl) + "m deep"
                render_text([trip_label_a, trip_label_b], 0, tripline_y_pos, Color.YELLOW, screen, -10)
    
    #draw countdown
    meters_to_go = int(viewengine.seabed.water_depth - viewengine.instrument.depth)
    if(meters_to_go <= AppSettings.countdown_distance_m and meters_to_go >= 0):
        ttb = FONT.render('To the Bottom', True, Color.WHITE)
        hugefont_size = int(AppSettings.font_size * 4)
        hugefont = pygame.font.SysFont(AppSettings.font, hugefont_size)
        mtg_text = hugefont.render(str(meters_to_go) + 'm', True, Color.WHITE)
        
        screen.blit(mtg_text, (50, window.height_px - (hugefont_size * 2)))
        screen.blit(ttb, (50, window.height_px - hugefont_size))

    #draw history
    draw_cast_history()
    draw_bathy_history()

    #draw the instrument
    screen.blit(viewengine.instrument.image_scaled, ((window.horizontal_center) - (viewengine.instrument.width_px / 2),ctd_ypos, viewengine.instrument.width_px, viewengine.instrument.height_px))
    
    #draw instrument depth value
    wd = FONT.render(float2str(viewengine.instrument.depth) + 'm', True, Color.LIGHTBLUE)
    screen.blit(wd, ((window.horizontal_center) + viewengine.instrument.width_px, ctd_ypos))

    #draw the depth source and value
    #todo depth source should be its own class eventually since this is a mess
    depth_source_text_color = Color.ORANGE
    depth_source_text = ""
    depth_source_subtext = ""
    if (viewengine.seabed.depth_source == DepthSource.ECHO):
        depth_source_text =  "Echosounder"
        depth_source_text_color = Color.ORANGE2
    elif (viewengine.seabed.depth_source == DepthSource.ALTIMETER):
        depth_source_text = "Altimeter"
        depth_source_text_color = Color.ORANGE3
    if(viewengine.seabed.depth_corrected):
        depth_source_subtext = "Corrected"
    str_depth_val = float2str(viewengine.seabed.water_depth) + "m " 
    
    #depth_text_ypos = viewport.get_ypos_px(viewengine.seabed.water_depth_lower_threshold - (viewengine.seabed.water_depth_lower_threshold - viewengine.seabed.water_depth_upper_threshold))
    depth_text_ypos = viewport.get_ypos_px(viewengine.seabed.water_depth_upper_threshold + (viewengine.seabed.depth_padding/2))
    #text_ypos = viewport.get_ypos_px(viewengine.seabed.water_depth)
    depth_text_offset = render_text(str_depth_val, window.horizontal_center + 10, depth_text_ypos, depth_source_text_color, screen)
    
    render_text([depth_source_text, depth_source_subtext], window.horizontal_center + depth_text_offset[0] * 1.1, depth_text_ypos, depth_source_text_color, screen)
    #sub_y = viewport.get_ypos_px(viewengine.seabed.water_depth_upper_threshold)
    #render_text([bottom_subtext], 10, sub_y,bottom_text_color, screen)

    #draw the seabed window
    if AppSettings.draw_seabed_window:
        # show the bottom depth window
        yt = viewport.get_ypos_px(viewengine.seabed.water_depth_upper_threshold)
        yb = viewport.get_ypos_px(viewengine.seabed.water_depth_lower_threshold) - 2
        tt = LITTLEFONT.render(str(viewengine.seabed.water_depth_upper_threshold) + 'm', True, Color.WHITE)
        tb = LITTLEFONT.render(str(viewengine.seabed.water_depth_lower_threshold) + 'm', True, Color.WHITE)
        screen.blit(tt, (5, yt))
        screen.blit(tb, (5, yb - 15))
        pygame.draw.line(screen, Color.WHITE, (0, yt), (window.width_px, yt), 1)
        pygame.draw.line(screen, Color.WHITE, (0, yb), (window.width_px, yb), 1)

    #pygame.display.flip()
    clock.tick(AppSettings.frame_rate)
pygame.quit()


