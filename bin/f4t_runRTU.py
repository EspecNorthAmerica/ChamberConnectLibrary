#!/bin/python3
'''
:author: Paul Nong-Laolam <pnong-laolam@espec.com>
:license: MIT, see LICENSE for more detail.
:copyright: (c) 2020, 2022. ESPEC North America, INC.
:updated: 2023 Included sample call programs to provide ease of use.
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

This sample program applies TCP for communication. 

The programmer may add the additional program section to call the library for 
the exact feature(s) not implemented here to meet their requirement. Thus, the 
following program serves as a starting point on how to utilize our 
ChamberConnectLibrary in the Python 3 environment. 

Tested: 
GNU/Linux platform: Python 3.8.x, 3.9.x, 3.10.x
MS Windows platform: Python 3.9.x 

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

DISCLAIMER: 
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF 
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE 
OR THE USE OR OTHER DEALINGS IN THE SOFTWARE. 
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
'''
import time,re
import os, sys
import logging
sys.path.insert(0,'../ChamberConnectLibrary')

from chamberconnectlibrary.watlowf4t import WatlowF4T
from chamberconnectlibrary.controllerinterface import ControllerInterfaceError

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
    
def set_loop(str, loop):
    '''set new temp value
    '''
    print ('\n<Applying new Set Point>')
    try:
        while True:
            try:
                val = float(input('Enter new SP value: '))
                if isinstance(val, int) or isinstance(val,float):
                    CONTROLLER.set_loop_sp(loop,val)
                    break
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
    """
    Read current values of Temp SP and PV
    """
    time.sleep(0.5)
    currentSP = CONTROLLER.get_loop_sp(loop)
    currentPV = CONTROLLER.get_loop_pv(loop)
    print(f'\nrsp> {str} status:\n     PV: {currentPV}\n     SP: {currentSP}')

def operation_status(): 
    '''Check current status of chamber before executing a new program
    '''
    str = CONTROLLER.get_status()
    time.sleep(0.5)
    if 'Program Running' in str or 'Program Paused' in str:
        print ('\nrsp> Program execution in progress... must first terminate it.') 
    else:
        # execute new program 
        run_prog() 

def run_prog(): 
    '''select and set profile for execution.
    '''
    print ('\n<Select a profile to execute>')
    try: 
        while True:
            pn = int(input('Enter profile number (Ctrl+C to exit profile execution): '))
            if isinstance(pn, int) and 1 <= pn <= 40:
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
                print ('Invalid Profile No. Must be between 1 and 40.')
    except KeyboardInterrupt:
            pass

def prog_mode(mode):
    '''set program mode of currently running profile

       available modes: 
          stop: terminate program
          pause: suspend current running program
          resume: resume execution of program
          mode: STOP, PAUSE, RESUME 
    '''
    nlist = { 
        'nact': f'\nrsp> No program running. Action terminated.',
        'act' : f'\nrsp> {mode} current program.',
        'pau' : f'\nrsp> Program is in paused...request is ignored.',
        'run' : f'\nrsp> Program is running...request is ignored.',
    }
    str = CONTROLLER.get_status()
    time.sleep(0.5)
    if "Program Running" in str:
        if mode == 'STOP':
            print (nlist["act"])
            CONTROLLER.stop()        
        if mode == 'PAUSE':
            print (nlist["act"])
            CONTROLLER.prgm_pause()
        if mode == 'SKIP':  
            print ('\nrsp> Skip to next step in program...') 
            CONTROLLER.prgm_next_step()
        if mode == 'RESUME':
            print (nlist['run'])
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
    '''Set TS value on the selected TS number
    '''
    try:
        ts_num = int(input('Enter TS number: '))
        if isinstance(ts_num, int) and ts_num in range(1,9):
            CONTROLLER.set_event(ts_num,state)
            print ('\nrsp> DONE') 
        else:
            print ('\nrsp> Invalid TS number.')
    except ValueError:
        print ('Invalid TS number.')

def read_time_signal():
    '''Read TS value on the select TS number
    '''
    print ('\nrsp> ')
    for i in range(8):
        ts_list = CONTROLLER.get_event(i+1)
        tsout = 'ON' if ts_list['current'] == True else 'OFF'
        print (f'    Time signal #{i+1} : {tsout}')

def const_start():
    '''Start Constant mode on chamber
    '''
    str = CONTROLLER.get_status()
    time.sleep(0.5)
    if ('Program Running' in str) or ('Program Paused' in str):
        print (f'\nrsp> Chamber is running in {str} mode. Must stop it first.')
    elif 'Constant' in str:
        print (f'\nrsp> Chamber is already in {str} mode.')
    else:
        CONTROLLER.const_start()
        time.sleep(0.5)
        print (f'\nrsp> Done') 

def stop_const():
    '''Stop constant mode on chamber
    '''
    CONTROLLER.stop()
    time.sleep(0.5) 
    print ('\nrsp > Done ') 

def temp_controller():
    '''
       set options for Temp controls
    '''
    def temp_menu(choice):
        '''return Temp menu option'''
        return {
            'r': lambda: read_val('Temp',1),
            't': lambda: set_loop('Temp',1),
            'z': lambda: main_menu()
        }.get(choice, lambda: print ('\nrsp> Not a valid option.') )()  

    while(True):
        print_menu('2','Temp')
        option = input('Select option (r, t, z): ')
        temp_menu(option)

def prog_menu():  # test 
    '''set up selection menu for operation
       main menu 
       m: Program status
       e: execute program
       n: skip to next step 
       p: pause program
       r: resume program
       s: stop program
       z: return to Main Menu 
    '''
    def progOperation(choice):
        '''return status option'''
        return {
            'm': lambda: print (f'\nrsp> {CONTROLLER.get_status()}'),
            'e': lambda: operation_status(),
            'n': lambda: prog_mode('SKIP'),
            'p': lambda: prog_mode('PAUSE'),
            'r': lambda: prog_mode('RESUME'),
            's': lambda: prog_mode('STOP'),
            'z': lambda: main_menu(),
        }.get(choice, lambda: print ('\nrsp> Not a valid option') )()

    while(True):
        print_menu('3','Program')
        option = input('Select option: ')
        progOperation(option)

def event_controller():
    '''Test TS events
    '''
    def eventOpt(option) :
        '''get event seelction menu
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
        option = input('Select option (r, s, z): ')
        eventOpt(option) 


def status_menu():
    '''read chamber status
    '''
    def statOption(choice):
        '''return status options'''
        return {
            's': lambda: print (f'\nrsp> {CONTROLLER.get_status()}'),
            'c': lambda: const_start(), 
            'o': lambda: stop_const(), # print (f'\nrsp> {CONTROLLER.stop()}'),
            'a': lambda: print (f'\nrsp> {CONTROLLER.get_alarm_status()}'),
            'd': lambda: print (f'\nrsp> {CONTROLLER.get_datetime()}'),
            'z': lambda: main_menu(),
        }.get(choice, lambda: print ('\nrsp> Not a valid option') )()

    while(True):
        print_menu('5','Chamber Status')
        option = input('Select option: ')
        statOption(option)

def main_menu(): 
    '''
       Set options for program control
    '''
    def main_option(choice):
        '''return main menu options'''
        return {
            't': lambda: temp_controller(),
            'p': lambda: prog_menu(),
            'e': lambda: event_controller(),
            's': lambda: status_menu(),
            'z': lambda: exit(),
        }.get(choice, lambda: print ('\nrsp> Not a valid option') )()

    while(True):
        print_menu('1','Main Menu')
        option = input('Select option: ')
        main_option(option)

def print_menu(choice, menu_name):
    '''set up selection menu
    '''
    print (f'\nF4T control options: {menu_name}'
            '\n--------------------------------') 
    for key in menu(choice).keys():
        print (f'  [{key}]:', menu(choice)[key] )
    print ('--------------------------------') 

def menu(choice):
    '''menu list
    main menu option: 
       1: main control menu
       2: Temp control menu
       3: Program control menu
       4: Output (Time Signal) menu
       5: Chamber operating mode
    '''
    # main menu 
    main_menu = {
        't': 'Temp SP control               ',
        'p': 'Program control               ',
        'e': 'Event control                 ',        
        's': 'Chamber operating mode        ',
        'z': 'Exit                          '
    }

    # temp and humi ctrl menu
    th_menu = {
        'r': 'Read Temperature SP and PV    ',
        't': 'New Temperature Set Point     ',
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
        's': 'Read chamber status           ',
        'c': 'Start constant mode           ',
        'o': 'Stop constant mode            ',
        'a': 'Read alarm history            ', 
        'd': 'Read chamber date/time        ',
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
    '''
    chamber/F4T call blocks for different types of ESPEC Chambers
       Models: BTX-???, BTZ-???, BTU-???, etc
       Types: Temp only, Temp/Humi, etc
       Communciation: ModbusRTU, RS232/RS485 
    '''
    # clear terminal; consider MS Windows environment as well...
    os.system('clear||cls')

    ###############################################################################################
    # MS Windows 7/10/11 environment
    # example interface_params for RS232/RS485 on port 7 (windows) Modbus address=1
    # uncomment the following line and check MS Window OS to confirm COM being used 
    #interface_params = {'interface':'RTU', 'baudrate':38400, 'serialport':'//./COM7', 'adr':1}

    # GNU/Linux environment
    # exec ls -l /dev/ttyUSB* to determine USB# being used...
    # should be USB0 or USB1; the following line must be changed accordingly. 
    # example interface_params for RS232/RS485 on ttyUSB0 (linux) Modbus address=1
    interface_params = {'interface':'RTU', 'baudrate':38400, 'serialport':'/dev/ttyUSB0', 'adr':1}

    # BEGIN 
    ###############################################################################################
    # BEGIN SELECTION OF THE SPECIFIC CHAMBER AND F4T 
    #sepcifically for ESPEC Chambers and Types with Watlow F4T
    ############################################################################################### 

    # Chamber models: BTU-??? or BTZ-??? with temp only 
    # for these two types, uncomment the following block of lines 
    CONTROLLER = WatlowF4T(
        alarms=8, # the number of available alarms
        profiles=True, # the controller has programming
        loops=1, # the number of control loops (ie temperature)
        cond_event=9, # the event that enables/disables conditioning
        cond_event_toggle=False, # is the condition momentary(False), or maintained(True)
        run_module=1, # The io module that has the chamber run output
        run_io=1, # The run output on the mdoule that has the chamber run out put
        limits=[5], # A list of modules that contain limit type cards.
        **interface_params 
    )

    '''
    # Chamber models: BTL-??? or BTX-??? with temperature and humidity
    # for thes two types, uncomment the following block of lines 
    CONTROLLER = WatlowF4T(
        alarms=8, # the number of available alarms
        profiles=True, # the controller has programming
        loops=2, # the number of control loops (ie temperature)
        cond_event=9, # the event that enables/disables conditioning (9 is key 1)
        cond_event_toggle=False, # is the condition momentary(False), or maintained(True)
        run_module=1, # The io module that has the chamber run output
        run_io=1, # The run output on the mdoule that has the chamber run out put
        limits=[5], # A list of modules that contain limit type cards.
        loop_event=[0,2,0,0], # A list of event #'s that enable/disable a control loop
        **interface_params
    )

    # Chamber models: BTU-??? or BTZ-???
    # with temp only w/ Product temperature control (aka "PTCON" or "cascade") 
    # for these two types, uncomment the following block of lines 
    CONTROLLER = WatlowF4T(
        alarms=8, # the number of available alarms
        profiles=True, # the controller has programming
        loops=0, # the number of control loops (ie temperature)
        cond_event=9, # the event that enables/disables conditioning
        cond_event_toggle=False, # is the condition momentary(False), or maintained(True)
        run_module=1, # The io module that has the chamber run output
        run_io=1, # The run output on the mdoule that has the chamber run out put
        limits=[5], # A list of modules that contain limit type cards.
        cascades=1, # the number of cascade loops (ie temperature with PTCON)
        cascade_ctl_event=[7,0,0,0] # the event that enables PTCON
        **interface_params
    )

    # Chamber models: BTL-??? or BTX-???
    # for temp/humidity w/ Product temperature control (aka "PTCON" or "cascade") 
    # for thes two types, uncomment the following block of lines 
    CONTROLLER = WatlowF4T(
        alarms=8, # the number of available alarms
        profiles=True, # the controller has programming
        loops=1, # the number of control loops (ie temperature)
        cond_event=9, # the event that enables/disables conditioning (9 is key 1)
        cond_event_toggle=False, # is the condition git config --global --add safe.directory /home/data_share/espec-work/py3-chamberlib/chamberconnectlibrarymomentary(False), or maintained(True)
        run_module=1, # The io module that has the chamber run output
        run_io=1, # The run output on the mdoule that has the chamber run out put
        limits=[5], # A list of modules that contain limit type cards.
        loop_event=[0,2,0,0], # A list of event #'s that enable/disable a control loop
        cascades=1, # the number of cascade loops (ie temperature with PTCON)
        cascade_ctl_event=[7,0,0,0] # the event that enables PTCON
        **interface_params
    )
    # END OF Chamber model selection 
    ###############################################################################################
    '''

    # initiate menu
    main_menu()
