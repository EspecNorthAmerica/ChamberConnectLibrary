#!/bin/python3
'''
:author: Paul Nong-Laolam <pnong-laolam@espec.com>
:license: MIT, see LICENSE for more detail.
:copyright: (c) 2020, 2024. ESPEC North America, Inc. 
:updated: May 2024; modified and expanded to support P300 Vib on Python 3.6+
:file: p300vib_rs232.py 

Application interface for controlling ESPEC P300 with Vibration
feature. This program may be reimplemented with additional
call methods to utilize ESPEC P300 w/ Vibration
from its class and method definitions. 

DISCLAIMER: 
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF 
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE 
OR THE USE OR OTHER DEALINGS IN THE SOFTWARE. 
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
README:
======

The following is a sample program call to the Library to control ESPEC P300
controller with Vibration via the RS232 communication protocol. 

It is programmed to provide a simple call function to our ESPEC 
ChamberConnectLibrary to connect to "especinteract.py" program which in 
turn communicates with the "p300.py" library offer and utilize the 
operational features from "p300.py" in the chamberconenctlibrary directory. 

Note: "especinteract.py" supports both features of communication protocl: 
    1. Serial RS-232/RS485
    2. TCP/IP

This sample program utilizes and explains the use of option 1. 

The programmer may add the additional methods or program sections to call 
the library for the exact feature(s) not implemented here to meet their 
requirement. Thus, the following program serves as a starting point on how 
to utilize our ChamberConnectLibrary in the Python 3 environment. 

Tested: 
GNU/Linux platform: Python 3.8.x, 3.9.x, 3.10.x
MS Windows platform: Python 3.9.x 
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
'''
import time,re
import os, sys
import logging
import serial 
sys.path.insert(0,'../ChamberConnectLibrary')

from chamberconnectlibrary.espec import EspecVib  
from chamberconnectlibrary.p300vib import P300Vib 
from chamberconnectlibrary.especinteract import EspecSerial, EspecTCP 
from chamberconnectlibrary.controllerinterface import ControllerInterfaceError

def fetch_temp_pv_sp(loop):
    val = CONTROLLER.get_loop_pv(loop)
    print (f'Temp PV: {val}')

    val = CONTROLLER.get_loop_sp(loop)
    print (f'Temp SP: {val}')

def fetch_vib_pv_sp(loop):
    val = CONTROLLER.get_loop_pv(loop)
    print (f'Vibration: {val}')

    val = CONTROLLER.get_loop_sp(loop)
    print (f'Vibration: {val}')

def fetch_temp_loop_range(loop):
    val = CONTROLLER.get_loop_range(loop)
    print (f'Temperature Range: {val}')

def fetch_vib_loop_range(loop): 
    val = CONTROLLER.get_loop_range(loop)
    print (f'Vibration Range: {val}')

def start_const():
    CONTROLLER.const_start() 
    print ("Starting CONSTANT mode...")

def stop():
    CONTROLLER.stop() 
    print ("Stopping operation...")

def set_new_val(loop,x):
    CONTROLLER.set_loop_sp(loop,x)
    print (f"Set Vib value to: {x}")

def fetch_event(loop):
    val = CONTROLLER.get_event(loop)
    return val 

def fetch_loop_mode(loop):
    val = CONTROLLER.get_event(loop) 
    return val 

def fetch_loop_all(loop):
    val = CONTROLLER.get_loop_all(loop)
    return val 

def fetch_status(loop): 
    val = CONTROLLER.get_loop_mode(loop) 
    return val 

def fetch_prgm_name(loop):
    val = CONTROLLER.get_prgm_name(loop)
    return val 

def fetch_mode():
    str1 = CONTROLLER.get_mode()
    return str1

def main():
    '''main driver program'''
    # TEMP: loop = 1
    # VIB: loop = 2
    print ("""\nThis simple program probes ESPEC P300 via RS232 and reads\n"""
        + """a few parameters from the controller and display them as follows.\n"""
        + """Programmers may add their own method definitions using the p300.py\n"""
        + """library to meet their programming requirements.\n"""
    )
    print ("Probing...reading...")
    time.sleep(1)
    fetch_temp_pv_sp(1) 
    fetch_vib_pv_sp(2) 
    fetch_temp_loop_range(1) 
    fetch_temp_loop_range(2) 


if __name__ == "__main__":
    '''main menu for the driver'''

    LOOP_NAMES = ['Temperature', 'Vibration']   # set for Vibration/Humidity 
    #os.system('clear||cls') 

    controller_type = "P300Vib"      # custom define for P300 or P300Vib 
    interface_params = {
        'interface':'Serial',
        'baudrate':'19200',          # opt: 9600, 19200
        #'serialport':'//./COM5',    # for MS Windows platform
        'serialport':'/dev/ttyUSB1', # GNU/Linux platform 
        'adr':1
    }
    
    CONTROLLER = EspecVib(
        ctrl_type=controller_type,
        loops = 1,
        **interface_params #,
        #loop_names = LOOP_NAMES
    )
    main()