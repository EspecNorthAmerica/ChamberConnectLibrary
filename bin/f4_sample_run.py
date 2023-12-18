#!/bin/python3
'''
:author: Paul Nong-Laolam <pnong-laolam@espec.com>
:license: MIT, see LICENSE for more detail.
:copyright: (c) 2022. ESPEC North America, INC.
:updated: 12/2023 for Watlow F4 (based on BTZ-133 chamber)
:file: f4_sample_run.py 

A simple test program to test RS232 communication with Watlow F4
via its RS232 interface, with a straight-through cable.  

baud rate: 19200
address: 1 

MS Windows: COM?   (? = number assigned by MS Windows OS)
Linux: /dev/ttyUSB?  (? = number (0,1,2) assigned by Linux)
'''
import pprint
import time
import os, sys
sys.path.insert(0,'../chamberconnectlibrary')

from chamberconnectlibrary.watlowf4t import WatlowF4T
from chamberconnectlibrary.watlowf4 import WatlowF4
from chamberconnectlibrary.espec import Espec

LOOP_NAMES = ['Temperature', 'Humidity']

def yy():
    i = input('READY...')
    return i 

os.system('clear||cls') 

#CONTROLLER = Espec(
#    interface='Serial',
#    serialport='//./COM10',
#    baudrate=19200,
#    loop_names=LOOP_NAMES
#)
CONTROLLER = WatlowF4(
    interface='RTU',
    serialport='//./COM4',
    baudrate=19200,
    loop_names=LOOP_NAMES
)

#CONTROLLER = WatlowF4T(
#     interface='TCP',
#     host='x.x.x.x', # requires the correct IP address of F4T
#     loop_names=LOOP_NAMES
#)
#CONTROLLER = WatlowF4T(
#    interface='RTU',
#    serialport='//./COM4', # COM4 must be the one used by your PC
#                           # or manually selected for the correct one
#    baudrate=38400,
#    loop_names=LOOP_NAMES
#)

# watlowf4t.process_controller() 

#print (f'{CONTROLLER.process_controller()}')

#print ('\ncascade loops:')
#for i in range(CONTROLLER.cascades):
#    print (CONTROLLER.get_loop(i+1, 'cascade', ['processvalue', 'setpoint']))
#


#print ('\nloops:')
#for i in range(CONTROLLER.loops):
#    print (CONTROLLER.get_loop(i+1, 'loop', 'processvalue', 'setpoint'))

### untested...bugs on Py3.6.8
#print ('\nnamed loops:')
#for name in LOOP_NAMES:
#    print (CONTROLLER.get_loop(name, ['processvalue', 'setpoint']))

#for name in LOOP_NAMES:
#    print (CONTROLLER.set_loop(name, setpoint=60.0))

#print ('\noperations:')
#print (CONTROLLER.get_operation())
#CONTROLLER.set_operation('standby')

#yy()
#os.system('clear||cls') 
#print ('\nEvents:')
#for i in range(8):
#    print (CONTROLLER.get_event(i+1))

#yy()
#os.system('clear||cls')
#for i in range(8):   # tested to turn on all events with 'on' string 
#    print (CONTROLLER.set_event(i+1,'on'))


print ('Get current Temp SP...')
yy()
for i in range(1): # tested with single loop 
   print (f'HERE IT IS: {CONTROLLER.get_loop_sp(i+1)}') 

print ('Get current Temp PV...')
yy()
for i in range(1): # tested with single loop 
   print (f'HERE IT IS: {CONTROLLER.get_loop_pv(i+1)}') 

print ('Set Temp SP to new val...')
try:
    value = float(input('Enter rate value: '))
    if isinstance(value, (int, float)):
        CONTROLLER.set_loop_sp(1,value) # set_loop_sp(self, N, value)
    else:
        print ('Value must be a decimal number.') 
except ValueError:
    print ('Invalid operation. Option terminated.') 

print ('CURRENT VALUES:')
pv=CONTROLLER.get_loop_pv(1)
sp=CONTROLLER.get_loop_sp(1)
print (f'\nPV: {pv} \nSP: {sp}')

for i in range(1): # tested with single loop 
   CONTROLLER.set_loop_sp(i+1,22.5) # set_loop_sp(self, N, value)

for i in range(1): # tested with single loop 
   print (f'HERE IT IS: {CONTROLLER.get_loop_pv(i+1)}') 

