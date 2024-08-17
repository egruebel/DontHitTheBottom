import socket
import time
import xml.etree.ElementTree as ET


class SeaSaveSocket:
    def __init__(self):
        self.field_list = []
        self.connected = False
        self.manual_disconnect = False
        self.buffer_size = 256000 #256 kbytes
   
    def get_field_list(self, welcome_message):
        sample = b'<SBE_ConvertedDataSettings>\n<SecondsBetweenUpdates>1.000000</SecondsBetweenUpdates>\r\n<FieldDefinition><CalcID>72</CalcID><UnitID>-1</UnitID><Ordinal>0</Ordinal><Units></Units><FullName>Scan Count</FullName><Tag>Field0</Tag><Digits>0</Digits></FieldDefinition>\r\n<FieldDefinition><CalcID>12</CalcID><UnitID>58</UnitID><Ordinal>0</Ordinal><Units>S/m</Units><FullName>Conductivity [S/m]</FullName><Tag>Field1</Tag><Digits>7</Digits></FieldDefinition>\r\n<FieldDefinition><CalcID>81</CalcID><UnitID>6</UnitID><Ordinal>0</Ordinal><Units>ITS-90, deg C</Units><FullName>Temperature [ITS-90, deg C]</FullName><Tag>Field2</Tag><Digits>5</Digits></FieldDefinition>\r\n<FieldDefinition><CalcID>65</CalcID><UnitID>3</UnitID><Ordinal>0</Ordinal><Units>db</Units><FullName>Pressure, Digiquartz [db]</FullName><Tag>Field3</Tag><Digits>4</Digits></FieldDefinition>\r\n<FieldDefinition><CalcID>17</CalcID><UnitID>31</UnitID><Ordinal>0</Ordinal><Units>salt water, m</Units><FullName>Depth [salt water, m]</FullName><Tag>Field4</Tag><Digits>4</Digits></FieldDefinition>\r\n<FieldDefinition><CalcID>70</CalcID><UnitID>49</UnitID><Ordinal>0</Ordinal><Units>PSU</Units><FullName>Salinity, Practical [PSU]</FullName><Tag>Field5</Tag><Digits>5</Digits></FieldDefinition>\r\n<FieldDefinition><CalcID>84</CalcID><UnitID>52</UnitID><Ordinal>0</Ordinal><Units>seconds</Units><FullName>Time, Elapsed [seconds]</FullName><Tag>Field6</Tag><Digits>4</Digits></FieldDefinition>\r\n<FieldDefinition><CalcID>54</CalcID><UnitID>40</UnitID><Ordinal>0</Ordinal><Units>ml/l</Units><FullName>Oxygen Saturation, Weiss [ml/l]</FullName><Tag>Field7</Tag><Digits>6</Digits></FieldDefinition>\r\n</SBE_ConvertedDataSettings>\r\n'
        #read the xml from the message that seasave sends upon connect
        root = ET.fromstring(welcome_message.decode('utf-8'))
        for field in root.iter('FieldDefinition'):
            f = [field.find('FullName').text, field.find('Tag').text, field.find('Units').text, -99]
            self.field_list.append(f)
        print(self.field_list)

    def update_field_list(self, update):
        sample = b"<Scan index='57'><Field0>3049</Field0><Field1>0.8615082</Field1><Field2>23.47035</Field2><Field3>1.1450</Field3><Field4>1.1361</Field4><Field5>4.95738</Field5><Field6>127.0000</Field6><Field7>5.769134</Field7></Scan>\r\n<Scan index='58'><Field0>3073</Field0><Field1>0.8614957</Field1><Field2>23.47016</Field2><Field3>1.0785</Field3><Field4>1.0702</Field4><Field5>4.95732</Field5><Field6>128.0000</Field6><Field7>5.769156</Field7></Scan>\r\n<Scan index='59'><Field0>3097</Field0><Field1>0.8614707</Field1><Field2>23.46997</Field2><Field3>1.1445</Field3><Field4>1.1356</Field4><Field5>4.95719</Field5><Field6>129.0000</Field6><Field7>5.769181</Field7></Scan>\r\n"
        d = update.splitlines()[0]
        update = ET.fromstring(d.decode('utf-8'))
        for field in self.field_list:
            val = update.find(field[1]).text
            field[3] = float(val)
            print(field)

    def connect(self, host, port, interval):
        print('connecting to ' + host + ' ' + str(port))
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.settimeout(100)
                s.connect((host, port))
                self.connected = True
                print("connected")
                settings = s.recv(self.buffer_size)
                self.get_field_list(settings)
                while(not self.manual_disconnect):
                    buffer = s.recv(self.buffer_size)
                    self.update_field_list(buffer)
                    time.sleep(1)
            except Exception as e:
                print("socket error: " + str(e))
                if(self.connected):
                    s.close()
                    print("closed")




a = SeaSaveSocket()
while(True):
    a.connect("192.168.1.34", 49161, 2)
    time.sleep(4)




