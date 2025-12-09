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
controller via the TCP/IP or Serial RS-232 communication protocol to
monitor and control the GL chamber. 

It is a "canned program" with selected options. You may use this program
to get started by exploring what it does. You can then modify it to
include specific function calls to accommplish your needs. 

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
GNU/Linux platform: Python 3.8.x, 3.9.x, 3.10.x,3.13.x
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

from chamberconnectlibrary.espec import Espec 
from chamberconnectlibrary.glc import GLC
from chamberconnectlibrary.dictcode import dict_code
from chamberconnectlibrary.especinteract import EspecSerial, EspecTCP 
from chamberconnectlibrary.controllerinterface import ControllerInterfaceError

def ip_addr():
    '''
    select and check for proper IP address format
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

def set_loop(str, loop):
    '''
    set new temp value
    '''
    # recording temp range 
    loop_num = [1,2] 
    val_range = CONTROLLER.get_loop_range(loop)
    str1 = "Temperature Range" if loop == 1 else "Humidity Range"
    print (f'\n{str1}:\nMAX: {val_range["max"]}\nMIN: {val_range["min"]}')
    print ('\n<Apply new Set Point>')
    try:
        while True:
            try:
                val = float(input('Enter new SP value (Ctrl-C to cancel): '))
                if isinstance(val, int) or isinstance(val,float):
                    if loop in loop_num:   # if loop == 1 or loop == 2: 
                        if val_range["min"] <= val <= val_range["max"]:                            
                            CONTROLLER.set_loop_sp(loop,val)
                            break
                        else:
                            print ('ERROR! Value out of range. Try again. \n')
            except ValueError:
                print ('Invalid value.\n')
            except KeyboardInterrupt:
                break
                pass 
    except KeyboardInterrupt:
        pass

    time.sleep(0.5)
    currentSP = CONTROLLER.get_loop_sp(loop)
    currentPV = CONTROLLER.get_loop_pv(loop)
    print(f'\nrsp> {str} status:\n     PV: {currentPV}\n     SP: {currentSP}')

def read_val(str,loop):
    '''
    Read current values of Temp or Temp and Humi SP and PV
    '''
    time.sleep(0.5)
    currentSP = CONTROLLER.get_loop_sp(loop)
    currentPV = CONTROLLER.get_loop_pv(loop)
    print(f'\nrsp> {str} status:\n     PV: {currentPV}\n     SP: {currentSP}')

def operation_status(): 
    '''
    Check current status of chamber before executing a new program
    '''
    chk_alarm = CONTROLLER.get_alarm_status() 
    if chk_alarm["active"] == 'active': 
        print ("Chamber is in alarm state and must be cleared first.")
    else: 
        str = CONTROLLER.get_mode()
        time.sleep(0.5)
        if str in ['Program Running']:
            print ('\nrsp> Program execution is in progress; it must be stopped first.') 
        elif str in ['Constant', 'CONSTANT', 'constant']:
            print ('\nrsp> Chamber in Constant mode; it must be stopped first.')            
        else:
            # execute new program 
            run_prog() 

def run_prog(): 
    '''
    select and set profile for execution.
    '''
    # checking existing programs, program numbers
    str = CONTROLLER.get_prgm_use()
    print(f'Available program number(s): {str}')
    prm_num = int(len(str)) - 1
    print ('\n<Select a profile to execute>')
    try: 
        while True:
            pn = int(input(f'Enter profile number between 1 and {prm_num} (Ctrl-C to exit profile execution): '))
            if isinstance(pn, int) and 1 <= pn <= prm_num:
                psteps = CONTROLLER.get_prgm_steps(pn)
                sn = int(input('Enter step number: '))
                if isinstance(sn, int) and 1 <= sn <= psteps:
                    print (f'\nrsp> Executing profile {pn} step number {sn}')
                    CONTROLLER.prgm_start(pn,sn)
                    break
                else:
                    print (f'Invalid step number; available steps: 1 through {psteps}.')
                break 
            else:
                print ('Invalid Profile No. Program not found.')
    except KeyboardInterrupt:
            pass

def prog_mode(mode):
    '''
    set program mode of currently running profile

       available modes: 
          stop: terminate program
          pause: suspend current running program
          resume: resume execution of program
          mode: STOP, PAUSE, RESUME 
    '''
    nlist = { 
        'nact': f'\nrsp> No program running. Nothing to do.',
        'act' : f'\nrsp> {mode} current program.',
        'pau' : f'\nrsp> Program is already in paused...request is ignored.',
        'run' : f'\nrsp> Program is already running...request is ignored.',
    }
    str = CONTROLLER.get_mode()
    time.sleep(0.5)
    if "Program Running" in str:  
        if "STOP" in mode:
            print (nlist["act"])
            CONTROLLER.stop()        
        if "PAUSE" in mode:
            print (nlist["act"])
            CONTROLLER.prgm_pause()
        if "SKIP" in mode:
            print ('\nrsp> Skip to next step in program...') 
            CONTROLLER.prgm_next_step()
        if "RESUME" in mode:
            print (nlist['run'])
            CONTROLLER.prgm_resume()     
    elif "Program Paused" in str: 
        if mode == 'RESUME':
            print (nlist["act"])
            CONTROLLER.prgm_resume()
        if mode == 'STOP':
            print (nlist["act"])
            CONTROLLER.stop()
        if mode == 'SKIP':  
            print (nlist["pau"])
        if mode == 'PAUSE':  
            print (nlist["pau"])
    else:
        print (nlist['nact']) 

def set_time_signal(state):
    '''
    Set TS value on the selected TS number
    '''
    try:
        ts_num = int(input('Enter TS number: '))
        if isinstance(ts_num, int) and ts_num in range(1,13):
            print ('\nrsp> To be implemented by programmer...')
            #CONTROLLER.set_event(ts_num,state)
            #print ('\nrsp> DONE') 
        else:
            print ('\nrsp> Invalid TS number.')
    except ValueError:
        print ('Invalid TS number.')

def read_time_signal():
    '''
    Read TS value on the select TS number
    '''
    print ('\nrsp> ')
    for i in range(12):
        ts_list = CONTROLLER.get_event(i+1)
        tsout = 'ON' if ts_list['current'] == True else 'OFF'
        print (f'    Time signal #{i+1} : {tsout}')

def const_start():
    '''
    Start Constant mode on chamber
    '''
    str = CONTROLLER.get_mode()
    time.sleep(0.5)
    if str in ['Program Running','Program Paused']: 
        print (f'\nrsp> Chamber is in {str} mode. Must stop it first.')
    elif str in ['constant', 'Constant', 'CONSTANT']:
        print (f'\nrsp> Chamber is already in {str} mode.')
    else:
        CONTROLLER.const_start()
        time.sleep(0.5)
        print (f'\nrsp> CONSTANT mode started.') 

def stop_const():
    '''
    Stop constant mode on chamber
    '''
    str = CONTROLLER.get_mode()
    time.sleep(0.5)
    if str in ['constant', 'Constant', 'CONSTANT']:
        CONTROLLER.stop()
        time.sleep(0.5) 
        print ('\nrsp> Done ')
    elif str in ['Program Running', 'Program Paused']:
        print (f'\nrsp> Chamber is in {str} mode. Request ignored.')
    else:    
        print ("\nrsp> Chamber not in Constant mode. Nothing to do.")

def temp_humi_controller():
    '''
       set options for Temp and Humi controls
    '''
    def temp_humi_menu(choice):
        '''return T/H menu option'''
        return {
            'r': lambda: read_val('Temp',1),
            't': lambda: set_loop('Temp',1),
            'h': lambda: read_val('Humi',2),
            's': lambda: set_loop('Humi',2),
            'z': lambda: main_menu()
        }.get(choice, lambda: print ('\nrsp> Not a valid option.') )()  

    while(True):
        print_menu('2','Temp/Humi')
        option = input('Select option (r, t, h, s, z): ')
        temp_humi_menu(option)

def prog_menu():  # tested 
    '''
    set up selection menu for operation
       main menu 
       m: Program status
       e: execute program
       n: skip to next step 
       p: pause program
       r: resume program
       s: stop program
       z: return to Main Menu 
    '''
    def prog_operation(choice):
        '''return status option'''
        return {
            'm': lambda: print (f'\nrsp> {CONTROLLER.get_mode()}'),
            'e': lambda: operation_status(),
            'n': lambda: prog_mode('SKIP'),
            'p': lambda: prog_mode('PAUSE'),
            'r': lambda: prog_mode('RESUME'),
            's': lambda: prog_mode('STOP'),
            'z': lambda: main_menu(),
        }.get(choice, lambda: print ('\nrsp> Not a valid option') )()

    while(True):
        print_menu('3','Program')
        option = input('Select option (m, e, n, p, r, s, z): ')
        prog_operation(option)

def event_controller():
    '''
    Test TS events
    '''
    def event_option(option) :
        '''
        get event seelction menu
        '''
        return {
            'r': lambda: read_time_signal(),
            's': lambda: set_time_signal(True),
            'o': lambda: set_time_signal(False),
            'z': lambda: main_menu()
        }.get(option, lambda: print ('\nrsp> Not a valid option.') )()

    while(True):
        print_menu('4','Event')
        option = ''
        option = input('Select option (r, s, o, z): ')
        event_option(option) 

def status_menu():
    '''
    read chamber mode
    '''
    def status_option(choice):
        '''
        return status options
        '''
        return {
            'r': lambda: print (f'\nrsp> {CONTROLLER.get_mode()}'),
            's': lambda: const_start(), 
            'o': lambda: stop_const(),
            'a': lambda: print (f'\nrsp> {CONTROLLER.get_alarm_status()}'),
            'd': lambda: print (f'\nrsp> {CONTROLLER.get_datetime()}'),
            'i': lambda: print (f'\nrsp> {CONTROLLER.get_rom()}'), 
            'z': lambda: main_menu(),
        }.get(choice, lambda: print ('\nrsp> Not a valid option') )()

    while(True):
        print_menu('5','chamber mode')
        option = input('Select option (r, s, o, a, d, i, z): ')
        status_option(option)

def end_program():
    print ("Program terminated.\n")
    exit() 

def main_menu(): 
    '''
       Set options for program control
    '''
    def main_option(choice):
        '''
        return main menu options
        '''
        return {
            't': lambda: temp_humi_controller(),
            'p': lambda: prog_menu(),
            'e': lambda: event_controller(),
            's': lambda: status_menu(),
            'z': lambda: end_program(),
        }.get(choice, lambda: print ('\nrsp> Not a valid option') )()

    while(True):
        print_menu('1','Main Menu')
        option = input('Select option (t, p, e, s, z): ')
        main_option(option)

def print_menu(choice, menu_name):
    '''
    set up selection menu
    '''
    print (f'\nGL control options: {menu_name}'
            '\n--------------------------------') 
    for key in menu(choice).keys():
        print (f'  [{key}]:', menu(choice)[key] )
    print ('--------------------------------') 

def menu(choice):
    '''
    menu list
    main menu option: 
       1: main menu
       2: Temp/Humi menu
       3: Program menu
       4: Output (Time Signal) menu
       5: Chamber operating mode
    '''
    # main menu 
    main_menu = {
        't': 'Temp/Humi SP control           ',
        'p': 'Program control               ',
        'e': 'Event control                 ',        
        's': 'Chamber operating mode        ',
        'z': 'Exit                          '
    }

    # temp and humi ctrl menu
    th_menu = {
        'r': 'Read Temperature SP and PV    ',
        't': 'New Temperature Set Point     ',
        'h': 'Read Humidity SP and PV      ',
        's': 'New Humidity Set Point       ',
        'z': 'Return to Main Menu           '
    }

    # program menu 
    prog_menu = {
        'm': 'Operating status              ',
        'e': 'Execute program               ',
        'n': 'Skip to next step             ',
        'p': 'Pause program                 ',
        'r': 'Resume program                ',
        's': 'Stop program                  ',
        'z': 'Return to Main Menu           '
    }

    # event ctrl menu 
    ts_menu = {
        'r': 'Read event (TS) output        ',
        's': 'Set event (TS) output         ', 
        'o': 'Turn off TS output            ',
        'z': 'Return to Main Menu           '
    }

    # unit menu 
    status_menu = {
        'r': 'Read chamber mode             ',
        's': 'Start constant mode           ',
        'o': 'Stop constant mode            ',
        'a': 'Read alarm history            ', 
        'd': 'Read chamber date/time        ',
        'i': 'Read ROM information          ',        
        'z': 'Return to Main Menu           '
    }

    return {
        '1': lambda: main_menu,
        '2': lambda: th_menu,
        '3': lambda: prog_menu,
        '4': lambda: ts_menu,
        '5': lambda: status_menu,
    }.get(choice, lambda: print('\nrsp> Not a valid option') )()

if __name__ == "__main__":
    '''main menu for the driver'''

    #LOOP_NAMES = ['Temperature', 'Humidity']
    os.system('clear||cls') 

    #############
    # To run this program on MS Windows, comment out the following
    # line that contains '/dev/ttyUSB0' and uncomment the line above
    # it to include the COM?, where ? is the number used by your OS;
    # read the "README" section at the top of this program.
    #

    # set controller type
    controller_type = "GLC"

    # set GLC parameters and protocol 
    #interface_params = {
    #    'interface':'Serial',
    #    'baudrate':'19200',          # opt: 9600, 19200
    #    #'serialport':'//./COM5',    # for MS Windows platform
    #    'serialport':'/dev/ttyUSB1', # GNU/Linux platform 
    #    'adr':1
    #}
    # SELECT_OPT = 1 for GLC via TCP/IP
    # IP addr is required to use this interface. 
    #interface_params = {
    #        'interface':'TCP',
    #        'host':'10.30.200.247'  # use correct IP addr
    #}

    # to manually enter IP address of GL controller system
    interface_params = {'interface':'TCP', 'host':ip_addr()}

    #interface_params = {
    #    'interface':'Serial',
    #    'baudrate':'19200',          # opt: 9600, 19200
    #    #'serialport':'//./COM5',    # for MS Windows platform
    #    'serialport':'/dev/ttyUSB1', # GNU/Linux platform 
    #    'adr':1

    CONTROLLER = Espec(
        ctrl_type=controller_type,
        loops = 1,
        **interface_params #,
        #loop_names = LOOP_NAMES
    )
    main_menu()

    '''
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
    print (f'MODE: {str}')          

    str = CONTROLLER.get_mon()
    print (f'MONITOR: {str}')      

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

    # err: NA: INVALID REQ 
    #str = CONTROLLER.get_constant_ptc()
    #print (f'Op Mode: {str}')       

    str = CONTROLLER.get_system_set('PTS')
    print (f'SYSTEM SET: {str}')     

    # err: NA: INVALID REQ 
    #str = CONTROLLER.get_mon_ptc()
    #print (f'Op Mode: {str}')      

    # err: NA: INVALID REQ 
    #str = CONTROLLER.get_prgm_mon()
    #print (f'Op Mode: {str}')     

    str = CONTROLLER.get_prgm_use()
    print (f'PRGM USE: {str}')       

    # err: CHB NOT READY 
    #str = CONTROLLER.get_prgm_set()   # err: chamber not ready 
    #print (f'Op Mode: {str}')       

    str = CONTROLLER.get_prgm_use()
    prm_num = len(str) 
    print (f'Select PRGM NUM BETWEEN 1 and {prm_num-1}:')
    num = int(input("PRGM NUM:"))
    str = CONTROLLER.get_prgm_use_num(num)
    print (f'PRGM USE NUM: {str}')    

    #str = CONTROLLER.get_prgm_use()
    #prm_num = len(str) 
    #print (f'Select PRGM NUM BETWEEN 1 and {prm_num-1}:')
    num = int(input("PRGM NUM:"))
    str = CONTROLLER.get_prgm_data(num)
    print (f'PRGM DATA: {str}')      

    num = int(input("PRGM NUM:"))
    str = CONTROLLER.get_prgm_data_detail(num)
    print (f'PRGM DATA DETAIL: {str}')        

    prgmnum = int(input("PRGM NUM:"))
    stepnum = int(input('STEP NUM:'))
    str = CONTROLLER.get_prgm_data_step(prgmnum,stepnum)
    print (f'PRGM DATA DETAIL STEP: {str}')       

    # err: NA: CHMB NOT READY 
    #str = CONTROLLER.get_prgm_mon()
    #print (f'PRGM DATA: {str}')  

    str = CONTROLLER.get_run_prgm()
    print (f'PRGM STATUS: {str}')  

    # err: NA: CHMB NOT READY 
    #str = CONTROLLER.get_run_prgm()
    #print (f'PRGM STATUS: {str}')  

    str = CONTROLLER.get_system_set('PTS')
    print (f'SYSTEM SET (PTS): {str}')          

    str = CONTROLLER.get_system_set('PTC')
    print (f'SYSTEM SET (PTC): {str}')      

    str = CONTROLLER.get_system_set('PTCOPT')
    print (f'SYSTEM SET (PTCOPT): {str}')      

    str = CONTROLLER.get_constant_set(1,'TEMP')
    print (f'CONSTANT SET (TEMP): {str}')    

    str = CONTROLLER.get_constant_set(1,'HUMI')
    print (f'CONSTANT SET (HUMI): {str}')   

    str = CONTROLLER.get_constant_set(1,'REF')
    print (f'CONSTANT SET (REF): {str}')   

    str = CONTROLLER.get_constant_set(1,'RELAY')
    print (f'CONSTANT SET (RELAY): {str}')

    # err: INVALID REQ, missing description?
    #str = CONTROLLER.get_constant_set(1,'PTC')
    #print (f'CONSTANT SET (PTC): {str}')     

    str = CONTROLLER.get_ais_unit('UNIT') # option: UNIT, VER 
    print (f'AIS UNIT: {str}')  

    str = CONTROLLER.get_ais_all_temp() # standard 
    print (f'AIS ALL TEMP: {str}') 

    str = CONTROLLER.get_ais(1,'FREQ') # num = 1-4, arg=TEMP, ELV, FREQ, REF, PRESS 
    print (f'AIS NUM and ARG: {str}')                   

    str = CONTROLLER.get_equimon('REF') # Ref opt worked... 
    print (f'READ EQUIMON: {str}')       


    '''