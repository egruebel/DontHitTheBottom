
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
#seabed = Seabed()
window = ViewWindow(default_size)
viewport = ViewPort(window)
#inf = pygame.display.get_window_size()

def draw_cast_history():
    while (window.horizontal_center / scroll_speed) < len(viewport.ctd.history):
      viewport.ctd.history.pop(0)
    h_length = len(viewport.ctd.history)
    x = window.horizontal_center - ( scroll_speed * h_length)
    for i in range(h_length):
        y = viewport.get_ypos_px(viewport.ctd.history[i])
        x += scroll_speed
        pygame.draw.circle(screen, Color.BLUE, (x,y), 1)

def draw_bathy_history():
    while (window.horizontal_center / scroll_speed) < len(viewport.seabed.history):
      viewport.seabed.history.pop(0)
    h_length = len(viewport.seabed.history)
    x = window.horizontal_center - ( scroll_speed * h_length)
    dps = []
    #bottom mode
    bottom_text_color = Color.ORANGE
    bottom_text = ""
    bottom_subtext = ""
    if (viewport.seabed.depth_source == DepthSource.ECHO):
        bottom_text =  "Echosounder"
        bottom_text_color = Color.ORANGE2
    elif (viewport.seabed.depth_source == DepthSource.ALTIMETER):
        bottom_text = "Altimeter"
        bottom_text_color = Color.ORANGE3
    if(viewport.seabed.depth_corrected):
        bottom_subtext = "Corrected"

    for i in range(h_length):
        h_src = viewport.seabed.history[i][0] #depth source
        h_corr = viewport.seabed.history[i][1] #depth corrected?
        h_val = viewport.seabed.history[i][2] # depth value
        y = viewport.get_ypos_px(h_val)
        x += scroll_speed
        thk = 3 if h_corr else 2 #fatter circle if corrected
        col = Color.ORANGE if (h_src == 1) else Color.ORANGE3
        
        pygame.draw.circle(screen, col, (x,y), 2)
    str_depth_val = float2str(viewport.seabed.history[-1][2]) + "m "
    
    text_ypos = viewport.get_ypos_px(viewport.seabed.water_depth_lower_threshold - (viewport.seabed.water_depth_lower_threshold - viewport.seabed.water_depth_upper_threshold))
    text_offset = render_text(str_depth_val, window.horizontal_center + 10, text_ypos, bottom_text_color, screen)
    
    render_text([bottom_text, bottom_subtext], window.horizontal_center + text_offset[0] * 1.1, text_ypos, bottom_text_color, screen)
    
#setup echosounder
def echo_callback(message):
    print(message)
def seasave_callback(object):
    if(random.uniform(0,10) > 9):
        print(object.depth, object.altitude, object.sv_average)
echo = EchoSounder(AppSettings.echosounder_udp_port, echo_callback)
seasave = SeaSaveSerial("COM5", 9600, seasave_callback)

if DEBUG:
    seasave.start_simulate('EN695_008_test.cnv') #004 throws error, #001 is all messed up
    echo.start_simulate(seasave.debug_max_depth_of_cast + 10, .4)
    
else:
    echo.start_receive()
    seasave.start_receive()

while not done:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
        elif event.type == pygame.VIDEORESIZE:
            window.resize(event.size)
            viewport.resize()
            screen = pygame.display.set_mode((window.width_px, window.height_px), pygame.RESIZABLE)

    #screen background
    screen.fill(Color.BLUE) #you should never see this it's behind the other bg images
    screen.blit(window.sky_image,(0,0))
    #screen.blit(window.sky_image,(0,viewport.get_background_padding()))
    #screen.blit(viewport.bg_image,(0,viewport.get_background_padding()))
    #screen.blit(viewport.bg_image,(0,0))
    screen.blit(viewport.bg_image,(0,viewport.get_background_padding()))
    #screen.blit(viewport.bg_image,(0,0))

    #for testing only
    if DEBUG:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        ctd_depth = (viewport.seabed.water_depth_lower_threshold / window.width_px) * mouse_x
        
    else:
        
        if viewport.ctd.depth > viewport.seabed.water_depth:
            upcast = True

        if upcast:
            ctd_depth = ctd_depth - .6
            if ctd_depth < 5:
                done = True
        else:
            ctd_depth = ctd_depth + 1
    

    viewport.set_ctd_depth(seasave.depth)
    viewport.set_altimeter(seasave.altitude)
    viewport.ctd.average_sound_velocity = seasave.sv_average
    viewport.ctd.instantaneous_sound_velocity = seasave.sv_instantaneous

    #this stupid thing is needed to test sound velocity corrections
    #if(debug_water_depth == 0):
    #    debug_water_depth = viewport.seabed.water_depth #only on first loop
    #debug_water_depth = debug_water_depth + random.uniform(-.4,.4)
    
    #if(echo.depth > 0):
        #debug_water_depth = echo.depth + echo.keel_depth
    viewport.seabed.sound_velocity_m_s = echo.sound_velocity
    viewport.set_water_depth(echo.depth)

    ctd_ypos = viewport.get_ypos_px(viewport.ctd.depth) - viewport.ctd.height_px
   
    #draw transition line
    #(x,y)
    
    if 1 > 0:
        tripline_y_pos = viewport.get_ypos_px(viewport.triplines.get_next_tripline_depth(viewport.ctd.depth))
        #pygame.draw.line(screen, Color.YELLOW, (0, tripline_y_pos), (window.width_px, tripline_y_pos), 1)
        #trip_label = "m from bottom"
        draw_horizontal_line(screen, tripline_y_pos, Color.YELLOW, 60)
        next_depth = viewport.triplines.get_next_tripline_depth(viewport.ctd.depth)
        trip_label_a = float2str(viewport.seabed.water_depth - next_depth) + "m from bottom"
        trip_label_b = str(next_depth) + "m deep"
        render_text([trip_label_a, trip_label_b], 0, tripline_y_pos, Color.YELLOW, screen)
        #warntext_a = FONT.render(trip_label_a, True, Color.YELLOW)
        #warntext_b = FONT.render(trip_label_b, True, Color.YELLOW)
        #screen.blit (warntext_a, (0, tripline_y_pos))
        #screen.blit (warntext_b, (0, tripline_y_pos + AppSettings.font_size))

    wd = FONT.render(float2str(viewport.ctd.depth), True, Color.LIGHTBLUE)
    screen.blit(wd, ((window.horizontal_center) + viewport.ctd.width_px, ctd_ypos))

    draw_cast_history()
    draw_bathy_history()
    #ctd = pygame.draw.rect(screen, GREEN, pygame.Rect((window.horizontal_center) - (ctd_width_px / 2), ctd_ypos, ctd_width_px, ctd_height_px))
    #cg = pygame.transform.scale(viewport.ctd.image_file, (viewport.ctd.width_px, viewport.ctd.height_px))
    screen.blit(viewport.ctd.ctd_image_scaled, ((window.horizontal_center) - (viewport.ctd.width_px / 2),ctd_ypos, viewport.ctd.width_px, viewport.ctd.height_px))
    #screen.blit(cg, ((window.horizontal_center) - (viewport.ctd.width_px / 2),ctd_ypos, viewport.ctd.width_px, viewport.ctd.height_px))
    
    if DEBUG:
        # show the bottom depth window
        yt = viewport.get_ypos_px(viewport.seabed.water_depth_upper_threshold)
        yb = viewport.get_ypos_px(viewport.seabed.water_depth_lower_threshold) - 2
        pygame.draw.line(screen, Color.WHITE, (0, yt), (window.width_px, yt), 1)
        pygame.draw.line(screen, Color.WHITE, (0, yb), (window.width_px, yb), 1)

    pygame.display.flip()
    clock.tick(AppSettings.frame_rate)
pygame.quit()


