'''
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
:author: Paul Nong-Laolam <pnong-laolam@espec.com>
:license: MIT, see LICENSE for more detail.
:copyright: (c) 2025. ESPEC North America, Inc. 
:updated: December 2025
:file: glc.py 
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

This is the GL controller native command library for Python 3.6 and higher. 
It is a direct implimentation of the GL controller's communication interface.

Tested: 
GNU/Linux platform: Python 3.8.x, 3.9.x, 3.10.x
MS Windows platform: Python 3.9.x
'''
#pylint: disable=W0703
import re
from .especinteract import EspecSerial, EspecTCP

def tryfloat(val, default):
    '''
    Convert a value to a float, if its not valid return default
    '''
    try:
        return float(val)
    except Exception:
        return default

class GLC(object):
    '''
    ESPEC GL Controller communications basic implimentation

    Args:
        interface (str): The interface type to connect to: "Serial" or "TCP"
    Kwargs:
        serialport (str/int): The serial port to connect to when interface="Serial"
        baudrate (int): The baud rate to connect at when interface="Serial"
        address (int): The RS485 address of the chamber to connect to.
        host (str): The IP address or hostname of the chamber when interface="TCP"
    '''

    def __init__(self, interface, **kwargs):
        self.reflookup = {
            'REF0':{'mode':'off', 'setpoint':0},
            'REF1':{'mode':'manual', 'setpoint':20},
            'REF3':{'mode':'manual', 'setpoint':50},
            'REF6':{'mode':'manual', 'setpoint':100},
            'REF9':{'mode':'auto', 'setpoint':0}
        }
        self.ramprgms = 1000  # No program limit; limit is only due to storage size 
        if interface == 'Serial':
            self.ctlr = EspecSerial(
                port=kwargs.get('serialport'),
                baud=kwargs.get('baudrate'),
                address=kwargs.get('address')
            )
        else:
            self.ctlr = EspecTCP(
                host=kwargs.get('host'),
                address=kwargs.get('address')
            )

    def __del__(self):
        self.close()

    def close(self):
        '''
        Close the physical interface
        '''
        try:
            self.ctlr.close()
        except Exception:
            pass

    def rom_pgm(self, num):
        '''
        Get string for what type of program this is
        '''
        return 'RAM' if num <= self.ramprgms else 'ROM'

    def interact(self, message):
        '''
        Read a responce from the controller

        Args:
            message: the command to write
        returns:
            string: response
        '''
        return (self.ctlr.interact(message)).decode('utf-8', 'replace')

    ##################################################################################
    # MONITOR/READ COMMANDS: READ METHODS
    # Decorators for GLC (P300, SCP220 and ES102) by calling each read command
    # from their methods.
    ##################################################################################

    def read_rom(self, display=False):
        '''
        Get the rom version of the controller

        Args:
            display: If true get the controllers display rom
        returns:
            rom version as a string
        '''
        return (self.ctlr.interact('ROM?{}'.format(',DISP' if display else ''))).decode('utf-8', 'replace')

    def read_date(self):
        '''
        Get the date from the controller

        returns:
            {"year":int,"month":int,"day":int}
        '''
        rsp = ((self.ctlr.interact('DATE?')).decode('utf-8', 'replace')).split('.')
        date = [rsp[0]] + rsp[1].split('/')
        return {'year':2000+int(date[0]), 'month':int(date[1]), 'day':int(date[2])}

    def read_time(self):
        '''
        Get the time from the controller

        returns:
            {"hour":int, "minute":int, "second":int}
        '''
        time = ((self.ctlr.interact('TIME?')).decode('utf-8', 'replace')).split(':')
        return {'hour':int(time[0]), 'minute':int(time[1]), 'second':int(time[2])}

    def read_date_time(self):
        '''
        Get the date & time from the controller.
        Merges read_date and read_time to avoid date/time being read on a different day.
        Intended only for use with serial connections.

        returns:
            {"year":int,"month":int,"day":int, "hour":int, "minute":int, "second":int}
        '''
        date = (self.ctlr.interact('DATE?')).decode('utf-8', 'replace')        
        time = (self.ctlr.interact('TIME?')).decode('utf-8', 'replace')
        time = time.split(':')
        ret = {'hour':int(time[0]), 'minute':int(time[1]), 'second':int(time[2])}
        tmp_date = date.split('.')
        date = [tmp_date[0]] + tmp_date[1].split('/')
        ret.update({'year':2000+int(date[0]), 'month':int(date[1]), 'day':int(date[2])})
        return ret
        
    def read_srq(self):
        '''
        Read the SRQ status

        returns:
            {"alarm":boolean, "single_step_done":boolean, "state_change":boolean, "GPIB":boolean}
        '''
        srq = list((self.ctlr.interact('SRQ?')).decode('utf-8', 'replace'))
        return {
            'alarm':srq[1] == '1',
            'single_step_done':srq[2] == '1',
            'state_change':srq[3] == '1',
            'GPIB':srq[6] == '1'
        }

    def read_mask(self):
        '''
        Read the SRQ mask

        returns:
            {"alarm":boolean, "single_step_done":boolean, "state_change":boolean, "GPIB":boolean}
        '''
        mask = list((self.ctlr.interact('MASK?')).decode('utf-8', 'replace'))
        return {
            'alarm':mask[1] == '1',
            'single_step_done':mask[2] == '1',
            'state_change':mask[3] == '1',
            'GPIB':mask[6] == '1'
        }

    def read_timer_on(self):
        '''
        Return a list of valid timers by number

        returns:
            [int]
        '''
        rsp = ((self.ctlr.interact('TIMER ON?')).decode('utf-8', 'replace')).split(',')
        return [int(t) for t in rsp[1:]]

    def read_timer_use(self):
        '''
        Return the number of each set timer

        returns:
            [int]
        '''
        rsp = ((self.ctlr.interact('TIMER USE?')).decode('utf-8', 'replace')).split(',')
        return [int(t) for t in rsp[1:]]

    def read_timer_list_quick(self):
        '''
        Read the timer settings for the quick timer(timer 0)

        returns:
            {"mode":string, "time":{"hour":int, "minute":int}, "pgmnum":int, "pgmstep":int}
            "mode"="STANDBY" or "OFF" or "CONSTANT" or "RUN"
            "pgmnum" and "pgmstep" only present when mode=="RUN"
        '''
        get_rsp = (self.ctlr.interact('TIMER LIST?,0')).decode('utf-8', 'replace')
        parsed = re.search(
            r'(\w+)(?:,R[AO]M:(\d+),STEP(\d+))?,(\d+):(\d+)', get_rsp)
        ret = {
            'mode':parsed.group(1),
            'time':{'hour':int(parsed.group(4)), 'minute':int(parsed.group(5))}
        }
        if parsed.group(1) == 'RUN':
            ret.update({'pgmnum':int(parsed.group(2)), 'pgmstep':int(parsed.group(3))})
        return ret

    def read_timer_list_start(self):
        '''
        Read the timer settings for the start timer (timer 1)

        returns:
            {
                "repeat":string,
                "time":{"hour":int, "minute":int},
                "mode":string",
                "date":{"month":int, "day":int, "year":int},
                "day":string,
                "pgmnum":int,
                "pgmstep":int
            }
            "repeat"="once" or "weekly" or "daily"
            "mode"="CONSTANT" or "RUN"
            "date" only present when "repeat"=="once"
            "pgmnum" and "step" only present when "mode"=="RUN"
            "days" only present when "repeat"=="weekly"
        '''
        rsp = (self.ctlr.interact('TIMER LIST?,1')).decode('utf-8', 'replace')
        parsed = re.search(
            r'1,MODE(\d)(?:,(\d+).(\d+)/(\d+))?(?:,([A-Z/]+))?,(\d+):(\d+),(\w+)'
            r'(?:,R[AO]M:(\d+),STEP(\d+))?',
            rsp
        )
        ret = {
            'repeat':['once', 'weekly', 'daily'][int(parsed.group(1))-1],
            'time':{'hour':int(parsed.group(6)), 'minute':int(parsed.group(7))},
            'mode':parsed.group(8)
        }
        if parsed.group(2):
            ret['date'] = {
                'year':2000+int(parsed.group(2)),
                'month':int(parsed.group(3)),
                'day':int(parsed.group(4))
            }
        if parsed.group(5):
            ret['days'] = parsed.group(5).split('/')
        if parsed.group(9):
            ret.update({'pgmnum':int(parsed.group(9)), 'pgmstep':int(parsed.group(10))})
        return ret

    def read_timer_list_stop(self):
        '''
        Read the timer settings for the start timer (timer 1)

        returns:
            {
                "repeat":string,
                "time":{"hour":int, "minute":int},
                "mode":string",
                "date":{"month":int, "day":int, "year":int},
                "day":string
            }
            "repeat"="once" or "weekly" or "daily"
            "mode"="STANDBY" or "OFF"
            "date" only present when "repeat"=="once"
            "days" only present when "repeat"=="weekly"
        '''
        rsp = (self.ctlr.interact('TIMER LIST?,2')).decode('utf-8', 'replace')
        parsed = re.search(
            r'2,MODE(\d)(?:,(\d+).(\d+)/(\d+))?(?:,([A-Z]+))?,(\d+):(\d+),(\w+)',
            rsp
        )
        ret = {
            'repeat':['once', 'weekly', 'daily'][int(parsed.group(1))-1],
            'time':{'hour':int(parsed.group(6)), 'minute':int(parsed.group(7))},
            'mode':parsed.group(8)
        }
        if parsed.group(2):
            ret['date'] = {
                'year':2000+int(parsed.group(2)),
                'month':int(parsed.group(3)),
                'day':int(parsed.group(4))
            }
        if parsed.group(5):
            ret['days'] = parsed.group(5).split('/')
        return ret

    def read_alarm(self):
        '''
        Return a list of active alarm codes, an empty list if no alarms.

        returns:
            [int]
        '''
        rsp = ((self.ctlr.interact('ALARM?')).decode('utf-8', 'replace')).split(',')
        return [int(t) for t in rsp[1:]]

    def read_keyprotect(self):
        '''
        Returns the key protection state of the controller.

        returns:
            True if protection is enabled False if not
        '''
        return (self.ctlr.interact('KEYPROTECT?')).decode('utf-8', 'replace') == 'ON'

    def read_type(self):
        '''
        Returns the type of sensor(s), controller and max temperature of the controller

        returns:
            {"drybulb":string, "wetbulb":string, "controller":string, "tempmax":float}
            "wetbulb" only present if chamber has humidity
        '''
        rsp = ((self.ctlr.interact('TYPE?')).decode('utf-8', 'replace')).split(',')
        if len(rsp) == 4:
            return {
                'drybulb':rsp[0],
                'wetbulb':rsp[1],
                'controller':rsp[2],
                'tempmax':float(rsp[3])
            }
        else:
            return {
                'drybulb':rsp[0],
                'controller':rsp[1],
                'tempmax':float(rsp[2])
            }

    def read_mode(self, detail=False):
        '''
        Return the chamber operation state.

        Args:
            detail: boolean, if True get additional information (not SCP220 compatible)
        returns:
            detail=Faslse: string "OFF" or "STANDBY" or "CONSTANT" or "RUN"
            detail=True: string (one of the following):
                "OFF""STANDBY" or "CONSTANT" or "RUN" or "RUN PAUSE" or "RUN END HOLD" or
                "RMT RUN" or "RMT RUN PAUSE" or "RMT RUN END HOLD"
        '''
        return (self.ctlr.interact(f'MODE?{",DETAIL" if detail else ""}')).decode('utf-8', 'replace')

    def read_mon(self, detail=False):
        '''
        Returns the conditions inside the chamber

        Args:
            detail: boolean, when True "mode" parameter has additional details
        returns:
            {"temperature":float,"humidity":float,"mode":string,"alarms":int}
            "humidity": only present if chamber has humidity
            "mode": see read_mode for valid parameters (with and without detail flag).
        '''
        rsp = ((self.ctlr.interact(f'MON?{",DETAIL" if detail else ""}')).decode('utf-8', 'replace')).split(',')        
        data = {'temperature':float(rsp[0]), 'mode':rsp[2], 'alarms':int(rsp[3])}
        if rsp[1]:
            data['humidity'] = float(rsp[1])
        return data

    def read_temp(self):
        '''
        Returns the temperature parameters

        returns:
            {
                "processvalue":float,
                "setpoint":float,
                "enable":boolean(always True),
                "range":{"max":float, "min":float}
            }
        '''
        rsp = ((self.ctlr.interact('TEMP?')).decode('utf-8', 'replace')).split(',')
        return {
            'processvalue':float(rsp[0]),
            'setpoint':float(rsp[1]),
            'enable':True,
            'range':{'max':float(rsp[2]), 'min':float(rsp[3])}
        }

    def read_humi(self):
        '''
        Returns the humidity parameters

        returns:
            {
                "processvalue":float,
                "setpoint":float,
                "enable":boolean,
                "range":{"max":float, "min":float}
            }
        '''
        rsp = ((self.ctlr.interact('HUMI?')).decode('utf-8', 'replace')).split(',')
        try:
            hsp = float(rsp[1])
            enable = True
        except Exception:
            hsp = 0
            enable = False
        return {
            'processvalue':float(rsp[0]),
            'setpoint':hsp,
            'enable':enable,
            'range':{'max':float(rsp[2]), 'min':float(rsp[3])}
        }

    def read_set(self):
        '''
        returns the regrigeration capacity set point of the chamber

        returns:
            {"mode":string,"setpoint":int}
            "mode": "off" or "manual" or "auto"
            "setpoint: 20 or 50 or 100 (percent cooling power)
        '''
        return self.reflookup.get((self.ctlr.interact('SET?')).decode('utf-8', 'replace'), {'mode':'manual', 'setpoint':0})

    def read_ref(self):
        '''
        returns the state of the compressors on the system

        returns:
            [boolean] 0=high stage, 1=low stage
        '''
        rsp = ((self.ctlr.interact('REF?')).decode('utf-8', 'replace')).split(',')
        if len(rsp) == 3:
            return [rsp[1] == 'ON1', rsp[2] == 'ON2']
        else:
            return [rsp[1] == 'ON1']

    def read_relay(self):
        '''
        returns the status of each relay(time signal)

        returns:
            [boolean] len=12
        '''
        rsp = ((self.ctlr.interact('RELAY?')).decode('utf-8', 'replace')).split(',')
        return [str(i) in rsp[1:] for i in range(1, 13)]

    def read_htr(self):
        '''
        returns the heater outputs

        returns:
            {"dry":flaot,"wet":float}
            "wet" is only present with humidity chambers
        '''
        rsp = ((self.ctlr.interact('%?')).decode('utf-8', 'replace')).split(',')
        if len(rsp) == 3:
            return {'dry':float(rsp[1]), 'wet':float(rsp[2])}
        else:
            return {'dry':float(rsp[1])}

    ######################################################################
    # NOTE: 
    # Requires rewriting, reimplementation to include CONSTANT #1, 2, 3
    ###################################################################### 
    def read_constant_temp(self): # GL legacy command to CONSTANT 1 values 
        '''
        Get the constant settings for the temperature loop

        returns:
            {"setpoint":float,"enable":True}
        '''
        rsp = ((self.ctlr.interact('CONSTANT SET?,TEMP')).decode('utf-8', 'replace')).split(',')
        return {'setpoint':float(rsp[0]), 'enable':rsp[1] == 'ON'}

    def read_constant_humi(self): # GL legacy command to CONSTANT 1 values 
        '''
        Get the constant settings for the humidity loop

        returns:
            {"setpoint":float,"enable":boolean}
        '''
        rsp = ((self.ctlr.interact('CONSTANT SET?,HUMI')).decode('utf-8', 'replace')).split(',')
        return {'setpoint':float(rsp[0]), 'enable':rsp[1] == 'ON'}

    def read_constant_ref(self): # GL legacy command to CONSTANT 1 values 
        '''
        Get the constant settings for the refigeration system

        returns:
            {"mode":string,"setpoint":float}
        '''
        rsp = (self.ctlr.interact('CONSTANT SET?,REF')).decode('utf-8', 'replace')
        try:
            return {'mode':'manual', 'setpoint':float(rsp)}
        except Exception:
            return {'mode':rsp.lower(), 'setpoint':0}

    def read_constant_relay(self): # GL legacy command to CONSTANT 1 values 
        '''
        Get the constant settings for the relays(time signals)

        returns:
            [int]
        '''
        rsp = ((self.ctlr.interact('CONSTANT SET?,RELAY')).decode('utf-8', 'replace')).split(',')
        return [str(i) in rsp[1:] for i in range(1, 13)]

    def read_constant_ptc(self): # GL legacy command to CONSTANT 1 values 
        '''
        Get the constant settings for product temperature control

        returns:
            {"enable":boolean,"deviation":{"positive":float,"negative":float}}
        '''
        rsp = ((self.ctlr.interact('CONSTANT SET?,PTC')).decode('utf-8', 'replace')).split(',')
        return {
            'enable': rsp[0] == 'ON',
            'deviation': {'positive':float(rsp[1]), 'negative':float(rsp[2])}
        }
    #
    #######################################################################################

    #######################################################################################
    # Only for GL controller system 
    def read_constant_set(self, cnum, arg='TEMP'):
        '''
        Get the constant settings for all system parameters: 
            TEMP, HUMI, REF, RELAY, PTC

        returns:
            [int] and [string]
        '''
        if arg in ['TEMP', 'HTEMP', 'LTEMP', 'HUMI', 'HHUMI', 'LHUMI', 'REF', 'RELAY', 'PTC'] and cnum in [1,2,3]:
            return (self.ctlr.interact(f'CONSTANT SET?,{cnum},{arg}')).decode('utf-8', 'replace').split(',')
        else:
            raise ValueError('arg must be one of the following: "TEMP", "HTEMP", "LTEMP", "HUMI", "HHUMI", "LHUMI", "REF", "RELAY", "PTC" and cnum must be between 1 and 3')

    def read_ais(self, num, arg='TEMP'):
        '''
        Read and report the refrigeration installation information.

        Args:
            arg: what to read options are: 'TEMP', 'ELV', 'FREQ', 'REF', 'PRESS'
        returns:
            [string] in list 
        '''
        if arg in ['TEMP', 'ELV', 'FREQ', 'REF', 'PRESS'] and num in [1,2,3,4]:
            return (self.ctlr.interact(f'AIS?,{num},{arg}')).decode('utf-8', 'replace').split(',')
        else:
            raise ValueError('arg must be one of the following: "TEMP", "HUMI", "REF", "RELAY", "PTC" and num must be between 1 and 4')

    def read_ais_unit(self, arg='UNIT'):
        '''
        Read and report the refrigeration installation information.
        
        required arguments: UNIT, VER 
        returns:
            [string] and list
        '''
        if arg in ['UNIT', 'VER']:
            rsp=(self.ctlr.interact(f'AIS?,{arg}')).decode('utf-8', 'replace').split(',')
            return rsp # return as list of strings 
        else:
            raise ValueError('arg must be one of the following: "UNIT" or "VER"')

    def read_ais_all_temp(self):
        '''
        Read and report all the refrigeration installation information.
        
        returns:
            [string] and list
        '''
        rsp=(self.ctlr.interact(f'AIS?,ALL,TEMP')).decode('utf-8', 'replace').split(',')
        return rsp # return as list of strings 

    def read_system_set(self, arg='PTS'):
        '''
        return controller product monitor and or control configuration

        Args:
            arg: what to read options are: "PTCOPT","PTC","PTS"
        returns:
            string
        '''
        if arg in ['PTS', 'PTC', 'PTCOPT']:            
            return (self.ctlr.interact(f'SYSTEM SET?,{arg}')).decode('utf-8', 'replace')
        else:
            raise ValueError('arg must be one of the following: "PTCOPT","PTC","PTS"')
 
    def read_equimon(self, arg='REF'):
        '''
        Read and report...

        Args:
            arg: what to read options are: "REF", "FAN", "AUXHUMI"
        returns:
            [string] list 

        '''
        if arg in ['REF', 'FAN', 'AUXHUMI']:
            rsp = (self.ctlr.interact(f'EQUIMON?,{arg}')).decode('utf-8', 'repalce') 
            return rsp 
        else:
            raise ValueError('arg must be one of the following: "REF"", "FAN", "AUXHUMI"')

    def read_mon_ptc(self):
        '''
        Returns the conditions inside the chamber, including PTCON

        returns:
            {
                "temperature":{"product":float,"air":float},
                "humidity":float,
                "mode":string,
                "alarms":int
            }
            "humidity" is present only on humidity chambers
        '''
        rsp = ((self.ctlr.interact('MON PTC?')).decode('utf-8', 'replace')).split(',')
        if len(rsp) == 5:
            return {
                'temperature':{'product':float(rsp[0]), 'air':float(rsp[1])},
                'humidity':float(rsp[2]),
                'mode':rsp[3],
                'alarms':int(rsp[4])
            }
        else:
            return {
                'temperature':{'product':float(rsp[0]), 'air':float(rsp[1])},
                'mode':rsp[2],
                'alarms':int(rsp[3])
            }

    ############################################################################
    # Unsupported or not working on GL Controller!!
    # Feature-related options 
    def read_temp_ptc(self):
        '''
        returns the temperature paramers including product temp control settings

        returns:
            {
                "enable":boolean,
                "enable_cascade":boolean,
                "deviation":{"positive":float, "negative":float},
                "processvalue":{"air":float, "product":float},
                "setpoint":{"air":float, "product":float}
            }
        '''
        rsp = ((self.ctlr.interact('TEMP PTC?')).decode('utf-8', 'replace')).split(',')
        return {
            'enable':True,
            'enable_cascade':rsp[0] == 'ON',
            'deviation':{'positive':tryfloat(rsp[5], 0), 'negative':tryfloat(rsp[6], 0)},
            'processvalue':{'air':tryfloat(rsp[2], 0), 'product':tryfloat(rsp[1], 0)},
            'setpoint':{'air':tryfloat(rsp[3], 0), 'product':tryfloat(rsp[4], 0)}
        }

    def read_set_ptc(self):
        '''
        get the product temperature control parameters (on/off, deviation settings)

        returns:
            {"enable_cascade":boolean,"deviation":{"positive":float,"negative":float}}
        '''
        rsp = ((self.ctlr.interact('SET PTC?')).decode('utf-8', 'replace')).split(',')
        return {
            'enable_cascade':rsp[0] == 'ON',
            'deviation':{'positive':tryfloat(rsp[1], 0), 'negative':tryfloat(rsp[2], 0)}
        }

    def read_ptc(self):
        '''
        get the product temperature control parameters (range,p,i,filter,opt1,opt2)

        returns:
            {
                "range":{"max":float, "min":float},
                "p":float,
                "filter":float,
                "i":float,
                "opt1":0.0,
                "opt2":0.0
            }
        '''
        rsp = ((self.ctlr.interact('PTC?')).decode('utf-8', 'replace')).split(',')
        return {
            'range':{'max':float(rsp[0]), 'min':float(rsp[1])},
            'p':float(rsp[2]),
            'filter':float(rsp[3]),
            'i':float(rsp[4]),
            'opt1':float(rsp[5]),
            'opt2':float(rsp[6])
        }

    def read_prgm_data_ptc(self, pgmnum):
        '''
        get the parameters for a given program that includes ptc

        Args:
            pgmnum: int, the program to get
        returns:
            {
                "steps":int,
                "name":string,
                "end":string,
                "counter_a":{"start":int, "end":int, "cycles":int},
                "counter_b":{"start":int, "end":int, "cycles":int}
            }
            "END"="OFF" or "CONSTANT" or "STANDBY" or "RUN"
        '''
        pdata = (self.ctlr.interact(f'PRGM DATA PTC?,{self.rom_pgm(pgmnum)}:{pgmnum}')).decode('utf-8', 'replace')
        return self.parse_prgm_data(pdata)

    def read_prgm_data_ptc_detail(self, pgmnum):
        '''
        get the conditions a program will start with and its operational range including ptc

        Args:
            pgmnum: int, the program to get
        returns:
            {
                "temperature":{"range":{"max":float, "min":float}, "mode":string,"setpoint":float},
                "humidity":{"range":{"max":float, "min":float}, "mode":string, "setpoint":float}
            }
        '''
        tmp = (self.ctlr.interact(f'PRGM DATA PTC?,{self.rom_pgm(pgmnum)}:{pgmnum},DETAIL')).decode('utf-8', 'replace')
        return self.parse_prgm_data_detail(tmp)

    def read_prgm_data_ptc_step(self, pgmnum, pgmstep):
        '''
        get a programs step parameters including ptc

        Args:
            pgmnum: int, the program to read from
            pgmstep: int, the step to read from
        returns:
            {
                "number":int,
                "time":{"hour":int, "minute":int},
                "paused":boolean,
                "granty":boolean,
                "refrig":{"mode":string, "setpoint":int},
                "temperature":{
                    "setpoint":float,
                    "ramp":boolean,
                    "enable_cascade":boolean,
                    "deviation":{"positive":float, "negative":float}
                },
                "humidity":{
                    "setpoint":float,
                    "enable":boolean,
                    "ramp":boolean
                },
                "relay":[int]
            }
        '''
        tmp = (self.ctlr.interact(f'PRGM DATA PTC?,{self.rom_pgm(pgmnum)}:{pgmnum},STEP{pgmstep}')).decode('utf-8', 'replace')
        return self.parse_prgm_data_step(tmp)
                                                                               #
    ############################################################################

    def read_prgm_mon(self):
        '''
        get the status of the running program

        returns:
            {
                "pgmstep":int,
                "temperature":float,
                "humidity":float,
                "time":{"hour":int, "minute":int},
                "counter_a":int,
                "counter_b":int
            }
            "humidity" is only present on chambers with humidity
            "counter_?" is the cycles remaining
        '''
        rsp = ((self.ctlr.interact('PRGM MON?')).decode('utf-8', 'replace')).split(',')
        if len(rsp) == 6:
            time = rsp[3].split(':')
            return {
                'pgmstep':int(rsp[0]),
                'temperature':float(rsp[1]),
                'humidity':tryfloat(rsp[2], 0),
                'time':{'hour':int(time[0]), 'minute':int(time[1])},
                'counter_a':int(rsp[4]),
                'counter_b':int(rsp[5])
            }
        else:
            time = rsp[2].split(':')
            return {
                'pgmstep':int(rsp[0]),
                'temperature':float(rsp[1]),
                'time':{'hour':int(time[0]), 'minute':int(time[1])},
                'counter_a':int(rsp[3]),
                'counter_b':int(rsp[4])
            }

    def read_prgm_set(self):
        '''
        get the name,number and end mode of the current program

        returns:
            {"number":int,"name":string,"end":string}
            "end"="OFF" or "STANDBY" or "CONSTANT" or "HOLD" or "RUN"
        '''
        rsp = (self.ctlr.interact('PRGM SET?')).decode('utf-8', 'replace')
        parsed = re.search(r'R[AO]M:(\d+),(.+),END\((\w+)\)', rsp)
        return {'number':int(parsed.group(1)), 'name':parsed.group(2), 'end':parsed.group(3)}

    def read_prgm_use(self):
        '''
        get the id number for each program on the controller as a list

        returns:
            [int]
        '''
        rsp = ((self.ctlr.interact('PRGM USE?')).decode('utf-8', 'replace')).split(',')
        prgm_list_size = len(rsp)
        return rsp #, int(prgm_list_size)

    def read_prgm_use_num(self, pgmnum):
        '''
        get the name and creation date of a specific program

        Args:
            pgmnum: the program to read
        returns:
            {"name":string,"date":{"year":int,"month":int,"day":int}}
        '''
        rsp = re.search(
            r'(.+)?,(\d+).(\d+)\/(\d+)',
            (self.ctlr.interact(f'PRGM USE?,{self.rom_pgm(pgmnum)}:{pgmnum}')).decode('utf-8', 'replace')
        )
        return {
            'name':rsp.group(1) if rsp.group(1) else '',
            'date':{
                'year':2000+int(rsp.group(2)),
                'month':int(rsp.group(3)),
                'day':int(rsp.group(4))
            }
        }

    def read_prgm_data(self, pgmnum):
        '''
        get the parameters for a given program

        Args:
            pgmnum: int, the program to get
        returns:
            {
                "steps":int,
                "name":string,
                "end":string,
                "counter_a":{"start":int, "end":int, "cycles":int},
                "counter_b":{"start":int, "end":int, "cycles":int}
            }
            "END"="OFF" or "CONSTANT" or "STANDBY" or "RUN"
        '''
        pdata = (self.ctlr.interact(f'PRGM DATA?,{self.rom_pgm(pgmnum)}:{pgmnum}')).decode('utf-8', 'repalce')        
        return self.parse_prgm_data(pdata)

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
        '''
        pdata = (self.ctlr.interact(f'PRGM DATA?,{self.rom_pgm(pgmnum)}:{pgmnum},DETAIL')).decode('utf-8', 'repalce')
        return self.parse_prgm_data_detail(pdata)

    def read_prgm_data_step(self, pgmnum, pgmstep):
        '''
        get a programs step parameters

        Args:
            pgmnum: int, the program to read from
            pgmstep: int, the step to read from
        returns:
            {
                "number":int,
                "time":{"hour":int, "minute":int},
                "paused":boolean,
                "granty":boolean,
                "refrig":{"mode":string, "setpoint":int},
                "temperature":{"setpoint":float, "ramp":boolean},
                "humidity":{"setpoint":float, "enable":boolean, "ramp":boolean},
                "relay":[int]
            }
        '''
        tmp = (self.ctlr.interact(f'PRGM DATA?,{self.rom_pgm(pgmnum)}:{pgmnum},STEP{pgmstep}'))#.decode('utf-8', 'replace')
        return self.parse_prgm_data_step(tmp)

    def read_run_prgm_mon(self):
        '''
        Get the state of the remote program being run

        returns:
            {
                "pgmstep":int,
                "temperature":float,
                "humidity":float,
                "time":{"hour":int, "minute":int},
                "counter":int
            }
            "humidity" is present only on humidity chambers
        '''
        rsp = ((self.ctlr.interact('RUN PRGM MON?')).decode('utf-8', 'replace')).split(',')
        if len(rsp) == 5:
            time = rsp[3].split(':')
            return {
                'pgmstep':int(rsp[0]),
                'temperature':float(rsp[1]),
                'humidity':float(rsp[2]),
                'time':{'hour':int(time[0]), 'minute':int(time[1])},
                'counter':int(rsp[4])
            }
        else:
            time = rsp[2].split(':')
            return {
                'pgmstep':int(rsp[0]),
                'temperature':float(rsp[1]),
                'time':{'hours':int(time[0]), 'minuets':int(time[1])},
                'counter':int(rsp[3])
            }

    def read_run_prgm(self):
        '''
        get the settings for the remote program being run

        returns:
            {
                "temperature":{"start":float,"end":float},"humidity":{"start":float,"end":float},
                "time":{"hours":int,"minutes":int},"refrig":{"mode":string,"setpoint":}
            }
        '''
        rsp = (self.ctlr.interact('RUN PRGM?')).decode('utf-8', 'replace')
        parsed = re.search(
            r'TEMP([0-9.-]+) GOTEMP([0-9.-]+)(?: HUMI(\d+) GOHUMI(\d+))? TIME(\d+):(\d+) (\w+)'
            r'(?: RELAYON,([0-9,]+))?',
            rsp
        )
        ret = {
            'temperature':{'start':float(parsed.group(1)), 'end':float(parsed.group(2))},
            'time':{'hours':int(parsed.group(5)), 'minutes':int(parsed.group(6))},
            'refrig':self.reflookup.get(parsed.group(7), {'mode':'manual', 'setpoint':0})
        }
        if parsed.group(3):
            ret['humidity'] = {'start':float(parsed.group(3)), 'end':float(parsed.group(4))}
        if parsed.group(8):
            relays = parsed.group(8).split(',')
            ret['relay'] = [str(i) in relays for i in range(1, 13)]
        else:
            ret['relay'] = [False for i in range(1, 13)]
        return rsp # return rsp from GL controller

    def read_ip_set(self): # Unsupport on GL controller.
        '''
        Read the configured IP address of the controller
        '''
        return dict(list(zip(['address', 'mask', 'gateway'], ((self.ctlr.interact('IPSET?')).decode('utf-8', 'replace')).split(','))))

    ##################################################################################
    # CONTROL/SET COMMANDS: WRITE METHODS 
    # Decorators for GLC by calling each set command
    # to set or control the chamber 
    ##################################################################################
    #
    #--- write methods --- write methods --- write methods --- write methods --- write methods ---
    #

    # Do not attempt to write date/time to mess up the system config
    def write_date(self, year, month, day, dow):
        '''
        write a new date to the controller

        Args:
            year: int,2007-2049
            month: int,1-12
            day: int,1-31
        '''
        cyear = (year - 2000) if year > 2000 else year
        (self.ctlr.interact(f'DATE,{cyear}.{month}/{day}.{dow}')).decode('utf-8', 'replace')
        #(self.ctlr.interact('DATE,{}.{}/{}. {}'.format(cyear, month, day, dow))).decode('utf-8', 'replace')

    # Do not attempt to write date/time to mess up the system config
    def write_time(self, hour, minute, second):
        '''
        write a new time to the controller

        Args:
            hour: int,0-23
            minute: int,0-59
            second: int,0-59
        '''
        (self.ctlr.interact(f'TIME,{hour}:{minute}:{second}')).decode('utf-8', 'replace') 

    def write_mask(self, alarm=False, single_step_done=False, state_change=False, gpib=False):
        '''
        write the srq mask

        Args:
            alarm,single_step_done,state_change,GPIB: boolean
        '''
        #self.ctlr.interact('MASK,0%d%d%d00%d0' % (
        #    int(alarm),
        #    int(single_step_done),
        #    int(state_change),
        #    int(gpib)))
        (self.ctlr.interact(f'MASK,0{int(alarm)}{int(single_step_done)}{int(state_change)}00{int(gpib)}0')).decode('utf-8', 'replace') 

    def write_srq(self):
        '''
        reset the srq register
        '''
        (self.ctlr.interact('SRQ,RESET')).decode('utf-8', 'replace')

    def write_timer_quick(self, mode, time, pgmnum=None, pgmstep=None):
        '''
        write the quick timer parameters to the controller(timer 0)

        Args:
            mode: string, "STANDBY" or "OFF" or "CONSTANT" or "RUN"
            time: {"hour":int,"minute":int}, the time to wait
            pgmnum: int, program to run if mode=="RUN"
            pgmstep: int, program step to run if mode=="RUN"
        '''
        cmd = f"TIMER WRITE,NO0,{time['hour']}:{time['minute']},{mode}"
        if mode == 'RUN':
            cmd = f'{cmd},{self.rom_pgm(pgmnum)}:{pgmnum},STEP{pgmstep:d}'
        (self.ctlr.interact(cmd)).decode('utf-8', 'replace') 

    def write_timer_start(self, repeat, time, mode, **kwargs):
        '''
        write the start timer parameters to the controller (timer 1)

        Args:
            repeat: string, "once" or "weekly" or "daily"
            time: {"hour":int,"minute":int}, the time of day to start the chamber
            mode: string, "CONSTANT" or "RUN"
            date: {"month":int,"day":int,"year":int}, date to start chamber on when repeat=="once"
            days: [string], the day to start the chamber on when repeat=="weekly" i.e. "WED"
            pgmnum: int,
            pgmstep: int, only present when "mode"=="RUN"
        '''
        date, days, pgmnum = kwargs.get('date'), kwargs.get('days'), kwargs.get('pgmnum')
        pgmstep = kwargs.get('pgmstep')
        cmd = 'TIMER WRITE,NO1,MODE{}'.format({'once':1, 'weekly':2, 'daily':3}[repeat])
        if repeat == 'once':
            cmd = '{},{}.{}/{}'.format(cmd, date['year']-2000, date['month'], date['day'])
        elif repeat == 'weekly':
            cmd = '{},{}'.format(cmd, '/'.join(days))
        cmd = '{},{}:{},{}'.format(cmd, time['hour'], time['minute'], mode)
        if mode == 'RUN':
            cmd = '{},{}:{},STEP{}'.format(cmd, self.rom_pgm(pgmnum), pgmnum, pgmstep)
        (self.ctlr.interact(cmd)).decode('utf-8', 'replace')

    def write_timer_stop(self, repeat, time, mode, date=None, days=None):
        '''
        write the stop timer parameters to the controller (timer 2)

        Args:
            repeat: string, "once" or "weekly" or "daily"
            time: {"hour":int,"minute":int}, the time of day to start the chamber
            mode: string, "STANDBY" or "OFF"
            date: {"month":int,"day":int,"year":int}, date to start chamber on when repeat=="once"
            days: [string], the day to start the chamber on when repeat=="weekly" i.e. "WED"
        '''
        cmd = 'TIMER WRITE,NO2,MODE{}'.format({'once':1, 'weekly':2, 'daily':3}[repeat])
        if repeat == 'once':
            cmd = '{},{}.{}/{}'.format(cmd, date['year']-2000, date['month'], date['day'])
        elif repeat == 'weekly':
            cmd = '{},{}'.format(cmd, '/'.join(days))
        cmd = '{},{}:{},{}'.format(cmd, time['hour'], time['minute'], mode)
        (self.ctlr.interact(cmd)).decode('utf-8', 'replace')

    def write_timer_erase(self, timer):
        '''
        erase the give timer

        Args:
            timer: string, "quick" or "start" or "stop"
        '''
        (self.ctlr.interact('TIMER ERASE,NO{}'.format({'quick':0, 'start':1, 'stop':2}[timer]))).decode('utf-8', 'replace') 

    def write_timer(self, timer, run):
        '''
        set the run mode of a give timer

        Args:
            timer: string, "quick" or "start" or "stop"
            run: boolean, True=turn timer on, False=turn timer off
        '''
        tmp = {'quick':0, 'start':1, 'stop':2}
        (self.ctlr.interact('TIMER,{},{}'.format('ON' if run else 'OFF', tmp[timer]))).decode('utf-8', 'replace')

    def write_keyprotect(self, enable):
        '''
        enable/disable change and operation protection

        Args:
            enable: boolean True=protection on, False=protection off
        '''
        (self.ctlr.interact('KEYPROTECT,{}'.format('ON' if enable else 'off'))).decode('utf-8', 'replace')

    def write_power(self, start): # No quite usable on GL controller to power oof/on.
        '''
        turn on the chamber power

        Args:
            start: boolean True=start constant1, False=Turn contoller off)
        '''
        (self.ctlr.interact(f"POWER,{'ON' if start else 'off'}")).decode('utf-8', 'replace')

    def write_temp(self, **kwargs):
        '''
        update the temperature parameters

        Args:
            setpoint: float
            max: float
            min: float
            range: {"max":float, "min":float}
        '''
        setpoint, maximum, minimum = 24,30,10
        setpoint, maximum, minimum = kwargs.get('setpoint'), kwargs.get('max'), kwargs.get('min')
        if setpoint is not None and minimum is not None and maximum is not None:
            (self.ctlr.interact(f'TEMP, S{setpoint:.1f} H{maximum:.1f} L{minimum:.1f}')).decode('utf-8', 'replace')
        else:
            if setpoint is not None:
                (self.ctlr.interact(f'TEMP, S{setpoint:.1f}')).decode('utf-8', 'replace')
            if minimum is not None:
                (self.ctlr.interact(f'TEMP, L{minimum:.1f}')).decode('utf-8', 'replace')
            if maximum is not None:
                (self.ctlr.interact(f'TEMP, H{maximum:.1f}')).decode('utf-8', 'replace')

    def write_humi(self, **kwargs):
        '''
        update the humidity parameters

        Args:
            enable: boolean
            setpoint: float
            max: float
            min: float
            range: {"max":float,"min":float}
        '''
        setpoint, maximum, minimum = kwargs.get('setpoint'), kwargs.get('max'), kwargs.get('min')
        enable = kwargs.get('enable')
        if enable is False:
            spstr = f'SOFF'
        elif setpoint is not None:
            spstr = f' S{setpoint:.1f}'
        else:
            spstr = None
        if spstr is not None and minimum is not None and maximum is not None:
            (self.ctlr.interact(f'HUMI,{spstr} H{maximum:.1f} {minimum:.1f}')).decode('utf-8', 'replace')
        else:
            if spstr is not None:
                (self.ctlr.interact(f'HUMI,{spstr}')).decode('utf-8', 'replace')
            if minimum is not None:
                (self.ctrl.interact(f'HUMI, L{minimum:0.1f}')).decode('utf-8', 'replace')
            if maximum is not None:
                (self.ctlr.interact(f'HUMI, H{maximum:0.1f}')).decode('utf-8', 'replace')

    def write_set(self, mode, setpoint=0):
        '''
        Set the constant setpoints refrig mode

        Args:
            mode: string,"off" or "manual" or "auto"
            setpoint: int,20 or 50 or 100
        '''
        (self.ctlr.interact(f'SET,{self.encode_refrig(mode, setpoint)}')).decode('utf-8', 'replace')

    def write_relay(self, relays):
        '''
        set each relay(time signal)

        Args:
            relays: [boolean] True=turn relay on, False=turn relay off, None=do nothing
        '''
        vals = (self.parse_relays(relays))     
        if len(vals['on']) > 0:
            (self.ctlr.interact(f"RELAY,ON,{','.join(str(v) for v in vals['on'])}")).decode('utf-8', 'replace')
        if len(vals['off']) > 0:
            (self.ctlr.interact(f"RELAY,OFF,{','.join(str(v) for v in vals['off'])}")).decode('utf-8', 'replace') 

    def write_prgm_run(self, pgmnum, pgmstep):
        '''
        runs a program at the given step

        params:
            pgmnum: int, program to run
            prgmstep: int, step to run
        '''
        (self.ctlr.interact(f'PRGM,RUN,{self.rom_pgm(pgmnum)}:{pgmnum},STEP{pgmstep}')).decode('utf-8', 'replace')

    def write_prgm_pause(self):
        '''
        pause a running program.
        '''
        (self.ctlr.interact('PRGM,PAUSE')).decode('utf-8', 'replace') 

    def write_prgm_continue(self):
        '''
        resume execution of a paused program
        '''
        (self.ctlr.interact('PRGM,CONTINUE')).decode('utf-8', 'replace')

    def write_prgm_advance(self):
        '''
        skip to the next step of a running program
        '''
        (self.ctlr.interact('PRGM,ADVANCE')).decode('utf-8', 'replace')

    def write_prgm_end(self, mode="STANDBY"):
        '''
        stop the running program

        Args:
            mode: string, vaid options: "HOLD"/"CONST"/"OFF"/"STANDBY"(default)
        '''
        if mode in ["HOLD", "CONST", "OFF", "STANDBY"]:
            (self.ctlr.interact(f'PRGM,END,{mode}')).decode('utf-8', 'replace') 
        else:
            raise ValueError('"mode" must be "HOLD"/"CONST"/"OFF"/"STANDBY"')

    def write_mode_off(self):
        '''
        turn the controller screen off
        '''
        (self.ctlr.interact('MODE,OFF')).decode('utf-8', 'replace')

    def write_mode_standby(self):
        '''
        stop operation(STANDBY)
        '''
        (self.ctlr.interact('MODE,STANDBY')).decode('utf-8', 'replace')

    def write_mode_constant(self, cstnum):
        '''
        run constant setpoint 1
        '''
        #(self.ctlr.interact('MODE,CONSTANT')).decode('utf-8', 'replace')
        # modified for all three Constant modes 
        (self.ctlr.interact(f'MODE,CONSTANT,{cstnum}')).decode('utf-8', 'replace')

    def write_mode_run(self, pgmnum):
        '''
        run a program given by number

        Args:
            pgmnum: int, the program to run
        '''
        (self.ctlr.interact(f'MODE,RUN{pgmnum}')).decode('utf-8', 'replace')

    def write_prgm_data_edit(self, pgmnum, mode, overwrite=False):
        '''
        start/stop/cancel program editing on a new or exising program

        Args:
            pgmnum: int, the program to start/stop/cancel editing on
            mode: string, "START" or "END" or "CANCEL"
            overwrite: boolean, when true programs/steps may be overwritten
        '''
        tmp = f"PRGM DATA WRITE,PGM{pgmnum},{'OVER WRITE' if overwrite else 'EDIT'} {mode}"
        (self.ctlr.interact(tmp)).decode('utf-8', 'replace')

    def write_prgm_data_details(self, pgmnum, **pgmdetail):
        '''
        write the various program wide parameters to the controller

        Args:
            pgmnum: int, the program being written or edited
            pgmdetail: the program details see write_prgmDataDetail for parameters
        '''
        if 'counter_a' in pgmdetail and pgmdetail['counter_a']['cycles'] > 0:
            ttp = (pgmnum, pgmdetail['counter_a']['start'], pgmdetail['counter_a']['end'],
                   pgmdetail['counter_a']['cycles'])
            tmp = 'PRGM DATA WRITE,PGM%d,COUNT,A(%d.%d.%d)' % ttp
            if 'counter_b' in pgmdetail and pgmdetail['counter_b']['cycles'] > 0:
                ttp = (tmp, pgmdetail['counter_b']['start'], pgmdetail['counter_b']['end'],
                       pgmdetail['counter_b']['cycles'])
                tmp = '{},B({}.{}.{})'.format(*ttp)
            (self.ctlr.interact(tmp)).decode('utf-8', 'replace') 
        elif 'counter_b' in pgmdetail and pgmdetail['counter_b']['cycles'] > 0:
            ttp = (pgmnum, pgmdetail['counter_b']['start'], pgmdetail['counter_b']['end'],
                   pgmdetail['counter_b']['cycles'])
            (self.ctlr.interact('PRGM DATA WRITE,PGM{},COUNT,B({}.{}.{})'.format(*ttp))).decode('utf-8', 'replace')              
        if 'name' in pgmdetail:
            (self.ctlr.interact('PRGM DATA WRITE,PGM{},NAME,{}'.format(pgmnum, pgmdetail['name']))).decode('utf-8', 'replace') 
        if 'end' in pgmdetail:
            if pgmdetail['end'] != 'RUN':
                ttp = (pgmnum, pgmdetail['end'])
            else:
                ttp = (pgmnum, 'RUN,PTN{}'.format(pgmdetail['next_prgm']))
            (self.ctlr.interact('PRGM DATA WRITE,PGM{},END,{}'.format(*ttp))).decode('utf-8', 'replace') 
        if 'tempDetail' in pgmdetail:
            if 'range' in pgmdetail['tempDetail']:
                ttp = (pgmnum, pgmdetail['tempDetail']['range']['max'])
                (self.ctlr.interact('PRGM DATA WRITE,PGM{},HTEMP,{0:.1f}'.format(*ttp))).decode('utf-8', 'replace') 
                ttp = (pgmnum, pgmdetail['tempDetail']['range']['min'])
                (self.ctlr.interact('PRGM DATA WRITE,PGM{},LTEMP,{0:.1f}'.format(*ttp))).decode('utf-8', 'replace') 
            if 'mode' in pgmdetail['tempDetail']:
                ttp = (pgmnum, pgmdetail['tempDetail']['mode'])
                (self.ctlr.interact('PRGM DATA WRITE,PGM{},PRE MODE,TEMP,{}'.format(*ttp))).decode('utf-8', 'replace') 
            if 'setpoint' in pgmdetail['tempDetail'] and pgmdetail['tempDetail']['mode'] == 'SV':
                ttp = (pgmnum, pgmdetail['tempDetail']['setpoint'])
                (self.ctlr.interact('PRGM DATA WRITE,PGM{},PRE TSV,{0:.1f}'.format(*ttp))).decode('utf-8', 'replace') 
        if 'humiDetail' in pgmdetail:
            if 'range' in pgmdetail['humiDetail']:
                ttp = (pgmnum, pgmdetail['humiDetail']['range']['max'])
                (self.ctlr.interact('PRGM DATA WRITE,PGM{},HHUMI,{0:.0f}'.format(*ttp))).decode('utf-8', 'replace') 
                ttp = (pgmnum, pgmdetail['humiDetail']['range']['min'])
                (self.ctlr.interact('PRGM DATA WRITE,PGM{},LHUMI,{0:.0f}'.format(*ttp))).decode('utf-8', 'replace') 
            if 'mode' in pgmdetail['humiDetail']:
                ttp = (pgmnum, pgmdetail['humiDetail']['mode'])
                (self.ctlr.interact('PRGM DATA WRITE,PGM{},PRE MODE,HUMI,{}'.format(*ttp))).decode('utf-8', 'replace') 
            if 'setpoint' in pgmdetail['humiDetail'] and pgmdetail['humiDetail']['mode'] == 'SV':
                ttp = (pgmnum, pgmdetail['humiDetail']['setpoint'])
                (self.ctlr.interact('PRGM DATA WRITE,PGM{},PRE HSV,{0:.0f}'.format(*ttp))).decode('utf-8', 'replace') 

    def write_prgm_data_step(self, pgmnum, **pgmstep):
        '''
        write a program step to the controller

        Args:
            pgmnum: int, the program being written/edited
            pgmstep: the program parameters, see read_prgm_data_step for parameters
        '''
        cmd = f"PRGM DATA WRITE,PGM{pgmnum},STEP{pgmstep['number']}"
        if 'temperature' in pgmstep:
            if 'setpoint' in pgmstep['temperature']:
                cmd = f"{cmd},TEMP{pgmstep['temperature']['setpoint']:.1f}"
            if 'ramp' in pgmstep['temperature']:
                cmd = f"{cmd},TRAMP{'ON' if pgmstep['temperature']['ramp'] else 'OFF'}"                
            if 'enable_cascade' in pgmstep['temperature']:
                cmd = f"{cmd},PTC{'ON' if pgmstep['temperature']['enable_cascade'] else 'OFF'}"
            if 'deviation' in pgmstep['temperature']:
                ttp = (cmd, pgmstep['temperature']['deviation']['positive'],
                       pgmstep['temperature']['deviation']['negative'])
                cmd = '{},DEVP{:.1f},DEVN{:.1f}'.format(*ttp)
        if 'humidity' in pgmstep:
            if 'setpoint' in pgmstep['humidity']:
                if pgmstep['humidity']['enable']:
                    htmp = '{:.0f}'.format(pgmstep['humidity']['setpoint'])
                else:
                    htmp = 'OFF'
                cmd = '{},HUMI{}'.format(cmd, htmp)
            if 'ramp' in pgmstep['humidity'] and pgmstep['humidity']['enable']:
                cmd = '{},HRAMP{}'.format(cmd, 'ON' if pgmstep['humidity']['ramp'] else 'OFF')
        if 'time' in pgmstep:
            cmd = '{},TIME{}:{}'.format(cmd, pgmstep['time']['hour'], pgmstep['time']['minute'])
        if 'granty' in pgmstep:
            cmd = '{},GRANTY {}'.format(cmd, 'ON' if pgmstep['granty'] else 'OFF')
        if 'paused' in pgmstep:
            cmd = '{},PAUSE {}'.format(cmd, 'ON' if pgmstep['paused'] else 'OFF')
        if 'refrig' in pgmstep:
            cmd = '{},{}'.format(cmd, self.encode_refrig(**pgmstep['refrig']))
        if 'relay' in pgmstep:
            rlys = self.parse_relays(pgmstep['relay'])
            if rlys['on']:
                cmd = '{},RELAY ON{}'.format(cmd, '.'.join(str(v) for v in rlys['on']))
            if rlys['off']:
                cmd = '{},RELAY OFF{}'.format(cmd, '.'.join(str(v) for v in rlys['off']))
        (self.ctlr.interact(cmd)).decode('utf-8', 'replace') 

    def write_prgm_erase(self, pgmnum):
        '''
        erase a program

        Args:
            pgmnum: int, the program to erase
        '''
        (self.ctlr.interact('PRGM ERASE,{}:{}'.format(self.rom_pgm(pgmnum), pgmnum))).decode('utf-8', 'replace') 

    def write_run_prgm(self, temp, hour, minute, gotemp=None, humi=None, gohumi=None, relays=None):
        '''
        Run a remote program (single step program)

        Args:
            temp: float, temperature to use at the start of the step
            hour: int, # of hours to run the step
            minute: int, # of minutes to run the step
            gotemp: float, temperature to end the step at(optional for ramping)
            humi: float, the humidity to use at the start of the step (optional)
            gohumi: float, the humidity to end the steap at (optional for ramping)
            relays: [boolean], True= turn relay on, False=turn relay off, None=Do nothing
        '''
        cmd = f'RUN PRGM, TEMP{temp:.1f} TIME{hour}:{minute}'
        if gotemp is not None:
            cmd = f'{cmd} GOTEMP{gotemp:.1f}'
        if humi is not None:
            cmd = f'{cmd} HUMI{humi:.0f}'
        if gohumi is not None:
            cmd = f'{cmd} GOHUMI{gohumi:.0f}'
        rlys = self.parse_relays(relays) if relays is not None else {'on':None, 'off':None}
        if rlys['on']:
            cmd = f"{cmd} RELAYON,{','.join(str(v) for v in rlys['on'])}"
        if rlys['off']:
            cmd = f"{cmd} RELAYOFF,{','.join(str(v) for v in rlys['off'])}"
        (self.ctlr.interact(cmd)).decode('utf-8', 'replace') 

    def write_temp_ptc(self, enable, positive, negative):
        '''
        set product temperature control settings

        Args:
            enable: boolean, True(on)/False(off)
            positive: float, maximum positive deviation
            negative: float, maximum negative deviation
        '''
        ttp = ('ON' if enable else 'OFF', positive, negative)
        (self.ctlr.interact('TEMP PTC, PTC{}, DEVP{:0.1f}, DEVN{:0.1f}'.format(*ttp))).decode('utf-8', 'replace') 

    def write_ptc(self, op_range, pid_p, pid_filter, pid_i, **kwargs):
        '''
        write product temp control parameters to controller

        Args:
            range: {"max":float,"min":float}, allowable range of operation
            p: float, P parameter of PID
            i: float, I parameter of PID
            filter: float, filter value
            opt1,opt2 not used set to 0.0
        '''
        opt1, opt2 = kwargs.get('opt1', 0), kwargs.get('opt2', 0)
        ttp = (op_range['max'], op_range['min'], pid_p, pid_filter, pid_i, opt1, opt2)
        (self.ctlr.interact('PTC,{:.1f},{:.1f},{:.1f},{:.1f},{:.1f},{:.1f},{:.1f}'.format(*ttp))).decode('utf-8', 'replace') 

    def write_ip_set(self, address, mask, gateway):
        '''
        Write the IP address configuration to the controller
        '''
        (self.ctlr.interact('IPSET,{},{},{}'.format(address, mask, gateway))).decode('utf-8', 'replace') 

    # --- helpers etc --- helpers etc --- helpers etc --- helpers etc -- helpers etc -- helpers etc
    def parse_prgm_data_step(self, arg):
        '''
        Parse a program step
        '''
        parsed = re.search(
            r'(\d+),TEMP([0-9.-]+),TEMP RAMP (\w+)(?:,PTC (\w+))?(?:,HUMI([^,]+)'
            r'(?:,HUMI RAMP (\w+))?)?,TIME(\d+):(\d+),GRANTY (\w+),REF(\w+)'
            r'(?:,RELAY ON([0-9.]+))?(?:,PAUSE (\w+))?(?:,DEVP([0-9.-]+),DEVN([0-9.-]+))?',
            arg.decode('utf-8', 'replace')
        )
        base = {'number':int(parsed.group(1)),
                'time':{'hour':int(parsed.group(7)),
                        'minute':int(parsed.group(8))},
                'paused':parsed.group(12) == 'ON',
                'granty':parsed.group(9) == 'ON',
                'refrig':self.reflookup.get(
                    'REF' + parsed.group(10),
                    {'mode':'manual', 'setpoint':0}
                ),
                'temperature':{'setpoint':float(parsed.group(2)),
                               'ramp':parsed.group(3) == 'ON'}}
        if parsed.group(5):
            base['humidity'] = {
                'setpoint':tryfloat(parsed.group(5), 0.0),
                'enable':parsed.group(5) != ' OFF',
                'ramp':parsed.group(6) == 'ON'
            }
        if parsed.group(4):
            base['temperature'].update({
                'enable_cascade':parsed.group(4) == 'ON',
                'deviation': {
                    'positive':float(parsed.group(13)),
                    'negative':float(parsed.group(14))
                }
            })
        if parsed.group(11):
            relays = parsed.group(11).split('.')
            base['relay'] = [str(i) in relays for i in range(1, 13)]
        else:
            base['relay'] = [False for i in range(1, 13)]
        return base

    def parse_prgm_data_detail(self, arg):
        '''
        Parse the program data command with details flag
        '''
        parsed = re.search(
            r'([0-9.-]+),([0-9.-]+),(?:(\d+),(\d+),)?TEMP(\w+)'
            r'(?:,([0-9.-]+))?(?:,HUMI(\w+)(?:,(\d+))?)?',
            arg.decode('utf-8', 'replace')
        )
        ret = {
            'tempDetail':{
                'range':{
                    'max':float(parsed.group(1)),
                    'min':float(parsed.group(2))
                },
                'mode':parsed.group(5),
                'setpoint':parsed.group(6)
            }
        }
        if parsed.group(3):
            ret['humiDetail'] = {
                'range':{
                    'max':float(parsed.group(3)),
                    'min':float(parsed.group(4))
                },
                'mode':parsed.group(7),
                'setpoint':parsed.group(8)
            }
        return ret

    #currently not parsing the patern number on endmode run
    def parse_prgm_data(self, arg):
        '''
        Parse the program data command
        '''
        parsed = re.search(
            r'(\d+),<(.+)?>,COUNT,A\((\d+).(\d+).(\d+)\),B\((\d+).(\d+).(\d+)\),'
            r'END\(([a-zA-Z0-9:]+)\)',
            arg
        )
        return {
            'steps':int(parsed.group(1)),
            'name':parsed.group(2) if parsed.group(2) else '',
            'end':parsed.group(9) if 'RUN' not in parsed.group(9) else parsed.group(9)[:3],
            'next_prgm':int('0' if 'RUN' not in parsed.group(9) else parsed.group(9)[4:]),
            'counter_a':{
                'start':int(parsed.group(3)),
                'end':int(parsed.group(4)),
                'cycles':int(parsed.group(5))
            },
            'counter_b':{
                'start':int(parsed.group(6)),
                'end':int(parsed.group(7)),
                'cycles':int(parsed.group(8))
            }
        }

    def read_prgm(self, pgmnum, with_ptc=False):
        '''
        read an entire program helper method
        '''
        if pgmnum > 0 and pgmnum <= 40:
            pgm = self.read_prgm_data_ptc(pgmnum) if with_ptc else self.read_prgm_data(pgmnum)
            pgm = self.read_prgm_data_ptc(pgmnum) if with_ptc else self.read_prgm_data(pgmnum)
            if with_ptc:
                try:
                    pgm.update(self.read_prgm_data_ptc_detail(pgmnum))
                    pgm.update(self.read_prgm_data_ptc_detail(pgmnum))
                except NotImplementedError:
                    pass #SCP-220 does not have the detail command
                tmp = [self.read_prgm_data_ptc_step(pgmnum, i) for i in range(1, pgm['steps']+1)]
            else:
                try:
                    pgm.update(self.read_prgm_data_detail(pgmnum))
                except NotImplementedError:
                    pass #SCP-220 does not have the detail command
                tmp = [self.read_prgm_data_step(pgmnum, i) for i in range(1, pgm['steps']+1)]
            pgm['steps'] = tmp
        elif pgmnum == 0:
            pgm = {
                'counter_a':{'cycles':0, 'end':0, 'start':0},
                'counter_b':{'cycles':0, 'end':0, 'start':0},
                'end':'OFF',
                'name':'',
                'next_prgm':0,
                'tempDetail':{'mode':'OFF', 'setpoint':None, 'range':self.read_temp()['range']},
                'steps':[
                    {
                        'granty':False,
                        'number':1,
                        'paused':False,
                        'refrig':{'mode':'auto', 'setpoint':0},
                        'time':{'hour':1, 'minute':0},
                        'relay':[False for i in range(12)],
                        'temperature':{'ramp':False, 'setpoint':0.0}
                    }
                ]
            }
            if with_ptc:
                pgm['steps'][0]['temperature'].update({
                    'deviation':self.read_temp_ptc()['deviation'],
                    'enable_cascade':False
                })
            try:
                pgm['humiDetail'] = {
                    'mode':'OFF',
                    'setpoint':None,
                    'range':self.read_humi()['range']
                }
                pgm['steps'][0]['humidity'] = {'enable':False, 'ramp':False, 'setpoint':0.0}
            except Exception:
                pass
        else:
            raise ValueError('pgmnum must be 0-40')
        return pgm

    def write_prgm(self, pgmnum, program):
        '''
        write an entire program helper method (must use same program format as read_prgm)
        '''
        max_write = 40 if self.ramprgms == 40 else 20 #SCP220 has 20 programs P300 40
        if pgmnum > max_write:
            raise ValueError('Program #%d is readonly and connot be saved over.' % pgmnum)
        self.write_prgm_data_edit(pgmnum, 'START')
        try:
            set_humi = False
            for num, step in enumerate(program['steps']):
                step['number'] = num+1 #ensure the step number is sequential
                self.write_prgm_data_step(pgmnum, **step)
                if step.get('humidity', {'enable':False})['enable']:
                    set_humi = True
            if not set_humi and 'humiDetail' in program:
                program['humiDetail'].pop('range', None)
            self.write_prgm_data_details(pgmnum, **program)
            self.write_prgm_data_edit(pgmnum, 'END')
        except:
            self.write_prgm_data_edit(pgmnum, 'CANCEL')
            raise

    def encode_refrig(self, mode, setpoint):
        '''
        Convert refig mode dict to string
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
        handle relays
        '''
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

# GL features: superset commands for GL on P300 library 

    def write_constant_set_mode(self, cnum, arg, value):
        '''
        Get the constant settings for all system parameters: 
            TEMP, HUMI, REF, RELAY, PTC

        returns:
            [int] and [string]
        '''
        if arg in ['TEMP', 'HTEMP', 'LTEMP', 'HUMI', 'HHUMI', 'LHUMI', ] and cnum in [1,2,3]:            
            self.ctlr.interact(f'CONSTANT SET,{cnum},{arg},{value}').decode('utf-8', 'replace').split(',')
        else:
            raise ValueError('Invalid parameter values and cnum must be between 1 and 3')

    def write_constant_set_mode_ref(self, cnum, arg, value):
        '''
        Get the constant settings for all system parameters: REF

        returns:
            [int] and [string]
        '''
        if arg in ['REF'] and cnum in [1,2,3]:            
            self.ctlr.interact(f'CONSTANT SET,{cnum},{arg},{value}').decode('utf-8', 'replace').split(',')
        else:
            raise ValueError('Invalid parameter values and cnum must be between 1 and 3')

    def write_constant_set_relay(self, cstnum, relays):
        '''
        run constant setpoint 1
        '''
        vals = (self.parse_relays(relays))     
        if len(vals['on']) > 0:
            (self.ctlr.interact(f"CONSTANT SET,{cstnum},RELAY,ON,{','.join(str(v) for v in vals['on'])}")).decode('utf-8', 'replace')
        else:
            raise ValueError('Invalid parameter.')

        if len(vals['off']) > 0:
            (self.ctlr.interact(f"CONSTATN SET,{cstnum},RELAY,OFF,{','.join(str(v) for v in vals['off'])}")).decode('utf-8', 'replace') 
        else:
            raise ValueError('Invladi parameter')          
            
    """
    def write_relay(self, relays):
        '''
        set each relay(time signal)

        Args:
            relays: [boolean] True=turn relay on, False=turn relay off, None=do nothing
        '''
        vals = (self.parse_relays(relays))     
        if len(vals['on']) > 0:
            (self.ctlr.interact(f"RELAY,ON,{','.join(str(v) for v in vals['on'])}")).decode('utf-8', 'replace')
        if len(vals['off']) > 0:
            (self.ctlr.interact(f"RELAY,OFF,{','.join(str(v) for v in vals['off'])}")).decode('utf-8', 'replace') 
    """


