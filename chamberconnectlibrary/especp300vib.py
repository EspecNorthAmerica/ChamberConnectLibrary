'''
Upper level interface for Espec Corp. P300 Controller's w/ vibration firmware

:copyright: (C) Espec North America, INC.
:license: MIT, see LICENSE for more details.
'''
from chamberconnectlibrary.p300vib import P300Vib
from chamberconnectlibrary.especp300extended import EspecP300Extended, exclusive

class EspecP300Vib(EspecP300Extended):
    '''
    A class for interfacing with Espec controllers (P300)

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
        enable_air_speed (bool): Set to True if this P300 has air speed control
    '''

    def __init__(self, **kwargs):
        super(EspecP300Vib, self).__init__(**kwargs)
        self.temp, self.humi, self.vib = 1, None, 2
        self.lpd = {
            'temp':self.temp,
            'temperature':self.temp,
            'Temperature':self.temp,
            'vib':self.vib,
            'vibration':self.vib,
            'Vibration':self.vib,
            self.temp:self.temp,
            self.vib:self.vib
        }
        self.lp_exmsg = (
            'The EspecP300Vib controller only supports 2 loops (1:temperature,2:vibration)'
        )
        self.__update_loop_map()

    def __update_loop_map(self):
        '''
        update the loop map.
        '''
        if self.cascades > 0:
            self.loop_map = [{'type':'cascade', 'num':1}]
        else:
            self.loop_map = [{'type':'loop', 'num':1}]
        if self.cascades + self.loops > 1:
            self.loop_map += [{'type':'loop', 'num':2}]
        self.named_loop_map = {'Temperature':0, 'temperature':0, 'Temp':0, 'temp':0}
        if len(self.loop_map) > 1:
            self.named_loop_map.update({'Vibration':1, 'vibration':1, 'Vib':1, 'vib':1})

    def connect(self):
        self.client = P300Vib(self.interface, **self.connect_args)

    @exclusive
    def set_loop(self, identifier, loop_type='loop', param_list=None, **kwargs):
        '''
        cannot use the default controllerInterface version.
        '''
        lpfuncs = {
            'cascade':{
                'setpoint':self.set_cascade_sp,
                'setPoint':self.set_cascade_sp,
                'setValue':self.set_cascade_sp,
                'range':self.set_cascade_range,
                'enable':self.set_cascade_en,
                'deviation':self.set_cascade_deviation,
                'enable_cascade':self.set_cascade_ctl,
                'mode': self.set_cascade_mode
            },
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
        if spt1 or spt2 or spt3 or 'enable' in param_list or 'mode' in param_list:
            if 'enable' in param_list:
                enable = param_list.pop('enable')
                if isinstance(enable, dict):
                    enable = enable['constant']
            elif 'mode' in param_list:
                my_mode = param_list.pop('mode')
                if isinstance(my_mode, dict):
                    my_mode = my_mode['constant']
                enable = my_mode in ['On', 'ON', 'on']
            else:
                enable = None
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
            elif self.lpd[loop_number] == self.vib: 
                self.client.write_vib(**params) 
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
    def get_loop_sp(self, N):
        if self.lpd[N] == self.temp:
            cur = self.cached(self.client.read_temp)['setpoint']
            con = self.cached(self.client.read_constant_temp)['setpoint']
        elif self.lpd[N] == self.vib:
            cur = self.cached(self.client.read_vib)['setpoint']
            con = self.cached(self.client.read_constant_vib)['setpoint']
        else:
            raise ValueError(self.lp_exmsg)
        return {'constant':con, 'current':cur}

    @exclusive
    def set_loop_sp(self, N, value):
        value = value['constant'] if isinstance(value, dict) else value
        if self.lpd[N] == self.temp:
            self.client.write_temp(setpoint=value)
        elif self.lpd[N] == self.vib:
            self.client.write_vib(setpoint=value)
        else:
            raise ValueError(self.lp_exmsg)

    @exclusive
    def get_loop_pv(self, N):
        if self.lpd[N] == self.temp:
            return {'air':self.cached(self.client.read_temp)['processvalue']}
        elif self.lpd[N] == self.vib:
            return {'air':self.cached(self.client.read_vib)['processvalue']}
        else:
            raise ValueError(self.lp_exmsg)

    @exclusive
    def set_loop_range(self, N, value):
        if 'max' not in value or 'min' not in value:
            raise AttributeError('missing "max" or "min" property')
        if self.lpd[N] == self.temp:
            self.client.write_temp(min=value['min'], max=value['max'])
        elif self.lpd[N] == self.vib:
            self.client.write_vib(min=value['min'], max=value['max'])
        else:
            raise ValueError(self.lp_exmsg)

    @exclusive
    def get_loop_range(self, N):
        if self.lpd[N] == self.temp:
            return self.cached(self.client.read_temp)['range']
        elif self.lpd[N] == self.vib:
            return self.cached(self.client.read_vib)['range']
        else:
            raise ValueError(self.lp_exmsg)

    @exclusive
    def get_loop_en(self, N):
        if self.lpd[N] == self.temp:
            return {'constant':True, 'current':True}
        elif self.lpd[N] == self.vib:
            return {
                'current':self.cached(self.client.read_vib)['enable'],
                'constant':self.cached(self.client.read_constant_vib)['enable']
            }
        else:
            raise ValueError(self.lp_exmsg)

    @exclusive
    def set_loop_en(self, N, value):
        value = value['constant'] if isinstance(value, dict) else value
        if self.lpd[N] == self.temp:
            pass
        elif self.lpd[N] == self.vib:
            if value:
                self.client.write_vib(
                    enable=True,
                    setpoint=self.cached(self.client.read_constant_vib)['setpoint']
                )
            else:
                self.client.write_vib(enable=False)
        else:
            raise ValueError(self.lp_exmsg)

    @exclusive
    def get_loop_units(self, N):
        if self.lpd[N] == self.temp:
            return u'\xb0C'
        elif self.lpd[N] == self.vib:
            return u'Grms'
        else:
            raise ValueError(self.lp_exmsg)

    @exclusive
    def get_loop_mode(self, N):
        if self.lpd[N] == self.temp:
            cur, con = 'On', 'On'
        elif self.lpd[N] == self.vib:
            cur = 'On' if self.cached(self.client.read_vib)['enable'] else 'Off'
            con = 'On' if self.cached(self.client.read_constant_vib)['enable'] else 'Off'
        else:
            raise ValueError(self.lp_exmsg)
        if self.client.read_mode() in ['OFF', 'STANDBY']:
            cur = 'Off'
        return {"current": cur, "constant": con}

    def get_loop_modes(self, N):
        if self.lpd[N] == self.temp:
            return ['On']
        elif self.lpd[N] == self.vib:
            return ['Off', 'On']
        else:
            raise ValueError(self.lp_exmsg)

    @exclusive
    def get_loop_power(self, N):
        if self.lpd[N] == self.temp:
            val = self.cached(self.client.read_htr)['dry']
        elif self.lpd[N] == self.vib:
            val = self.cached(self.client.read_htr)['vib']
        else:
            raise ValueError(self.lp_exmsg)
        return {'current':val, 'constant':val}
