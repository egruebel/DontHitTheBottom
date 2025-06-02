import socket
import time
import threading
import xml.etree.ElementTree as ET

class SeasaveApi:
    
    def __init__(self, ip, port, receive_callback):
        self.ip = ip
        self.port = port
        self.field_list = []
        self.connected = False
        self.acquiring = False
        self.manual_disconnect = False
        self.buffer_size = 4000 #4kb
        self.socket_timeout = 10 #seconds

        self.depth_qualifier = 'Depth [salt water, m]'
        self.altimeter_qualifier = 'Altimeter [m]'
        self.pressure_qualifier = 'Pressure, Digiquartz [db]'
        self.sv_qualifier = 'Sound Velocity [Chen-Millero, m/s]'
        self.sv_avg_qualifier = 'Average Sound Velocity [Chen-Millero, m/s]'

        self.depth = 0
        self.pressure = 0
        self.altitude = 0
        self.sv_instantaneous = 0
        self.sv_average = 0

    #after connecting to the server, Seasave will reply with a list of the fields it's configured for in the TCP/IP output settings
    def get_field_list(self, seasave_settings):
        #this isn't used it's just an example for future me of the XML that Seasave sends upon connect
        sample = b'<SBE_ConvertedDataSettings>\n<SecondsBetweenUpdates>1.000000</SecondsBetweenUpdates>\r\n<FieldDefinition><CalcID>72</CalcID><UnitID>-1</UnitID><Ordinal>0</Ordinal><Units></Units><FullName>Scan Count</FullName><Tag>Field0</Tag><Digits>0</Digits></FieldDefinition>\r\n<FieldDefinition><CalcID>12</CalcID><UnitID>58</UnitID><Ordinal>0</Ordinal><Units>S/m</Units><FullName>Conductivity [S/m]</FullName><Tag>Field1</Tag><Digits>7</Digits></FieldDefinition>\r\n<FieldDefinition><CalcID>81</CalcID><UnitID>6</UnitID><Ordinal>0</Ordinal><Units>ITS-90, deg C</Units><FullName>Temperature [ITS-90, deg C]</FullName><Tag>Field2</Tag><Digits>5</Digits></FieldDefinition>\r\n<FieldDefinition><CalcID>65</CalcID><UnitID>3</UnitID><Ordinal>0</Ordinal><Units>db</Units><FullName>Pressure, Digiquartz [db]</FullName><Tag>Field3</Tag><Digits>4</Digits></FieldDefinition>\r\n<FieldDefinition><CalcID>17</CalcID><UnitID>31</UnitID><Ordinal>0</Ordinal><Units>salt water, m</Units><FullName>Depth [salt water, m]</FullName><Tag>Field4</Tag><Digits>4</Digits></FieldDefinition>\r\n<FieldDefinition><CalcID>70</CalcID><UnitID>49</UnitID><Ordinal>0</Ordinal><Units>PSU</Units><FullName>Salinity, Practical [PSU]</FullName><Tag>Field5</Tag><Digits>5</Digits></FieldDefinition>\r\n<FieldDefinition><CalcID>84</CalcID><UnitID>52</UnitID><Ordinal>0</Ordinal><Units>seconds</Units><FullName>Time, Elapsed [seconds]</FullName><Tag>Field6</Tag><Digits>4</Digits></FieldDefinition>\r\n<FieldDefinition><CalcID>54</CalcID><UnitID>40</UnitID><Ordinal>0</Ordinal><Units>ml/l</Units><FullName>Oxygen Saturation, Weiss [ml/l]</FullName><Tag>Field7</Tag><Digits>6</Digits></FieldDefinition>\r\n</SBE_ConvertedDataSettings>\r\n'
        try:
            #convert byte array to xml obj
            root = ET.fromstring(seasave_settings.decode('utf-8'))
            #get each FieldDefinition tag and strip the useful information that we need
            for field in root.iter('FieldDefinition'):
                f = [field.find('FullName').text, field.find('Tag').text, field.find('Units').text, -99]
                self.field_list.append(f)
                print(f[0])
            #print(self.field_list)
            return True
        except Exception as e:
            print("error parsing seasave settings: " + str(e))
            return False


    def update_field_list(self, update):
        #this isn't used it's just an example of the XML data structure that Seasave sends repeatedly when CTD acquisition is in progress
        sample = b"<Scan index='57'><Field0>3049</Field0><Field1>0.8615082</Field1><Field2>23.47035</Field2><Field3>1.1450</Field3><Field4>1.1361</Field4><Field5>4.95738</Field5><Field6>127.0000</Field6><Field7>5.769134</Field7></Scan>\r\n<Scan index='58'><Field0>3073</Field0><Field1>0.8614957</Field1><Field2>23.47016</Field2><Field3>1.0785</Field3><Field4>1.0702</Field4><Field5>4.95732</Field5><Field6>128.0000</Field6><Field7>5.769156</Field7></Scan>\r\n<Scan index='59'><Field0>3097</Field0><Field1>0.8614707</Field1><Field2>23.46997</Field2><Field3>1.1445</Field3><Field4>1.1356</Field4><Field5>4.95719</Field5><Field6>129.0000</Field6><Field7>5.769181</Field7></Scan>\r\n"

        d = update.splitlines()[0]
        update = ET.fromstring(d.decode('utf-8'))
        for field in self.field_list:
            val = update.find(field[1]).text
            field[3] = float(val)
    
    def get_value_from_fieldlist(self, qualifier):
        for field in self.field_list:
            if field[0] == qualifier:
                return field[3]

    def populate_output_variables(self):
        self.depth = self.get_value_from_fieldlist(self.depth_qualifier)
        self.pressure = self.get_value_from_fieldlist(self.pressure_qualifier)
        self.altitude = self.get_value_from_fieldlist(self.altimeter_qualifier)
        self.sv_instantaneous = self.get_value_from_fieldlist(self.sv_qualifier)
        self.sv_average = self.get_value_from_fieldlist(self.sv_avg_qualifier)

    def check_minimum_viable_fields(self):
        #this application requires three fields from Seasave. Depth (m), pressure (db), and altimeter (m)
        #this function lets the user know if a meaningful way that they have Seasave set up incorrectly
        
        if not any(self.depth_qualifier in subl for subl in self.field_list):
            raise Exception("Required parameter Depth was not found in Seasave TCP/IP output")
        if not any(self.pressure_qualifier in subl for subl in self.field_list):
            raise Exception("Required parameter Pressure was not found in Seasave TCP/IP output")
        if not any(self.altimeter_qualifier in subl for subl in self.field_list):
            raise Exception("Required parameter Altimeter was not found in Seasave TCP/IP output")
        if not any(self.sv_qualifier in subl for subl in self.field_list):
            raise Exception("Required parameter Sound Velocity was not found in Seasave TCP/IP output")
        if not any(self.sv_avg_qualifier in subl for subl in self.field_list):
            raise Exception("Required parameter Average Sound Velocity was not found in Seasave TCP/IP output")

    def deliver_data(self):
        self.populate_output_variables()
        print('Depth: ' + str(self.depth))
        print('Altitude: ' + str(self.altitude))
        print('SV: ' + str(self.sv))
        print('SV Average: ' + str(self.sv_avg))

    def receive_loop(self, socket):
        try:
            print('1')
            while not self.manual_disconnect:
                tries = 4
                seasave_data = socket.recv(self.buffer_size)
                while not ord('\n') in seasave_data:
                    tries -= 1
                    if(tries == 0):
                        raise Exception("Error in Seasave acquisition")
                    seasave_data += socket.recv(self.buffer_size)
                self.update_field_list(seasave_data)
                self.deliver_data()

        except Exception as e:
            print('error in receive loop')

    def connect(self):
        print('connecting to ' + self.ip + ':' + str(self.port))
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.settimeout(self.socket_timeout)
                s.connect((self.ip, self.port))
                self.connected = True
                seasave_settings = s.recv(self.buffer_size) #blocks until receive or timeout
                readblocks = 4
                while not seasave_settings.endswith(b'</SBE_ConvertedDataSettings>\r\n'): #self.get_field_list(seasave_settings):
                    #if you're here it's because we haven't received the full welcome message from Seasave. Go get remaining data in the TCP buffer.
                    readblocks -= 1
                    if(readblocks == 0):
                        raise Exception("Error in Seasave connection protocol")
                    seasave_settings += s.recv(self.buffer_size)
                self.get_field_list(seasave_settings)
                
                self.check_minimum_viable_fields()
                
                while(not self.manual_disconnect):
                    self.receive_loop(s)

            except Exception as e:
                print(type(e))
                print("error: " + str(e))

                if(self.connected):
                    s.close()
                    self.connected = False

    def acquisition_loop(self):
        while(True):
            self.connect()
            time.sleep(4)

    def begin_receive(self):
        r = threading.Thread(target = self.acquisition_loop)
        r.start()







