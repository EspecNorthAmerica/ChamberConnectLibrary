#!/bin/python3
'''
:author: Paul Nong-Laolam <pnong-laolam@espec.com>
:license: MIT, see LICENSE for more detail.
:copyright: (c) 2020, 2022, 2023. ESPEC North America, INC.
:file: f4t_runRTU.py 

Application interface for controlling Watlow F4T operations. 
This program may be and can be reimplemented with additional
call methods to utilize the Watlow F4T control interface
from its class and method definitions. 

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
README:
======

The following is a sample program call to the Library to control the F4T controller.
It is programmed to provide a menu to offer some of the operational features
of the F4T selected from ESPEC ChamberConnectLibrary.

This sample program applies Modbus/RTU (RS-232) protocol for communication. 

The programmer may add the additional program section to call the library for 
the exact feature(s) not implemented here to meet their requirement. Thus, the 
following program serves as a starting point on how to utilize our 
ChamberConnectLibrary in the Python 3 environment. 

Tested: Python 3.9.2; requires at least Python 3.6
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
'''
import time,re
import os, sys
import logging
sys.path.insert(0,'../chamberconnectlibrary')

from chamberconnectlibrary.watlowf4t import WatlowF4T
from chamberconnectlibrary.controllerinterface import ControllerInterfaceError

#example interface_params for RS232/RS485 on port 7 (windows) Modbus address=1
#interface_params = {'interface':'RTU', 'baudrate':38400, 'serialport':'//./COM7', 'adr':1}

#example interface_params for RS232/RS485 on ttyUSB0 (linux) Modbus address=1
interface_params = {'interface':'RTU', 'baudrate':38400, 'serialport':'/dev/ttyUSB0', 'adr':1}

#example interface_params for a TCP connection to 10.30.100.55
#interface_params = {'interface':'TCP', 'host':10.30.100.55}

#example for temp only chamber (BTU-??? or BTZ-???)
controller = WatlowF4T(
    alarms=8,                # number of available alarms
    profiles=True,           # controller has programming
    loops=1,                 # number of control loops (i.e., temperature)
    cond_event=9,            # events with enables/disables properties
    cond_event_toggle=False, # is the condition momentary(False), or maintained(True)
    run_module=1,            # module with chamber run output
    run_io=1,                # run output on the mdoule on chamber with run out put
    limits=[5],              # list of modules with limit type cards.
    **interface_params
)

LOOP_NAMES = ['Temperature', 'Humidity']

#CONTROLLER = Espec(
#    interface='Serial',
#    serialport='//./COM10',
#    baudrate=19200,
#    loop_names=LOOP_NAMES
#)
# CONTROLLER = WatlowF4(
#     interface='RTU',
#     serialport='//./COM7',
#     baudrate=19200,
#     loop_names=LOOP_NAMES
# )
# CONTROLLER = WatlowF4T(
#     interface='TCP',
#     host='10.30.100.138',
#     loop_names=LOOP_NAMES
# )
CONTROLLER = WatlowF4T(
     interface='RTU',
     serialport='/dev/ttyUSB0',
     #serialport='//./COM4',
     baudrate=38400,
     loop_names=LOOP_NAMES
)
#print CONTROLLER.process_controller()

# print '\ncascade loops:'
# for i in range(CONTROLLER.cascades):
#     print CONTROLLER.get_loop(i+1, 'cascade', ['processvalue', 'setpoint'])

# print '\nloops:'
# for i in range(CONTROLLER.loops):
#     print CONTROLLER.get_loop(i+1, 'loop', 'processvalue', 'setpoint')

# print '\nnamed loops:'
# for name in LOOP_NAMES:
#     print CONTROLLER.get_loop(name, ['processvalue', 'setpoint'])

# for name in LOOP_NAMES:
#     print CONTROLLER.set_loop(name, setpoint=60.0)

# print '\noperations:'
# print CONTROLLER.get_operation()
# CONTROLLER.set_operation('standby')

# print '\nEvents:'
# for i in range(8):
#     print CONTROLLER.get_event(i+1)
loop=1
currentSP = controller.get_loop_sp(loop)
currentPV = controller.get_loop_pv(loop)
print(f'\nrsp> {str} status:\n     PV: {currentPV}\n     SP: {currentSP}')
