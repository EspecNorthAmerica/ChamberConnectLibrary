#!/bin/python3
'''
:author: Paul Nong-Laolam <pnong-laolam@espec.com>
:license: MIT, see LICENSE for more detail.
:copyright: (c) 2020, 2022. ESPEC North America, INC.
:updated: 2023 Included sample call programs to provide ease of use.
:file: f4t_runTCP.py 

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

Tested: Python 3.6.8; requires at least Python 3.6
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
'''
import time,re
import os, sys
import logging
sys.path.insert(0,'../chamberconnectlibrary')

from chamberconnectlibrary.watlowf4t import WatlowF4T
from chamberconnectlibrary.controllerinterface import ControllerInterfaceError

def ip_addr():
    '''select and check for proper IP address format
    '''
    while True:
        try:
            ip_addr = input('Enter F4T IP address (e.g., 192.168.0.101): ')
            #ip_addr = '10.30.100.96'
            chk_ip = re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip_addr)
            if chk_ip:
                print ('\n')
                break
        except Exception:
            print ('Invalid IP address.')
    return ip_addr
    
def setLoop(str, loop):
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

def chkProg(): 
    '''Check current status of chamber before executing a new program
    '''
    str = CONTROLLER.get_status()
    time.sleep(0.5)
    if 'Program Running' in str or 'Program Paused' in str:
        print ('\nrsp> Program execution in progress... must first terminate it.') 
    else:
        # execute new program 
        runProg() 

def runProg(): 
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

def progMode(mode):
    '''set program mode of currently running profile

       available modes: 
          stop: terminate program
          pause: suspend current running program
          resume: resume execution of program
          mode: STOP, PAUSE, RESUME 
    '''
    nlist = { 
        'nact': '\nrsp> No program running. Action terminated.',
        'act' : f'\nrsp> {mode} current program.',
        'pau' : '\nrsp> Program is in paused...request is ignored.',
        'run' : '\nrsp> Program is running...request is ignored.',
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

def setTS_on():
    '''Set TS value on the selected TS number
    '''
    try:
        ts_num = int(input('Enter TS number: '))
        if isinstance(ts_num, int) and ts_num in range(1,9):
            CONTROLLER.set_event(ts_num,True)
            print ('\nrsp> DONE') 
        else:
            print ('\nrsp> Invalid TS number.')
    except ValueError:
        print ('Invalid TS number.')

def setTS_off():
    '''turn off time signal (Event#)'''
    try:
        ts_num = int(input('Enter TS number: '))
        if isinstance(ts_num, int) and ts_num in range(1,9):
            CONTROLLER.set_event(ts_num,False)
            print ('\nrsp> DONE') 
        else:
            print ('\nrsp> Invalid TS number.')
    except ValueError:
        print ('Invalid TS number.')

def readTS():
    '''Read TS value on the select TS number
    '''
    print ('\nrsp> ')
    for i in range(8):
        ts_list = CONTROLLER.get_event(i+1)
        tsout = 'ON' if ts_list['current'] == True else 'OFF'
        print (f'    Time signal #{i+1} : {tsout}')

def constStart():
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

def stopConst():
    '''Stop constant mode on chamber
    '''
    CONTROLLER.stop()
    time.sleep(0.5) 
    print ('\nrsp > Done ') 

def thCtrl():
    '''
       set options for Temp and Humi controls
    '''
    def thMenu(choice):
        '''return T/H menu option'''
        return {
            't': lambda: setLoop('Temp',1),
            'h': lambda: print ('No yet implemented.'),
            'z': lambda: main_menu()
        }.get(choice, lambda: print ('\nrsp> Not a valid option.') )()  

    while(True):
        print_menu('2','Temp/Humi')
        option = input('Select option (t, h, z): ')
        thMenu(option)

def progMenu():  # test 
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
            'e': lambda: chkProg(),
            'n': lambda: progMode('SKIP'),
            'p': lambda: progMode('PAUSE'),
            'r': lambda: progMode('RESUME'),
            's': lambda: progMode('STOP'),
            'z': lambda: main_menu(),
        }.get(choice, lambda: print ('\nrsp> Not a valid option') )()

    while(True):
        print_menu('3','Program')
        option = input('Select option: ')
        progOperation(option)

def eventCtrl():
    '''Test TS events
    '''
    def eventOpt(option) :
        '''get event seelction menu
        '''
        return {
            'r': lambda: readTS(),
            's': lambda: setTS_on(),
            'o': lambda: setTS_off(),
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
            'c': lambda: constStart(), 
            'o': lambda: stopConst(), # print (f'\nrsp> {CONTROLLER.stop()}'),
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
    def mainOption(choice):
        '''return main menu options'''
        return {
            't': lambda: thCtrl(),
            'p': lambda: progMenu(),
            'e': lambda: eventCtrl(),
            's': lambda: status_menu(),
            'z': lambda: exit(),
        }.get(choice, lambda: print ('\nrsp> Not a valid option') )()

    while(True):
        print_menu('1','Main Menu')
        option = input('Select option: ')
        mainOption(option)

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
       1: main menu
       2: Temp/Humi menu
       3: Program menu
       4: Output (Time Signal) menu
       5: Chamber operating mode
    '''
    # main menu 
    main_menu = {
        't': 'Temp/Humi SP control          ',
        'p': 'Program control               ',
        'e': 'Event control                 ',        
        's': 'Chamber operating mode        ',
        'z': 'Exit                          '
    }

    # temp and humi ctrl menu
    th_menu = {
        't': 'New Temperature Set Point     ',
        'h': 'New Humidity Set Point        ',
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
       Communciation: ModbusTCP; IP address is prompted for input. It can be assigned by 
           modifying the interface_params with ip_addr() = x.x.x.x of your F4T. 
    '''

    # clear terminal; consider MS Windows environment as well...
    os.system('clear||cls')

    # the general setup for Watlow F4T, directly calling T or H loop
    # connect to watlow F4T via proper IP address using TCP/IP protocol
    '''
    LOOP_NAMES = ['Temperature', 'Humidity']
    CONTROLLER = WatlowF4T(
        interface='TCP',
        host=ip_addr(),        # requires the correct IP address of F4T
        loop_names=LOOP_NAMES  # set loop names for temp and humi 
    )
    '''

    # BEGIN 
    ###############################################################################################
    # BEGIN SELECTION OF THE SPECIFIC CHAMBER AND F4T 
    #sepcifically for ESPEC Chambers and Types with Watlow F4T
    ############################################################################################### 

    #example interface_params for a TCP connection to 10.30.100.55
    #interface_params = {'interface':'TCP', 'host':10.30.100.55}
    
    # to manually enter IP address of Watlow F4T 
    interface_params = {'interface':'TCP', 'host':ip_addr()}


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
        cond_event_toggle=False, # is the condition momentary(False), or maintained(True)
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

    # test section



