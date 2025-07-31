

class AppSettings:
    initial_water_depth = 100 #default water depth when application is started before any inputs from CTD or echosounder
    tripline_jitter_m = 6 #prevents flapping by raising/lowering the tripline by x meters once the ctd has passed
    bottom_window_m = 30 #the altitude from the bottom where the display is fully zoomed in for situational awareness
    bottom_padding_coefficient = .14 #larer number adds more padding to the bottom depth so the screen doesn't resize every update from the echosounder
    horizontal_center = .7 #where the CTD is shown in relation to the left side of the screen in %
    surface_padding_coefficient = .06 #size of the sky at the surface in %
    
    ctd_min_height_px = 14 #otherwise CTD will appear teeny tiny during deep casts of 6000m or greater due to auto scaling
    ship_min_height_px = 22 #prevents ship from being too small in very deep water
    ship_max_height_px = 500 #prevents ship from being too large in shallow water
        
    altimeter_max_range_m = 100 #max range in m that altimeter can detect
    altimeter_minimum_viable_m = 2 #lowest altimeter reading in m which could be considered good
    altimeter_filtering_window = 25 #number of valid altimeter readings needed to use it as a depth source
    altimeter_averaging = False #use the median average of the last n altimeter readings where n = altimeter_hit_count
    altimeter_default_sv = 1500 #sound velocity in meters/sec that the altimeter uses in firmware
    altimeter_sv_correction = True #correct the altimeter reading using the instantaneous sv from the CTD 

    ctd_image = 'images/ctd_trans_v2.png'
    bg_image = 'images/deepsea_bg_v2.png'
    sky_image = 'images/sky_3.png'
    ship_image = 'images/rv_trans.png'
    font = "Arial"
    font_size = 40
    title = "Don't Hit the Bottom"
    
    #common user preference settings
    frame_rate = 200 #frames per second
    scroll_speed = .02 #pixels to scroll the screen between frames
    animate_transitions = True #animate the zoom in/out events
    default_screen_size = [1100,800] #width, height
    echosounder_color = [255,100,90] #RGB color to use for the bottom trace when the echosounder is displayed
    altimeter_color = [0,255,0] #RGB color to use for the bottom trace when the altimeter is displayed
    countdown_distance_m = 30 #altitude from the bottom where the countdown begins.
    console_display_time = 4 #number of seconds to display console messages

    #settings for troubleshooting
    draw_triplines = False #draw the dotted triplines that trigger a zoom in/out event
    draw_seabed_window = False #draw the high and low threshold where the screen gets redrawn due to seafloor change
    draw_screen_top = False #draw the meters at screen top
    draw_horizon = False #draw the calculated horizon position
       
    #001 hit the bottom (for real)
    #005 is deep with altim issue
    #008 shallow with tripline adjustment issue on upcast
    #003 is nice medium case demo
    #004 has tripline adjustment issue
    playback_mode = False
    playback_file = "test_casts/EN695_004_test.cnv"
    playback_speed = .002 #seconds to pause between cnv file line scans, larger number = slower
    
    echosounder_udp_port = 16008 #UDP broadcast port to listen for NMEA
    echosounder_default_sv = 1500 #sound velocity in meters/sec
    echosounder_sv_correction = True #correct echosounder reading using the average sv from the CTD
    echosounder_nmea_depth_index = 6 #NMEA comma index of the water depth in meters
    echosounder_nmea_keeldepth_index = 8 #NMEA comma index of the vessel keel depth
    echosounder_nmea_sv_index = 9 #NMEA comma index of the echosounder sound velocity

    seasave_ip = '127.0.0.1'
    seasave_port = 49161
    seasave_depth_qualifier = 'Depth [salt water, m]'
    seasave_altimeter_qualifier = 'Altimeter [m]'
    seasave_pressure_qualifier = 'Pressure, Digiquartz [db]'
    seasave_sv_qualifier = 'Sound Velocity [Chen-Millero, m/s]'
    seasave_sv_avg_qualifier = 'Average Sound Velocity [Chen-Millero, m/s]'
    seasave_bottom_depth_qualifier = 'Echosounder Bottom Depth [m]'
