# VICINITY-AAU-VAS- Abnormal situation identification for elderly residents
This documentation describes the adapter of AAU VAS - Abnormal situation identification for elderly residents.

# Infrastructure overview

Parking slot usage data is collected through VICINITY by using three parking sensors to achieve monitoring function. A residential microgrid, which consists of PV, wind turbine and battery, is emulated based on a real-time dSPACE experimental platform in AAU IoT-microgrid Lab. The residential microgrid is assumed to supply power to EV chargers in the three parking slots. GORENJE smart refrigerator is included in the residential microgrid. The real-time charging price is calculated by considering the simulated real-time utility electricity price, state-of-charge of batteries, and forecasts of the PV and wind turbine power generation. The VAS identifys abnormal situations for instance a GORENJE refrigerator’ door has been left open more than normal time and trigger notifications to care providers and reserve a free parking slot for an ambulance. 

Adapter serves as the interface between VICINITY and LabVIEW enabling to use all required interaction patterns.

![Image text](https://github.com/YajuanGuan/pics/blob/master/AbnormalElderly.png)

# Configuration and deployment

Adapter runs on Python 3.6.

# Adapter changelog by version
Adapter releases are as aau_adapter_x.y.z.py

## 1.0.0
Start version, it works with agent-service-full-0.6.3.jar, and it subscribes to the events of PlacePod parking sensor usage and GORENJE smart refrigerator #7 door status. 

# Functionality and API

## Publish an event to the subscribers. 
### Endpoint:
            PUT : /remote/objects/{oid}/events/{eid}
Publish the emergency alarm, the reserved parking slot number (0/1) and current time. 
### Return:
After subscribing the VAS successfully, the subscriber receives a response for instance:  
{  
    "state": "alarm",  
    "parking slot reserved": "1",  
    "time": "2018-11-10 11:30:29"  
}
