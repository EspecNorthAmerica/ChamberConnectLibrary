'''
A direct implimentation of the ES102's command and instruction
set for communication interface.

Copyright (C) April 2019 ESPEC North America, INC. - All rights reserved 
Author: Paul Nong-Laolam, Software Engineer; pnong-laolam@espec.com 
:license: MIT, see LICENSE for more details.
'''
import re
from p300 import P300
from scp220 import SCP220
from datetime import datetime 

def tryfloat(val, default):
    '''
    Convert a value to a float, if its not valid return default
    '''
    try:
        return float(val)
    except Exception:
        return default

class ES102(SCP220):
    '''
    ES102 communication basic implementation 

    Args: 
        interface (str): The interface type to connect to: "Serial" or "TCP"
    Kwargs: 
        serialport (str/int): The serial port to connect to when interface="Serial"
        baudrate (int): The baud rate to connect at when interface="Serial"
        address (int): The RS232C/RS485 address of the chamber to connect to.
        host (str): The IP address or hostname of the chamber when interface="TCP"
    '''

    def __init__(self, interface, **kwargs):
        super(ES102, self).__init__(interface, **kwargs)
        self.ramprgms = 1  # ES102 can store only one program in memory 
        self.es102err = 'ES102 does not have '
        self.errmsg = {
            'datetime': 'internal clock to store date/time',
            'timer': {
                'on': 'timer on control feature',
                'use': 'timer use control feature',
                'list': 'timer list (quick, start, stop) control feature',
                'erase': 'timer erase control feature',
                'run': 'timer run control feature'
            },
            'relay': 'relay feature',
            'const': {
                'ref': 'constant refrigeration control feature',
                'ptc': 'constant product temperature control feature'
            },
            'prgm_set': 'program set feature',
            'prgm_use': 'program use feature', 
            'sys_set': 'system set feature',
            'ptc': 'product temperature control command',
            'ip': 'IP configuration feature',
            'prgm_op': {
                'pause': 'operation feature for Pause',
                'continue': 'operation feature for Continue'
            },
            'prgm_run': 'PRGM RUN command',
            'detail': 'detailed stepped commands',
            'prgm_upld_err': ' Cannot upload a new program while the current program is still running.'
                            ' Current program must be stopped first for this operation to work.',
            'prgm_del_err': ' Cannot delete program while it is still running. Program must be stopped first.',
            'prgm_adv_err': ' Cannot move past last step; program is holding the last step in HOLD mode.'
        }

    def rom_pgm(self, num):
        '''
        Get string for what type of program this is 
        '''
        # may just need to set a return 'PGM'
        return 'PGM' if num <= self.ramprgms else 'ROM'

    # interact() inherits from P300/SCP220

    def read_rom(self, display=False):
        '''ES102 has no additional parameters or details with ROM cmd'''
        return super(ES102,self).read_rom(False) 

    def read_date(self): 
        '''
        ES102 does not have date/time; thus we read date/time from the os
        args: 
            date: split values into int; e.g., 2019-04-29
        '''
        dt = datetime.today().strftime('%Y-%m-%d').split('-')
        return {
            'year': int(dt[0]),
            'month': int(dt[1]),
            'day': int(dt[2])
        }

    def read_time(self): 
        '''
        es102 does not have date/time; thus we read date/time from the os
        args: 
            time: split values into int; e.g., 05:25:23, hour:min:sec
        '''
        tm = datetime.today().strftime('%H:%M:%S').split(':')
        return {
            'hour': int(tm[0]),
            'minute': int(tm[1]),
            'second': int(tm[2])
        } 

    def read_date_time(self):
        '''
        es102 does not have date/time; thus we read date/time from the os
        args: 
            date: split values into int; e.g., 2019-04-29
            time: split values into int; e.g., 05:25:23, hour:min:sec
        '''
        tmp_time = datetime.today().strftime('%H:%M:%S').split(':')
        ret = {
            'hour': int(tmp_time[0]), 
            'minute': int(tmp_time[1]), 
            'second': int(tmp_time[2])
        }
        tmp_date = datetime.today().strftime('%Y-%m-%d').split('-')
        ret.update({
            'year': int(tmp_date[0]), 
            'month': int(tmp_date[1]), 
            'day': int(tmp_date[2])
        }) 
        return ret

    # read_srq() inherits from SCP220/P300

    # read_mask() inherits from SCP220/P300

    def read_timer_on(self):
        '''
        fetch a list of valid timers by number
        returns: [int]

        ES102 does not support the timer set feature
        ''' 
        raise NotImplementedError(self.es102err + self.errmsg['timer']['on'])

    def read_timer_use(self):
        '''
        fetch the number of each set timer
        returns: [int] 

        ES102 does not support the timer use feature
        '''
        raise NotImplementedError(self.es102err + self.errmsg['timer']['use'])

    def read_timer_list_quick(self):
        '''
        read the timer settings for the quick timer
        returns:
            {"mode":string, "time":{"hour":int, "minute":int}, "pgmnum":int, "pgmstep":int}
            "mode"="STANDBY" or "OFF" or "CONSTANT" or "RUN"
            "pgmnum" and "pgmstep" only present when mode=="RUN"

            ES102 does not support the timer list feature 
        '''        
        raise NotImplementedError(self.es102err + self.errmsg['timer']['list'])

    def read_timer_list_start(self):
        '''
        read the timer setting  for start timer

        ES102 does not support the timer list (start) feature 
        '''
        raise NotImplementedError(self.es102err + self.errmsg['timer']['list'])

    def read_timer_list_stop(self):
        '''
        read the timer setting  for stop timer

        ES102 does not support the timer list (stop) feature 
        '''
        raise NotImplementedError(self.es102err + self.errmsg['timer']['list'])

    # read_alarm() inherits from SCP220/P300

    # read_keyprotect() inherits from SCP220/P300

    # read_type() inherits from SCP220/P300

    def read_mode(self, detail=False):
        '''
        obtain the chamber operation status. 
        ES102's mode feature has no additional parameters
        '''
        return super(ES102,self).read_mode(False) 

    def read_mon(self, detail=False):
        '''
        obtain conditions inside the chamber.
        ES102's monitor feature has no additional parameters
        '''
        return super(ES102,self).read_mon(False) 

    # read_temp() inherits from SCP220/P300 

    # read_humi() inherits from SCP220/P300

    # read_set() inherits from SCP220/P300

    # read_ref() inherits from SCP220/P300 

    def read_relay(self): # test only...
        '''
        fetch the status of each relay (time signal).
        ES102 does not have a RELAY command; there is an
        undocumented command related to CONSTANT SET?,RELAY. 

        NOTE: If relay is included in the fron-end UI, if set 
              for raise NotImplementedError, reading errors
              will be generated. Per current Web Controller functionality
              this method must be implemented; hence, using the 
              CONSTANT SET?,RELAY command.  
        '''
        #rsp = '0'.split(',') # fake data, no signals set to on. 
        #rsp = self.ctlr.interact('CONSTANT SET?,RELAY').split(',') 
        print ('Test print relay signals (read_relay): ')
        #print rsp 
        #return [str(i) in rsp[1:] for i in range(1,13)]
        raise NotImplementedError('RELAY is an unsupported command')

    # read_htr() inherits from SCP220/P300 
    
    # read_constant_temp() inherits from SCP220/P300
    # undocumented in the manual
    # eg: constant set?,temp

    # read_constant_humi() inherits from SCP220/P300 
    # undocumented in the manual
    # eg: constant set?,humi 

    def read_constant_ref(self):
        '''
        fetch constant settings for the refrigeration system.
        ES102 has two identical cmds : 
            - CONSTANT SET?,REF
            - SET? 
        They both yield identical response: REF# 
            e.g.: REF9 
        ES102 supports REF9 for auto refrig, full feature. 
        '''
        rsp = self.ctlr.interact('CONSTANT SET?,REF')
        try:
            return {
                'mode':'manual',
                'setpoint':float(rsp)
            }
        except Exception:
            return {
                'mode':rsp.lower(),
                'setpoint':0
            }

    def read_constant_relay(self):
        '''
        fetch the time signals of relay switch
        '''
        rsp = self.ctlr.interact('CONSTANT SET?,RELAY').split(',') 
        print ('Test print constant relay settings: ')
        print rsp 
        return [str(i) in rsp[1:] for i in range(1,13)]
        # read result: [False,False,...] 

    def read_constant_ptc(self):
        '''
        fetch constant settings for product temperature control.
        ES102 does not support Product Temp Control feature; 
        hence, no constant set cmd.  
        '''
        raise NotImplementedError(self.es102err + self.errmsg['const']['ptc'])

    def read_prgm_mon(self):
        '''
        get the status of the currently running program

        returns:
            {
                "prgmnum": int, ES102 also gives program number
                "pgmstep": int,
                "temperature": float,
                "humidity": float,
                "time": {"hour":int, "minute":int},
                "counter": int
            }
            "humidity" is present only on chambers with humidity
            "counter_?" is the cycles remaining
        '''
        rsp = self.ctlr.interact('PRGM MON?').split(',')
        print('Print read_prgm_mon: {}'.format(rsp)) 
        if len(rsp) == 6:  # ES102 with humidity feature 
            time = rsp[4].split(':')
            return {
                #'pgmnum':int(rsp[0]),    # does not need program noumber.
                'pgmstep':int(rsp[1]),
                'temperature':float(rsp[2]),
                'humidity':tryfloat(rsp[3], 0),
                'time':{'hour':int(time[0]), 'minute':int(time[1])},
                'counter_a':int(rsp[5])   # ES102 has single counter w/ 99 cycles max 
                #'counter_b':int(0)       # ES102 does not have counter_b
            }
        else: # ES102 without humidity feature 
            time = rsp[3].split(':')
            return {
                #'pgmnum':int(rsp[0]),    # does not need program number. 
                'pgmstep':int(rsp[1]),
                'temperature':float(rsp[2]),
                'time':{'hour':int(time[0]), 'minute':int(time[1])},
                'counter_a':int(rsp[4])   # ES102 has single counter 
                #'counter_b':int(0)       # ES102 does not have/use counter_b   
            }

    def read_prgm_set(self):
        '''
        fetch info of the currently running program: name, number and end mode.

        returns: 
            number of steps in program
            counter: { start, end, cycles } 
            end mode  

        NOTE: ES102 does not support 'PRGM SET?' command to extract  
        and fetch program name, number and end mode of the currently 
        running program. Similar & comparable command is 'PRGM DATA?,PGM:1' 
        which is the general fetch command even when ES102 is not running a program. 
        '''
        rsp = self.ctlr.interact('PRGM DATA?,PGM:1')
        parsed = re.search(
            r'(\d+),COUNT\((\d+).(\d+).(\d+)\),END\((\w+)\)', 
            rsp
        )
        text0 = 'Test read_prgm_set: number of steps:{}, name:{}, mode:{}'
        print (text0.format(parsed.group(1), self.rom_pgm(1), parsed.group(5)))
        return {
            'number':int(1),  # program number, default: 1  
            'name':' ' if rsp.startswith('NA:') else 'PGM',  
            'end':parsed.group(5)  
        }

    def read_prgm_use(self):
        '''
        fetch id number of the program on the controller as a list;
        there is only one program to be loaded and listed.
        NOTE: ES102 does not have PRGM USE command. To conform with P300
        class, a conditional statement is used to check if a program list
        contains Program/Profile. If True, return Program no. and location,
        else return Program no. as 0.  

        returns:
            [int] 
        '''
        if self.ctlr.interact('PRGM DATA?,PGM:1').startswith('NA:'):
            rsp = '0'.split(',')   # no program stored in memory
            print ('Program List empty; ES102 has no program.')
        else:
            rsp = '1,1'.split(',') # program is on the list 
            print ('PGM:1 found in Program List.')
        return [str(i) in rsp[1:] for i in range(1,2)] 

    def read_prgm_use_num(self, pgmnum):
        '''
        obtain the general information of the current program: name and creation date
        
        NOTE: ES102 neither supports unique program name nor date/time, since it
        has no internal clock to store that information. Date/time string will be fetched
        from the host machine. This date will produce a false program creation date, though. 

        Default name and location will be: PGM:1; that is, name = PGM and location = 1. 
        If NotImplementedError is raised, program information will not be rendered
        and displayed properly. A generic string must be implemented for this.

        args:
            pgmnum: the program to read

        returns:
            { "name": PGM
              "date": {
                  "year": int,
                  "month": int,
                  "day": int
                
              }
            }
        '''
        if self.ctlr.interact('PRGM DATA?,PGM:1').startswith('NA:'):
            prgmname = '' + ','
        else:
            prgmname = self.rom_pgm(pgmnum) + ',' 
        rsp = re.search(
            r'(.+)?,(\d+).(\d+)\/(\d+)', 
            prgmname + str(datetime.today().strftime('%Y.%m/%d')) 
        )
        text0 = 'Test print on program info (def read_prgm_use_num): {} {} {} {}'
        print (text0.format( rsp.group(1), int(rsp.group(2)), int(rsp.group(3)), int(rsp.group(4)) ))
        return {
            'name':rsp.group(1) if rsp.group(1) else '', 
            'date':{
                'year':int(rsp.group(2)),
                'month':int(rsp.group(3)),
                'day':int(rsp.group(4))
            }
        }

    def read_prgm_data(self, pgmnum):
        '''
        fetch the parameters of the specified program

        Args:
            steps: int, program to fetch the following: 
        returns:
            {
                'steps':int,
                'name':string, 
                'end':string,
                'counter_a':{'start':int, 'end':int, 'cycles':int}
            }
            END='OFF', 'CONSTANT', or 'HOLD'
            But according to P300 rsp cmd, it requires program name; hence, no RUN cmd. 
            NOTE: ES102 does not support RUN NEXT PROGRAM 
        '''
        pdata = self.ctlr.interact('PRGM DATA?,{0:s}:{1:d}'.format(self.rom_pgm(pgmnum), pgmnum))
        text0 = 'Test print on program name and location (def read_prgm_data): name:loc => {0:s}:{1:d}'
        print (text0.format(self.rom_pgm(pgmnum), pgmnum)) 
        return self.parse_prgm_data(pdata)

    def parse_prgm_data(self, arg):
        '''
        Parse the program data command
        '''
        # cmd> PRGM DATA?,PGM:1
        # rsp> 4,COUNT(1.3.2),END(CONSTANT)
        parsed = re.search(
            r'(\d+),COUNT\((\d+).(\d+).(\d+)\),END\((\w+)\)',
            arg
        )
        print ('Test print on program parameters (def parse_prgm_data): {}'.format(parsed.group(5))) 
        return {
            'steps':int(parsed.group(1)), # number of steps in program; max = 9
            'name': ' ' if arg.startswith('NA:') else 'PGM', # default profile name: PGM  
            'end': parsed.group(5),
            'next_prgm': int(0),  # ES102 has no RUN option at program end
            'counter_a':{         # single counter, max = 99 loops/cycles 
                'start':int(parsed.group(2)),
                'end':int(parsed.group(3)),
                'cycles':int(parsed.group(4)) # note: ES102 has only one counter. 
            }
        }
    
    def read_prgm_data_detail(self, pgmnum):
        '''
        get the conditions a program will start with and its operational range

        Args:
            pgmnum: int, the program to get
        returns:
            {
                "temperature":{"range":{"max":float, "min":float},"mode":string,"setpoint":float},
                "humidity":{"range":{"max":float,"min":float},"mode":string,"setpoint":float}
            }
        
        pdata = self.ctlr.interact('PRGM DATA?,%s:%d,DETAIL'%(self.rom_pgm(pgmnum), pgmnum))
        return self.parse_prgm_data_detail(pdata)
        '''
        raise NotImplementedError(self.es102err + self.errmsg['detail'])

    def parse_prgm_data_detail(self, arg):
        '''
        Parse the program data command with details flag
        
        parsed = re.search(
            r'([0-9.-]+),([0-9.-]+),(?:(\d+),(\d+),)?TEMP(\w+)'
            r'(?:,([0-9.-]+))?(?:,HUMI(\w+)(?:,(\d+))?)?',
            arg
        )
        ret = {
            'tempDetail':{
                'range':{'max':float(parsed.group(1)), 'min':float(parsed.group(2))},
                'mode':parsed.group(5),
                'setpoint':parsed.group(6)
            }
        }
        if parsed.group(3):
            ret['humiDetail'] = {
                'range':{'max':float(parsed.group(3)), 'min':float(parsed.group(4))},
                'mode':parsed.group(7),
                'setpoint':parsed.group(8)
            }
        return ret
        '''
        raise NotImplementedError(self.es102err + self.errmsg['detail'])

    def read_prgm_data_step(self, pgmnum, pgmstep):
        '''
        get a programs step parameters

        Args:
            pgmnum: int, the program to read from
            pgmstep: int, the step to read from
        returns:
            {
                "number":int,
                "temperature":{"setpoint":float, "ramp":boolean},
                "humidity":{"setpoint":float, "enable":boolean, "ramp":boolean},
                "time":{"hour":int, "minute":int},
                "granty":boolean,
                "refrig":{"mode":string, "setpoint":int},
            }
        '''
        tmp = self.ctlr.interact('PRGM DATA?,{0:s}:{1:d},STEP{2:d}'.format(self.rom_pgm(pgmnum), pgmnum, pgmstep))
        # cmd> PRGM DATA?,PGM:1,STEP1
        print ('read_prgm_data_step: ')
        print tmp 
        return self.parse_prgm_data_step(tmp)

    def parse_prgm_data_step(self, arg):
        '''
        Parse a program step
        '''
        # cmd> PRGM DATA?,PGM:1,STEP1
        # rsp> 1,TEMP20.0,TEMP RAMP OFF,TIME0:02,GRANTY OFF,REF9
        # general rsp: 
        # 1,TEMP23.0,TEMP RAMP ON,HUMI50,HUMI RAMP OFF,TIME0:02,GRANTY OFF,REF9,RELAY ON1.2
        # The RELAY cmd is not part of the ES102 output response; it's got to be a typo. 
        parsed = re.search(
            r'(\d+),TEMP([0-9.-]+),TEMP RAMP (\w+)(?:,HUMI([^,]+)'
            r'(?:,HUMI RAMP (\w+))?)?,TIME(\d+):(\d+),GRANTY (\w+),REF(\w+)',
            arg
        )
        #r'(?:,HUMI RAMP (\w+))?)?,TIME(\d+):(\d+),GRANTY (\w+),REF(\w+)(?:,RELAY ON([0-9.]+))?',
        base = {
            'number':int(parsed.group(1)),
            'temperature':{
                'setpoint':float(parsed.group(2)),
                'ramp':parsed.group(3) == 'ON'
            },
            'time':{
                'hour':int(parsed.group(6)),
                'minute':int(parsed.group(7))
            },
            'granty':parsed.group(8) == 'ON',
            'refrig':self.reflookup.get(
                'REF' + parsed.group(9),
                {'mode':'manual', 'setpoint':0}
            )
        }

        if parsed.group(4):
            base['humidity'] = {
                'setpoint':tryfloat(parsed.group(4), 0.0),
                'enable':parsed.group(4) != ' OFF',
                'ramp':parsed.group(5) == 'ON'
            }
        
        #if parsed.group(10):
        #    relays = parsed.group(10).split('.')
        #    base['relay'] = [str(i) in relays for i in range(1, 13)]
        #else:
        #    base['relay'] = [False for i in range(1, 13)]
        return base

    def read_system_set(self, arg='PTCOPT'):
        '''ES102 does not have System Set command'''
        raise NotImplementedError(self.es102err + self.errmsg['sys_set'])

    def read_mon_ptc(self):
        '''ES102 does not support Product Temp related command'''
        raise NotImplementedError(self.es102err + self.errmsg['ptc'])

    def read_temp_ptc(self):
        '''ES102 does not support Product Temp related command'''
        raise NotImplementedError(self.es102err + self.errmsg['ptc'])

    def read_set_ptc(self):
        '''ES102 does not support Product Temp related command'''
        raise NotImplementedError(self.es102err + self.errmsg['ptc'])

    def read_ptc(self):
        '''ES102 does not support Product Temp related command'''
        raise NotImplementedError(self.es102err + self.errmsg['ptc'])

    def read_prgm_data_ptc(self, pgmnum):
        '''ES102 does not support Product Temp related command'''
        raise NotImplementedError(self.es102err + self.errmsg['ptc'])

    def read_prgm_data_ptc_detail(self, pgmnum):
        '''ES102 does not support Product Temp related command'''
        raise NotImplementedError(self.es102err + self.errmsg['ptc'])

    def read_prgm_data_ptc_step(self, pgmnum, pgmstep):
        '''ES102 does not support Product Temp related command'''
        raise NotImplementedError(self.es102err + self.errmsg['ptc'])

    # read_run_prgm_mon() inherits from SCP220/P300

    def read_run_prgm(self):
        '''
        fetch setup information of the remote program currently running

        returns:
            {
                "temperature":{"start":float,"end":float},
                "humidity":{"start":float,"end":float},
                "time":{
                    "hours":int,"minutes":int},
                    "refrig":{"mode":string,"setpoint":} 
                }
            }
        '''
        rsp = self.ctlr.interact('RUN PRGM?')
        # response pattern of ES102 is slightly different from P300:
        # P300: RELAYON
        # ES102: RELAY ON
        # sample rsp:
        # TEMP55.2 GOTEMP43.0 HUMI50 GOHUMI85 TIME1:00 REF9 RELAY ON,1
        parsed = re.search(
            r'TEMP([0-9.-]+) GOTEMP([0-9.-]+)(?: HUMI(\d+) GOHUMI(\d+))? TIME(\d+):(\d+)'
            r'(?: REF([0-9]+))?(?: RELAY ON,([0-9,]+))?',
            rsp
        )
        ret = {
            'temperature':{
                'start':float(parsed.group(1)), 
                'end':float(parsed.group(2))
            },
            'time':{
                'hours':int(parsed.group(5)),
                'minutes':int(parsed.group(6))
            },
            'refrig':self.reflookup.get(parsed.group(7), {'mode':'manual', 'setpoint':0})
        }
        if parsed.group(3):
            ret['humidity'] = {'start':float(parsed.group(3)), 'end':float(parsed.group(4))}
        if parsed.group(8):
            relays = parsed.group(8).split(',')
            ret['relay'] = [str(i) in relays for i in range(1, 13)]
        else:
            ret['relay'] = [False for i in range(1, 13)]

    def read_ip_set(self):
        '''ES102 does not support IP setting'''
        raise NotImplementedError(self.es102err + self.errmsg['ip'])

    def write_date(self, year, month, day, dow):
        '''ES102 does not support read/write date/time feature'''
        raise NotImplementedError(self.es102err + self.errmsg['datetime'])

    def write_time(self, hour, minute, second):
        '''ES102 does not have internal time'''
        raise NotImplementedError(self.es102err + self.errmsg['datetime'])

    # write_mask() inherits from SCP220/P300
    # write_srq() inherits from SCP220/P300

    def write_timer_quick(self, mode, time, pgmnum=None, pgmstep=None):
        '''ES102 does not support timer control feature'''
        raise NotImplementedError(self.es102err + self.errmsg['timer']['list'])

    def write_timer_start(self, repeat, time, mode, **kwargs):
        '''ES102 does not support timer control feature'''
        raise NotImplementedError(self.es102err + self.errmsg['timer']['list'])

    def write_timer_stop(self, repeat, time, mode, date=None, days=None):
        '''ES102 does not support timer control feature'''
        raise NotImplementedError(self.es102err + self.errmsg['timer']['list'])

    def write_timer_erase(self, timer):
        '''ES102 does not support timer control feature'''
        raise NotImplementedError(self.es102err + self.errmsg['timer']['erase'])

    def write_timer(self, timer, run):
        '''ES102 does not support timer control feature'''
        raise NotImplementedError(self.es102err + self.errmsg['timer']['run'])

    # write_keyprotect() inherits from SCP220/P300

    # write_power() inherits from SCP220/P300

    # write_temp() inherits from SCP220/P300

    # write_humi() inherits from SCP220/P300

    # write_set() inherits from SCP220/P300

    def write_relay(self, relays):
        '''
        ES102 does not have RELAY write command.
        
        This method applies the constant setpoints refrig mode

        Args:
            mode: string,"off" or "manual" or "auto"
            setpoint: int,20 or 50 or 100
        '''
        #self.ctlr.interact('SET,%s' % self.encode_refrig(mode, setpoint))
        try: 
            print ('Attempting to write relay signals to ES102.') 
            vals = self.parse_relays(relays)
            if len(vals['on']) > 0:
                self.ctlr.interact('RELAY ON%s' % ','.join(str(v) for v in vals['on']))
            if len(vals['off']) > 0:
                self.ctlr.interact('RELAY OFF%s' % ','.join(str(v) for v in vals['off']))
        except:
            print('Error occurred...ES102 does not support "relay set cmd".')
            raise NotImplementedError(self.es102err + self.errmsg['relay'])


    def write_prgm_run(self, pgmnum, pgmstep):
        '''
        Initiate a program from the program list.
        ES102 will always initiate the program starting at step 1.
        There is no option to start a program from any step; additionally, 
        there is only one program, stored in location 1; hence, 'RUN1' is implied.  
        '''
        print ('Start a program beginning at step 1 (write_prgm_run).')
        self.ctlr.interact('MODE,RUN1') 

    def write_prgm_pause(self):
        '''
        pause the currently running program.
        NOTE: ES102 does not support the Pause operation.
        '''
        raise NotImplementedError(self.es102err + self.errmsg['prgm_op']['pause'])

    def write_prgm_continue(self):
        '''
        Resume the currently running program from its pause mode.
        NOTE: ES102 does not support the Continue operation. 
        '''
        raise NotImplementedError(self.es102err + self.errmsg['prgm_op']['continue'])

    def write_prgm_advance(self):
        '''
        skip to the next step of a currently running program
        NOTE: ES102 advance cmd inherits from SCP220/P300; however, ES102 has only 9 steps.
        '''
        try: 
            self.ctlr.interact('PRGM,ADVANCE')
        except: 
            # will flag err msg when attempting to move past the last step in program
            raise Exception('Operation error:' + self.errmsg['prgm_adv_err'])
            
    # write_prgm_end inherits from SCP220/P300

    # write_mode_off inherits from SCP220/P300 

    # write_mode_standby inherits from SCP220/P300

    # write_mode_constant inherits from SCP220/P300

    # write_mode_run inherits from SCP220/P300 

    def write_prgm_data_edit(self, pgmnum, mode, overwrite=False):
        '''
        start/stop/cancel program editing on a new or exising program

        Args:
            pgmnum: int, the program to start/stop/cancel editing on
            mode: string, "START" or "END" or "CANCEL"
            overwrite: boolean, when true programs/steps may be overwritten
        '''
        tmp = ('PRGM DATA WRITE,PGM:{0:d},{1:s} {2:s}'.format(pgmnum, 
            'OVER WRITE' if overwrite else 'EDIT',mode)) 
        self.ctlr.interact(tmp)

    def write_prgm_data_details(self, pgmnum, **pgmdetail):
        '''
        configure and write counter/loop parameters to the ES102 controller.
        NOTE: ES102 has only one counter; it will be named as counter_a to 
        conform with P300/SCP220 counter_a. 

        Args:
            pgmnum: int, the program being written or edited
            pgmdetail: the program details see write_prgm_data_detail for parameters
        '''
        if 'counter_a' in pgmdetail and pgmdetail['counter_a']['cycles'] > 0:
            ttp = (pgmnum, pgmdetail['counter_a']['start'], 
                pgmdetail['counter_a']['end'], pgmdetail['counter_a']['cycles'])
            print ('Test print: counter info')  
            print ttp # test print: counter raw parameters (x,x,x,x) 
            cmd = 'PRGM DATA WRITE,PGM:{0:d},COUNT,({1:d}.{2:d}.{3:d})'
            tmp = ( cmd.format(ttp[0], ttp[1], ttp[2], ttp[3]) ) 
            self.ctlr.interact(tmp)
            print tmp # test print : counter parameters  
        if 'end' in pgmdetail and pgmdetail['end'] != 'RUN':
            self.ctlr.interact('PRGM DATA WRITE,PGM:1,END,{0:s}'.format(pgmdetail['end']) )
        print ('Test print: pgmdetail info: {}:'.format(pgmdetail))

    def write_prgm_data_step(self, pgmnum, **pgmstep): # major reimplementation!!
        '''
        write a program step to the ES102 controller
        NOTE: ES102 allows up to 9 steps in a program

        args:
            pgmstep: the program parameters, see read_prgm_data_step for parameters
        '''
        cmd = 'PRGM DATA WRITE,PGM:{0:d},STEP{1:d}'.format(pgmnum, pgmstep['number'])
        if 'temperature' in pgmstep:
            if 'setpoint' in pgmstep['temperature']:
                print('Writing Temp values...')
                cmd = '{0:s},TEMP{1:0.1f}'.format(cmd, pgmstep['temperature']['setpoint'])
            if 'ramp' in pgmstep['temperature']:
                print('Setting up Temp Ramp...')
                cmd = '{0:s},TRAMP{1:s}'.format(cmd, 'ON' if pgmstep['temperature']['ramp'] else 'OFF')
        
        if 'humidity' in pgmstep:
            if 'setpoint' in pgmstep['humidity']:
                if pgmstep['humidity']['enable']:
                    htmp = '{0:0.0f}'.format(pgmstep['humidity']['setpoint']) 
                else:
                    htmp = 'OFF'
                print('Write humi values...')
                cmd = '{0:s},HUMI{1:s}'.format(cmd,htmp) 
                print cmd 
            if 'ramp' in pgmstep['humidity'] and pgmstep['humidity']['enable']:
                print('Set Humi Ramp')
                cmd = '{0:s},HRAMP{1:s}'.format(cmd, 'ON' if pgmstep['humidity']['ramp'] else 'OFF')
                print cmd 

        if 'time' in pgmstep:
            cmd = '{0:s},TIME{1:d}:{2:d}'.format(cmd, pgmstep['time']['hour'], pgmstep['time']['minute'])
        if 'granty' in pgmstep:
            cmd = '{0:s},GRANTY {1:s}'.format(cmd, 'ON' if pgmstep['granty'] else 'OFF')
        if 'refrig' in pgmstep:
            cmd = '{0:s},{1:s}'.format(cmd, self.encode_refrig(**pgmstep['refrig']))
        
        # NOTE: ES102 has no RELAY command operation.
        #if 'relay' in pgmstep: 
        #    try: 
        #        rlys = self.parse_relays(pgmstep['relay'])
        #        print('Configuring relay settings...')
        #        if rlys['on']:
        #            cmd = '{0:s},RELAY ON{1:s}.'.format(cmd, '.'.join(str(v) for v in rlys['on']))
        #        if rlys['off']:
        #            cmd = '{0:s},RELAY OFF{1:s}.'.format(cmd, '.'.join(str(v) for v in rlys['off']))
        #        print('Configuring relay settings...successful')
        #    except:
        #       raise NotImplementedError('Relay setting cannot be done.') 

        self.ctlr.interact(cmd)
        print('prgm data step...successful.')
        print cmd 

    def write_prgm_erase(self, pgmnum):
        '''
        erase a program

        Args:
            pgmnum: int, the program to erase
        '''
        try:
            self.ctlr.interact('PRGM ERASE,PGM:1') # simpler cmd than the one below
            #self.ctlr.interact('PRGM ERASE,{0:s}:{1:d}'.format(self.rom_pgm(pgmnum),pgmnum))
        except:
            raise Exception(self.errmsg['prgm_del_err']) 

    def write_run_prgm(self, temp, hour, minute, gotemp=None, humi=None, gohumi=None):
        '''
        run a program remotely; this is a single-step program, issued from
        the command-line interface.

        Args:
            temp: float, # initial temperature at the start of the step
            gotemp: float # temperature to attain at the end
            humi: float, # initial humidity at the start of the step (optional)
            gohumi: float, # humidity to attain at the end (optional for ramping)
            hour: int, # duration the step will last (hour unit)
            minute: int, # duration the step will last (minute unit)
        '''
        cmd = 'RUN PRGM, TEMP{0:0.1f} TIME{1:d}:{2:d}'.format(temp, hour, minute)
        if gotemp is not None:
            cmd = '{0:s} GOTEMP{1:0.1f}'.format(cmd, gotemp)
        if humi is not None:
            cmd = '{0:s} HUMI{1:0.1f}'.format(cmd, humi)
        if gohumi is not None:
            cmd = '{0:s} GOHUMI{1:0.1f}'.format(cmd, gohumi)
        self.ctlr.interact(cmd)

    def write_temp_ptc(self, enable, positive, negative):
        raise NotImplementedError(self.es102err + self.errmsg['ptc'])

    def write_ptc(self, op_range, pid_p, pid_filter, pid_i, **kwargs):
        raise NotImplementedError(self.es102err + self.errmsg['ptc'])

    def write_ip_set(self, address, mask, gateway):
        raise NotImplementedError(self.es102err + self.errmsg['ip'])

    def read_prgm(self, pgmnum, with_ptc=False):
        '''
        The helper method: read the entire program
        ES102 does not have detail command feature for product temperature control.  
        '''
        msg = 'Test print on def read_prgm method for proper operation:'
        if pgmnum == 1:
            pgm = self.read_prgm_data(pgmnum)
            tmp = [self.read_prgm_data_step(pgmnum, i) for i in range(1, pgm['steps']+1)]
            pgm['steps'] = tmp
        elif pgmnum == 0:
            pgm = {
                'counter_a':{ 'cycles':0, 'end':0, 'start':0 },
                'end':'OFF',
                'name':'',
                'next_prgm':0,
                'steps':[ {
                    'granty':False,
                    'number':1,
                    'paused':False,
                    'refrig':{'mode':'auto', 'setpoint':0},
                    'time':{'hour':1, 'minute':0},
                    'relay':[False for i in range(12)],
                    'temperature':{'ramp':False, 'setpoint':0.0}
                } ]
            }
            try:
                pgm['humiDetail'] = {
                    'mode':'OFF',
                    'setpoint':None,
                    'range':self.read_humi()['range']
                }
                pgm['steps'][0]['humidity'] = {'enable':False, 'ramp':False, 'setpoint':0.0}
            except Exception:
                raise Exception('Humidity reading error. Be sure to enable humidity on the controller.')
        else:
            raise ValueError('ES102 can only store one program; its number must be 1')

        print ('{} --> {}'.format(msg, pgm))
        return pgm

    def write_prgm(self, pgmnum, program):
        '''
        write an entire program helper method (must use same program 
        format as read_prgm). 
        
        NOTE: 
        ES102 neither has program number nor program name; hence, only 1 
        program can be edited and stored in memory, with default name: PGM:1.
        '''
        self.write_prgm_data_edit(pgmnum, 'START')
        try:
            set_humi = False
            for num, step in enumerate(program['steps']):
                step['number'] = num+1 # to ensure sequential stepping 
                print('Writing prgm step..')
                print step['number'] 
                self.write_prgm_data_step(pgmnum, **step)
                print ('Writing prg data step...successful')
                if step.get('humidity', {'enable':False})['enable']:
                    set_humi = True
            if not set_humi and 'humiDetail' in program:
                print('Setting humiDetail...')
                program['humiDetail'].pop('range', None)
            self.write_prgm_data_details(pgmnum, **program)
            print('Writing data details...successful')
            self.write_prgm_data_edit(pgmnum, 'END')
            print('Editing data...successful')
        except:
            self.write_prgm_data_edit(pgmnum, 'CANCEL')
            if self.ctlr.interact('MODE?').startswith('RUN'):
                raise Exception(self.errmsg['prgm_upld_err'])
            else:
                raise Exception('Program writing error') 

    def encode_refrig(self, mode, setpoint):
        '''
        Convert refrig mode dictionary to string
        '''
        if mode in ['off', 'Off']:
            act = 'REF0'
        elif mode in ['auto', 'Auto']:
            act = 'REF9'
        elif mode in ['manual', 'Manual']:
            if setpoint == 0:
                act = 'REF0'
            elif setpoint == 20:
                act = 'REF1'
            elif setpoint == 50:
                act = 'REF3'
            elif setpoint == 100:
                act = 'REF6'
            else:
                raise ValueError('param "setpoint" must be one of the following: 20/50/100')
        else:
            raise ValueError('param "mode" must be: "off"/"Off"/"manual"/"Manual"/"auto"/"Auto"')
        return act

    def parse_relays(self, relays):
        '''
        handle the relay configuration
        Note: ES102 has limited options in relay settings.
        '''
        try: 
            ret = {'on':[], 'off':[]}
            for i, val in enumerate(relays):
                if val is not None:
                    if isinstance(val, bool):
                        if val:
                            ret['on'].append(i+1)
                        else:
                            ret['off'].append(i+1)
                    else:
                        if val['value']:
                            ret['on'].append(val['number'])
                        else:
                            ret['off'].append(val['number'])
            ret['on'] = sorted(ret['on'])
            ret['off'] = sorted(ret['off'])
            return ret
        except:
            raise NotImplementedError('Relay configuration feature not available')