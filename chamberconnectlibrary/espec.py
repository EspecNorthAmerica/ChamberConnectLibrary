'''
Upper level interface for Espec Corp. Controllers (just the P300 for now)

:copyright: (C) Espec North America, INC.
:license: MIT, see LICENSE for more details.
'''
#pylint: disable=R0902,R0904
import datetime
import time
from chamberconnectlibrary.controllerinterface import ControllerInterface, exclusive
from chamberconnectlibrary.controllerinterface import ControllerInterfaceError
from chamberconnectlibrary.p300 import P300
from chamberconnectlibrary.scp220 import SCP220
from chamberconnectlibrary.especinteract import EspecError

class Espec(ControllerInterface):
    '''
    A class for interfacing with Espec controllers (P300, SCP220)

    Kwargs:
        interface (str): The connection method::
            "TCP" -- Use a Ethernet to serial adapter with raw TCP
            "Serial" -- Use a hardware serial port
        adr (int): The address of the controller (default=1)
        host (str): The hostname (IP address) of the controller when interface="TCP"
        serialport (str): The serial port to use when interface="Serial" (default=3(COM4))
        baudrate (int): The serial port's baud rate to use when interface="Serial" (default=9600)
        loops (int): The number of control loops the controller has (default=1, max=2)
        cascades (int): The number of cascade control loops the controller has (default=0, max=1)
        lock (RLock): The locking method to use when accessing the controller (default=RLock())
        freshness (int): The length of time (in seconds) a command is cached (default = 0)
        ctlr_type (str): "SCP220" or "P300" (default = "P300")
    '''

    def __init__(self, **kwargs):
        self.client, self.loops, self.cascades = None, None, None
        self.init_common(**kwargs)
        self.freshness = kwargs.get('freshness', 0)
        self.cache = {}
        self.temp, self.humi = 1, 2
        self.lpd = {
            'temp':self.temp,
            'humi':self.humi,
            'temperature':self.temp,
            'humidity':self.humi,
            'Temperature':self.temp,
            'Humidity':self.humi,
            self.temp:self.temp,
            self.humi:self.humi
        }
        self.ctlr_type = kwargs.get('ctlr_type', 'P300')
        ttp = (self.ctlr_type, self.temp, self.humi)
        self.lp_exmsg = 'The %s controller only supports 2 loops (%d:temperature,%d:humidity)'%ttp
        ttp = (self.ctlr_type, self.temp)
        self.cs_exmsg = 'The %s controller can only have loop %d as cascade' % ttp
        self.alarms = 27
        self.profiles = True
        self.events = 12
        self.total_programs = 40 if self.ctlr_type == 'P300' else 30
        self.__update_loop_map()


    def __update_loop_map(self):
        '''
        update the loop map.
        '''
        self.named_loop_map = {'Temperature':0, 'temperature':0, 'Temp':0, 'temp':0}
        self.loop_map = [{'type':'cascade', 'num':j+1} for j in range(self.cascades)]
        self.loop_map += [{'type':'loop', 'num':j+1} for j in range(self.loops)]
        if len(self.loop_map) > 1:
            self.named_loop_map = {'Humidity':1, 'humidity':1, 'Hum':1, 'hum':1}

    def connect(self):
        '''
        connect to the controller using the paramters provided on class initialization
        '''
        args = {'serialport':self.serialport, 'baudrate':self.baudrate, 'host':self.host,
                'address':self.adr}
        if self.ctlr_type == 'P300':
            self.client = P300(self.interface, **args)
        elif self.ctlr_type == 'SCP220':
            self.client = SCP220(self.interface, **args)
        else:
            raise ValueError('"%s" is not a supported controller type' % self.ctlr_type)

    def close(self):
        '''
        close the connection to the controller
        '''
        try:
            self.client.close()
        except AttributeError:
            pass
        self.client = None

    def cached(self, func, *args, **kwargs):
        '''
        The P300 returns multiple parameters with each command. The commands responses will be
        cached and cached responses returned if they are fresh enough (settable property)
        '''
        now = time.time()
        incache = func.__name__ not in self.cache
        if incache or (now - self.cache[func.__name__]['timestamp'] > self.freshness):
            self.cache[func.__name__] = {'timestamp':now, 'values':func(*args, **kwargs)}
        return self.cache[func.__name__]['values']

    @exclusive
    def raw(self, command):
        '''
        connect directly to the controller
        '''
        try:
            return self.client.interact(command)
        except EspecError as exc:
            emsg = str(exc)
            if 'The chamber did not respond in time' in emsg:
                return 'NA: SERIAL TIMEOUT'
            qps = [i for i, c in enumerate(emsg) if c == '"']
            return 'NA:' + emsg[qps[len(qps)-2]+1:qps[len(qps)-1]]

    @exclusive
    def get_refrig(self):
        return self.client.read_constant_ref()

    @exclusive
    def set_refrig(self, value):
        self.client.write_set(**value)

    @exclusive
    def set_loop(self, identifier, loop_type='loop', param_list=None, **kwargs):
        #cannot use the default controllerInterface version.
        lpfuncs = {
            'cascade':{
                'setpoint':self.set_cascade_sp,
                'setPoint':self.set_cascade_sp,
                'setValue':self.set_cascade_sp,
                'range':self.set_cascade_range,
                'enable':self.set_cascade_en,
                'deviation':self.set_cascade_deviation,
                'enable_cascade':self.set_cascade_ctl,
                'mode': self.set_cascade_mode},
            'loop':{
                'setpoint':self.set_loop_sp,
                'setPoint':self.set_loop_sp,
                'range':self.set_loop_range,
                'enable':self.set_loop_en,
                'mode':self.set_loop_mode
            }
        }
        if param_list is None:
            param_list = kwargs
        if isinstance(identifier, basestring):
            my_loop_map = self.loop_map[self.named_loop_map[identifier]]
            loop_number = my_loop_map['num']
            loop_type = my_loop_map['type']
        elif isinstance(identifier, (int, long)):
            loop_number = identifier
        else:
            raise ValueError(
                'invalid argument format, call w/: '
                'set_loop(int(identifier), str(loop_type), **kwargs) or '
                'get_loop(str(identifier), **kwargs)'
            )
        spt1 = 'setpoint' in param_list
        spt2 = 'setPoint' in param_list
        spt3 = 'setValue' in param_list
        if (spt1 or spt2 or spt3) and ('enable' in param_list or 'mode' in param_list):
            if 'enable' in param_list:
                enable = param_list.pop('enable')
                if isinstance(enable, dict):
                    enable = enable['constant']
            else:
                my_mode = param_list.pop('mode')
                if isinstance(my_mode, dict):
                    my_mode = my_mode['constant']
                enable = my_mode in ['On', 'ON', 'on']
            if spt1:
                spv = param_list.pop('setpoint')
            elif spt2:
                spv = param_list.pop('setPoint')
            else:
                spv = param_list.pop('setValue')
            if isinstance(spv, dict):
                spv = spv['constant']
            params = {'setpoint':spv, 'enable':enable}
            if range in param_list:
                params.update(param_list.pop('range'))
            if self.lpd[loop_number] == self.temp:
                self.client.write_temp(**params)
            elif self.lpd[loop_number] == self.humi:
                self.client.write_humi(**params)
            else:
                raise ValueError(self.lp_exmsg)
        if 'deviation' in param_list and 'enable_cascade' in param_list:
            if isinstance(param_list['enable_cascade'], dict):
                params = {'enable':param_list.pop('enable_cascade')['constant']}
            else:
                params = {param_list.pop('enable_cascade')}
            params.update(param_list.pop('deviation'))
            self.client.write_temp_ptc(**params)
        for key, val in param_list.items():
            params = {'value':val}
            params.update({'exclusive':False, 'N':loop_number})
            try:
                lpfuncs[loop_type][key](**params)
            except KeyError:
                pass

    @exclusive
    def get_datetime(self):
        temp = self.client.read_time()
        temp.update(self.client.read_date())
        return datetime.datetime(**temp)

    @exclusive
    def set_datetime(self, value):
        weekday = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'][value.weekday()]
        self.client.write_time(value.hour, value.minute, value.second)
        self.client.write_date(value.year, value.month, value.day, weekday)

    @exclusive
    def get_loop_sp(self, N):
        if N not in self.lpd:
            raise ValueError(self.lp_exmsg)
        if self.lpd[N] == self.temp:
            cur = self.cached(self.client.read_temp)['setpoint']
            con = self.cached(self.client.read_constant_temp)['setpoint']
        else:
            cur = self.cached(self.client.read_humi)['setpoint']
            con = self.cached(self.client.read_constant_humi)['setpoint']
        return {'constant':con, 'current':cur}

    @exclusive
    def set_loop_sp(self, N, value):
        value = value['constant'] if isinstance(value, dict) else value
        if self.lpd[N] == self.temp:
            self.client.write_temp(setpoint=value)
        elif self.lpd[N] == self.humi:
            self.client.write_humi(setpoint=value)
        else:
            raise ValueError(self.lp_exmsg)

    @exclusive
    def get_loop_pv(self, N):
        if self.lpd[N] == self.temp:
            return {'air':self.cached(self.client.read_temp)['processvalue']}
        elif self.lpd[N] == self.humi:
            return {'air':self.cached(self.client.read_humi)['processvalue']}
        else:
            raise ValueError(self.lp_exmsg)

    @exclusive
    def set_loop_range(self, N, value):
        if 'max' not in value or 'min' not in value:
            raise AttributeError('missing "max" or "min" property')
        if self.lpd[N] == self.temp:
            self.client.write_temp(min=value['min'], max=value['max'])
        elif self.lpd[N] == self.humi:
            self.client.write_humi(min=value['min'], max=value['max'])
        else: raise ValueError(self.lp_exmsg)

    @exclusive
    def get_loop_range(self, N):
        if self.lpd[N] == self.temp:
            return self.cached(self.client.read_temp)['range']
        elif self.lpd[N] == self.humi:
            return self.cached(self.client.read_humi)['range']
        else: raise ValueError(self.lp_exmsg)

    @exclusive
    def get_loop_en(self, N):
        if self.lpd[N] == self.temp:
            return {'constant':True, 'current':True}
        elif self.lpd[N] == self.humi:
            return {'current':self.cached(self.client.read_humi)['enable'],
                    'constant':self.cached(self.client.read_constant_humi)['enable']}
        else: raise ValueError(self.lp_exmsg)

    @exclusive
    def set_loop_en(self, N, value):
        value = value['constant'] if isinstance(value, dict) else value
        if self.lpd[N] == self.temp:
            pass
        elif self.lpd[N] == self.humi:
            if value:
                self.client.write_humi(
                    enable=True,
                    setpoint=self.cached(self.client.read_constant_humi)['setpoint']
                )
            else:
                self.client.write_humi(enable=False)
        else: raise ValueError(self.lp_exmsg)

    @exclusive
    def get_loop_units(self, N):
        if self.lpd[N] == self.temp:
            return u'\xb0C'
        elif self.lpd[N] == self.humi:
            return u'%RH'
        else:
            raise ValueError(self.lp_exmsg)

    @exclusive
    def set_loop_mode(self, N, value):
        value = value['constant'] if isinstance(value, dict) else value
        if N > 2:
            raise ValueError(self.lp_exmsg)
        if value in ['Off', 'OFF', 'off']:
            self.set_loop_en(N, False, exclusive=False)
        elif value in ['On', 'ON', 'on']:
            self.set_loop_en(N, True, exclusive=False)
        else:
            raise ValueError('Mode must be on or off, recived:' + value)

    @exclusive
    def get_loop_mode(self, N):
        if N > 2:
            raise ValueError(self.lp_exmsg)
        if self.lpd[N] == self.humi:
            cur = 'On' if self.cached(self.client.read_humi)['enable'] else 'Off'
            con = 'On' if self.cached(self.client.read_constant_humi)['enable'] else 'Off'
        else:
            cur = 'On'
            con = 'On'
        if self.client.read_mode() in ['OFF', 'STANDBY']:
            cur = 'Off'
        return {"current": cur, "constant": con}

    def get_loop_modes(self, N):
        if N == 1:
            return ['On']
        elif N == 2:
            return ['Off', 'On']
        else:
            raise ValueError(self.lp_exmsg)

    @exclusive
    def get_loop_power(self, N):
        if self.lpd[N] == self.temp:
            val = self.cached(self.client.read_htr)['dry']
        elif self.lpd[N] == self.humi:
            val = self.cached(self.client.read_htr)['wet']
        else:
            raise ValueError(self.lp_exmsg)
        return {'current':val, 'constant':val}

    def set_loop_power(self, N, value):
        raise NotImplementedError

    @exclusive
    def get_cascade_sp(self, N):
        if self.lpd[N] != self.temp:
            raise ValueError(self.cs_exmsg)
        cur = self.cached(self.client.read_temp_ptc)
        enc = cur['enable_cascade']
        return {
            'constant':self.cached(self.client.read_constant_temp)['setpoint'],
            'current':cur['setpoint']['product'] if enc else cur['setpoint']['air'],
            'air':cur['setpoint']['air'],
            'product':cur['setpoint']['product']
        }

    @exclusive
    def set_cascade_sp(self, N, value):
        value = value['constant'] if isinstance(value, dict) else value
        if self.lpd[N] != self.temp:
            raise ValueError(self.cs_exmsg)
        self.client.write_temp(setpoint=value)

    @exclusive
    def get_cascade_pv(self, N):
        if self.lpd[N] != self.temp:
            raise ValueError(self.cs_exmsg)
        return self.cached(self.client.read_temp_ptc)['processvalue']

    @exclusive
    def get_cascade_range(self, N):
        if self.lpd[N] != self.temp:
            raise ValueError(self.cs_exmsg)
        return self.get_loop_range(self.temp, exclusive=False)

    @exclusive
    def set_cascade_range(self, N, value):
        if self.lpd[N] != self.temp:
            raise ValueError(self.cs_exmsg)
        self.set_loop_range(self.temp, value, exclusive=False)

    @exclusive
    def get_cascade_en(self, N):
        if self.lpd[N] != self.temp:
            raise ValueError(self.cs_exmsg)
        return self.get_loop_en(self.temp, exclusive=False)

    @exclusive
    def set_cascade_en(self, N, value):
        value = value['constant'] if isinstance(value, dict) else value
        if self.lpd[N] != self.temp:
            raise ValueError(self.cs_exmsg)
        return self.set_loop_en(self.temp, value, exclusive=False)

    @exclusive
    def get_cascade_units(self, N):
        if self.lpd[N] != self.temp:
            raise ValueError(self.cs_exmsg)
        return self.get_loop_units(self.temp, exclusive=False)

    @exclusive
    def set_cascade_mode(self, N, value):
        value = value['constant'] if isinstance(value, dict) else value
        if self.lpd[N] != self.temp:
            raise ValueError(self.cs_exmsg)
        return self.set_loop_mode(N, value, exclusive=False)

    @exclusive
    def get_cascade_mode(self, N):
        if self.lpd[N] != self.temp:
            raise ValueError(self.cs_exmsg)
        return self.get_loop_mode(self.temp, exclusive=False)

    def get_cascade_modes(self, N):
        return self.get_loop_modes(N)

    @exclusive
    def get_cascade_ctl(self, N):
        if self.lpd[N] != self.temp:
            raise ValueError(self.cs_exmsg)
        return {
            'current': self.cached(self.client.read_temp_ptc)['enable_cascade'],
            'constant': self.cached(self.client.read_constant_ptc)['enable']
        }

    @exclusive
    def set_cascade_ctl(self, N, value):
        value = value['constant'] if isinstance(value, dict) else value
        if self.lpd[N] != self.temp:
            raise ValueError(self.cs_exmsg)
        params = self.cached(self.client.read_temp_ptc)
        params['deviation'].update({'enable':value})
        self.client.write_temp_ptc(**params['deviation'])

    @exclusive
    def get_cascade_deviation(self, N):
        if self.lpd[N] != self.temp:
            raise ValueError(self.cs_exmsg)
        return self.cached(self.client.read_constant_ptc)['deviation']

    @exclusive
    def set_cascade_deviation(self, N, value):
        if self.lpd[N] != self.temp:
            raise ValueError(self.cs_exmsg)
        if 'positive' not in value or 'negative' not in value:
            raise ValueError('value must contain "positive" and "negative" keys')
        self.client.write_temp_ptc(self.get_cascade_ctl(self.temp, exclusive=False), **value)

    @exclusive
    def get_cascade_power(self, N):
        if self.lpd[N] != self.temp:
            raise ValueError(self.cs_exmsg)
        return self.get_loop_power(self.temp, exclusive=False)

    @exclusive
    def set_cascade_power(self, N, value):
        raise NotImplementedError

    @exclusive
    def get_event(self, N):
        if N >= 13:
            raise ValueError('There are only 12 events')
        return {
            'current':self.cached(self.client.read_relay)[N-1],
            'constant':self.cached(self.client.read_constant_relay)[N-1]
        }

    @exclusive
    def set_event(self, N, value):
        value = value['constant'] if isinstance(value, dict) else value
        if N >= 13:
            raise ValueError('There are only 12 events')
        self.client.write_relay([value if i == N else None for i in range(1, 13)])

    @exclusive
    def get_status(self):
        if self.cached(self.client.read_mon)['alarms'] > 0:
            return 'Alarm'
        return {
            'OFF':'Off',
            'STANDBY':'Standby',
            'CONSTANT':'Constant',
            'RUN':'Program Running',
            'RUN PAUSE':'Program Paused',
            'RUN END HOLD':'Program End Hold',
            'RMT RUN':'Remote Program Running',
            'RMT RUN PAUSE':'Remote Program Paused',
            'RMT RUN END HOLD':'Remote Program End Hold'
        }[self.client.read_mode(True)]

    @exclusive
    def get_alarm_status(self):
        active = self.client.read_alarm()
        alarmlist = [0, 1, 2, 3, 6, 7, 8, 9, 10, 11, 12, 18, 19, 21, 22, 23, 26,
                     30, 31, 40, 41, 43, 46, 48, 50, 51, 99]
        inactive = [x for x in alarmlist if x not in active]
        return {'active':active, 'inactive':inactive}

    @exclusive
    def const_start(self):
        self.client.write_mode_constant()

    @exclusive
    def stop(self):
        self.client.write_mode_standby()

    @exclusive
    def prgm_start(self, N, step):
        self.client.write_prgm_run(N, step)

    @exclusive
    def prgm_pause(self):
        self.client.write_prgm_pause()

    @exclusive
    def prgm_resume(self):
        self.client.write_prgm_continue()

    @exclusive
    def prgm_next_step(self):
        self.client.write_prgm_advance()

    @exclusive
    def get_prgm_counter(self):
        prgm_set = self.client.read_prgm_set()
        prgm_data = self.client.read_prgm_data(prgm_set['number'])
        prgm_mon = self.client.read_prgm_mon()
        ret = [
            {'name':'A', 'remaining': prgm_mon['counter_a']},
            {'name':'B', 'remaining': prgm_mon['counter_b']},
        ]
        ret[0].update(prgm_data['counter_a'])
        ret[1].update(prgm_data['counter_b'])
        return ret

    @exclusive
    def get_prgm_cur(self):
        return self.cached(self.client.read_prgm_set)['number']

    @exclusive
    def get_prgm_cstep(self):
        return self.cached(self.client.read_prgm_mon)['pgmstep']

    @exclusive
    def get_prgm_cstime(self):
        rtime = self.cached(self.client.read_prgm_mon)['time']
        return '%d:%02d:00' % (rtime['hour'], rtime['minute'])

    @exclusive
    def get_prgm_time(self, pgm=None):
        if pgm is None:
            pgm = self.client.read_prgm(self.cached(self.client.read_prgm_set)['number'])
        pgms = self.cached(self.client.read_prgm_mon)

        #counter_a must be the inner counter or the only counter
        if (pgm['counter_a']['end'] >= pgm['counter_b']['end'] and \
           pgm['counter_a']['start'] <= pgm['counter_b']['start']) or \
           pgm['counter_a']['cycles'] == 0 and pgm['counter_b']['cycles'] != 0:
            pgm['counter_a'], pgm['counter_b'] = pgm['counter_b'], pgm['counter_a']
            pgms['counter_a'], pgms['counter_b'] = pgms['counter_b'], pgms['counter_a']
        cap = len(pgm['steps'])
        cap = cap*(pgm['counter_a']['cycles'] + 2) if pgm['counter_a']['cycles'] else cap
        cap = cap*(pgm['counter_b']['cycles'] + 2) if pgm['counter_b']['cycles'] else cap
        cap += 2

        cnta = pgms['counter_a']
        cntb = pgms['counter_b']
        cstp = pgms['pgmstep']-1
        tminutes = pgms['time']['hour']*60 + pgms['time']['minute']
        pcntb = cntb
        while cstp < len(pgm['steps']) and cap:
            cap -= 1
            if pgm['counter_a']['start'] == pgm['counter_b']['start'] and \
               pgm['counter_a']['cycles'] and pgm['counter_b']['cycles'] and \
               cstp == pgm['counter_b']['start']-1:
                if pcntb != cntb:
                    cnta = pgm['counter_a']['cycles']
            elif cstp == pgm['counter_b']['start']-1 and pgm['counter_b']['cycles']:
                cnta = pgm['counter_a']['cycles']
            if cstp == pgm['counter_a']['end']-1 and pgm['counter_a']['cycles'] and cnta:
                cstp = pgm['counter_a']['start']-1
                cnta -= 1
            elif cstp == pgm['counter_b']['end']-1 and pgm['counter_b']['cycles'] and cntb:
                cstp = pgm['counter_b']['start']-1
                pcntb = cntb
                cntb -= 1
            else:
                pcntb = cntb
                cstp += 1
            if cstp < len(pgm['steps']):
                tminutes += pgm['steps'][cstp]['time']['hour']*60 + \
                            pgm['steps'][cstp]['time']['minute']
        if cap == 0:
            raise RuntimeError('Calculating the total program time remaining aborted.')
        return "%d:%02d:00" % (int(tminutes/60), tminutes%60)

    @exclusive
    def get_prgm_name(self, N):
        return self.cached(self.client.read_prgm_data, N)['name']

    def set_prgm_name(self, N, value):
        raise NotImplementedError

    @exclusive
    def get_prgm_steps(self, N):
        return self.client.read_prgm_data(N)['steps']

    @exclusive
    def get_prgms(self):
        names = []
        for i in range(1, self.total_programs+1):
            try:
                names.append({'number':i, 'name':self.client.read_prgm_use_num(i)['name']})
            except EspecError:
                names.append({'number':i, 'name':''})
        return names

    @exclusive
    def get_prgm(self, N):
        try:
            return self.client.read_prgm(N, self.cascades > 0)
        except EspecError:
            raise ControllerInterfaceError('Could not read program from chamber controller.')

    @exclusive
    def set_prgm(self, N, prgm):
        self.client.write_prgm(N, prgm)

    @exclusive
    def prgm_delete(self, N):
        self.client.write_prgm_erase(N)

    @exclusive
    def sample(self, lookup=None):
        ltype = 'cascade' if self.cascades > 0 else 'loop'
        if ltype == 'loop':
            items = ['setpoint', 'processvalue', 'enable']
        else:
            items = ['setpoint', 'processvalue', 'enable', 'enable_cascade']
        loops = [self.get_loop(1, ltype, items, exclusive=False)]
        if lookup:
            loops[0].update(lookup[ltype][0])
        if self.loops + self.cascades > 1:
            tlst = ['setpoint', 'processvalue', 'enable']
            loops.append(self.get_loop(2, 'loop', tlst, exclusive=False))
            if lookup:
                loops[1].update(lookup['loop'][0 if ltype == 'cascade' else 1])
        return {
            'datetime':self.get_datetime(exclusive=False),
            'loops':loops,
            'status':self.get_status(exclusive=False)
        }

    @exclusive
    def process_controller(self, update=True):
        if update:
            self.loops = 0
            self.cascades = 0
        msg = 'P300 ' if self.client.read_rom().startswith('P3') else 'SCP-220 '
        try:
            if update:
                self.client.read_temp_ptc()
                self.cascades = 1
            msg += 'W/PTCON '
        except EspecError:
            if update:
                self.loops += 1
        try:
            if update:
                self.client.read_humi()
                self.loops += 1
            msg += 'W/Humidity'
        except EspecError:
            pass
        self.__update_loop_map()
        return msg

    @exclusive
    def get_network_settings(self):
        ret = self.client.read_ip_set()
        ret.update({'message':'', 'host':''})
        return ret

    @exclusive
    def set_network_settings(self, value):
        if value:
            self.client.write_ip_set(value.get('address', '0.0.0.0'),
                                     value.get('mask', '0.0.0.0'), value.get('gateway', '0.0.0.0'))
        else:
            self.client.write_ip_set('0.0.0.0', '0.0.0.0', '0.0.0.0')
