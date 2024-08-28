
import pygame
pygame.init()
import random
from echosounder import EchoSounder
from seasave_serial import SeaSaveSerial
from app_settings import AppSettings
from primitives import *
from views import *

#constants
DEBUG = True

#pygame variables
default_size = AppSettings.default_screen_size
screen = pygame.display.set_mode(default_size, pygame.RESIZABLE)
pygame.display.set_caption(AppSettings.title)
clock = pygame.time.Clock()
done = False

ctd_depth = 0
upcast = False
scroll_speed = AppSettings.scroll_speed
window = ViewWindow(default_size)
viewport = ViewPort(window, CTD()) #todo make the instrument configurable in the AppSettings
viewengine = ViewEngine(viewport, CTD())

def draw_cast_history():
    while (window.horizontal_center / scroll_speed) < len(viewengine.instrument.history):
      viewengine.instrument.history.pop(0)
    h_length = len(viewengine.instrument.history)
    x = window.horizontal_center - ( scroll_speed * h_length)
    for i in range(h_length):
        y = viewport.get_ypos_px(viewengine.instrument.history[i])
        x += scroll_speed
        pygame.draw.circle(screen, Color.BLUE, (x,y), 1)

def draw_bathy_history():
    while (window.horizontal_center / scroll_speed) < len(viewengine.seabed.history):
      viewengine.seabed.history.pop(0)
    h_length = len(viewengine.seabed.history)
    x = window.horizontal_center - ( scroll_speed * h_length)
    #dps = []
    #bottom mode
    bottom_text_color = Color.ORANGE
    bottom_text = ""
    bottom_subtext = ""
    if (viewengine.seabed.depth_source == DepthSource.ECHO):
        bottom_text =  "Echosounder"
        bottom_text_color = Color.ORANGE2
    elif (viewengine.seabed.depth_source == DepthSource.ALTIMETER):
        bottom_text = "Altimeter"
        bottom_text_color = Color.ORANGE3
    if(viewengine.seabed.depth_corrected):
        bottom_subtext = "Corrected"

    for i in range(h_length):
        h_src = viewengine.seabed.history[i][0] #depth source
        h_corr = viewengine.seabed.history[i][1] #depth corrected?
        h_val = viewengine.seabed.history[i][2] # depth value
        y = viewport.get_ypos_px(h_val)
        x += scroll_speed
        thk = 3 if h_corr else 2 #fatter circle if corrected
        col = Color.ORANGE if (h_src == 1) else Color.ORANGE3
        
        pygame.draw.circle(screen, col, (x,y), 2)
    str_depth_val = float2str(viewengine.seabed.history[-1][2]) + "m "
    
    text_ypos = viewport.get_ypos_px(viewengine.seabed.water_depth_lower_threshold - (viewengine.seabed.water_depth_lower_threshold - viewengine.seabed.water_depth_upper_threshold))
    text_ypos = viewport.get_ypos_px(viewengine.seabed.water_depth_upper_threshold + (viewengine.seabed.depth_padding/2))
    text_offset = render_text(str_depth_val, window.horizontal_center + 10, text_ypos, bottom_text_color, screen)
    
    render_text([bottom_text, bottom_subtext], window.horizontal_center + text_offset[0] * 1.1, text_ypos, bottom_text_color, screen)
    
#setup echosounder
def echo_callback(message):
    return
def seasave_callback(object):
    return
    #if(random.uniform(0,10) > 9):
        #print(object.depth, object.altitude, object.sv_average)
echo = EchoSounder(AppSettings.echosounder_udp_port, echo_callback)
seasave = SeaSaveSerial("COM5", 9600, seasave_callback)

if DEBUG:
    #005 is deep with altim issue
    seasave.start_simulate('EN695_004_test.cnv') #004 throws error, #001 is all messed up, 007 has flapping issue on upcast, 008 has weird padding
    echo.start_simulate(seasave.debug_max_depth_of_cast + 10, 1500, .4)
    
else:
    echo.start_receive()
    seasave.start_receive()

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

    #screen background
    screen.fill(Color.BLUE) #you should never see this it's behind the other bg images
    screen.blit(viewport.sky_image,(0,0))
    screen.blit(viewport.bg_image,(0, viewport.get_background_padding()))

    #for testing only
    if DEBUG:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        ctd_depth = (viewengine.seabed.water_depth_lower_threshold / window.width_px) * mouse_x
        
    else:
        
        if viewport.instrument.depth > viewport.seabed.water_depth:
            upcast = True

        if upcast:
            ctd_depth = ctd_depth - .6
            if ctd_depth < 5:
                done = True
        else:
            ctd_depth = ctd_depth + 1
    

    viewengine.set_instrument_depth(seasave.depth)
    viewengine.set_altimeter(seasave.altitude)
    viewengine.instrument.average_sound_velocity = seasave.sv_average
    viewengine.instrument.instantaneous_sound_velocity = seasave.sv_instantaneous
    viewengine.seabed.sound_velocity_m_s = echo.sound_velocity
    viewengine.set_water_depth(echo.depth)

    ctd_ypos = viewport.get_ypos_px(viewengine.instrument.depth) - viewengine.instrument.height_px
   
    #draw transition line
    #(x,y)
    
    if 1 > 0:
        for tl in viewengine.triplines.depth_triplines:
            if(tl > viewengine.instrument.depth):

                tripline_y_pos = viewport.get_ypos_px(tl)
                #pygame.draw.line(screen, Color.YELLOW, (0, tripline_y_pos), (window.width_px, tripline_y_pos), 1)
                #trip_label = "m from bottom"
                draw_horizontal_line(screen, tripline_y_pos, Color.YELLOW, 60)
                #next_depth = viewport.triplines.get_next_tripline_depth(viewport.instrument.depth)
                trip_label_a = float2str(viewengine.seabed.water_depth - tl) + "m from bottom"
                trip_label_b = str(tl) + "m deep"
                render_text([trip_label_a, trip_label_b], 0, tripline_y_pos, Color.YELLOW, screen)
        #warntext_a = FONT.render(trip_label_a, True, Color.YELLOW)
        #warntext_b = FONT.render(trip_label_b, True, Color.YELLOW)
        #screen.blit (warntext_a, (0, tripline_y_pos))
        #screen.blit (warntext_b, (0, tripline_y_pos + AppSettings.font_size))

    wd = FONT.render(float2str(viewengine.instrument.depth) + 'm', True, Color.LIGHTBLUE)
    screen.blit(wd, ((window.horizontal_center) + viewengine.instrument.width_px, ctd_ypos))

    draw_cast_history()
    draw_bathy_history()

    if(viewengine.instrument.rotate):
        #counterclockwise
        viewengine.instrument.angle += .1
        if(viewengine.instrument.angle >= 3):
            viewengine.instrument.rotate = False
    #else:
    #    #clockwise
    #    viewport.instrument.angle -= .1
    #    if(viewport.instrument.angle <= -3):
    #        viewport.instrument.rotate = True
    #rt = pygame.transform.rotate(viewport.instrument.instrument_image_scaled, viewport.instrument.angle)
    
    screen.blit(viewengine.instrument.image_scaled, ((window.horizontal_center) - (viewengine.instrument.width_px / 2),ctd_ypos, viewengine.instrument.width_px, viewengine.instrument.height_px))
    
    if DEBUG:
        # show the bottom depth window
        yt = viewport.get_ypos_px(viewengine.seabed.water_depth_upper_threshold)
        yb = viewport.get_ypos_px(viewengine.seabed.water_depth_lower_threshold) - 2
        tt = LITTLEFONT.render(str(viewengine.seabed.water_depth_upper_threshold) + 'm', True, Color.WHITE)
        tb = LITTLEFONT.render(str(viewengine.seabed.water_depth_lower_threshold) + 'm', True, Color.WHITE)
        screen.blit(tt, (5, yt))
        screen.blit(tb, (5, yb - 15))
        pygame.draw.line(screen, Color.WHITE, (0, yt), (window.width_px, yt), 1)
        pygame.draw.line(screen, Color.WHITE, (0, yb), (window.width_px, yb), 1)

    pygame.display.flip()
    clock.tick(AppSettings.frame_rate)
pygame.quit()


