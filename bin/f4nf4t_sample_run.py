#!/usr/bin/python3
'''
:author: Paul Nong-Laolam <pnong-laolam@espec.com>
:license: MIT, see LICENSE for more detail.
:copyright: (c) 2022. ESPEC North America, INC.
:updated: 12/2023 for Watlow F4 (based on BTZ-133 chamber)
:file: f4nf4t_sample_run.py 
-------------------------------------------------------------------------------

README:
======
A simple test program to test RS232 communication with Watlow F4 and F4T.
Communication itnerface support: 

RTU serial connect
F4 and F4t via RTU (RS232) interface, with a straight-through or null cable.  

F4 RTU settings: 
baud rate: 19200
address: 1 

F4T RTU settings:
baud rate: 38400
address: 1

TCP/IP connect: 
F4T can also communicate via TCP/IP. 

Program performs communication test by reading temperature values from target controller.

MS Windows: COM? How to determine COM number assigned by MS Windows OS.
GNU/Linux: /dev/ttyUSB? How to determine USB number assigned by Linux.

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

HOW TO USE THIS PROGRAM:
-----------------------
All interactions with the process controller are accomplished with the 
def methods; each method is called to probe and read information
from the controller. 

To add more control options, build the def methods then call them to
perform the required tasks.

DISCLAIMER: 
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF 
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE 
OR THE USE OR OTHER DEALINGS IN THE SOFTWARE. 
'''
import pprint
import time
import os, sys, re
sys.path.insert(0,'../ChamberConnectLibrary')

from chamberconnectlibrary.watlowf4 import WatlowF4
from chamberconnectlibrary.watlowf4t import WatlowF4T

LOOP_NAMES = ['Temperature', 'Humidity']

def com_num():
    '''get com port input number
    '''
    COM_NUM = 0
    while True:
        try:
            COM_NUM = int(input("Enter COM port number: "))
        except ValueError:
            print("Invalid number. Try again..")
            continue
        else:
            # uncomment for MS Windows
            serialport=f'//./COM{COM_NUM}'       # MS Windows
            # uncomment for GNU/Linux
            #serialport=f'/dev/ttyUSB{COM_NUM}'   # GNU/Linux
            break
    return serialport 

def ip_addr():
    '''select and check for proper IP address format
    '''
    while True:
        try:
            ip_addr = input('Enter F4T IP address (e.g., 192.168.0.101): ')
            chk_ip = re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip_addr)
            if chk_ip:
                print ('\n')
                break
        except Exception:
            print ('Invalid IP address.')
    return ip_addr

def chamber_status(): 
    '''get operation status'''
    status = CONTROLLER.get_operation()
    return status # CONTROLLER.set_operation('standby')

def get_current_temp():
    '''get current temp values'''
    # get current Temp SP
    for i in range(1): # tested with single loop 
        get_sp = CONTROLLER.get_loop_sp(i+1)

    # get current Temp PV
    for i in range(1): # tested with single loop 
        get_pv = CONTROLLER.get_loop_pv(i+1)
    return get_sp, get_pv 

def read_current_temp_val():
    '''read new values from chamber'''
    pv = CONTROLLER.get_loop_pv(1)
    sp = CONTROLLER.get_loop_sp(1) 
    return (f'\nPV: {pv} \nSP: {sp}')

def get_event():
    '''read current event output, time signals'''
    print ('\nEvents:')
    for i in range(8):
        print (CONTROLLER.get_event(i+1))

def set_temp_val():
    '''set a new temp value'''
    print ('\nSetting a new Temp SP value...')
    try:
        value = float(input('Enter value (press <Enter> to skip): '))
        if isinstance(value, (int, float)):
            CONTROLLER.set_loop_sp(1,value) #set_loop_sp(self, N, value)
        else:
            print ('Value must be a decimal number.') 
    except ValueError:
        print ('Invalid operation. Option terminated.') 

def main():
    '''main driver to read chamber status
    
    To add more features, create a method for that feature
    and add the call statement in this main. 
    '''
    print(f'\nChamber Status:\n{chamber_status()}')
    #print(f'\nCurrent temp: {get_current_temp()}') 
    print(f'\nCurrent Temp Readings: {read_current_temp_val()}')
    get_event()
    set_temp_val()

def options():
    '''list of chamber/controller options'''
    print ("\nChamber/Controller Option:\n"
           "==================================\n"
           "0. Chamber with F4\n"
           "1. Chamber with F4T via TCP/IP\n"
           "2. Chamber with F4T via Serial RTU\n"
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
            # SELECT_OPT = 0 for F4 RTU SERIAL INTERFACE 
            if SELECT_OPT == 0: 
                CONTROLLER = WatlowF4(
                    interface='RTU',
                    #serialport=f'//./COM{COM_NUM}', # e.g.: COM4, COM5
                    serialport = com_num(),
                    baudrate=19200,
                    loop_names=LOOP_NAMES
                )
                print (f'\nWatlow F4:')

            elif SELECT_OPT == 1:
            # SELECT_OPT = 1 for F4T TCP/IP INTERFACE 
                CONTROLLER = WatlowF4T(
                    interface='TCP',
                    # host='x.x.x.x', # requires the correct IP address of F4T
                    host=ip_addr(), 
                    loop_names=LOOP_NAMES
                )
                print (f'\nWatlow F4T via TCP/IP:')

            elif SELECT_OPT == 2:
            # SELECT_OPT = 1 for F4T RTU SERIAL INTERFACE
                CONTROLLER = WatlowF4T(
                    interface='RTU',
                    serialport = com_num(), 
                    baudrate=38400,
                    loop_names=LOOP_NAMES
                )
                print (f'\nWatlow F4T via RTU:')
            else: 
                print ("Number out of range. Try again") 
                continue  
            break
    main()