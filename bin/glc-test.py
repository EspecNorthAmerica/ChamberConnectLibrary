#!/bin/python3
'''
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
:author: Paul Nong-Laolam <pnong-laolam@espec.com>
:license: MIT, see LICENSE for more detail.
:copyright: (c) 2025. ESPEC North America, Inc. 
:updated: December 2025
:file: glc_runTCP.py 

Application interface for controlling ESPEC GL controller with temperature
and humidity feature. This program may be reimplemented with additional
call methods to utilize ESPEC GL controller from its class and method 
definitions.  
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

README:
======

The following is a sample program call to the Library to control ESPEC GL 
controller via the TCP/IP or Serial RS-232 communication protocol. 

It is programmed to provide a simple call function to our ESPEC 
ChamberConnectLibrary to connect to "especinteract.py" program which in 
turn communicates with the "glc.py" library offer and utilize the 
operational features from "glc.py" in the chamberconenctlibrary directory. 

Note: 
"especinteract.py" supports both features of communication protocol: 
    1. Serial RS-232/RS485
    2. TCP/IP

This sample program utilizes and explains the use of option 1 and option 2
with correct setup for TCP/IP communication. 

The programmer may add the additional methods or program sections to call 
the library for the exact feature(s) not implemented here to meet their 
requirement. Thus, the following program serves as a starting point on how 
to utilize our ChamberConnectLibrary in the Python 3 environment. 

====================================
How to Determine Communication Port: 
====================================

MS Windows: COM? How to determine COM number assigned by MS Windows OS.
DOS command to list COM ports: \> chgport

GNU/Linux: /dev/ttyUSB? How to determine USB number assigned by Linux. 
Linux command to list /dev/ttyUSB: $ ls -l /dev/ttyUSB* 

How to find COM or USB number: 
MS Windows:
1. At the CMD prompt, issue:
   chgport
2. Study the list of COM numbers in output.
3. Plug in the USB-to-Serial cable and reissue the command: 
   chgport
4. Study the list of COM numbers in out put again. A new device with COM number 
should be listed, such as (for example): 

   COM5 = \Device\VCP0

5. Use this COM number in the program. Example: 
   port = '//./COM5' 

GNU/Linux 
1. At the shell terminal, issue:
   ls -l /dev/ttyUSB* 
2. Study the list of USB numbers in output.
3. Plug in the USB-to-Serial cable and reissue the command: 
   ls -l /dev/ttyUSB*
4. Study the list of USB numbers in output again. A new device with USB? number 
should be listed, such as (for example): 

   /dev/ttyUSB0

5. Use this number in the program. Example: 
   port = '/dev/ttyUSB0' 

Tested: 
GNU/Linux platform: Python 3.8.x, 3.9.x, 3.10.x
MS Windows platform: Python 3.9.x 

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% DISCLAIMER: 
% THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
% INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
% PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
% HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF 
% CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE 
% OR THE USE OR OTHER DEALINGS IN THE SOFTWARE. 
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
'''
import time,re
import os, sys
import logging
import serial 
sys.path.insert(0,'../chamberconnectlibrary')

from chamberconnectlibrary.glc import GLC
from chamberconnectlibrary.espec import Espec 
from chamberconnectlibrary.dictcode import dict_code
from chamberconnectlibrary.especinteract import EspecSerial, EspecTCP 
from chamberconnectlibrary.controllerinterface import ControllerInterfaceError

def ip_addr():
    '''select and check for proper IP address format
    '''
    while True:
        try:
            #ip_addr = input('Enter F4T IP address (e.g., 192.168.0.101): ')
            ip_addr = "10.30.200.247"
            chk_ip = re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip_addr)
            if chk_ip:
                print ('\n')
                break
        except Exception:
            print ('Invalid IP address.')
    return ip_addr

if __name__ == "__main__":
    '''main menu for the driver'''

    #LOOP_NAMES = ['Temperature', 'Humidity']
    os.system('clear||cls') 

    # set controller type
    controller_type = "GLC"

    # to manually enter IP address of GL controller system
    interface_params = {'interface':'TCP', 'host':ip_addr()}
    
    #    'adr':1

    CONTROLLER = Espec(
        ctrl_type=controller_type,
        loops = 1,
        **interface_params #,
        #loop_names = LOOP_NAMES
    )
    # Main action 

    ts_list = CONTROLLER.get_event(1)
    print (f'ROM: {ts_list}')

    str = CONTROLLER.get_mode()
    print (f'Op Mode: {str}')

    str = CONTROLLER.get_rom()
    print (f'Op Mode: {str}')

    str = CONTROLLER.get_date()
    print (f'Op Mode: {str}')

    str = CONTROLLER.get_date_time()
    print (f'Op Mode: {str}') 

    str = CONTROLLER.get_srq()
    print (f'Op Mode: {str}') 

    str = CONTROLLER.get_mask()
    print (f'Op Mode: {str}') 

    str = CONTROLLER.get_timer_on()
    print (f'Op Mode: {str}')     

    str = CONTROLLER.get_timer_use()
    print (f'Op Mode: {str}')         

    str = CONTROLLER.get_timer_list_quick()
    print (f'Op Mode: {str}')  

    str = CONTROLLER.get_timer_list_start()
    print (f'Op Mode: {str}')      

    str = CONTROLLER.get_timer_list_stop()
    print (f'Op Mode: {str}')       

    str = CONTROLLER.get_alarm()
    print (f'Op Mode: {str}')       

    str = CONTROLLER.get_keyprotect()
    print (f'Op Mode: {str}')       

    str = CONTROLLER.get_type()
    print (f'Op Mode: {str}')  

    str = CONTROLLER.get_mode()
    print (f'Op Mode: {str}')          

    str = CONTROLLER.get_mon()
    print (f'Op Mode: {str}')      

    str = CONTROLLER.get_temp()
    print (f'Op Mode: {str}')       

    str = CONTROLLER.get_humi()
    print (f'Op Mode: {str}')         

    str = CONTROLLER.get_set()
    print (f'Op Mode: {str}')           

    str = CONTROLLER.get_ref()
    print (f'Op Mode: {str}')     

    str = CONTROLLER.get_relay()
    print (f'Op Mode: {str}')       

    str = CONTROLLER.get_htr()
    print (f'Op Mode: {str}') 

    str = CONTROLLER.get_constant_temp()
    print (f'Op Mode: {str}')     

    str = CONTROLLER.get_constant_humi()
    print (f'Op Mode: {str}')                    

    str = CONTROLLER.get_constant_ref()
    print (f'Op Mode: {str}')         

    str = CONTROLLER.get_constant_relay()
    print (f'Op Mode: {str}')         

    #str = CONTROLLER.get_constant_ptc()
    #print (f'Op Mode: {str}')       

    str = CONTROLLER.get_system_set()
    print (f'Op Mode: {str}')     

    #str = CONTROLLER.get_mon_ptc()
    #print (f'Op Mode: {str}')      

    str = CONTROLLER.get_prgm_mon()
    print (f'Op Mode: {str}')     