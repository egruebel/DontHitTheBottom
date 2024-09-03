
class AppSettings:
    initial_water_depth = 500 #default water depth when application is started before any inputs from CTD or echosounder
    tripline_jitter_m = 6 #prevents flapping by raising/lowering the tripline by x meters once the ctd has passed
    bottom_window_m = 30 #the altitude from the bottom where the display is fully zoomed in for situational awareness
    bottom_padding_coefficient = .1 #larer number adds more padding to the bottom depth so the screen doesn't resize every update from the echosounder
    horizontal_center = .7 #where the CTD is shown in relation to the left side of the screen in %
    surface_padding = .05 #size of the sky at the surface in %
    
    ctd_min_height_px = 18 #otherwise CTD will appear teeny tiny during deep casts of 6000m or greater due to auto scaling
        
    altimeter_max_range_m = 100 #max range in m that altimeter can detect
    altimeter_minimum_viable_m = .9 #lowest altimeter reading in m which could be considered good
    altimeter_hit_count = 25 #number of valid altimeter readings needed to use it as a depth source
    altimeter_averaging = True #use the median average of the last n altimeter readings where n = altimeter_hit_count
    altimeter_default_sv = 1500 #sound velocity in meters/sec that the altimeter uses in firmware
    altimeter_sv_correction = True #correct the altimeter reading using the instantaneous sv from the CTD 

    ctd_image = 'images/ctd_trans_v2.png'
    bg_image = 'images/deepsea_bg_v2.png'
    sky_image = 'images/sky_3.png'
    font = "Arial"
    font_size = 32
    title = "Don't Hit the Bottom"
    default_screen_size = [900,800] #width, height
    frame_rate = 200 #milliseconds between frames
    scroll_speed = .05
    animate_transitions = True
    
    echosounder_udp_port = 16008 #16008 for Endeavor
    echosounder_default_sv = 1500 #sound velocity in meters/sec
    echosounder_sv_correction = True #correct echosounder reading using the average sv from the CTD

    seasave_serial_port = "COM5"
    seasave_serial_baud = 9600