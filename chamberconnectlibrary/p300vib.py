'''
A direct implementation of the SCP220's communication interface.

:copyright: (C) Espec North America, INC.
:license: MIT, see LICENSE for more details.
'''
import re
import time
from especinteract import EspecError
from p300extended import P300Extended, tryfloat

class P300Vib(P300Extended):
    '''
    This is the basic implementation for communications with the P300
    with vibration feature.

    Most of its standard features are inherited from the superclass, standard P300.

    Args:
        interface (str): The interface type to connect to: "Serial" or "TCP"
    Kwargs:
        serialport (str/int): The serial port to connect to when interface="Serial"
        baudrate (int): The baud rate to connect at when interface="Serial"
        address (int): The RS485 address of the chamber to connect to.
        host (str): The IP address or hostname of the chamber when interface="TCP"
    '''

    def read_vib(self):
        '''
        Read and return vibration values

        returns:
            { 'processvalue': float,
              'setpoint': float,
              'enable': boolean,
              'range': {'max': float, 'min': float}
            }
        '''
        rsp = self.ctlr.interact('VIB?').split(',')
        try:
            hsp = float(rsp[1])
            enable = True
        except Exception:
            hsp = 0
            enable = False
        return {
            'processvalue': float(rsp[0]),
            'setpoint': hsp,
            'enable': enable,
            'range': { 'max': float(rsp[2]), 'min': float(rsp[3]) }
        }

    def read_mon(self, detail=False, constant=False):
        '''
        Returns the conditions inside the chamber

        Args:
            detail: boolean, when True "mode" parameter has additional details
        returns:
            {"temperature":float,"vibration":float,"mode":string,"alarms":int}
            "vibration": only present if chamber has vibration
            "mode": see read_mode for valid parameters (with and without detail flag).
        '''
        if constant:
            rsp = self.ctlr.interact('MON?,DETAIL,CONSTANT').split(',')
        else:
            rsp = self.ctlr.interact('MON?%s%s' % (',DETAIL' if detail else '', ',CONSTANT' if constant else '')).split(',')
        data = {'temperature':float(rsp[0]), 'mode':rsp[2], 'alarms':int(rsp[3])}

        rsp = self.ctlr.interact('MON?,EXT1').split(',')
        if rsp[1]:
            data['vibration'] = float(rsp[1])
        return data

    def read_htr(self):
        '''
        Read the heater outputs and number of controllable heaters.

        returns:
            {
                'dry': float,
                'vib': float,
                'vib' is only present with vibration chambers
            }
        '''
        rsp = self.ctlr.interact('%?,EXT1').split(',')
        if len(rsp) == 3:
            return {
                'dry': float(rsp[1]),
                'vib': float(rsp[2])
            }
        else:
            return { 'dry': float(rsp[1]) }

    def read_constant_vib(self, constant=1):
        '''
        Read the constant settings for vibration loop.

        returns:
        {
            'setpoint': float,
            'enable': string
        }
        '''
        if constant in [1, 2, 3]:
            rsp = self.ctlr.interact('CONSTANT SET?, VIB, C{0:d}'.format(constant)).split(',')
        else:
            raise ValueError("Constant must be None or 1, 2, 3.")
        return {'setpoint': float(rsp[0]), 'enable': rsp[1] == 'ON'}

    def read_prgm_mon(self):
        '''
        Read status of running program

        Parameters:
            'pgmstep': int,
            'temperature': float,
            'vibration': float,
            'time':{'hour':int, 'minute':int},
            'counter_a': int,
            'counter_b': int

            Note: 'humidity' is only available on chambers having that feature.
            This means that for chambers with temperature and humidity, return
            parameters will be six. Chambers without humidity will return
            five parameters. Thus, two types of chambers are those with
            temperature and vibration, temperature and humidity.
        '''
        rsp = self.ctlr.interact('PRGM MON?,EXT1').split(',')
        if len(rsp) == 6:
            time = rsp[3].split(':')
            return {
                'pgmstep': int(rsp[0]),
                'temperature': float(rsp[1]),
                'vibration': tryfloat(rsp[2], 0),
                'time': { 'hour': int(time[0]), 'minute': int(time[1]) },
                'counter_a': int(rsp[4]),
                'counter_b': int(rsp[5])
            }
        else:
            time = rsp[2].split(':')
            return {
                'pgmstep': int(rsp[0]),
                'temperature': float(rsp[1]),
                'time': { 'hour': int(time[0]), 'minute': int(time[1]) },
                'counter_a': int(rsp[3]),
                'counter_b': int(rsp[4])
            }

    def read_prgm_data_step(self, pgmnum, pgmstep):
        '''
        get a programs step parameters and air feature

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
                "vibration":{"setpoint":float, "enable":boolean, "ramp":boolean},
                "relay":[int]
            }
        '''
        cmd = 'PRGM DATA?,{0}:{1:d},STEP{2:d}'.format(self.rom_pgm(pgmnum), pgmnum, pgmstep)
        rtrn = self.parse_prgm_data_step(self.ctlr.interact(cmd + ',EXT1'))
        if self.enable_air_speed:
            rtrn['air'] = self.parse_prgm_data_step(self.ctlr.interact(cmd + ',AIR'))['air']
        return rtrn

    def read_prgm_data_ptc_step(self, pgmnum, pgmstep):
        data = self.read_prgm_data_step(pgmnum, pgmstep)
        data.update(super(P300Vib, self).read_prgm_data_ptc_step(pgmnum, pgmstep))
        return data

    def parse_prgm_data_step(self, arg):
        '''
        Parse the program parameters with vibration feature
        '''
        parsed = re.search(
            r'(\d+),TEMP([0-9.-]+),TEMP RAMP (\w+)(?:,PTC (\w+))?(?:,VIB([^,]+)'
            r'(?:,VIB RAMP (\w+))?)?,TIME(\d+):(\d+),GRANTY (\w+),REF(\w+)'
            r'(?:,RELAY ON([0-9.]+))?(?:,PAUSE (\w+))?(?:,DEVP([0-9.-]+),DEVN([0-9.-]+))?'
            r'(?:,AIR(\d+)\/(\d+))?',
            arg
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
            base['vibration'] = {
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
        if parsed.group(15): # air speed settings
            base['air'] = {
                'selected':int(parsed.group(15)),
                'options':range(1, int(parsed.group(16))+1)
            }
        return base

    def read_prgm_data_detail(self, pgmnum):
        '''
        get the conditions a program will start with and its operational range

        Args:
            pgmnum: int, the program to get
        returns:
            {
                "temperature":{"range":{"max":float, "min":float},"mode":string,"setpoint":float},
                "vibration":{"range":{"max":float,"min":float},"mode":string,"setpoint":float}
            }
        '''
        pdata = self.ctlr.interact('PRGM DATA?,{0}:{1:d},DETAIL,EXT1'.format( self.rom_pgm(pgmnum),
            pgmnum))
        return self.parse_prgm_data_detail(pdata) # need to write parse def

    def read_prgm_data_ptc_detail(self, pgmnum):
        return self.read_prgm_data_detail(pgmnum)

    def parse_prgm_data_detail(self, arg):
        '''
        Parse the program data command with details flag
        '''
        parsed = re.search(
            r'([0-9.-]+),([0-9.-]+),([0-9.-]+),([0-9.-]+),TEMP(\w+)'
            r'(?:,([0-9.-]+))?,VIB(\w+)(?:,([0-9.-]+))?',
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
            ret['vibDetail'] = {
                'range':{'max':float(parsed.group(3)), 'min':float(parsed.group(4))},
                'mode':parsed.group(7),
                'setpoint':parsed.group(8)
            }
        return ret

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
            tmp = ('PRGM DATA WRITE,PGM{0:d},COUNT,A({1:d}.{2:d}.{3:d})'.format(*ttp))
            if 'counter_b' in pgmdetail and pgmdetail['counter_b']['cycles'] > 0:
                ttp = (tmp, pgmdetail['counter_b']['start'], pgmdetail['counter_b']['end'],
                       pgmdetail['counter_b']['cycles'])
                #tmp = '%s,B(%d.%d.%d)' % ttp
                tmp = ('{0:s},B({1:d}.{2:d}.{3:d})'.format(*ttp))
            self.ctlr.interact(tmp)
        elif 'counter_b' in pgmdetail and pgmdetail['counter_b']['cycles'] > 0:
            ttp = (pgmnum, pgmdetail['counter_b']['start'], pgmdetail['counter_b']['end'],
                   pgmdetail['counter_b']['cycles'])
            self.ctlr.interact('PRGM DATA WRITE,PGM{0:d},COUNT,B({1:d}.{2:d}.{3:d})'.format(*ttp))
        if 'name' in pgmdetail:
            self.ctlr.interact('PRGM DATA WRITE,PGM{0:d},NAME,{1:s}'.format(pgmnum, pgmdetail['name']))

        if 'end' in pgmdetail:
            if pgmdetail['end'] != 'RUN':
                ttp = (pgmnum, pgmdetail['end'])
            else:
                ttp = (pgmnum, 'RUN,PTN{0:d}'.format(pgmdetail['next_prgm']))
            self.ctlr.interact('PRGM DATA WRITE,PGM{0:d},END,{1:s}'.format(*ttp))

        if 'tempDetail' in pgmdetail:
            if 'range' in pgmdetail['tempDetail']:
                ttp = (pgmnum, pgmdetail['tempDetail']['range']['max'])
                self.ctlr.interact('PRGM DATA WRITE,PGM{0:d},HTEMP,{1:0.1f}'.format(*ttp))
                ttp = (pgmnum, pgmdetail['tempDetail']['range']['min'])
                self.ctlr.interact('PRGM DATA WRITE,PGM{0:d},LTEMP,{1:0.1f}'.format(*ttp))
            if 'mode' in pgmdetail['tempDetail']:
                ttp = (pgmnum, pgmdetail['tempDetail']['mode'])
                self.ctlr.interact('PRGM DATA WRITE,PGM{0:d},PRE MODE,TEMP,{1:s}'.format(*ttp))
            if 'setpoint' in pgmdetail['tempDetail'] and pgmdetail['tempDetail']['mode'] == 'SV':
                ttp = (pgmnum, pgmdetail['tempDetail']['setpoint'])
                (td, tsetp) = ttp   # splitting a tuple of mixed data type into individual arguments
                self.ctlr.interact('PRGM DATA WRITE,PGM{0:d},PRE TSV,{1:0.1f}'.format(td, float(tsetp)) )
                # self.ctlr.interact('PRGM DATA WRITE,PGM{0:d},PRE TSV,{1:0.1f}'.format(*ttp))

        if 'vibDetail' in pgmdetail:
            if 'range' in pgmdetail['vibDetail']:
                ttp = (pgmnum, pgmdetail['vibDetail']['range']['max'])
                self.ctlr.interact('PRGM DATA WRITE,PGM{0:d},HVIB,{1:0.1f}'.format(*ttp))
                ttp = (pgmnum, pgmdetail['vibDetail']['range']['min'])
                self.ctlr.interact('PRGM DATA WRITE,PGM{0:d},LVIB,{1:0.1f}'.format(*ttp))
            if 'mode' in pgmdetail['vibDetail']:
                ttp = (pgmnum, pgmdetail['vibDetail']['mode'])
                self.ctlr.interact('PRGM DATA WRITE,PGM{0:d},PRE MODE,VIB,{1:s}'.format(*ttp))
            if 'setpoint' in pgmdetail['vibDetail'] and pgmdetail['vibDetail']['mode'] == 'SV':
                ttp = (pgmnum, pgmdetail['vibDetail']['setpoint'])
                (vd, vsetp) = ttp  # splitting a tuple of mixed data type into individual arguments 
                self.ctlr.interact('PRGM DATA WRITE,PGM{0:d},PRE VSV,{1:0.1f}'.format(vd, float(vsetp)) )

    def write_prgm_data_step(self, pgmnum, **pgmstep):
        '''
        write a program step includiong vibration feature to the controller

        Args:
            pgmnum: int, the program being written/edited
            pgmstep: the program parameters, see read_prgm_data_step for parameters
        '''
        cmd = ('PRGM DATA WRITE,PGM{0:d},STEP{1:d}'.format(pgmnum, pgmstep['number']))
        if 'time' in pgmstep:
            cmd = '{0:s},TIME{1:d}:{2:d}'.format(cmd, pgmstep['time']['hour'], pgmstep['time']['minute'])
        if 'paused' in pgmstep:
            cmd = '{0:s},PAUSE {1:s}'.format(cmd, 'ON' if pgmstep['paused'] else 'OFF')
        if 'air' in pgmstep:
            if isinstance (pgmstep['air'], dict): # added to test...
                cmd = '{0:s},AIR{1:d}'.format(cmd, pgmstep['air']['selected'])
            else:
                cmd = '{0:s},AIR{1:d}'.format(cmd, pgmstep['air'])
        if 'refrig' in pgmstep:
            cmd = '{0:s},{1:s}'.format(cmd, self.encode_refrig(**pgmstep['refrig']))
        if 'granty' in pgmstep:
            cmd = '{0:s},GRANTY {1:s}'.format(cmd, 'ON' if pgmstep['granty'] else 'OFF')
        if 'temperature' in pgmstep:
            if 'setpoint' in pgmstep['temperature']:
                cmd = '{0:s},TEMP{1:0.1f}'.format(cmd, pgmstep['temperature']['setpoint'])
            if 'ramp' in pgmstep['temperature']:
                cmd = ('{0:s},TRAMP{1:s}'
                    .format(cmd, 'ON' if pgmstep['temperature']['ramp'] else 'OFF'))
            if 'enable_cascade' in pgmstep['temperature']:
                cmd = ('{0:s},PTC{1:s}'
                .format(cmd, 'ON' if pgmstep['temperature']['enable_cascade'] else 'OFF'))
            if 'deviation' in pgmstep['temperature']:
                ttp = (cmd, pgmstep['temperature']['deviation']['positive'],
                       pgmstep['temperature']['deviation']['negative'])
                cmd = '{0:s},DEVP{1:0.1f},DEVN{2:0.1f}'.format(*ttp)

        if 'vibration' in pgmstep:
            if 'setpoint' in pgmstep['vibration']:
                if pgmstep['vibration']['enable']:
                    vtmp = '{0:0.1f}'.format(pgmstep['vibration']['setpoint'])
                else:
                    vtmp = 'OFF'
                cmd = '{0:s},VIB{1:s}'.format(cmd, vtmp)
            if 'ramp' in pgmstep['vibration'] and pgmstep['vibration']['enable']:
                cmd = '{0:s},VRAMP{1:s}'.format(cmd, 'ON' if pgmstep['vibration']['ramp'] else 'OFF')

        if 'relay' in pgmstep:
            rlys = self.parse_relays(pgmstep['relay'])
            if rlys['on']:
                cmd = '{0:s},RELAY ON{1:s}'.format(cmd, '.'.join(str(v) for v in rlys['on']))
            if rlys['off']:
                cmd = '{0:s},RELAY OFF{1:s}'.format(cmd, '.'.join(str(v) for v in rlys['off']))
        self.ctlr.interact(cmd)

    def write_prgm_erase(self, pgmnum):
        '''
        erase a program

        Args:
            pgmnum: int, the program to erase
        '''
        self.ctlr.interact('PRGM ERASE,{0:s}:{1:d}'.format(self.rom_pgm(pgmnum), pgmnum))

    def write_run_prgm(self, temp, hour, minute, gotemp=None, vib=None, govib=None, relays=None, air=None):
        '''
        Run a remote program (single step program)

        Args:
            temp: float, temperature to use at the start of the step
            hour: int, # of hours to run the step
            minute: int, # of minutes to run the step
            gotemp: float, temperature to end the step at(optional for ramping)
            vib: float, the humidity to use at the start of the step (optional)
            govib: float, the humidity to end the step at (optional for ramping)
            relays: [boolean], True= turn relay on, False=turn relay off, None=Do nothing
            air: int, # of air speed to provide to system to operate
        '''
        cmd = 'RUN PRGM, TEMP{0:0.1f} TIME{1:d}:{2:d}'.format(temp, hour, minute)
        if gotemp is not None:
            cmd = '{0:s} GOTEMP{1:0.1f}'.format(cmd, gotemp)
        if vib is not None:
            cmd = '{0:s} VIB{1:0.1f}'.format(cmd, vib)
        if govib is not None:
            cmd = '{0:s} GOVIB{1:0.1f}'.format(cmd, govib)
        rlys = self.parse_relays(relays) if relays is not None else {'on':None, 'off':None}
        if rlys['on']:
            cmd = '{0:s} RELAYON,{1:s}'.format(cmd, ','.join(str(v) for v in rlys['on']))
        if rlys['off']:
            cmd = '{0:s} RELAYOFF,{1:s}'.format(cmd, ','.join(str(v) for v in rlys['off']))
        if air is not None:
            cmd = '{0:s} AIR{1:d}'.format(cmd, air)
        self.ctlr.interact(cmd)

    def write_vib(self, **kwargs):
        '''
        update the vibration parameters

        Args:
            enable: boolean
            setpoint: float
            max: float
            min: float
            range: {"max":float,"min":float}
        '''
        setpoint, maximum, minimum = kwargs.get('setpoint'), kwargs.get('max'), kwargs.get('min')
        enable, constant = kwargs.get('enable'), kwargs.get('constant', 1)
        if enable is False:
            spstr = 'SOFF'
        elif setpoint is not None:
            # spstr = ' S%0.1f' % setpoint
            spstr = ('S{0:0.1f}'.format(setpoint))
        else:
            spstr = None

        try:
            time.sleep(0.1) # ensure P300 has had time to update after a wrte_temp_ptc
            ptc = self.read_temp_ptc()
        except EspecError:
            ptc = {'enable_cascade': False}

        if spstr is not None and minimum is not None and maximum is not None:
            self.ctlr.interact('VIB, {0:s} H{1:0.1f} L{2:0.1f},C{3:d}'.format(spstr, maximum, minimum, constant))
        else:
            if spstr is not None:
                self.ctlr.interact('VIB,%s, C%d' % (spstr, constant))
            if minimum is not None:
                self.ctlr.interact('VIB, L%0.1f, C%d' % (minimum, constant))
            if maximum is not None:
                self.ctlr.interact('VIB, H%0.1f, C%d' % (maximum, constant))
        if ptc['enable_cascade']:
            self.write_temp_ptc(ptc['enable_cascade'], ptc['deviation']['positive'], 0-ptc['deviation']['positive'], constant)


    def read_prgm(self, pgmnum, with_ptc=False):
        '''
        read an entire program helper method
        '''
        pgm = super(P300Vib, self).read_prgm(pgmnum, with_ptc)
        if pgmnum == 0:
            try:
                pgm['vibDetail'] = {
                    'mode':'OFF',
                    'setpoint':None,
                    'range':self.read_vib()['range']
                }
                pgm['steps'][0]['vibration'] = {'enable':False, 'ramp':False, 'setpoint':0.0}
            except Exception:
                pass
        return pgm
