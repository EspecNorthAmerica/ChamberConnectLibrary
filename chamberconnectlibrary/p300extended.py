'''
A direct implementation of the SCP220's communication interface.

:copyright: (C) Espec North America, INC.
:license: MIT, see LICENSE for more details.
'''
import re
from p300 import P300, tryfloat

class P300Extended(P300):
    '''
    P300 communications basic implementation for p300 firmware with extended command set
    (air speed & constant modes 2 & 3)

    Args:
        interface (str): The interface type to connect to: "Serial" or "TCP"
    Kwargs:
        serialport (str/int): The serial port to connect to when interface="Serial"
        baudrate (int): The baud rate to connect at when interface="Serial"
        address (int): The RS485 address of the chamber to connect to.
        host (str): The IP address or hostname of the chamber when interface="TCP"
    '''

    def __init__(self, interface, **kwargs):
        super(P300Extended, self).__init__(interface, **kwargs)
        self.enable_air_speed = kwargs.get('enable_air_speed', False)

    def read_mode(self, detail=False, constant=False):
        '''
        Return the chamber operation state.

        Added new feature: CONSTANT 

        Args:
            detail: boolean, if True get additional information (not SCP220 compatible)
            constant: boolean, (overrides detail) get the constant number.
        returns:
            detail=False & constant=False: string "OFF" or "STANDBY" or "CONSTANT" or "RUN"
            detail=True: string (one of the following):
                "OFF" or "STANDBY" or "CONSTANT" or "RUN" or "RUN PAUSE" or "RUN END HOLD" or
                "RMT RUN" or "RMT RUN PAUSE" or "RMT RUN END HOLD"
            constant=True: string (one of the following)
                "OFF" or "STANDBY" or "CONSTANT1" or "CONSTANT2" or "CONSTANT3" or "RUN" or
                "RUN PAUSE" or "RUN END HOLD" or "RMT RUN" or "RMT RUN PAUSE" or "RMT RUN END HOLD"
        '''
        if constant:
            return self.ctlr.interact('MODE?,DETAIL,CONSTANT')
        else:
            return self.ctlr.interact('MODE?' + (',DETAIL' if detail else ''))

    def read_mon(self, detail=False, constant=False):
        '''
        Returns the conditions inside the chamber

        Args:
            detail: boolean, when True "mode" parameter has additional details
            constant: boolean, if True get the number for the running consant mode.
        returns:
            {"temperature":float,"humidity":float,"mode":string,"alarms":int}
            "humidity": only present if chamber has humidity
            "mode": see read_mode for valid parameters (with and without detail flag).
        '''
        if constant:
            rsp = self.ctlr.interact('MON?,DETAIL,CONSTANT').split(',')
        else:
            rsp = self.ctlr.interact('MON?%s%s' % (',DETAIL' if detail else '', ',CONSTANT' if constant else '')).split(',')
        data = {'temperature':float(rsp[0]), 'mode':rsp[2], 'alarms':int(rsp[3])}
        if rsp[1]:
            data['humidity'] = float(rsp[1])
        return data
    
    def read_air(self): #is this correct??????
        '''
        Read the currently selected air speed value and the options values.

        returns:
            {'selected':int, 'options':[int]}
        '''
        selected, options = self.ctlr.interact('AIR?').split('/')
        return {'selected':int(selected), 'options':range(1, int(options)+1)}

    def read_constant_air(self, constant=1):
        '''
        Read the selected air speed value and the options values for the specified constant mode.

        Args:
            constant: int, the constant mode to read from with a range of 1 to 3; 1 is default
        returns:
            {'selected':int, 'options':[int]}
        '''
        if constant in [1, 2, 3]:
            selected, options = self.ctlr.interact('CONSTANT SET?,AIR,C%d' % constant).split('/')
        else: 
            raise ValueError("Constant must be None or 1, 2, 3") 
        return {'selected':int(selected), 'options':range(1, int(options)+1)}

    def read_constant_temp(self, constant=1):
        '''
        Get the constant settings for the temperature loop

        returns:
            {"setpoint":float,"enable":True}
        '''
        if constant in [1, 2, 3]:
            rsp = self.ctlr.interact('CONSTANT SET?,TEMP,C%d' % constant).split(',')
        else:
            raise ValueError("Constant must be None or 1, 2, 3")
        return {'setpoint':float(rsp[0]), 'enable':rsp[1] == 'ON'}

    def read_constant_humi(self, constant=1):
        '''
        Get the constant settings for the humidity loop

        returns:
            {"setpoint":float,"enable":boolean}
        '''
        if constant in [1, 2, 3]:
            rsp = self.ctlr.interact('CONSTANT SET?,HUMI,C%d' % constant).split(',')
        else: 
            raise ValueError("Constant must be None or 1, 2, 3")
        return {'setpoint':float(rsp[0]), 'enable':rsp[1] == 'ON'}

    def read_constant_ref(self, constant=1):
        '''
        Get the constant settings for the refrigeration system

        returns:
            {"mode":string,"setpoint":float}
        '''
        if constant in [1, 2, 3]:
            rsp = self.ctlr.interact('CONSTANT SET?,REF,C%d' % constant)
        else: 
            raise ValueError("Constant must be None or 1, 2, 3")
        try:
            return {'mode':'manual', 'setpoint':float(rsp)}
        except Exception:
            return {'mode':rsp.lower(), 'setpoint':0}

    def read_constant_relay(self, constant=1):
        '''
        Get the constant settings for the relays(time signals)

        returns:
            [int]
        '''
        if constant in [1, 2, 3]:
            rsp = self.ctlr.interact('CONSTANT SET?,RELAY,C%d' % constant).split(',')
        else: 
            raise ValueError("Constant must be None or 1, 2, 3")
        return [str(i) in rsp[1:] for i in range(1, 13)]

    def read_constant_ptc(self, constant=1):
        '''
        Get the constant settings for product temperature control

        returns:
            {"enable":boolean,"deviation":{"positive":float,"negative":float}}
        '''
        if constant in [1, 2, 3]:
            rsp = self.ctlr.interact('CONSTANT SET?,PTC,C%d' % constant).split(',')
        else: 
            raise ValueError("Constant must be None or 1, 2, 3")
        return {
            'enable': rsp[0] == 'ON',
            'deviation': {'positive':float(rsp[1]), 'negative':float(rsp[2])}
        }

    def read_prgm(self, pgmnum, with_ptc=False):
        pgm = super(P300Extended, self).read_prgm(pgmnum, with_ptc)
        if pgmnum == 0 and self.enable_air_speed:
            pgm['steps'][0]['air'] = self.read_air()
        return pgm

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
        pdata = self.ctlr.interact('PRGM DATA?,%s:%d,CONSTANT' % (self.rom_pgm(pgmnum), pgmnum))
        return self.parse_prgm_data(pdata)

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
                "relay":[int],
                "air":{"selected":int, "options":[int]}
            }
        '''
        cmd = 'PRGM DATA?,%s:%d,STEP%d'
        if self.enable_air_speed:
            cmd += ',AIR'
        tmp = self.ctlr.interact(cmd % (self.rom_pgm(pgmnum), pgmnum, pgmstep))
        return self.parse_prgm_data_step(tmp)

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
            "END"="OFF" or "CONSTANT1" or "CONSTANT2" or "CONSTANT3" or "STANDBY" or "RUN"
        '''
        pdata = self.ctlr.interact('PRGM DATA PTC?,%s:%d,CONSTANT' % (self.rom_pgm(pgmnum), pgmnum))
        return self.parse_prgm_data(pdata)

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
                "relay":[int],
                "air":{"selected":int, "options":[int]}
            }
        '''
        cmd = 'PRGM DATA PTC?,%s:%d,STEP%d'
        if self.enable_air_speed:
            cmd += ',AIR'
        tmp = self.ctlr.interact(cmd % (self.rom_pgm(pgmnum), pgmnum, pgmstep))
        return self.parse_prgm_data_step(tmp)

    def read_run_prgm(self):
        '''
        get the settings for the remote program being run

        returns:
            {
                "temperature":{"start":float,"end":float},"humidity":{"start":float,"end":float},
                "time":{"hours":int,"minutes":int},"refrig":{"mode":string,"setpoint":}
            }
        '''
        rsp = self.ctlr.interact('RUN PRGM?' + ',AIR' if self.enable_air_speed else '')
        parsed = re.search(
            r'TEMP([0-9.-]+) GOTEMP([0-9.-]+)(?: HUMI(\d+) GOHUMI(\d+))? TIME(\d+):(\d+) (\w+)'
            r'(?: RELAYON,([0-9,]+))?(?: AIR(\d+)\/(\d+))?',
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
        if parsed.group(9):
            ret['air'] = {
                'selected':int(parsed.group(9)),
                'options':range(1, int(parsed.group(10))+1)
            }

    def read_timer_list_quick(self):
        '''
        Read the timer settings for the quick timer(timer 0)

        returns:
            {"mode":string, "time":{"hour":int, "minute":int}, "pgmnum":int, "pgmstep":int}
            "mode"="STANDBY" or "OFF" or "CONSTANT1" or "CONSTANT2" or "CONSTANT3" or "RUN"
            "pgmnum" and "pgmstep" only present when mode=="RUN"
        '''
        parsed = re.search(
            r"(\w+)(?:,R[AO]M:(\d+),STEP(\d+))?,(\d+):(\d+)",
            self.ctlr.interact('TIMER LIST?,0,CONSTANT')
        ) 
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
            "mode"="CONSTANT1" or "CONSTANT2" or "CONSTANT3" or "RUN"
            "date" only present when "repeat"=="once"
            "pgmnum" and "step" only present when "mode"=="RUN"
            "days" only present when "repeat"=="weekly"
        '''
        parsed = re.search(
            r"1,MODE(\d)(?:,(\d+).(\d+)/(\d+))?(?:,([A-Z/]+))?,(\d+):(\d+),(\w+[123])",
            self.ctlr.interact('TIMER LIST?,1,CONSTANT')
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

    def write_mode_constant(self, constant=1):
        '''
        Run a constant setpoint

        Args:
            constant: int, the constant mode to write to; valid range of 1 to 3; 1 is default
        '''
        if constant in [1, 2, 3]:
            self.ctlr.interact('MODE,CONSTANT,C%d' % constant)
        else:
            raise ValueError("Constant must be None or 1, 2 or 3")

    def write_temp(self, **kwargs):
        '''
        update the temperature parameters

        Args:
            setpoint: float
            max: float
            min: float
            range: {"max":float, "min":float}
            constant: int, the constant mode to write to; valid range of 1 to 3; 1 is default
        '''
        setpoint, maximum, minimum = kwargs.get('setpoint'), kwargs.get('max'), kwargs.get('min')
        constant = kwargs.get('constant', 1)
        if setpoint is not None and minimum is not None and maximum is not None:
            cmd = 'TEMP, S%0.1f H%0.1f L%0.1f, C%d'
            self.ctlr.interact(cmd % (setpoint, maximum, minimum, constant))
        else:
            if setpoint is not None:
                self.ctlr.interact('TEMP, S%0.1f, C%d' % (setpoint, constant))
            if minimum is not None:
                self.ctlr.interact('TEMP, L%0.1f, C%d' % (minimum, constant))
            if maximum is not None:
                self.ctlr.interact('TEMP, H%0.1f, C%d' % (maximum, constant))

    def write_humi(self, **kwargs):
        '''
        update the humidity parameters

        Args:
            enable: boolean
            setpoint: float
            max: float
            min: float
            range: {"max":float,"min":float}
            constant: int, the constant mode to write to; valid range of 1 to 3; 1 is default
        '''
        setpoint, maximum, minimum = kwargs.get('setpoint'), kwargs.get('max'), kwargs.get('min')
        enable, constant = kwargs.get('enable'), kwargs.get('constant', 1)
        if enable is False:
            spstr = 'SOFF'
        elif setpoint is not None:
            spstr = ' S%0.1f' % setpoint
        else:
            spstr = None
        if spstr is not None and minimum is not None and maximum is not None:
            self.ctlr.interact('HUMI,%s H%0.1f L%0.1f, C%d' % (spstr, maximum, minimum, constant))
        else:
            if spstr is not None:
                self.ctlr.interact('HUMI,%s, C%d' % (spstr, constant))
            if minimum is not None:
                self.ctlr.interact('HUMI, L%0.1f, C%d' % (minimum, constant))
            if maximum is not None:
                self.ctlr.interact('HUMI, H%0.1f, C%d' % (maximum, constant))

    def write_relay(self, relays, constant=1):
        '''
        set each relay(time signal)

        Args:
            relays: [boolean] True=turn relay on, False=turn relay off, None=do nothing
            constant: int, the constant mode to write to; valid range of 1 to 3; 1 is default
        '''
        vals = self.parse_relays(relays)
        cmd = 'RELAY,%s,%s,C%d'
        if len(vals['on']) > 0:
            self.ctlr.interact(cmd % ('ON', ','.join(str(v) for v in vals['on']), constant))
        if len(vals['off']) > 0:
            self.ctlr.interact(cmd % ('OFF', ','.join(str(v) for v in vals['off']), constant))

    def write_set(self, mode, setpoint=0, constant=1):
        '''
        Set the constant setpoints refrig mode

        Args:
            mode: string,"off" or "manual" or "auto"
            setpoint: int,20 or 50 or 100
            constant: int, the constant mode to write to; valid range of 1 to 3; 1 is default
        '''
        self.ctlr.interact('SET,%s,C%d' % (self.encode_refrig(mode, setpoint), constant))

    def write_temp_ptc(self, enable, positive, negative, constant=1):
        '''
        set product temperature control settings

        Args:
            enable: boolean, True(on)/False(off)
            positive: float, maximum positive deviation
            negative: float, maximum negative deviation
            constant: int, the constant mode to write to; valid range of 1 to 3; 1 is default
        '''
        ttp = ('ON' if enable else 'OFF', positive, negative, constant)
        self.ctlr.interact('TEMP PTC, PTC%s, DEVP%0.1f, DEVN%0.1f, C%d' % ttp)

    def write_air(self, value, constant=1):
        '''
        Set the selected air speed value and the options values for the specified constant mode.

        Args:
            constant: int, the constant mode to write to; valid range of 1 to 3; 1 is default
            value: int, the selected air speed read_air()["options"] will give the allowable values
        '''
        if constant in [1, 2, 3]:
            self.ctlr.interact('AIR,%d,C%d' % (value, constant))
        else:
            raise ValueError("Constant must be None or 1, 2, 3")

    def write_prgm_data_step(self, pgmnum, **pgmstep):
        '''
        write a program step to the controller

        Args:
            pgmnum: int, the program being written/edited
            pgmstep: the program parameters, see read_prgm_data_step for parameters
        '''
        cmd = 'PRGM DATA WRITE,PGM%d,STEP%d' % (pgmnum, pgmstep['number'])
        if 'temperature' in pgmstep:
            if 'setpoint' in pgmstep['temperature']:
                cmd = '%s,TEMP%0.1f' % (cmd, pgmstep['temperature']['setpoint'])
            if 'ramp' in pgmstep['temperature']:
                cmd = '%s,TRAMP%s' % (cmd, 'ON' if pgmstep['temperature']['ramp'] else 'OFF')
            if 'enable_cascade' in pgmstep['temperature']:
                cmd = '%s,PTC%s'%(cmd, 'ON' if pgmstep['temperature']['enable_cascade'] else 'OFF')
            if 'deviation' in pgmstep['temperature']:
                ttp = (cmd, pgmstep['temperature']['deviation']['positive'],
                       pgmstep['temperature']['deviation']['negative'])
                cmd = '%s,DEVP%0.1f,DEVN%0.1f' % ttp
        if 'humidity' in pgmstep:
            if 'setpoint' in pgmstep['humidity']:
                if pgmstep['humidity']['enable']:
                    htmp = '%0.0f' % pgmstep['humidity']['setpoint']
                else:
                    htmp = 'OFF'
                cmd = '%s,HUMI%s' % (cmd, htmp)
            if 'ramp' in pgmstep['humidity'] and pgmstep['humidity']['enable']:
                cmd = '%s,HRAMP%s' % (cmd, 'ON' if pgmstep['humidity']['ramp'] else 'OFF')
        if 'time' in pgmstep:
            cmd = '%s,TIME%d:%d' % (cmd, pgmstep['time']['hour'], pgmstep['time']['minute'])
        if 'granty' in pgmstep:
            cmd = '%s,GRANTY %s' % (cmd, 'ON' if pgmstep['granty'] else 'OFF')
        if 'paused' in pgmstep:
            cmd = '%s,PAUSE %s' % (cmd, 'ON' if pgmstep['paused'] else 'OFF')
        if 'refrig' in pgmstep:
            cmd = '%s,%s' % (cmd, self.encode_refrig(**pgmstep['refrig']))
        if 'relay' in pgmstep:
            rlys = self.parse_relays(pgmstep['relay'])
            if rlys['on']:
                cmd = '%s,RELAY ON%s' % (cmd, '.'.join(str(v) for v in rlys['on']))
            if rlys['off']:
                cmd = '%s,RELAY OFF%s' % (cmd, '.'.join(str(v) for v in rlys['off']))
        if 'air' in pgmstep:
            if isinstance(pgmstep['air'], dict):
                cmd = '%s,AIR%d' % (cmd, pgmstep['air']['selected'])
            else:
                cmd = '%s,AIR%d' % (cmd, pgmstep['air'])
        self.ctlr.interact(cmd)

    def write_run_prgm(self, temp, hour, minute, gotemp=None, humi=None, gohumi=None, relays=None, air=None):
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
            air: int, selector for the air speed.
        '''
        cmd = 'RUN PRGM, TEMP%0.1f TIME%d:%d' % (temp, hour, minute)
        if gotemp is not None:
            cmd = '%s GOTEMP%0.1f' % (cmd, gotemp)
        if humi is not None:
            cmd = '%s HUMI%0.0f' % (cmd, humi)
        if gohumi is not None:
            cmd = '%s GOHUMI%0.0f' % (cmd, gohumi)
        rlys = self.parse_relays(relays) if relays is not None else {'on':None, 'off':None}
        if rlys['on']:
            cmd = '%s RELAYON,%s' % (cmd, ','.join(str(v) for v in rlys['on']))
        if rlys['off']:
            cmd = '%s RELAYOFF,%s' % (cmd, ','.join(str(v) for v in rlys['off']))
        if air is not None:
            cmd = '%s AIR%d' % (cmd, air)
        self.ctlr.interact(cmd)

    def write_prgm_end(self, mode="STANDBY"):
        '''
        stop the running program

        Args:
            mode: string, vaid options: "HOLD"/"CONST"/"CONST1"/"CONST2"/"CONST3"/"OFF"/"STANDBY"
        '''
        if mode in ["HOLD", "CONST", "CONST1", "CONST2", "CONST3", "OFF", "STANDBY"]:
            self.ctlr.interact('PRGM,END,%s' % mode)
        else:
            raise ValueError('"mode" must be "HOLD"/"CONST"/"CONST1"/"CONST2"/"CONST3"/"OFF"/"STANDBY"')

    # --- helpers etc --- helpers etc --- helpers etc --- helpers etc -- helpers etc -- helpers etc
    def parse_prgm_data_step(self, arg):
        '''
        Parse a program step
        '''
        parsed = re.search(
            r'(\d+),TEMP([0-9.-]+),TEMP RAMP (\w+)(?:,PTC (\w+))?(?:,HUMI([^,]+)'
            r'(?:,HUMI RAMP (\w+))?)?,TIME(\d+):(\d+),GRANTY (\w+),REF(\w+)'
            r'(?:,RELAY ON([0-9.]+))?(?:,PAUSE (\w+))?(?:,DEVP([0-9.-]+),DEVN([0-9.-]+))?'
            r'(?:,AIR(\d+)\/(\d+))?',
            arg
        )
        base = {
            'number':int(parsed.group(1)),
            'time':{
                'hour':int(parsed.group(7)),
                'minute':int(parsed.group(8))
            },
            'paused':parsed.group(12) == 'ON',
            'granty':parsed.group(9) == 'ON',
            'refrig':self.reflookup.get(
                'REF' + parsed.group(10),
                {'mode':'manual', 'setpoint':0}
            ),
            'temperature':{
                'setpoint':float(parsed.group(2)),
                'ramp':parsed.group(3) == 'ON'
            }
        }
        if parsed.group(5): # humidity settings
            base['humidity'] = {
                'setpoint':tryfloat(parsed.group(5), 0.0),
                'enable':parsed.group(5) != ' OFF',
                'ramp':parsed.group(6) == 'ON'
            }
        if parsed.group(4): # ptcon settings
            base['temperature'].update({
                'enable_cascade':parsed.group(4) == 'ON',
                'deviation': {
                    'positive':float(parsed.group(13)),
                    'negative':float(parsed.group(14))
                }
            })
        if parsed.group(11): # relay settings
            relays = parsed.group(11).split('.')
            base['relay'] = [str(i) in relays for i in range(1, 13)]
        else:
            base['relay'] = [False for i in range(1, 13)]
        if parsed.group(15): # air speed settings
            base['air'] = {
                'selected':int(parsed.group(15)),
                'options':range(1, int(parsed.group(16))+1)
            }
        return base
