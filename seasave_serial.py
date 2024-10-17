import serial
import threading
import time
import xml.etree.ElementTree as ET

class SeaSaveSerial:
    
    def __init__(self, com, baud, receive_callback):
        self.field_list = []
        self.callback = receive_callback
        self.comport = com
        self.baud = baud
        self.buffer_size = 256000 #256 kbytes
        
        self.altitude = 0
        self.depth = 0
        self.sv_average = 0
        self.sv_instantaneous = 0
        self.debug_max_depth_of_cast = 0
   
    def get_field_list(self, welcome_message):
        sample = b'<SBE_ConvertedDataSettings>\n<SecondsBetweenUpdates>1.000000</SecondsBetweenUpdates>\r\n<FieldDefinition><CalcID>72</CalcID><UnitID>-1</UnitID><Ordinal>0</Ordinal><Units></Units><FullName>Scan Count</FullName><Tag>Field0</Tag><Digits>0</Digits></FieldDefinition>\r\n<FieldDefinition><CalcID>12</CalcID><UnitID>58</UnitID><Ordinal>0</Ordinal><Units>S/m</Units><FullName>Conductivity [S/m]</FullName><Tag>Field1</Tag><Digits>7</Digits></FieldDefinition>\r\n<FieldDefinition><CalcID>81</CalcID><UnitID>6</UnitID><Ordinal>0</Ordinal><Units>ITS-90, deg C</Units><FullName>Temperature [ITS-90, deg C]</FullName><Tag>Field2</Tag><Digits>5</Digits></FieldDefinition>\r\n<FieldDefinition><CalcID>65</CalcID><UnitID>3</UnitID><Ordinal>0</Ordinal><Units>db</Units><FullName>Pressure, Digiquartz [db]</FullName><Tag>Field3</Tag><Digits>4</Digits></FieldDefinition>\r\n<FieldDefinition><CalcID>17</CalcID><UnitID>31</UnitID><Ordinal>0</Ordinal><Units>salt water, m</Units><FullName>Depth [salt water, m]</FullName><Tag>Field4</Tag><Digits>4</Digits></FieldDefinition>\r\n<FieldDefinition><CalcID>70</CalcID><UnitID>49</UnitID><Ordinal>0</Ordinal><Units>PSU</Units><FullName>Salinity, Practical [PSU]</FullName><Tag>Field5</Tag><Digits>5</Digits></FieldDefinition>\r\n<FieldDefinition><CalcID>84</CalcID><UnitID>52</UnitID><Ordinal>0</Ordinal><Units>seconds</Units><FullName>Time, Elapsed [seconds]</FullName><Tag>Field6</Tag><Digits>4</Digits></FieldDefinition>\r\n<FieldDefinition><CalcID>54</CalcID><UnitID>40</UnitID><Ordinal>0</Ordinal><Units>ml/l</Units><FullName>Oxygen Saturation, Weiss [ml/l]</FullName><Tag>Field7</Tag><Digits>6</Digits></FieldDefinition>\r\n</SBE_ConvertedDataSettings>\r\n'
        #read the xml from the message that seasave sends upon connect
        try:
            root = ET.fromstring(welcome_message.decode('utf-8'))
            for field in root.iter('FieldDefinition'):
                f = [field.find('FullName').text, field.find('Tag').text, field.find('Units').text, -99]
                self.field_list.append(f)
            print(self.field_list)
            #save this configuration for the future
            f = open("last_seasave_config.txt", "w")
            f.write(welcome_message.decode('utf-8'))
            f.close()
        except:
            f = open("last_seasave_config.txt", "r")
            try_again = f.read()
            f.close()
            pass
        

    def update_field_list(self, update):
        sample = b"<Scan index='57'><Field0>3049</Field0><Field1>0.8615082</Field1><Field2>23.47035</Field2><Field3>1.1450</Field3><Field4>1.1361</Field4><Field5>4.95738</Field5><Field6>127.0000</Field6><Field7>5.769134</Field7></Scan>\r\n<Scan index='58'><Field0>3073</Field0><Field1>0.8614957</Field1><Field2>23.47016</Field2><Field3>1.0785</Field3><Field4>1.0702</Field4><Field5>4.95732</Field5><Field6>128.0000</Field6><Field7>5.769156</Field7></Scan>\r\n<Scan index='59'><Field0>3097</Field0><Field1>0.8614707</Field1><Field2>23.46997</Field2><Field3>1.1445</Field3><Field4>1.1356</Field4><Field5>4.95719</Field5><Field6>129.0000</Field6><Field7>5.769181</Field7></Scan>\r\n"
        try:
            d = update.splitlines()[0]
            update = ET.fromstring(d.decode('utf-8'))
            for field in self.field_list:
                val = update.find(field[1]).text
                field[3] = float(val)
                print(field)
        except:
            pass
        
    def sim(self, asc_file_name):
        #get the max depth so we can set up the simulated echosounder
        with open(asc_file_name, 'rt') as f:
            row = 0
            begin = False
            depth_index = 1 
            altitude_index = 0
            sv_index = 2
            sv_sum = 0
            sv_count = 0
            header = []
            for line in f:
                #if(row == 0):
                #    header = line.split(';')
                #    depth_index = header.index('DepSM')
                #    altitude_index = header.index('AltM')
                #    sv_index = header.index('SvCM')
                #    row += 1
                #    continue
                #every other row
                if(line == '*END*\n'):
                    begin = True
                    continue
                if(begin):
                    dat = line.split()
                    self.depth = float(dat[depth_index])
                    self.altitude = float(dat[altitude_index])
                    self.sv_instantaneous = float(dat[sv_index])
                    sv_sum += self.sv_instantaneous
                    sv_count += 1
                    self.sv_average = sv_sum / sv_count
                    row += 1
                    self.callback(self)
                    time.sleep(.000001)




            else:
                # No more lines to be read from file
                return
            
    def start_simulate(self, asc_file_name):
        #get the max depth so we can set up the simulated echosounder
        with open(asc_file_name, 'rt') as f:
            row = 0
            begin = False
            depth_index = 1 
            
            header = []
            for line in f:
                #if(row == 0):
                #    header = line.split(';')
                #    depth_index = header.index('DepSM')
                #    altitude_index = header.index('AltM')
                #    sv_index = header.index('SvCM')
                #    row += 1
                #    continue
                #every other row
                if(line == '*END*\n'):
                    begin = True
                    continue
                if(begin):
                    dat = line.split()
                    d = float(dat[depth_index])
                    if(d > self.debug_max_depth_of_cast ):
                        self.debug_max_depth_of_cast = d
                    row += 1


        #start a new thread and pump out CTD data
        x = threading.Thread(target=self.sim, args = (asc_file_name,))
        x.start()    

    def connect(self):
        #print(serial.tools.list_ports.comports())
        while True:
            try:
                ser = serial.Serial(self.comport, baudrate = self.baud)  # open serial port
                #ser.open()
                #get the ConvertedDataSettings that Seasave sends when you start acquisition
                #this line should block forever when ctd is not in use
                settings = ser.read_until(b"</SBE_ConvertedDataSettings>\r\n")
                self.get_field_list(settings)
                #close and reopen with timeout
                ser.close()
                ser = serial.Serial(self.comport, baudrate = self.baud, timeout = 4)  # open serial port
                while True:
                    buffer = ser.read_until(b"</Scan>\r\n")
                    if(len(buffer) == 0):
                        ser.close()
                        break
                    self.update_field_list(buffer)
                    time.sleep(.5)
            except serial.SerialException as e:
                print("SerialException")
                for a in e.args:
                    print(a)
                time.sleep(4)
            
    def start_receive(self):
        x = threading.Thread(target=self.connect)
        x.start()


