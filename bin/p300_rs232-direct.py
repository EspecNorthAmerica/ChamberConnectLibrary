#!/usr/bin/python3
'''
:author: Paul Nong-Laolam <pnong-laolam@espec.com>
:license: MIT, see LICENSE for more detail.
:copyright: (c) 2020, 2021. ESPEC North America, INC.
:file: p300_rs232-direct.py 
:date: March 2022
:updated: May 2024
--------------------------------------------------------------------------
README:
====== 

Application interface for controlling ESPEC P300 operations. 
This program may be and can be reimplemented with additional
call methods to utilize the P300 operation modes from its 
class and method definitions. 

The program has been modified from its original code that made use of
the original call methods from chamberconnectlibrary file p300.py. 
To make is easy and accessible, this file has been modified 
and placed under a new filename (p300serial.py) to provide a 
direct call to each method. The ESPEC P300 library has been 
extracted, modified and formalized to support all the available features. 

The following is a simple sample call program to serve as a starting 
point on how to utilize our ESPEC P300 library. Programmer can implement
or/and modify to include more complex call methods for their 
specific application. All you need to do is create a new definition with 
a specific call to the "p300serial.py" library and include that call
in the main method.   
--------------------------------------------------------------------------

How to Determine Communication Port: 
===================================

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

DISCLAIMER: 
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF 
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE 
OR THE USE OR OTHER DEALINGS IN THE SOFTWARE. 
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
'''
import time
import serial
import os, sys
import re
import logging
sys.path.insert(0,'../ChamberConnectLibrary')

from chamberconnectlibrary.p300serial import EspecP300
from chamberconnectlibrary.dictcode import dict_code

def get_temp():
    '''read parameters from chamber/controller
    
    this is a general method for reading a type of chamber
    operating values (status). 

    Examples: 
    To read temperature value, modify the try statment as:
    get_val = p300.read_temp() 

    To read vibration value, modify the try statment as:
    get_val = p300.read_vib() 

    To read ROM value, modify the try statment as:
    get_val = p300.read_rom()

    To read 'product temperature control' value (PTC value), modify the try statment as:
    get_val = p300.read_constant_ptc() 

    To read alarm, set it as: 
    get_val = p300.read_alarm() 
    '''
    try:
        get_val = p300.read_temp()
    except Exception as e: 
        get_val = e 
    return get_val 

def get_vib():
    '''read vib values
    if target chamber only supports temperature only 
    and/or temperature and humidity, it will throw an 
    exception.
    '''
    try:
       get_val = p300.read_vib()
    except Exception as e: 
       get_val = e 
    return get_val 

def get_op_mode():
    '''read operating mode value'''
    try: 
        mon_val = p300.read_mode()
    except Exception as e: 
        mon_val = e        
    return mon_val 

def main():
    '''main driver program'''
    print ("Probing the target controller...")
    time.sleep(1) 
    print (f'\nrsp> Temperature:\n {get_temp()}')
    print (f'\nrsp> Vibration:\n {get_vib()}') 
    print (f'\nrsp> Operating Mode: {get_op_mode()}')

if __name__ == '__main__':
    '''set up low-level communication with ESPEC P300 via RS232C
       call to the main definition to start the sample program. 
    '''
    os.system('clear||cls')
    p300=EspecP300()
    p300.open()
    main()
    p300.close()