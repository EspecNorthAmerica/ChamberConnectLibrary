#!/bin/python3
'''
:author: Paul Nong-Laolam <pnong-laolam@espec.com>
:license: MIT, see LICENSE for more detail.
:copyright: (c) 2020, 2022, 2023. ESPEC North America, Inc. 
:file: p300_rs232.py 

Application interface for controlling Watlow F4T operations. 
This program may be and can be reimplemented with additional
call methods to utilize the Watlow F4T control interface
from its class and method definitions. 

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
README:
======

The following is a sample program call to the Library to control ESPEC P300
controller via the RS232 communication protocol. 

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

from chamberconnectlibrary.espec import Espec
from chamberconnectlibrary.p300 import P300 
from chamberconnectlibrary.especinteract import EspecSerial, EspecTCP 
from chamberconnectlibrary.controllerinterface import ControllerInterfaceError

'''
The following is a list of communication options: 

#example interface_params for RS232/RS485 on port 7 (windows) RS485 address = 1
interface_params = { 'interface':'Serial', 
                    'baudrate':19200, 
                    'serialport':'//./COM7', 
                    'adr':1}

#example interface_params for RS232/RS485 on ttyUSB0 (linux) RS485 address = 1
interface_params = {'interface':'Serial', 
                    'baudrate':19200, 
                    'serialport':'/dev/ttyUSB0',
                    'adr':1}

#example interface_params for a TCP connection to 10.30.100.55
interface_params = {'interface':'TCP', 'host':10.30.100.55}

#when connecting to a P300:
controller_type = 'P300'

#when connecting to a SCP220:
#controller_type = 'SCP220'

#example for temp only chamber
controller = Espec(ctlr_type=controller_type, loops=1, **interface_params)

#example for temp/humidity chamber
#controller = Espec(ctlr_type=controller_type, loops=2, **interface_params)

#example for temp only chamber w/ product temperature control (aka PTCON)
#controller = Espec(ctlr_type=controller_type, loops=0, cascades=1, **interface_params)

#example for temp/humidity chamber w/ product temperature control (aka PTCON)
#controller = Espec(ctlr_type=controller_type, loops=1, cascades=1, **interface_params)

#or the library can figure it out automatically:
#controller = Espec(ctlr_type=controller_type, **interface_params)

get_refrig()
get_datetime() 
get_loop_sp(N) # N = number of loop 
get_loop_pv(1) 
get_loop_range(N)
get_loop_en(N)
get_loop_units(N) 
get_loop_mode(N) 
get_loop_power(N)
get_cascade_sp(N)
get_cascade_pv(N) 
get_cascade_range(N) 
get_cascade_en(N) 
get_cascade_units(N) 
get_cascade_modes(N) 
'''

def fetch_temp_pv_sp():
    val = CONTROLLER.get_loop_pv(1)
    print (f'Temp PV: {val}')

    val = CONTROLLER.get_loop_sp(1)
    print (f'Temp SP: {val}')

def fetch_event_pwr_status(): 
    val = CONTROLLER.get_event(5)
    print (f'Time Signal (Event): {val}')

    val = CONTROLLER.get_loop_power(1)
    print (f'Power: {val}')

def main():
    '''main driver program'''
    fetch_temp_pv_sp() 
    fetch_event_pwr_status() 

def options():
    '''list of chamber/controller options'''
    print ("\nChamber/Controller Option:\n"
           "==================================\n"
           "0. ESPEC SCP-220 via RS232\n"
           "1. ESPEC P300 via RS232\n"
           "2. ESPEC P300 via TCP/IP\n"
           "==================================")

if __name__ == "__main__":
    '''main menu for the driver'''
    os.system('clear||cls') 

    SELECT_OPT = 0

    options() 
    while True:
        try:
            SELECT_OPT = int(input("Make Selection: "))
        except ValueError:
            print("Invalid number. Try again..")
            continue
        else:
            # SELECT_OPT = 0 for SCP220 RTU SERIAL INTERFACE 
            if SELECT_OPT == 0:
                controller_type = "SCP220"
                interface_params = {
                    'interface':'Serial',
                    'baudrate':'9600',           # opt: 9600, 19200
                    #'serialport':'//./COM5',    # for MS Windows platform
                    'serialport':'/dev/ttyUSB0', # GNU/Linux platform 
                    'adr':1
                }
                CONTROLLER = Espec(
                    ctrl_type=controller_type,
                    loops = 1,
                    **interface_params
                    #loop_names = LOOP_NAMES
                )
                print ("\nESPEC SCP220 CONTROLLER via RS232:")

            elif SELECT_OPT == 1:
            # SELECT_OPT = 1 for P300 via RS232 INTERFACE 
                controller_type = "P300"
                interface_params = {
                    'interface':'Serial',
                    'baudrate':'19200',          # opt: 9600, 19200
                    #'serialport':'//./COM5',    # for MS Windows platform
                    'serialport':'/dev/ttyUSB0', # GNU/Linux platform 
                    'adr':1
                }
                CONTROLLER = Espec(
                    ctrl_type=controller_type,
                    loops = 1,
                    **interface_params
                    #loop_names = LOOP_NAMES
                )

                print ("\nESPEC P300 CONTROLLER via RS232:")
            
            elif SELECT_OPT == 2:
            # SELECT_OPT = 1 for P300 via TCP/IP 
                controller_type = "P300"
                interface_params = {
                     'interface':'TCP',
                     'host':'10.30.100.10'  # use correct IP addr
                }
                CONTROLLER = Espec(
                    ctrl_type=controller_type,
                    loops = 1,
                    **interface_params
                    #loop_names = LOOP_NAMES
                )
                print ("\nThis option requires further implementation for IP address.")   
                exit()     
            else: 
                print ("Number out of range. Try again") 
                continue  
            break 

    main() 