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

        self.combined_event = [
            self.cascade_event[0] if self.cascades > 0 else self.loop_event[0],
        ]
        if self.loops == 2:
            self.combined_event.append(self.loop_event[1])
        elif self.cascades == 1 and self.loops == 1:
            self.combined_event.append(self.loop_event[0])

        self.events = 8

        self.named_loop_map_list = kwargs.get('loop_names', [])

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
        if len(self.named_loop_map_list) == len(self.loop_map):
            self.named_loop_map = {name:i for i, name in enumerate(self.named_loop_map_list)}

    def __get_scalar(self, N):
        '''
        Get the scalar factor for a analog input

        Args:
            N (int): 1 or 2
        Returns:
            float
        '''
        try:
            if self.scalar[N-1] is None:
                my_scalar = self.client.read_holding([606, 616, 626][N-1])[0]*10
                self.scalar[N-1] = 1 / float(my_scalar if my_scalar > 0 else 1)
            return self.scalar[N-1]
        except Exception:
            return 1

    def __get_digital_input(self, N):
        '''
        Get the state of a digital input

        Args:
            N (int): 1-4
        Returns:
            Boolean
        '''
        tval = self.client.read_holding(1061 + 2*(N-1))[0]
        return self.client.read_holding(201 + 12*(N-1))[0] != tval

    def __set_prgm_name(self, N, value):
        '''write a profile name, does not save eeprom'''
        value = value.upper()
        value = value.rstrip()
        if len(value) > 10:
            value = value[0:10]
        if re.match("^[A-Z0-9 ]*$", value):
            self.client.write_holding_string(3500+10*(N-1), value, 10, 32)
        else:
            raise ValueError('Name must be uppercase letters and numbers only.')

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
            self.client.write_holding(4008, daylookup.index(step['start_time']['day']))
        else:
            date = [
                0,
                step['start_date']['month'],
                step['start_date']['day'],
                step['start_date']['year']
            ]
            self.client.write_holding(4004, date)
        my_time = [
            step['start_time']['hours'],
            step['start_time']['minutes'],
            step['start_time']['seconds']
        ]
        self.client.write_holding(4009, my_time)

    def __edit_prgm_step_rampsoak(self, step):
        eventlookup = ['disable', 'off', 'on']
        stypes = {'ramptime':1, 'ramprate':2, 'soak':3}
        self.client.write_holding(4003, stypes[step['type']])
        if step['wait']['enable']:
            self.client.write_holding(4012, 1)
            for event in step['wait']['digital']:
                self.client.write_holding(
                    4013+event['number']-1,
                    eventlookup.index(event['value']) if event['enable'] else 0
                )
            for analog in step['wait']['analog']:
                if analog['enable']:
                    reg = 4021+(analog['number']-1)*2
                    value = int(analog['value']/self.__get_scalar(analog['number']))
                    self.client.write_holding(reg, 1)
                    self.client.write_holding_signed(reg+1, value)
                else:
                    self.client.write_holding(4021+(analog['number']-1)*2, 0)
        else:
            self.client.write_holding(4012, 0)
        for event in step['events']:
            self.client.write_holding(4030+event['number']-1, 1 if event['value'] == 'on' else 0)
        if step['type'] != 'ramprate':
            dur = step['duration']
            self.client.write_holding(4009, [dur['hours'], dur['minutes'], dur['seconds']])
        else:
            self.client.write_holding(4043, int(step['loops'][0]['rate']*10))
        for i, loop in enumerate(step['loops']):
            if i < self.loops + self.cascades:
                target = int(loop['target']/self.__get_scalar(i+1))
                self.client.write_holding_signed(4044+i, target)#setpoint
                self.client.write_holding(4046+i, loop['pidset'] - 5*i - 1)#pid set
                self.client.write_holding(4048+i, 1 if loop['gsoak'] else 0) #guarrneteed soak
                if self.combined_event[i]:
                    reg = 4030+self.combined_event[i]-1
                    self.client.write_holding(reg, 1 if loop['enable'] else 0)
        if self.cond_event: #if we have a condition event force it on for the profile
            self.client.write_holding(4030+self.cond_event-1, 1)

    def __edit_prgm_step_jump(self, step):
        '''setup an jump step'''
        if step['jprofile'] == 0:
            profile_num = self.client.read_holding(4000)[0]
        else:
            profile_num = step['jprofile']
        self.client.write_holding(4003, 4)
        self.client.write_holding(4050, [profile_num, step['jstep'], step['jcount']])

    def __edit_prgm_step_end(self, step):
        '''setup an end step'''
        if step['action'] == 'hold':
            self.client.write_holding(4060, 0)
        elif step['action'] == 'controloff':
            self.client.write_holding(4060, 1)
        elif step['action'] == 'alloff':
            self.client.write_holding(4060, 2)
        elif step['action'] == 'idle':
            cache = [3]
            for idxl, loop in enumerate(step['loops']):
                cache.append(int(loop['target'] / self.__get_scalar(idxl+1)))
            self.client.write_holding_signed(4060, cache)
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

    def __create_prgm(self, value):
        '''create a new program return its number'''
        self.client.write_holding(4002, 1)
        num = self.client.read_holding(4000)[0]
        self.__set_prgm_name(num, value['name'])
        for i, step in enumerate(value['steps']):
            if step['type'] != 'end':
                self.client.write_holding(4001, [i+1, 2])
            else:
                self.client.write_holding(4001, i+1)
            self.__edit_prgm_step(step)
        return num

    def __edit_prgm(self, num, value):
        '''Edit an existing program'''
        self.prgm_delete(num, exclusive=False)
        return self.__create_prgm(value)


    def connect(self):
        '''
        connect to the controller using the paramters provided on class initialization
        '''
        if self.interface == "RTU":
            self.client = ModbusRTU(
                address=self.adr,
                port=self.serialport,
                baud=self.baudrate,
                timeout=10.0
            )
        else:
            self.client = ModbusTCP(self.adr, self.host, timeout=10.0)

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
    def get_loop_sp(self, N, range_restrict=True):
        self.__range_check(N, 1, self.loops + self.cascades)
        minsp = self.client.read_holding_signed([602, 612][N-1])[0] * self.__get_scalar(N)
        const = self.client.read_holding_signed([300, 319][N-1])[0] * self.__get_scalar(N)
        if self.client.read_holding(200)[0] in [2, 3]: #running or holding profile
            cur = self.client.read_holding_signed([4122, 4123][N-1])[0] * self.__get_scalar(N)
        else:
            cur = const
        if range_restrict:
            return {
                'constant': const if const > minsp else minsp,
                'current': cur if cur > minsp else minsp
            }
        else:
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
        cmd = self.get_loop_sp(N, False, exclusive=False)['current'] >= lrange['min']
        if self.combined_event[N-1] > 0:
            eve = self.get_event(self.combined_event[N-1], exclusive=False)['constant']
            running = self.get_event(self.cond_event, exclusive=False)['current'] if self.cond_event else True
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
        if self.combined_event[N-1] != 0:
            self.set_event(self.combined_event[N-1], value, exclusive=False)

    @exclusive
    def get_loop_units(self, N):
        self.__range_check(N, 1, self.loops + self.cascades)
        units = ['Temp', '%RH', 'PSI', ''][self.client.read_holding([608, 618, 628][N-1])[0]]
        if units == 'Temp':
            units = '\xb0C' if self.client.read_holding(901)[0] else '\xb0F'
        return units

    @exclusive
    def get_loop_mode(self, N):
        self.__range_check(N, 1, self.loops + self.cascades)
        lpen = self.get_loop_en(N, exclusive=False)
        lpen['constant'] = 'On' if lpen['constant'] else 'Off'
        lpen['current'] = 'On' if lpen['current'] else 'Off'
        return lpen

    @exclusive
    def get_loop_modes(self, N):
        self.__range_check(N, 1, self.loops + self.cascades)
        return ['On', 'Off'] if self.combined_event[N-1] != 0 else ['On']

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
        vals = self.get_loop_sp(1, exclusive=False)
        vals.update({
            'air':self.client.read_holding_signed(1922)[0]*self.__get_scalar(1),
            'product':vals['current']
        })
        return vals

    @exclusive
    def set_cascade_sp(self, N, value):
        self.__range_check(N, 1, self.cascades)
        return self.set_loop_sp(N, value, exclusive=False)

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
        return self.get_loop_range(N, exclusive=False)

    @exclusive
    def set_cascade_range(self, N, value):
        self.__range_check(N, 1, self.cascades)
        return self.set_loop_range(N, value, exclusive=False)

    @exclusive
    def get_cascade_en(self, N):
        self.__range_check(N, 1, self.cascades)
        return self.get_loop_en(N, exclusive=False)

    @exclusive
    def set_cascade_en(self, N, value):
        self.__range_check(N, 1, self.cascades)
        return self.set_loop_en(N, value, exclusive=False)

    @exclusive
    def get_cascade_units(self, N):
        self.__range_check(N, 1, self.cascades)
        return self.get_loop_units(N, exclusive=False)

    @exclusive
    def get_cascade_mode(self, N):
        self.__range_check(N, 1, self.cascades)
        return self.get_loop_mode(N, exclusive=False)

    @exclusive
    def get_cascade_modes(self, N):
        self.__range_check(N, 1, self.cascades)
        return self.get_loop_modes(N, exclusive=False)

    @exclusive
    def set_cascade_mode(self, N, value):
        self.__range_check(N, 1, self.cascades)
        return self.set_loop_mode(N, value, exclusive=False)

    @exclusive
    def get_cascade_ctl(self, N):
        self.__range_check(N, 1, self.cascades)
        return {'constant':True, 'current':True}

    @exclusive
    def set_cascade_ctl(self, N, value):
        raise NotImplementedError

    @exclusive
    def get_cascade_deviation(self, N):
        self.__range_check(N, 1, self.cascades)
        vals = self.client.read_holding_signed(1926, 2)
        return {
            'positive': vals[1] * self.__get_scalar(1),
            'negative': vals[0] * self.__get_scalar(1)
        }

    @exclusive
    def set_cascade_deviation(self, N, value):
        self.__range_check(N, 1, self.cascades)
        vals = [
            int(value['negative']/self.__get_scalar(1)),
            int(value['positive']/self.__get_scalar(1))
        ]
        self.client.write_holding_signed(1926, vals)
        self.client.write_holding(25, 0)

    @exclusive
    def get_cascade_power(self, N):
        self.__range_check(N, 1, self.cascades)
        return self.get_loop_power(N, exclusive=False)

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
        if len(self.get_alarm_status(exclusive=False)['active']) > 0:
            return 'Alarm'
        mode = self.client.read_holding(200)[0]
        prof = ['Constant', 'Constant', 'Program Running', 'Program Paused'][mode]
        if self.cond_event:
            return prof if self.get_event(self.cond_event, exclusive=False)['current'] else 'Standby'
        else:
            return prof

    @exclusive
    def get_alarm_status(self):
        aalms, ialms = [], []
        for alm in self.limits:
            if self.__get_digital_input(abs(alm)): #this needs to be configurable
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
    def get_prgm_counter(self):
        try:
            status = self.client.read_holding(4126, 3) #status params: count, profile, step
            self.client.write_holding(4000, (status[1:]))
            prof = self.client.read_holding(4050, 3) #jump step params: profile, step, repeats
            return [
                {
                    'name':'Jump Step %d' % status[2],
                    'start':prof[1],
                    'end':status[2],
                    'cycles':prof[2],
                    'remaining':prof[2]-status[0],
                    'count':status[0]
                }
            ]
        except Exception:
            return []

    @exclusive
    def prgm_next_step(self):
        program = self.get_prgm_cur(exclusive=False)
        nextstep = self.get_prgm_cstep(exclusive=False) + 1
        self.const_start(exclusive=False)
        time.sleep(2)
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
        rpgmi = self.get_prgm_cur(exclusive=False)
        if pgm is None:
            pgm = self.get_prgm(rpgmi, exclusive=False)
        jumps = 0
        for step in pgm['steps']:
            jumps += 1 if step['type'] == 'jump' else 0
            if jumps > 1:
                return 'ERROR:jump qty'
            if step['type'] == 'jump' and step.get('jprofile', rpgmi) != 0:
                return 'ERROR:jump prfl'
        rtime = list(self.client.read_holding(4119, 3)) #[hours,minutes,seconds]
        jump_cnt = self.client.read_holding(4126)[0]
        stepi = self.get_prgm_cstep(exclusive=False) + 1
        ptarget = None
        subtractor = 2
        while ptarget is None and stepi - subtractor > 0:
            if pgm['steps'][stepi-subtractor]['type'] in ['ramprate', 'ramptime', 'soak']:
                ptarget = pgm['steps'][stepi-subtractor]['loops'][0]['target']
            subtractor -= 1
        if ptarget is None:
            ptarget = 0 #useless default
        while stepi < len(pgm['steps']):
            step = pgm['steps'][stepi-1]
            if step['type'] in ['ramptime', 'soak']:
                rtime[0] += step['duration']['hours']
                rtime[1] += step['duration']['minutes']
                rtime[2] += step['duration']['seconds']
                ptarget = step['loops'][0]['target']
            elif step['type'] == 'ramprate':
                diff = abs(step['loops'][0]['target'] - ptarget)
                minutes = diff/step['loops'][0]['rate']
                rtime[1] += int(minutes)
                rtime[2] += int(minutes%60)
                ptarget = step['loops'][0]['target']
            if step['type'] == 'jump' and jump_cnt < step['jcount']:
                jump_cnt += 1
                stepi = step['jstep']
            else:
                stepi += 1
        rtime[1] += int(rtime[2]/60)
        rtime[2] = int(rtime[2]%60)
        rtime[0] += int(rtime[2]/60)
        rtime[1] = int(rtime[1]%60)
        return '%d:%02d:%02d' % tuple(rtime)

    @exclusive
    def get_prgm_name(self, N):
        parsed = re.search(r'([A-Z0-9 ]+)', self.client.read_holding_string(3500+10*(N-1), 10))
        return parsed.group(1).rstrip()

    @exclusive
    def set_prgm_name(self, N, value):
        self.__set_prgm_name(N, value)
        self.client.write_holding(25, 0) #save changes to profiles

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
            self.client.write_holding(4001, 2)
            if num_programs > 0:
                self.client.write_holding(4000, [idx, 1])
                if self.client.read_holding(4003)[0] <= 5:
                    programs.append({'number':idx, 'name':self.get_prgm_name(idx, exclusive=False)})
                    num_programs -= 1
                else:
                    programs.append({'number': idx, 'name': ''})
            else:
                programs.append({'number': idx, 'name': ''})
        return programs

    def __get_prgm_empty(self):
        '''
        create an empty null program
        '''
        dins = [self.client.read_holding(1060+i*2)[0] == 10 for i in range(4)]
        analogs = self.__get_analog_input_setup()
        ret = {
            'name':'PROFILE',
            'steps_available': self.client.read_holding(1219)[0],
            'steps':[{
                'type':'end',
                'start_type':'day',
                'start_date':{'month':1, 'day':1, 'year':2000},
                'start_time':{'day':'sunday', 'hours':0, 'minutes':0, 'seconds':0},
                'loops':[
                    {
                        'enable':True,
                        'target':0,
                        'pidset':1 + 5*i,
                        'gsoak':False,
                        'isCascade': self.cascades > 0 if i == 0 else False,
                        'showEnable': self.combined_event[i] > 0
                    }
                    for i in range(self.loops + self.cascades)
                ],
                'events':[
                    {'number':i, 'value':'off'}
                    for i in range(1, 9) if i not in self.combined_event and i != self.cond_event
                ],
                'wait':{
                    'enable':False,
                    'digital':[
                        {'number':i+1, 'enable':False, 'value':'off'}
                        for i in range(4) if dins[i]
                    ],
                    'analog':[
                        {'number':i+1, 'enable':False, 'value':0.0}
                        for i in range(len(analogs)) if analogs[i] != 'off'
                    ]
                },
                'duration':{'hours':0, 'minutes':0, 'seconds':0},
                'jprofile':0,
                'jstep':0,
                'jcount':0,
                'action':'hold'
            }]
        }
        if self.loops + self.cascades == 1:
            ret['steps'][0]['loops'][0]['rate'] = 0.0
        return ret


    @exclusive
    def get_prgm(self, N):
        if N == 0:
            return self.__get_prgm_empty()
        rbase = 4003 #first register to read
        self.__range_check(N, 1, 40)
        self.client.write_holding(4000, N)
        program = {
            'steps':[],
            'name': self.get_prgm_name(N, exclusive=False),
            'steps_available': self.client.read_holding(1219)[0]
        }
        daylookup = ['daily', 'sun', 'mon', 'tue', 'wed', 'thur', 'fri', 'sat']
        dins = [self.client.read_holding(1060+i*2)[0] == 10 for i in range(4)]
        analogs = self.__get_analog_input_setup()
        for step in range(1, 257):
            self.client.write_holding(4001, step)
            params = self.client.read_holding_signed(rbase, 4062-rbase+1) #registers 4003-4062
            step_params = {
                'type':'soak',
                'start_type':'day',
                'start_date':{'month':1, 'day':1, 'year':2000},
                'start_time':{'day':'sunday', 'hours':0, 'minutes':0, 'seconds':0},
                'loops':[
                    {
                        'enable':True,
                        'target':0,
                        'pidset':1 + 5*i,
                        'gsoak':False,
                        'isCascade': self.cascades > 0 if i == 0 else False,
                        'showEnable': self.combined_event[i] > 0
                    }
                    for i in range(self.loops + self.cascades)
                ],
                'events':[
                    {'number':i, 'value':'off'}
                    for i in range(1, 9) if i not in self.combined_event and i != self.cond_event
                ],
                'wait':{
                    'enable':False,
                    'digital':[
                        {'number':i+1, 'enable':False, 'value':'off'}
                        for i in range(4) if dins[i]
                    ],
                    'analog':[
                        {'number':i+1, 'enable':False, 'value':0.0}
                        for i in range(len(analogs)) if analogs[i] != 'off'
                    ]
                },
                'duration':{'hours':0, 'minutes':0, 'seconds':0},
                'jprofile':0,
                'jstep':0,
                'jcount':0,
                'action':'hold'
            }
            if self.loops + self.cascades == 1:
                step_params['loops'][0]['rate'] = 0
            if params[4003-rbase] == 0:#Auto start
                step_params.update({
                    'type':'autostart',
                    'start_type':['date', 'day'][params[4004-rbase]],
                    'start_date':{
                        'month':params[4005-rbase],
                        'day':params[4006-rbase],
                        'year':params[4007-rbase]
                    },
                    'start_time':{
                        'day':daylookup[params[4008-rbase]],
                        'hours':params[4009-rbase],
                        'minutes':params[4010-rbase],
                        'seconds':params[4011-rbase]
                    }
                })
            elif params[4003-rbase] in [1, 2, 3]: #ramptime, ramprate, soak
                step_params.update({
                    'type': ['', 'ramptime', 'ramprate', 'soak'][params[4003-rbase]],
                    'wait':{'enable': params[4012-rbase] == 1},
                    'events':[
                        {'number':i, 'value':'on' if params[4030-rbase-1+i] else 'off'}
                        for i in range(1, 9) if i not in self.combined_event and i != self.cond_event
                    ],
                    'loops':[
                        {
                            'enable':params[4030-rbase-1+self.combined_event[i]] == 1 \
                                        if self.combined_event[i] else True,
                            'target':params[4044-rbase+i] * self.__get_scalar(i+1),
                            'pidset':params[4046-rbase+i] + 1 + 5*i,
                            'gsoak':params[4048-rbase+i] == 1,
                            'isCascade': self.cascades > 0 if i == 0 else False,
                            'showEnable': self.combined_event[i] > 0
                        }
                        for i in range(self.loops + self.cascades)
                    ]
                })
                if self.loops + self.cascades == 1:
                    step_params['loops'][0]['rate'] = 0
                if params[4003-rbase] != 2:
                    step_params['duration'] = {
                        'hours':params[4009-rbase],
                        'minutes':params[4010-rbase],
                        'seconds':params[4011-rbase]
                    }
                else:
                    step_params['loops'][0]['rate'] = params[4043-rbase] / 10.0
                step_params['wait'].update({
                    'digital':[
                        {
                            'number':i+1,
                            'enable':params[4013-rbase+i] != 0,
                            'value':['off', 'off', 'on'][params[4013-rbase+i]]
                        }
                        for i in range(4) if dins[i]
                    ],
                    'analog':[
                        {
                            'number':i+1,
                            'enable':params[4021-rbase+i*2] == 1,
                            'value':params[4022-rbase+i*2] * self.__get_scalar(i+1)
                        }
                        for i in range(len(analogs)) if analogs[i] != 'off'
                    ]
                })
            elif params[4003-rbase] == 4:#Jump
                #if we are jumping to the same profile hprofile will be 0
                prof_num = params[4050-rbase]
                prof_num = 0 if prof_num == N else prof_num
                step_params.update({
                    'type':'jump',
                    'jprofile':prof_num,
                    'jstep':params[4051-rbase],
                    'jcount':params[4052-rbase]
                })
            elif params[4003-rbase] == 5:#End
                step_params.update({
                    'type':'end',
                    'action':['hold', 'controloff', 'alloff', 'idle'][params[4060-rbase]],
                    'loops':[
                        {
                            'enable':True,
                            'target':params[4061-rbase+i]*self.__get_scalar(i+1),
                            'pidset':1 + 5*i,
                            'gsoak':False,
                            'isCascade': self.cascades > 0 if i == 0 else False,
                            'showEnable': self.combined_event[i] > 0
                        }
                        for i in range(self.loops + self.cascades)
                    ]
                })
                if self.loops + self.cascades == 1:
                    step_params['loops'][0]['rate'] = 0
            else:#Not a program
                raise ControllerInterfaceError('Program #%d does not exist' % N)
            program['steps'].append(step_params)
            if step_params['type'] == 'end':
                break
        return program

    @exclusive
    def set_prgm(self, N, value):
        self.__range_check(N, 1, 40)
        try:
            self.get_prgm_steps(N, exclusive=False)
            self.__edit_prgm(N, value)
        except ValueError:
            N = self.__create_prgm(value)
        self.client.write_holding(25, 0) #save the new program
        return N

    @exclusive
    def prgm_delete(self, N):
        self.__range_check(N, 1, 40)
        self.client.write_holding(4000, [N, 1, 3]) #program #, step 1, action delete
        self.client.write_holding(25, 0) #save changes to profiles


    @exclusive
    def process_controller(self, update=True):
        part_no = 'Watlow F4'
        self.client.write_holding(300, self.client.read_holding(300)[0]) #fail fast!
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
        self.combined_event = [
            self.cascade_event[0] if self.cascades > 0 else self.loop_event[0],
        ]
        if self.loops == 2:
            self.combined_event.append(self.loop_event[1])
        elif self.cascades == 1 and self.loops == 1:
            self.combined_event.append(self.loop_event[0])
        return part_no

    @exclusive
    def get_network_settings(self):
        raise NotImplementedError

    @exclusive
    def set_network_settings(self, value):
        raise NotImplementedError

    def get_operation_modes(self):
        if self.cond_event is None:
            return ['constant', 'program']
        else:
            return ['standby', 'constant', 'program']
