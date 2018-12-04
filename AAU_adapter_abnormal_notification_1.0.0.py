from http.server import HTTPServer, BaseHTTPRequestHandler
from io import BytesIO
from urllib.parse import urlparse
import requests
import socket   
import json
import time
import threading

#define global vars default state
Global_state_emengency = b'Normal'

Global_state_parking_sensor_1 = b'F'
Global_state_parking_sensor_2 = b'F'
Global_state_parking_sensor_3 = b'F'

Global_state_freezer_refrigerator_door = b'C'
Global_state_freezer_freezer_door = b'C'

Global_state_oven_door = b'C'
Global_state_oven_device_status = b'I'

Global_Status_Alarm = b'Disable'

Gloal_alarmdetecttime = 60*15 # for 1min

stopflag = 0

#define global OID of devices
OID_Oven_7 = '9b4f2d11-addf-46b0-bec5-0773f5763612'
OID_Freezer_7 = 'ea0e3e81-56ce-4f8d-b843-2ff54c62a72f'
OID_Parking_Sensor_1 = '87bacf3e-ad0e-4120-938c-e01ce8014e16'
OID_Parking_Sensor_2 = 'f16b8c05-3bc0-4c81-b805-6dec543ba35b'
OID_Parking_Sensor_3 = 'f43c2e21-627c-44dd-b051-efd2ca4f29e3'


#Alarm timer
def timerfun_alarm():
   global handle_timer_alarm
   global Global_Status_Alarm
   global Global_state_emengency
   
   Global_state_emengency = b'Alarm'
   
   handle_timer_alarm.cancel()
   Global_Status_Alarm = b'Disable'

   
#Enquire data and state from EMS
#Publish events to subscribers through VICINITY agnet
def timerfun_publishevent():
   global Global_state_parking_sensor_1
   global Global_state_parking_sensor_2
   global Global_state_parking_sensor_3
 
   
   global handel_timer_publishevent
   global handel_TCPclient_interruptthread
   
   global Global_state_emengency
   
   global OID_Freezer_7
   global stopflag
   global Gloal_alarmdetecttime

   #Derive System time
   ISOTIMEFORMAT = '%Y-%m-%d %X'        
   systemtime = time.strftime(ISOTIMEFORMAT,time.localtime())
   systemtime = str(systemtime)
   systemtime = bytes(systemtime, encoding = "utf8")
   
   if (Global_state_emengency == b'Alarm'):
       
       #Set red alarm LED in EMS
       handel_TCPclient_interruptthread.send(b'USet_DoorAlr_1NN')     
       print('The emergency alarm should be published here!')     
   
       if(Global_state_parking_sensor_1 == b'R'):
           num_parking_resv = b'1'
       elif(Global_state_parking_sensor_2 == b'R'):
           num_parking_resv = b'2'
       elif(Global_state_parking_sensor_3 == b'R'):
           num_parking_resv = b'3'
       else:
           num_parking_resv = b'None'
    
       #Publish the alarm event
       hd = {'adapter-id':'AAU_Adapter','infrastructure-id':'VAS_AN'}
       url = 'http://localhost:9997/agent/events/EmergencyAlarm'     
       payload = b'{' + b'"state":"alarm",' + b'"parking slot reserved":"'+ num_parking_resv + b'","time":"'+ systemtime +b'"}'
       print(payload)
       r=requests.request('PUT',url,headers=hd,data = payload)
       print(r.text)
       
   else:
       num_parking_resv = b'None'
    
       #Publish the alarm event
       hd = {'adapter-id':'AAU_Adapter','infrastructure-id':'VAS_AN'}
       url = 'http://localhost:9997/agent/events/EmergencyAlarm'     
       payload = b'{' + b'"state":"Normal",' + b'"parking slot reserved":"'+ num_parking_resv + b'","time":"'+ systemtime +b'"}'
       print(payload)
       r=requests.request('PUT',url,headers=hd,data = payload)
       print(r.text)
   
   handel_timer_publishevent = threading.Timer(5,timerfun_publishevent,())         
   
   if stopflag==1:
        handel_timer_publishevent.cancel()
   else:
        handel_timer_publishevent.start()
   

#Handle the http requests from VICINITY agent 
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
 
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
 
        querypath = urlparse(self.path)
        path = str(querypath.path)
              
 
    def do_POST(self):
        
        global stopflag
        
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        
        self.send_response(200)
        self.end_headers()
                  
        string = body.decode() #encode()
        string = json.loads(string)
        
        control_ID=string['control_ID']
        control_val=string['value']
        
        if (control_ID=='shutdown' and control_val=='1'):
            response = BytesIO()
            response.write(b'HTTP/1.1 200 OK/Server is shutdown successfully')
            self.wfile.write(response.getvalue())   
            httpd.shutdown
            httpd.socket.close()            
            print('AAU adapter is shutdown successfully!')
            stopflag = 1
    
        else:
            response = BytesIO()
            response.write(b'HTTP/1.1 406 Failed')
            self.wfile.write(response.getvalue())   
 
    def do_PUT(self):
        
        global Global_state_parking_sensor_1
        global Global_state_parking_sensor_2
        global Global_state_parking_sensor_3
        
        global Global_state_freezer_refrigerator_door
        global Global_state_freezer_freezer_door
        global Global_state_oven_door
        global Global_state_oven_device_status
        
        global Global_Status_Alarm
        global handle_timer_alarm
        
        global OID_Oven_7
        global OID_Freezer_7
        global Global_state_emengency
        global Gloal_alarmdetecttime
        
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        
        self.send_response(200)
        self.end_headers()
        
        if (self.path.count(OID_Freezer_7) == 1):  #Freezer
            
            string = body.decode() #encode()
            print(string)
            
            if (string.count('refrigerator_door') == 1 and  string.count('CLOSED') == 1):     
                Global_state_freezer_refrigerator_door = b'C'   
               
                if (Global_state_freezer_freezer_door == b'C' and Global_state_oven_door == b'C'):
                    handle_timer_alarm.cancel()
                    Global_Status_Alarm = b'Disable'
                    Global_state_emengency = b'Normal'
                   
                    Finalsenddata = b'USet_DoorAlr_' + b'0' + b'N' + b'N'   
                    handel_TCPclient_mainthread.send(Finalsenddata) 
                else:
                     #Stop alarm timer
                    handle_timer_alarm.cancel()
                    Global_Status_Alarm = b'Disable'
                    
                    #refersh alarm timer again
                    handle_timer_alarm=threading.Timer(Gloal_alarmdetecttime,timerfun_alarm,())  
                    handle_timer_alarm.start()
                    Global_Status_Alarm = b'Enable'
            
            elif (string.count('refrigerator_door') == 1 and string.count('OPENED') == 1):
                Global_state_freezer_refrigerator_door = b'O' 
              
                if (Global_Status_Alarm == b'Enable'):
                    #Stop alarm timer
                    handle_timer_alarm.cancel()
                    Global_Status_Alarm = b'Disable'
                    
                    #refersh alarm timer again
                    handle_timer_alarm=threading.Timer(Gloal_alarmdetecttime,timerfun_alarm,())  
                    handle_timer_alarm.start()
                    Global_Status_Alarm = b'Enable'
                else:
                    #start alarm timer again
                    handle_timer_alarm=threading.Timer(Gloal_alarmdetecttime,timerfun_alarm,())  
                    handle_timer_alarm.start()
                    Global_Status_Alarm = b'Enable'
                
            elif (string.count('freezer_door') == 1 and string.count('CLOSED') == 1):
                Global_state_freezer_freezer_door = b'C'  
                
                if (Global_state_freezer_refrigerator_door == b'C' and Global_state_oven_door == b'C'):
                    Global_state_emengency = b'Normal'
                    handle_timer_alarm.cancel()
                    Global_Status_Alarm = b'Disable'
                    Finalsenddata = b'USet_DoorAlr_' + b'0' + b'N' + b'N'   
                    handel_TCPclient_mainthread.send(Finalsenddata) 
                else:
                     #Stop alarm timer
                    handle_timer_alarm.cancel()
                    Global_Status_Alarm = b'Disable'
                    
                    #refersh alarm timer again
                    handle_timer_alarm=threading.Timer(Gloal_alarmdetecttime,timerfun_alarm,())  
                    handle_timer_alarm.start()
                    Global_Status_Alarm = b'Enable'
                
            elif (string.count('freezer_door') == 1 and string.count('OPENED') == 1):
                Global_state_freezer_freezer_door = b'O'  
                
                if (Global_Status_Alarm == b'Enable'):
                    #Stop alarm timer
                    handle_timer_alarm.cancel()
                    Global_Status_Alarm = b'Disable'
                    
                    #refersh alarm timer again
                    handle_timer_alarm=threading.Timer(Gloal_alarmdetecttime,timerfun_alarm,())  
                    handle_timer_alarm.start()
                    Global_Status_Alarm = b'Enable'
                else:
                    #start alarm timer again
                    handle_timer_alarm=threading.Timer(Gloal_alarmdetecttime,timerfun_alarm,())  
                    handle_timer_alarm.start()
                    Global_Status_Alarm = b'Enable'
                    
            else:
                response = BytesIO()
                response.write(b'HTTP/1.1 406 Failed')
                self.wfile.write(response.getvalue())           
            
            if (Global_state_freezer_refrigerator_door == b'C' and Global_state_freezer_freezer_door == b'C'):
                doorstate = b'0'
            elif (Global_state_freezer_refrigerator_door == b'O' and Global_state_freezer_freezer_door == b'C'):
                doorstate = b'1'
            elif (Global_state_freezer_refrigerator_door == b'C' and Global_state_freezer_freezer_door == b'O'):
                doorstate = b'2'
            else:
                doorstate = b'3'  
                   
            Finalsenddata = b'USet_Freezer_' + doorstate + b'N' + b'N'   
            handel_TCPclient_mainthread.send(Finalsenddata)        
                    
        elif (self.path.count(OID_Oven_7) == 1):  #Oven   
            string = body.decode() #encode()
            print(string)
            if (string.count('door') == 1 and  string.count('CLOSED') == 1):     
                Global_state_oven_door = b'C'   
                
                if (Global_state_freezer_freezer_door == b'C' and Global_state_freezer_refrigerator_door == b'C'):
                    Global_state_emengency = b'Normal'
                    handle_timer_alarm.cancel()
                    Global_Status_Alarm = b'Disable'
                    Finalsenddata = b'USet_DoorAlr_' + b'0' + b'N' + b'N'   
                    handel_TCPclient_mainthread.send(Finalsenddata) 
                else:
                     #Stop alarm timer
                    handle_timer_alarm.cancel()
                    Global_Status_Alarm = b'Disable'
                    
                    #refersh alarm timer again
                    handle_timer_alarm=threading.Timer(Gloal_alarmdetecttime,timerfun_alarm,())  
                    handle_timer_alarm.start()
                    Global_Status_Alarm = b'Enable'
                    
            elif (string.count('door') == 1 and string.count('OPENED') == 1):
                Global_state_oven_door = b'O'  
                
                if (Global_Status_Alarm == b'Enable'):
                    #Stop alarm timer
                    handle_timer_alarm.cancel()
                    Global_Status_Alarm = b'Disable'
                    
                    #refersh alarm timer again
                    handle_timer_alarm=threading.Timer(Gloal_alarmdetecttime,timerfun_alarm,())  
                    handle_timer_alarm.start()
                    Global_Status_Alarm = b'Enable'
                else:
                    #start alarm timer again
                    handle_timer_alarm=threading.Timer(Gloal_alarmdetecttime,timerfun_alarm,())  
                    handle_timer_alarm.start()
                    Global_Status_Alarm = b'Enable'                
                
                
            elif (string.count('device_status') == 1 and string.count('RUNNING') == 1):
                Global_state_oven_device_status = b'R'  
                
            elif (string.count('device_status') == 1 and string.count('PAUSE') == 1):
                Global_state_oven_device_status = b'I'  
                
            elif (string.count('device_status') == 1 and string.count('IDLE') == 1):
                Global_state_oven_device_status = b'I'  
          
            else:
                response = BytesIO()
                response.write(b'HTTP/1.1 406 Failed')
                self.wfile.write(response.getvalue())                       
                   
            Finalsenddata = b'USet_OvenSta_' + Global_state_oven_door + Global_state_oven_device_status + b'N'   
            handel_TCPclient_mainthread.send(Finalsenddata)        
            
        else:   #Parking sensor
            
            string = body.decode() #encode()
            string = json.loads(string)
            print(string)
            Sensor_ID=string['sensor_id']
            Sensor_State=string['value']
        
            if (Sensor_ID=='008000000400882f'):
                if(Sensor_State=='Occupied'):
                    Global_state_parking_sensor_1 = b'O'
                else:
                    Global_state_parking_sensor_1 = b'F'

            elif (Sensor_ID=='0080000004008835'):   
               if(Sensor_State=='Occupied'):
                   Global_state_parking_sensor_2 = b'O'
               else:
                   Global_state_parking_sensor_2 = b'F'
         
            elif (Sensor_ID=='008000000400884a'):
                if(Sensor_State=='Occupied'):
                    Global_state_parking_sensor_3 = b'O'
                else:
                    Global_state_parking_sensor_3 = b'F'
          
            else:
                response = BytesIO()
                response.write(b'HTTP/1.1 406 Failed')
                self.wfile.write(response.getvalue())  
                
            if (Global_state_emengency == b'Alarm' and Global_state_parking_sensor_1 != b'R' and Global_state_parking_sensor_2 != b'R' and Global_state_parking_sensor_3 != b'R'):
                if (Global_state_parking_sensor_1 == b'F'):
                    Global_state_parking_sensor_1 = b'R'
                
                elif (Global_state_parking_sensor_2 == b'F'):
                    Global_state_parking_sensor_2 = b'R'
               
                elif (Global_state_parking_sensor_3 == b'F'):
                    Global_state_parking_sensor_3 = b'R'      
                    
            Finalsenddata = b'USet_ParkSen_' + Global_state_parking_sensor_1 + Global_state_parking_sensor_2 + Global_state_parking_sensor_3                     
            handel_TCPclient_mainthread.send(Finalsenddata)  

if __name__ == '__main__':
     #Create handel for TCP client to connect to Labview (main)  
     address = ('17486633in.iask.in', 31127)  
     handel_TCPclient_mainthread = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
     handel_TCPclient_mainthread.connect(address) 

     #Create handel for TCP client to connect to Labview (interrupt)
     address = ('17486633in.iask.in', 36539 )  
     handel_TCPclient_interruptthread = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
     handel_TCPclient_interruptthread.connect(address) 

     #Open the channel for publishing the Emergency Alarm event of AAU
     hd = {'adapter-id':'AAU_Adapter','infrastructure-id':'VAS_AN'}
     url = 'http://localhost:9997/agent/events/EmergencyAlarm'
     r=requests.request('POST',url,headers=hd)
     print(r.text)

     #subscribe to the event of freezer 7 (freezer door)            
     hd = {'adapter-id':'AAU_Adapter','infrastructure-id':'VAS_AN'}
     url = 'http://localhost:9997/agent/objects/' + OID_Freezer_7 + '/events/freezer_door'
     r=requests.request('POST',url,headers=hd)
     print(r.text)

     #subscribe to the event of freezer 7 (refrigerator_door)            
     hd = {'adapter-id':'AAU_Adapter','infrastructure-id':'VAS_AN'}
     url = 'http://localhost:9997/agent/objects/' + OID_Freezer_7 + '/events/refrigerator_door'
     r=requests.request('POST',url,headers=hd)
     print(r.text)

     #subscribe to the event of oven 7 (door)            
     hd = {'adapter-id':'AAU_Adapter','infrastructure-id':'VAS_AN'}
     url = 'http://localhost:9997/agent/objects/' + OID_Oven_7 + '/events/door'
     r=requests.request('POST',url,headers=hd)
     print(r.text)
     
     #subscribe to the event of oven 7 (device statusr)            
     hd = {'adapter-id':'AAU_Adapter','infrastructure-id':'VAS_AN'}
     url = 'http://localhost:9997/agent/objects/' + OID_Oven_7 + '/events/device_status'
     r=requests.request('POST',url,headers=hd)
     print(r.text)

     #subscribe to the event of parking sensor 1(sensor_id:008000000400882f)           
     hd = {'adapter-id':'AAU_Adapter','infrastructure-id':'VAS_AN'}
     url = 'http://localhost:9997/agent/objects/' + OID_Parking_Sensor_1 + '/events/sensor-b4be8848-35bd-4720-9158-305d7e5c8c2b'
     r=requests.request('POST',url,headers=hd)
     print(r.text)

     #subscribe to the event of parking sensor 2(sensor_id:0080000004008835)           
     hd = {'adapter-id':'AAU_Adapter','infrastructure-id':'VAS_AN'}
     url = 'http://localhost:9997/agent/objects/' + OID_Parking_Sensor_2 + '/events/sensor-849da2b0-8ed1-4d3b-bcac-46572b390acf'
     r=requests.request('POST',url,headers=hd)
     print(r.text)

     #subscribe to the event of parking sensor 3(sensor_id:008000000400884a)           
     hd = {'adapter-id':'AAU_Adapter','infrastructure-id':'VAS_AN'}
     url = 'http://localhost:9997/agent/objects/' + OID_Parking_Sensor_3 + '/events/sensor-64f41424-93ee-4130-8519-66a250f5bfe3'
     r=requests.request('POST',url,headers=hd)
     print(r.text)
     
     #start thread for publish event
     handel_timer_publishevent = threading.Timer(5,timerfun_publishevent,())  
     handel_timer_publishevent.start()

     #start main http server
     print('AAU Server is working!')
     httpd = HTTPServer(('localhost', 9995), SimpleHTTPRequestHandler)
     httpd.serve_forever()
    
