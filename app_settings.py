
class AppSettings:
    initial_water_depth = 10000 #default water depth when application is started before any inputs from CTD or echosounder
    altitude_triplines = [700, 400, 250, 80] #highest to lowest altitude (altitude not depth)
    tripline_jitter_m = 6
    bottom_padding_coefficient = .03 #larer number adds more padding to the bottom depth so the screen doesn't resize every update
    horizontal_center = .68 #where the CTD is shown in relation to the left side of the screen
    
    ctd_min_height_px = 18 #otherwise CTD will appear teeny tiny during deep casts of 6000m or greater due to auto scaling
    ctd_size_scaling_coeff = 6000 #larger number equals bigger CTD as you zoom in
    
    altimeter_max_range_m = 100 #max range in m that altimeter can detect
    altimeter_minimum_viable_m = .9 #lowest altimeter reading in m which could be considered good
    altimeter_hit_count = 16 #number of successful altimeter readings needed to use it as a depth source
    altimeter_default_sv = 1500 #sound velocity in meters/sec
    altimeter_sv_correction = True #correct the altimeter reading using the instantaneous sv reading from the CTD 

    viewport_padding_top = 14 #padding in meters at the top of the viewport
    ctd_image = 'ctd_trans_v2.png'
    bg_image = 'deepsea_bg_v2.png'
    sky_image = 'sky_3.png'
    font = "Arial"
    font_size = 32
    title = "Don't Hit the Bottom"
    default_screen_size = [900,900] #width, height
    frame_rate = 20 #milliseconds between frames
    scroll_speed = .2
    

    echosounder_udp_port = 16008 #16008 for Endeavor
    echosounder_default_sv = 1500 #sound velocity in meters/sec

    seasave_serial_port = "COM5"
    seasave_serial_baud = 9600