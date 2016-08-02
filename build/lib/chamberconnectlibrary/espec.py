'''
Upper level interface for Espec Corp. Controllers (just the P300 for now)

:copyright: (C) Espec North America, INC.
:license: MIT, see LICENSE for more details.
'''
import datetime, time
from controllerabstract import CtlrProperty, ControllerInterfaceError, exclusive
from p300 import *

class Espec(CtlrProperty):

    def __init__(self,**kwargs):
        self.init_common(**kwargs)
        self.freshness = kwargs.get('freshness',0)
        self.cache = {}
        self.temp,self.humi = 1,2
        self.lpd = {'temp':self.temp,'humi':self.humi,
                    'temperature':self.temp,'humidity':self.humi,
                    'Temperature':self.temp,'Humidity':self.humi,
                    self.temp:self.temp,self.humi:self.humi}
        self.loopExMsg = 'The P300 controller only supports 2 loops (%d:temperature,%d:humidity)' % (self.temp,self.humi)
        self.cascEsMsg = 'The P300 controller can only have loop %d as cascade' % self.temp
        self.alarms = 27
        self.profiles = True
        self.events = 12

    def connect(self):
        self.client = P300(self.interface,serialport=self.serialport,baudrate=self.baudrate,host=self.host)

    def close(self):
        self.client.cleanup()
        self.client = None

    def cached(self, func, *args, **kwargs):
        '''The P300 returns multiple parameters with each command. The commands responses will be cached and cached
        responses returned if they are fresh enough (settable property)'''
        now = time.time()
        if func.__name__ not in self.cache or (now - self.cache[func.__name__]['timestamp'] > self.freshness):
            self.cache[func.__name__] = {'timestamp':now,'values':func(*args,**kwargs)}
        return self.cache[func.__name__]['values']

    @exclusive
    def raw(self,command):
        try:
            return self.client.interact(command)
        except EspecError as e:
            emsg = str(e)
            if 'The chamber did not respond in time' in emsg:
                return 'NA: SERIAL TIMEOUT'
            qps = [i for i,c in enumerate(emsg) if c == '"']
            return 'NA:' + emsg[qps[len(qps)-2]+1:qps[len(qps)-1]]
    @exclusive
    def directRead(self,**kwargs):
        return self.client.interact(kwargs.get('register'))

    @exclusive
    def directWrite(self,**kwargs):
        return self.client.interact(kwargs.get('register'))

    @exclusive
    def get_loop(self,N,type,list=None):
        '''Get a loops parameters, takes a list of values to get'''
        loopFunctions = {'cascade':{'setpoint':self.get_cascade_sp,'setPoint':self.get_cascade_sp,'setValue':self.get_cascade_sp,
                                    'processvalue':self.get_cascade_pv,'processValue':self.get_cascade_pv,
                                    'range':self.get_cascade_range,
                                    'enable':self.get_cascade_en,
                                    'units':self.get_cascade_units,
                                    'mode':self.get_cascade_mode,
                                    'deviation':self.get_cascade_deviation,
                                    'enable_cascade':self.get_cascade_ctl},
                            'loop':{'setpoint':self.get_loop_sp,'setPoint':self.get_loop_sp,'setValue':self.get_loop_sp,
                                    'processvalue':self.get_loop_pv,'processValue':self.get_loop_pv,
                                    'range':self.get_loop_range,
                                    'enable':self.get_loop_en,
                                    'units':self.get_loop_units,
                                    'mode':self.get_loop_mode}}
        if list is None:
            list = loopFunctions[type].keys()
            list = [x for x in list if x not in ['setPoint','setValue','processValue']]
        return {key:loopFunctions[type][key](N,exclusive=False) if key in loopFunctions[type] else 'invalid key' for key in list}

    @exclusive
    def set_loop(self,N,type,list):
        '''apply loop parameters, requires a dictionary in the format: {function:namedAgrs}
        see loopFunctions for possible functions'''
        loopFunctions = {'cascade':{'setpoint':self.set_cascade_sp,'setPoint':self.set_cascade_sp,'setValue':self.set_cascade_sp,
                                    'range':self.set_cascade_range,
                                    'enable':self.set_cascade_en,
                                    'deviation':self.set_cascade_deviation,
                                    'enable_cascade':self.set_cascade_ctl},
                            'loop':{'setpoint':self.set_loop_sp,'setPoint':self.set_loop_sp,
                                    'range':self.set_loop_range,
                                    'enable':self.set_loop_en,}}
        if 'setpoint' in list and 'enable' in list:
            params = {'setpoint':list.pop('setpoint'),'enable':list.pop('enable')}
            if range in list:
                params.update(list.pop('range'))
            if self.lpd[N] == self.temp:
                self.client.write_temp(**params)
            elif self.lpd[N] == self.humi:
                self.client.write_humi(**params)
            else:
                raise ValueError(self.loopExMsg)
        if 'deviation' in list and 'enable_cascade' in list:
            if list['deviation']['negative'] > 0: list['deviation']['negative'] = 0 - list['deviation']['negative']
            params = {'enable':list.pop('enable_cascade')}
            params.update(list.pop('deviation'))
            self.client.write_tempPtc(**params)
        for k,v in list.items():
            params = {'value':v}
            params.update({'exclusive':False,'N':N})
            try: loopFunctions[type][k](**params)
            except KeyError: pass

    @exclusive
    def get_datetime(self):
        temp = self.client.read_time()
        temp.update(self.client.read_date())
        return datetime.datetime(**temp)

    @exclusive
    def set_datetime(self,value):
        self.client.write_time(value.hour, value.minute, value.second)
        self.client.write_date(value.year, value.month, value.day)

    @exclusive
    def get_loop_sp(self, N):
        if N not in self.lpd:
            raise ValueError(self.loopExMsg)
        cur = self.cached(self.client.read_temp)['setpoint'] if self.lpd[N] == self.temp else self.cached(self.client.read_humi)['setpoint']
        con = self.cached(self.client.read_constantTemp)['setpoint'] if self.lpd[N] == self.temp else self.cached(self.client.read_constantHumi)['setpoint']
        return {'constant':con,'current':cur}

    @exclusive
    def set_loop_sp(self, N, value):
        if self.lpd[N] == self.temp:
            self.client.write_temp(setpoint=value)
        elif self.lpd[N] == self.humi:
            self.client.write_humi(setpoint=value)
        else:
            raise ValueError(self.loopExMsg)

    @exclusive
    def get_loop_pv(self,N):
        if self.lpd[N] == self.temp: return {'air':self.cached(self.client.read_temp)['processvalue']}
        elif self.lpd[N] == self.humi: return {'air':self.cached(self.client.read_humi)['processvalue']}
        else: raise ValueError(self.loopExMsg)

    @exclusive
    def set_loop_range(self,N,value):
        if 'max' not in value or 'min' not in value:
            raise AttributeError('missing "max" or "min" property')
        if self.lpd[N] == self.temp: self.client.write_temp(max=value['max'],min=value['min'])
        elif self.lpd[N] == self.humi: self.client.write_humi(max=value['max'],min=value['min'])
        else: raise ValueError(self.loopExMsg)

    @exclusive
    def get_loop_range(self,N):
        if self.lpd[N] == self.temp: return self.cached(self.client.read_temp)['range']
        elif self.lpd[N] == self.humi: return self.cached(self.client.read_humi)['range']
        else: raise ValueError(self.loopExMsg)

    @exclusive
    def get_loop_en(self,N):
        if self.lpd[N] == self.temp: return {'constant':True,'current':True}
        elif self.lpd[N] == self.humi: return {'current':self.cached(self.client.read_humi)['enable'],
                                               'constant':self.cached(self.client.read_constantHumi)['enable']}
        else: raise ValueError(self.loopExMsg)

    @exclusive
    def set_loop_en(self,N,value):
        if self.lpd[N] == self.temp: pass
        elif self.lpd[N] == self.humi:
            if value:self.client.write_humi(setpoint=self.cached(self.client.read_constantHumi)['setpoint'])
            else: self.client.write_humi(enable=False)
        else: raise ValueError(self.loopExMsg)

    @exclusive
    def get_loop_units(self,N):
        if self.lpd[N] == self.temp: return u'\xb0C'
        elif self.lpd[N] == self.humi: return u'%RH'
        else: raise ValueError(self.loopExMsg)

    @exclusive
    def get_loop_mode(self,N):
        if N > 2: raise ValueError(self.loopExMsg)
        mode = self.client.read_mode() 
        if mode in ['OFF','STANDBY']:
            return 0
        elif self.lpd[N] == self.temp:
            return 1 if mode == 'CONSTANT' else 2
        elif self.lpd[N] == self.humi:
            if self.cached(self.client.read_humi)['enable']:
                return 1 if mode == 'CONSTANT' else 2
            else:
                return 0

    @exclusive
    def get_cascade_sp(self,N):
        if self.lpd[N] != self.temp: raise ValueError(self.cascEsMsg)
        cur = self.cached(self.client.read_tempPtc)
        return {'constant':self.cached(self.client.read_constantTemp)['setpoint'],
                'current':cur['setpoint']['product'] if cur['enable_cascade'] else cur['setpoint']['air'],
                'air':cur['setpoint']['air'],'product':cur['setpoint']['product']}

    @exclusive
    def set_cascade_sp(self,N,value):
        if self.lpd[N] != self.temp: raise ValueError(self.cascEsMsg)
        self.client.write_temp(setpoint=value)

    @exclusive
    def get_cascade_pv(self,N):
        if self.lpd[N] != self.temp: raise ValueError(self.cascEsMsg)
        return self.cached(self.client.read_tempPtc)['processvalue']

    @exclusive
    def get_cascade_range(self,N):
        if self.lpd[N] != self.temp: raise ValueError(self.cascEsMsg)
        return self.get_loop_range(self.temp,exclusive=False)

    @exclusive
    def set_cascade_range(self,N,value):
        if self.lpd[N] != self.temp: raise ValueError(self.cascEsMsg)
        self.set_loop_range(self.temp,value,exclusive=False)

    @exclusive
    def get_cascade_en(self,N):
        if self.lpd[N] != self.temp: raise ValueError(self.cascEsMsg)
        return self.get_loop_en(self.temp,exclusive=False)

    @exclusive
    def set_cascade_en(self,N,value):
        if self.lpd[N] != self.temp: raise ValueError(self.cascEsMsg)
        return self.set_loop_en(self.temp,value,exclusive=False)

    @exclusive
    def get_cascade_units(self,N):
        if self.lpd[N] != self.temp: raise ValueError(self.cascEsMsg)
        return self.get_loop_units(self.temp,exclusive=False)

    @exclusive
    def get_cascade_mode(self,N):
        if self.lpd[N] != self.temp: raise ValueError(self.cascEsMsg)
        return self.get_loop_mode(self.temp,exclusive=False)

    @exclusive
    def get_cascade_ctl(self,N):
        if self.lpd[N] != self.temp: raise ValueError(self.cascEsMsg)
        return self.cached(self.client.read_tempPtc)['enable_cascade']

    @exclusive
    def set_cascade_ctl(self,N,value):
        if self.lpd[N] != self.temp: raise ValueError(self.cascEsMsg)
        params = self.cached(self.client.read_tempPtc)
        params['deviation'].update({'enable':value})
        self.client.write_tempPtc(**params['deviation'])

    @exclusive
    def get_cascade_deviation(self,N):
        if self.lpd[N] != self.temp: raise ValueError(self.cascEsMsg)
        deviation = self.cached(self.client.read_constantPtc)['deviation']
        if deviation['negative'] < 0: deviation['negative'] = 0 - deviation['negative'] #flip the sign
        return deviation

    @exclusive
    def set_cascade_deviation(self,N,value):
        if self.lpd[N] != self.temp: raise ValueError(self.cascEsMsg)
        if 'positive' not in value or 'negative' not in value: raise ValueError('value must contain "positive" and "negative" keys')
        if value['negative'] > 0: value['negative'] = 0 - value['negative'] # flip the sign
        self.client.write_tempPtc(self.get_cascade_ctl(self.temp,exclusive=False), **value)

    @exclusive
    def get_event(self,N):
        if N >= 13: raise ValueError('There are only 12 events')
        return {'current':self.cached(self.client.read_relay)[N-1],'constant':self.cached(self.client.read_constantRelay)[N-1]}

    @exclusive
    def set_event(self,N,value):
        if N >= 13: raise ValueError('There are only 12 events')
        self.client.write_relay([value if i==N else None for i in range(1,13)])

    @exclusive
    def get_status(self):
        if self.cached(self.client.read_mon)['alarms'] > 0:
            return 'Alarm'
        return {'OFF':'Off','STANDBY':'Standby','CONSTANT':'Constant',
                'RUN':'Program Running','RUN PAUSE':'Program Paused',
                'RUN END HOLD':'Program End Hold','RMT RUN':'Remote Program Running',
                'RMT RUN PAUSE':'Remote Program Paused',
                'RMT RUN END HOLD':'Remote Program End Hold'}[self.client.read_mode(True)]

    @exclusive
    def get_alarm_status(self):
        active = self.client.read_alarm()
        alarmlist = [0,1,2,3,6,7,8,9,10,11,12,18,19,21,22,23,26,30,31,40,41,43,46,48,50,51,99]
        inactive = [x for x in alarmlist if x not in active]
        return {'active':active,'inactive':inactive}

    @exclusive
    def const_start(self):
        self.client.write_modeConstant()

    @exclusive
    def stop(self):
        self.client.write_modeStandby()

    @exclusive
    def prgm_start(self,N,step):
        self.client.write_prgmRun(N,step)

    @exclusive
    def prgm_pause(self):
        self.client.write_prgmPause()

    @exclusive
    def prgm_resume(self):
        self.client.write_prgmContinue()

    @exclusive
    def prgm_next_step(self):
        self.client.write_prgmAdvance()

    @exclusive
    def get_prgm_cur(self):
        return self.cached(self.client.read_prgmSet)['number']

    @exclusive
    def get_prgm_cstep(self):
        return self.cached(self.client.read_prgmMon)['pgmstep']

    @exclusive
    def get_prgm_cstime(self):
        rtime = self.cached(self.client.read_prgmMon)['time']
        return '%d:%02d:00' % (rtime['hour'],rtime['minute'])

    @exclusive
    def get_prgm_time(self):
        pgm = self.client.read_prgm(self.cached(self.client.read_prgmSet)['number'])
        pgms = self.cached(self.client.read_prgmMon)
        cA = pgms['counter_a']
        cB = pgms['counter_b']
        cS = pgms['pgmstep']-1
        tminutes = pgms['time']['hour']*60 + pgms['time']['minute'] - pgm['steps'][cS]['time']['hour']*60 + pgm['steps'][cS]['time']['minute']
        while cS < len(pgm['steps']):
            tminutes += pgm['steps'][cS]['time']['hour']*60 + pgm['steps'][cS]['time']['minute']
            if pgm['counter_a']['end']-1 == cS and cA > 0:
                cS = pgm['counter_a']['start']-1
                cA -= 1
            elif pgm['counter_b']['end']-1 == cS and cB > 0:
                cS = pgm['counter_b']['start']-1
                cB -= 1
            else:
                cS += 1
        return "%d:%02d:00" % (int(tminutes/60), tminutes%60)

    @exclusive
    def get_prgm_name(self,N):
        return self.cached(self.client.read_prgmData,N)['name']

    @exclusive
    def get_prgm_steps(self,N):
        return self.client.read_prgmData(N)['steps']

    @exclusive
    def get_prgms(self):
        names = []
        for i in range(1,41):
            try:
                names.append({'number':i,'name':self.client.read_prgmUseNum(i)['name']})
            except EspecError:
                names.append({'number':i,'name':''})
        return names

    @exclusive
    def get_prgm(self, N):
        return self.client.read_prgm(N, self.cascades > 0)

    @exclusive
    def set_prgm(self,N,prgm):
        self.client.write_prgm(N,prgm)

    @exclusive
    def prgm_delete(self,N):
        self.client.write_prgmErase(N)

    @exclusive
    def sample(self, lookup=None):
        type = 'cascade' if self.cascades > 0 else 'loop'
        items = ['setpoint','processvalue','enable'] if type == 'loop' else ['setpoint','processvalue','enable','enable_cascade']
        loops = [self.get_loop(1,type,items,exclusive=False)]
        if lookup: loops[0].update(lookup[type][0])
        if self.loops + self.cascades > 1:
            loops.append(self.get_loop(2,'loop',['setpoint','processvalue','enable'],exclusive=False))
            if lookup: loops[1].update(lookup['loop'][0 if type=='cascade' else 1])
        return {'datetime':self.get_datetime(exclusive=False),'loops':loops,'status':self.get_status(exclusive=False)} 

    @exclusive
    def process_controller(self, update=True):
        if update:
            self.loops = 0
            self.cascades = 0
        msg = 'P300 ' if self.client.read_rom().startswith('P3') else 'SCP-220 '
        try:
            if update:
                self.client.read_tempPtc()
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
        return msg

    @exclusive
    def get_networkSettings(self):
        ret = self.client.read_IPSet()
        ret.update({'message':'','host':''})
        return ret

    @exclusive
    def set_networkSettings(self,value):
        self.client.write_IPSet(value.get('address','0.0.0.0'),value.get('mask','0.0.0.0'),value.get('gateway','0.0.0.0'))


if __name__ == '__main__':
    print 'running self test:'
    ctlr = Espec(interface='Serial',serialport='\\.\COM3',baudrate=19200)
    ctlr.process_controller()
    ctlr.self_test(ctlr.loops+ctlr.cascades,ctlr.cascades)