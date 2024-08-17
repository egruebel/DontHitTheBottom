
class AppSettings:
    initial_water_depth = 500 #default water depth when application is started before any inputs from CTD or echosounder
    altitude_triplines = [700, 400, 250, 40] #highest to lowest altitude (altitude not depth)
    tripline_jitter_m = 6 #prevents flapping
    bottom_padding_coefficient = .03 #larer number adds more padding to the bottom depth so the screen doesn't resize every update from the echosounder
    horizontal_center = .68 #where the CTD is shown in relation to the left side of the screen
    
    ctd_min_height_px = 18 #otherwise CTD will appear teeny tiny during deep casts of 6000m or greater due to auto scaling
        
    altimeter_max_range_m = 100 #max range in m that altimeter can detect
    altimeter_minimum_viable_m = .9 #lowest altimeter reading in m which could be considered good
    altimeter_hit_count = 25 #number of successful altimeter readings needed to use it as a depth source
    altimeter_default_sv = 1500 #sound velocity in meters/sec
    altimeter_sv_correction = False #correct the altimeter reading using the instantaneous sv reading from the CTD 

    #viewport_padding_top = 14 #padding in meters at the top of the viewport
    ctd_image = 'images/ctd_trans_v2.png'
    bg_image = 'images/deepsea_bg_v2.png'
    sky_image = 'images/sky_3.png'
    font = "Arial"
    font_size = 32
    title = "Don't Hit the Bottom"
    default_screen_size = [900,800] #width, height
    frame_rate = 200 #milliseconds between frames
    scroll_speed = .1
    
    echosounder_udp_port = 16008 #16008 for Endeavor
    echosounder_default_sv = 1500 #sound velocity in meters/sec

    seasave_serial_port = "COM5"
    seasave_serial_baud = 9600