'''
Upper level interface for the Watlow F4 controller

:copyright: (C) Espec North America, INC.
:license: MIT, see LICENSE for more details.
'''
#pylint: disable=W0703
import datetime
import re
import time
from chamberconnectlibrary.modbus import ModbusError, ModbusRTU, ModbusTCP
from chamberconnectlibrary.controllerinterface import ControllerInterface, exclusive
from chamberconnectlibrary.controllerinterface import ControllerInterfaceError

class WatlowF4(ControllerInterface):
    '''
    A class for interfacing with Watlow F4T

    Kwargs:
        interface (str): The connection method::
            "TCP" -- modbusTCP (default)
            "RTU" -- modbusRTU
        adr (int): The modbus address of the controller (default=1)
        host (str): The hostname (IP address) of the Watlow F4T when interface="TCP"
        serialport (str): The serial port to use when interface="RTU"
        baudrate (int): The serial port's baud rate to use when interface="RTU"
        loops (int): The number of control loops the controller has (default=1, max=4)
        cascades (int): The number of cascade control loops the controller has (default=0, max=3)
        cond_event (int): The event # used to the controller on/off (default=0(disabled))
        limits (list(bool)): list of slots where limit controllers are installed (default=[5])
        loop_event (list(int)): list of events #'s that enable/disble loops (default=[0,2,0,0])
        cascade_event (list(int)): list of events #'s that enbl/dis casc.lps(default=[0,0,0,0])
        cascade_ctl_event (list(int)): list of event#'s enbl/dis casc. mode (default=[0,0,0,0])
        waits (list(str)): Configuration for the 4 waitfor inputs each index can be::
            "A" -- Analog
            "D" -- Digital
            "" -- Off(default x4)
        time_zone (None): Not currently used
        alarms (int): The number of alarms that the controller has (default=6)
        profiles (bool): If True the controller supports profiles(programs) (default=False)
        lock (RLock): The locking method to use when accessing the controller (default=RLock())
    '''

    def __init__(self, **kwargs):
        self.iwatlow_val_dict, self.client, self.loops, self.cascades = None, None, None, None
        self.init_common(**kwargs)
        self.cond_event = kwargs.get('cond_event')
        self.limits = kwargs.get('limits', [])

        #list of events that may enable or disable a loop index 0=loop1, events=1-8 0=not used
        self.loop_event = kwargs.get('loop_event', [0, 0, 0, 0])

        #list of events that may enable or disable a cascade loop
        self.cascade_event = kwargs.get('cascade_event', [0, 0, 0, 0])

        # waits 1-4 A= analog wait, D= digital wait
        self.waits = kwargs.get('waits', ['', '', '', ''])
        self.events = 8

        #these are detectable from the part number (call process_partno())
        self.alarms = kwargs.get('alarms', 6)
        self.profiles = kwargs.get('profiles', False)
        self.scalar = [None, None, None]
        self.__update_loop_map()


    def __range_check(self, val, minimum, maximum):
        '''
        min <= val <= max

        Args:
            val (int): the value to check the range of
            min (int): the minimum possible value
            max (int): the maximum possible value
        Returns:
            None
        Raises:
            ValueError
        '''
        if maximum < minimum or val < minimum or val > maximum:
            raise ValueError("Index is not within bounds or bounds are not valid")

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

    def __get_scalar(self, N):
        '''
        Get the scalar factor for a analog input

        Args:
            N (int): 1 or 2
        Returns:
            float
        '''
        if self.scalar[N-1] is None:
            my_scalar = self.client.read_holding([606, 616, 626][N-1])[0]*10
            self.scalar[N-1] = 1 / float(my_scalar if my_scalar > 0 else 1)
        return self.scalar[N-1]

    def __get_digital_input(self, N):
        '''
        Get the state of a digital input

        Args:
            N (int): 1-4
        Returns:
            Boolean
        '''
        return self.client.read_holding(201 + 12*(N-1))[0] == 1

    def __get_analog_input_setup(self):
        lookup = ['thermocouple', 'rtd', 'process', 'wetbulb-drybulb', 'off']
        try:
            inputs = [lookup[self.client.read_holding(600)[0]]]
            inputs.append(lookup[self.client.read_holding(610)[0]])
            inputs.append(lookup[self.client.read_holding(620)[0]])
        except ModbusError:
            pass
        return inputs

    def __edit_prgm_step_autostart(self, step):
        '''setup an autostart step'''
        daylookup = ['daily', 'sun', 'mon', 'tue', 'wed', 'thur', 'fri', 'sat']
        self.client.write_holding(4003, 0)
        if step['start_type'] == 'day':
            self.client.write_holding(4004, 1)
            self.client.write_holding(4008, daylookup.index(step['time']['day']))
        else:
            self.client.write_holding(4004, 0)
            date = [0, step['date']['month'], step['date']['day'], step['date']['year']]
            self.client.write_holding(4005, date)
        time = [step['time']['hours'], step['time']['minutes'], step['time']['seconds']]
        self.client.write_holding(4009, time)

    def __edit_prgm_step_rampsoak(self, step):
        eventlookup = ['disable', 'off', 'on']
        if step['waits']['waits']:
            self.client.write_holding(4012, 1)
            for event in step['waits']['events']:
                self.client.write_holding(4012+event['number']-1, eventlookup.index(event['value']))
            for analog in step['waits']['analog']:
                if analog['waits']:
                    reg = 4021+(analog['number']-1)*2
                    value = int(analog['value']/self.__get_scalar(analog['number']))
                    self.client.write_holding(reg, 1)
                    self.client.write_holding_signed(reg+1, value)
                else:
                    self.client.write_holding(4021+(analog['number']-1)*2, 0)
        else:
            self.client.write_holding(4012, 1)
        for event in step['events']:
            self.client.write_holding(4030+event['number']-1, 1 if event['value'] else 0)
        if step['type'] != 'ramprate':
            dur = step['duration']
            self.client.write_holding(4009, [dur['hours'], dur['minutes'], dur['seconds']])
        else:
            self.client.write_holding(4043, int(step['rate']*10))
        for i, loop in enumerate(step['loops']):
            target = int(loop['target'] * self.__get_scalar(i+1))
            self.client.write_holding_signed(4044+i, target)#setpoint
            self.client.write_holding(4046+i, loop['pidset'] - 5*i)#pid set
            self.client.write_holding(4048+i, 1 if loop['gsoak'] else 0) #guarrneteed soak
            if self.cond_event[i] > 0:
                reg = 4030+self.cond_event[i]-1
                self.client.write_holding(reg, 1 if loop['enable'] else 0)
        if self.cond_event: #if we have a condition event force it on for the profile
            self.client.write_holding(4030+self.cond_event-1, 1)

    def __edit_prgm_step_jump(self, step):
        '''setup an jump step'''
        self.client.write_holding(4003, 4)
        self.client.write_holding(4050, [step['jprofile'], step['jstep'], step['jcount']])

    def __edit_prgm_step_end(self, step):
        '''setup an end step'''
        if step['action'] == 'hold':
            self.client.write_holding(4060, 0)
        elif step['action'] == 'controloff':
            self.client.write_holding(4060, 1)
        elif step['action'] == 'alloff':
            self.client.write_holding(4060, 2)
        elif step['action'] == 'idle':
            self.client.write_holding(4060, 3)
            for idxl, loop in enumerate(step['loops']):
                value = int(loop['target'] / self.__get_scalar(idxl+1))
                self.client.write_holding_signed(4061+idxl, value)
        else:
            raise ValueError('invalid end step action')

    def __edit_prgm_step(self, step):
        '''edit the selected step parameters (excluding an end step)'''
        if step['type'] == 'autostart':
            self.__edit_prgm_step_autostart(step)
        elif step['type'] in ['ramptime', 'ramprate', 'soak']:
            self.__edit_prgm_step_rampsoak(step)
        elif step['type'] == 'jump':
            self.__edit_prgm_step_jump(step)
        elif step['type'] == 'end':
            self.__edit_prgm_step_end(step)
        else:
            raise ValueError('invalid step type')
        self.client.write_holding(25, 0) #save the step

    def __create_prgm(self, value):
        '''create a new program return its number'''
        self.client.write_holding(4002, 1)
        num = self.client.read_holding(4000)
        if re.match("^[A-Z0-9]*$", value['name']):
            self.client.write_holding_string(3500+10*(num-1), value['name'], 10)
        for i, step in enumerate(value['steps']):
            self.client.write_holding(4001, [i+1, 2])
            self.__edit_prgm_step(step)
        return num

    def __edit_prgm(self, num, value):
        '''Edit an existing program'''
        self.client.write_holding(4000, num)
        if re.match("^[A-Z0-9]*$", value['name']):
            self.client.write_holding_string(3500+10*(num-1), value['name'], 10)
        for i in range(1, 256): #delete all steps but the end step
            self.client.write_holding(4001, i+1)
            if self.client.read_holding(4003) == 5:
                break #is end step stop looping.
            self.client.write_holding(4002, 4) #delete this step
            self.client.write_holding(25, 0)
        for i, step in enumerate(value['steps']):
            if step['type'] != 'end': #insert a new step
                self.client.write_holding(4001, [i+1, 2])
                self.__edit_prgm_step(step)
            elif step['type'] == 'end': #edit the existing step
                self.client.write_holding(4001, i+1)
                self.__edit_prgm_step_end(step)
            else:
                raise ValueError('invalid step type')


    def connect(self):
        '''
        connect to the controller using the paramters provided on class initialization
        '''
        if self.interface == "RTU":
            self.client = ModbusRTU(address=self.adr, port=self.serialport, baud=self.baudrate)
        else:
            self.client = ModbusTCP(self.adr, self.host)

    def close(self):
        '''
        close the connection to the controller
        '''
        try:
            self.client.close()
        except AttributeError:
            pass
        self.client = None

    @exclusive
    def raw(self, command):
        '''
        connect directly to the controller
        '''
        return self.client.interact(command)

    @exclusive
    def get_datetime(self):
        dtl = self.client.read_holding(1916, 6)
        return datetime.datetime(
            hour=dtl[0],
            minute=dtl[1],
            second=dtl[2],
            month=dtl[3],
            day=dtl[4],
            year=dtl[5]
        )

    @exclusive
    def set_datetime(self, value):
        vals = [value.hour, value.minute, value.second, value.month, value.day, value.year]
        self.client.write_holding(1916, vals)

    @exclusive
    def get_refrig(self):
        raise NotImplementedError

    @exclusive
    def set_refrig(self, value):
        raise NotImplementedError

    @exclusive
    def get_loop_sp(self, N):
        self.__range_check(N, 1, self.loops + self.cascades)
        const = self.client.read_holding_signed([300, 319][N-1])[0] * self.__get_scalar(N)
        if self.client.read_holding(200)[0] in [2, 3]: #running or holding profile
            cur = self.client.read_holding_signed([4122, 4123][N-1])[0] * self.__get_scalar(N)
        else:
            cur = const
        return {'constant': const, 'current': cur}

    @exclusive
    def set_loop_sp(self, N, value):
        self.__range_check(N, 1, self.loops + self.cascades)
        value = value['constant'] if isinstance(value, dict) else value
        value = int(value / self.__get_scalar(N)) #trim to 16bit signed int
        self.client.write_holding_signed([300, 319][N-1], value)

    @exclusive
    def get_loop_pv(self, N):
        self.__range_check(N, 1, self.loops + self.cascades)
        return {'air': self.client.read_holding_signed([100, 104][N-1])[0] * self.__get_scalar(N)}

    @exclusive
    def get_loop_range(self, N):
        self.__range_check(N, 1, self.loops + self.cascades)
        return {
            'max':self.client.read_holding_signed([603, 613, 623][N-1])[0] * self.__get_scalar(N),
            'min':self.client.read_holding_signed([602, 612, 622][N-1])[0] * self.__get_scalar(N)
        }

    @exclusive
    def set_loop_range(self, N, value):
        self.__range_check(N, 1, self.loops + self.cascades)
        vals = [int(value['min'] / self.__get_scalar(N)), int(value['max'] / self.__get_scalar(N))]
        self.client.write_holding_signed([602, 612, 622][N-1], vals)

    @exclusive
    def get_loop_en(self, N):
        self.__range_check(N, 1, self.loops + self.cascades)
        lrange = self.get_loop_range(N, exclusive=False)
        profile = self.client.read_holding(200)[0] in [2, 3]
        cmd = self.get_loop_sp(N, exclusive=False)['constant'] >= lrange['min']
        if self.loop_event[N-1] != 0:
            eve = self.get_event(self.loop_event[N-1], exclusive=False)['constant']
            if self.cond_event:
                running = self.get_event(self.cond_event, exclusive=False)
            else:
                running = False
            return {'constant': eve, 'current': eve if running else cmd}
        else:
            return {'constant': cmd, 'current': True if profile else cmd}

    @exclusive
    def set_loop_en(self, N, value):
        self.__range_check(N, 1, self.loops + self.cascades)
        value = value['constant'] if isinstance(value, dict) else value
        lrange = self.get_loop_range(N, exclusive=False)
        if self.get_loop_sp(N, exclusive=False)['constant'] < lrange['min'] and value:
            self.set_loop_sp(N, lrange['min'], exclusive=False)
        if self.loop_event[N-1] != 0:
            self.set_event(self.loop_event[N-1], value)

    @exclusive
    def get_loop_units(self, N):
        self.__range_check(N, 1, self.loops + self.cascades)
        units = ['Temp', u'%RH', u'PSI', u''][self.client.read_holding([608, 618, 628][N-1])[0]]
        if units == 'Temp':
            units = u'\xb0C' if self.client.read_holding(901)[0] else u'\xb0F'
        return units

    @exclusive
    def get_loop_mode(self, N):
        self.__range_check(N, 1, self.loops + self.cascades)
        return 'On' if self.get_loop_en(N, exclusive=False) else 'Off'

    @exclusive
    def get_loop_modes(self, N):
        self.__range_check(N, 1, self.loops + self.cascades)
        return ['On', 'Off'] if self.loop_event[N-1] != 0 else ['On']

    @exclusive
    def set_loop_mode(self, N, value):
        self.__range_check(N, 1, self.loops + self.cascades)
        value = value['constant'] if isinstance(value, dict) else value
        if value in ['On', 'Off']:
            self.set_loop_en(N, value == 'On', exclusive=False)
        else:
            raise ValueError('Unsupported Loop Mode, must be "On" or "Off" not "%r"' % value)

    @exclusive
    def get_loop_power(self, N):
        self.__range_check(N, 1, self.loops + self.cascades)
        outa = self.client.read_holding_signed([103, 111][N-1])[0] / 100.0
        outb = self.client.read_holding_signed([107, 115][N-1])[0] / 100.0
        combined = outa + outb
        return {'constant':combined, 'current':combined}

    @exclusive
    def set_loop_power(self, N, value):
        raise NotImplementedError

    @exclusive
    def get_cascade_sp(self, N):
        self.__range_check(N, 1, self.cascades)
        vals = self.get_loop_sp(1)
        vals.update({
            'air':self.client.read_holding_signed(1922)[0]*self.__get_scalar(1),
            'product':vals['current']
        })
        return vals

    @exclusive
    def set_cascade_sp(self, N, value):
        self.__range_check(N, 1, self.cascades)
        return self.set_loop_sp(N, value)

    @exclusive
    def get_cascade_pv(self, N):
        self.__range_check(N, 1, self.cascades)
        return {
            'air':self.client.read_holding_signed(100)[0] * self.__get_scalar(1),
            'product':self.client.read_holding_signed(108)[0] * self.__get_scalar(3)
        }

    @exclusive
    def get_cascade_range(self, N):
        self.__range_check(N, 1, self.cascades)
        return self.get_loop_range(N)

    @exclusive
    def set_cascade_range(self, N, value):
        self.__range_check(N, 1, self.cascades)
        return self.set_loop_range(N, value)

    @exclusive
    def get_cascade_en(self, N):
        self.__range_check(N, 1, self.cascades)
        return self.get_loop_en(N)

    @exclusive
    def set_cascade_en(self, N, value):
        self.__range_check(N, 1, self.cascades)
        return self.set_loop_en(N, value)

    @exclusive
    def get_cascade_units(self, N):
        self.__range_check(N, 1, self.cascades)
        return self.get_loop_units(N)

    @exclusive
    def get_cascade_mode(self, N):
        self.__range_check(N, 1, self.cascades)
        return self.get_loop_mode(N)

    @exclusive
    def get_cascade_modes(self, N):
        self.__range_check(N, 1, self.cascades)
        return self.get_loop_modes(N)

    @exclusive
    def set_cascade_mode(self, N, value):
        self.__range_check(N, 1, self.cascades)
        return self.set_loop_mode(N, value)

    @exclusive
    def get_cascade_ctl(self, N):
        raise NotImplementedError

    @exclusive
    def set_cascade_ctl(self, N, value):
        raise NotImplementedError

    @exclusive
    def get_cascade_deviation(self, N):
        self.__range_check(N, 1, self.cascades)
        vals = self.client.read_holding_signed(1926, 2)
        return {'positive': vals[1] * self.__get_scalar(1),
                'negative': vals[0] * self.__get_scalar(1)}

    @exclusive
    def set_cascade_deviation(self, N, value):
        self.__range_check(N, 1, self.cascades)
        vals = [
            int(value['negative']/self.__get_scalar(1)),
            int(value['positive']/self.__get_scalar(1))
        ]
        self.client.write_holding_signed(1926, vals)

    @exclusive
    def get_cascade_power(self, N):
        self.__range_check(N, 1, self.cascades)
        return self.get_loop_power(N)

    @exclusive
    def set_cascade_power(self, N, value):
        raise NotImplementedError

    @exclusive
    def get_event(self, N):
        self.__range_check(N, 1, 8)
        val = self.client.read_holding(2000 + 10*(N-1))[0] == 1
        return {'current':val, 'constant':val}

    @exclusive
    def set_event(self, N, value):
        self.__range_check(N, 1, 8)
        value = value['constant'] if isinstance(value, dict) else value
        self.client.write_holding(2000 + 10*(N-1), 1 if value else 0)

    @exclusive
    def get_status(self):
        if self.get_alarm_status(exclusive=False):
            return 'Alarm'
        mode = self.client.read_holding(200)[0]
        prof = ['Constant', 'Constant', 'Program Running', 'Program Paused'][mode]
        if self.cond_event:
            return prof if self.get_event(self.cond_event, exclusive=False) else 'Standby'
        else:
            return prof

    @exclusive
    def get_alarm_status(self):
        aalms, ialms = [], []
        for alm in self.limits:
            if self.__get_digital_input(alm):
                ialms.append(alm)
            else:
                aalms.append(alm)
        return {'active': aalms, 'inactive': ialms}

    @exclusive
    def const_start(self):
        self.client.write_holding(1217, 1) #terminate profile
        if self.cond_event:
            self.set_event(self.cond_event, True, exclusive=False)

    @exclusive
    def stop(self):
        self.client.write_holding(1217, 1) #terminate profile
        if self.cond_event:
            self.set_event(self.cond_event, False, exclusive=False)

    @exclusive
    def prgm_start(self, N, step):
        self.client.write_holding(4000, N)
        self.client.write_holding(4001, step)
        self.client.write_holding(4002, 5)

    @exclusive
    def prgm_pause(self):
        self.client.write_holding(1210, 1)

    @exclusive
    def prgm_resume(self):
        self.client.write_holding(1209, 1)

    @exclusive
    def prgm_next_step(self):
        program = self.get_prgm_cur(exclusive=False)
        nextstep = self.get_prgm_cstep(exclusive=False) + 1
        self.const_start(exclusive=False)
        time.sleep(1)
        self.prgm_start(program, nextstep, exclusive=False)

    @exclusive
    def get_prgm_cur(self):
        return self.client.read_holding(4100)[0]

    @exclusive
    def get_prgm_cstep(self):
        return self.client.read_holding(4101)[0]

    @exclusive
    def get_prgm_cstime(self):
        data = self.client.read_holding(4119, 3)
        return "%d:%02d:%02d" % (data[0], data[1], data[2])

    @exclusive
    def get_prgm_time(self, pgm=None):
        return ''
        if pgm is None:
            pgm = self.get_prgm(self.get_prgm_cur(exclusive=False), exclusive=False)
        while True:
            self.client.write_holding(4001, 3)
            print 'count=%d, step=%d, step=%d' % self.client.read_holding(4126, 3)
            self.client.write_holding(4001, 4)
            print 'count=%d, step=%d, step=%d' % self.client.read_holding(4126, 3)
        raise NotImplementedError

    @exclusive
    def get_prgm_name(self, N):
        parsed = re.search(r'([A-Z0-9]+)', self.client.read_holding_string(3500+10*(N-1), 10))
        return parsed.group(1)

    @exclusive
    def set_prgm_name(self, N, value):
        if re.match("^[A-Z0-9]*$", value):
            self.client.write_holding_string(3500+10*(N-1), value, 10)
            self.client.write_holding(25, 0) #save changes to profiles
        else:
            raise ValueError('Name must be uppercase letters and numbers only.')

    @exclusive
    def get_prgm_steps(self, N):
        self.__range_check(N, 1, 41)
        self.client.write_holding(4000, N)
        for step in range(2, 257):
            self.client.write_holding(4001, step)
            step_type = self.client.read_holding(4003)[0]
            if step_type == 5:
                return step
            elif step_type > 5:
                raise ValueError('Program #%d does not exist' % N)

    @exclusive
    def get_prgms(self):
        programs = []
        num_programs = 40 - self.client.read_holding(1218)[0]
        for idx in range(1, 41):
            try:
                programs.append({
                    'number': idx,
                    'steps': self.get_prgm_steps(idx, exclusive=False),
                    'name': self.get_prgm_name(idx, exclusive=False)
                })
            except ValueError:
                pass
            if idx > num_programs:
                break
        return programs

    @exclusive
    def get_prgm(self, N):
        rbase = 4003 #first register to read
        self.__range_check(N, 1, 40)
        self.client.write_holding(4000, N)
        program = {'steps':[], 'name': self.get_prgm_name(N, exclusive=False)}
        daylookup = ['daily', 'sun', 'mon', 'tue', 'wed', 'thur', 'fri', 'sat']
        for step in range(1, 257):
            self.client.write_holding(4001, step)
            params = self.client.read_holding_signed(rbase, 4062-rbase+1)
            if params[4003-rbase] == 0:#Auto start
                program['steps'].append({
                    'type':'autostart',
                    'start_type':['date', 'day'][params[4004-rbase]],
                    'date':{
                        'month':params[4005-rbase],
                        'day':params[4006-rbase],
                        'year':params[4007-rbase]
                    },
                    'time':{
                        'day':daylookup[params[4008-rbase]],
                        'hours':params[4009-rbase],
                        'minutes':params[4010-rbase],
                        'seconds':params[4011-rbase]
                    }
                })
            elif params[4003-rbase] in [1, 2, 3]: #ramptime, ramprate, soak
                step_params = {
                    'type': ['', 'ramptime', 'ramprate', 'soak'][params[4003-rbase]],
                    'waits':{'waits': params[4012-rbase] == 1},
                    'events':[
                        {'number':i, 'value':params[4030-rbase-1+i] == 1}
                        for i in range(1, 9) if i not in self.loop_event and i != self.cond_event
                    ],
                    'loops':[{
                        'enable':params[4030-rbase-1+self.loop_event[i]] == 1 \
                                 if self.loop_event[i] else True,
                        'target':params[4044-rbase+i] * self.__get_scalar(i+1),
                        'pidset':params[4046-rbase+i] + 1 + 5*i,
                        'gsoak':params[4048-rbase+i] == 1
                    } for i in range(self.loops + self.cascades)]
                }
                if params[4003-rbase] != 2:
                    step_params['duration'] = {
                        'hours':params[4009-rbase],
                        'minutes':params[4010-rbase],
                        'seconds':params[4011-rbase]
                    }
                else:
                    step_params['rate'] = params[4043-rbase] / 10.0
                if step_params['waits']['waits']:
                    analogs = self.__get_analog_input_setup()
                    step_params['waits'].update({
                        'events':[
                            {'number':i+1, 'value':['disable', 'off', 'on'][params[4013-rbase+i]]}
                            for i in range(4) if self.client.read_holding(1060+i*2)[0] == 10
                        ],
                        'analog':[
                            {
                                'number':i+1,
                                'waits':params[4021-rbase+i*2] == 1,
                                'value':params[4022-rbase+i*2] * self.__get_scalar(i+1)
                            }
                            for i in range(len(analogs)) if analogs[i] != 'off'
                        ]
                    })
                program['steps'].append(step_params)
            elif params[4003-rbase] == 4:#Jump
                program['steps'].append({
                    'type':'jump',
                    'jprofile':params[4050-rbase],
                    'jstep':params[4051-rbase],
                    'jcount':params[4052-rbase]
                })
            elif params[4003-rbase] == 5:#End
                program['steps'].append({
                    'type':'end',
                    'action':['hold', 'controloff', 'alloff', 'idle'][params[4060-rbase]],
                    'loops':[
                        {'target':params[4061-rbase+i]*self.__get_scalar(i+1)}
                        for i in range(self.loops + self.cascades)
                    ]
                })
                break
            else:#Not a program
                raise ValueError('Program #%d does not exist' % N)
        return program

    @exclusive
    def set_prgm(self, N, value):
        self.__range_check(N, 1, 40)
        try:
            self.get_prgm_steps(N, exclusive=False)
            self.__edit_prgm(N, value)
        except ValueError:
            N = self.__create_prgm(value)
        return N

    @exclusive
    def prgm_delete(self, N):
        self.__range_check(N, 1, 40)
        self.client.write_holding(4000, [N, 1, 3]) #program #, step 1, action delete
        self.client.write_holding(25, 0) #save changes to profiles

    @exclusive
    def process_controller(self, update=True):
        part_no = 'Watlow F4'
        if update:
            self.loops = 1
            self.cascades = 0
        try:
            self.client.write_holding(319, self.client.read_holding(319)[0])
            if update:
                self.loops = 2
            part_no += 'D'
        except Exception:
            part_no += 'S'
        try:
            if self.client.read_holding(1925)[0]:
                part_no += ' W/Cascade'
                if update:
                    self.loops -= 1
                    self.cascades = 1
        except Exception:
            pass
        self.__update_loop_map()
        return part_no

    @exclusive
    def get_network_settings(self):
        raise NotImplementedError

    @exclusive
    def set_network_settings(self, value):
        raise NotImplementedError
