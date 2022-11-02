'''
Upper level interface for the Watlow F4T controller

:copyright: (C) Espec North America, INC.
:license: MIT, see LICENSE for more details.
:Updated: 2020, 2022 Paul Nong-Laolam <pnong-laolam@espec.com> 
:Important Notes:
     The following code has been updated and tested to run on 
     Python 3.6.8 and above.  
'''
#pylint: disable=W0703
import time
import datetime
import struct
from chamberconnectlibrary.modbus import ModbusError, ModbusRTU, ModbusTCP
from chamberconnectlibrary.controllerinterface import ControllerInterface, exclusive
from chamberconnectlibrary.controllerinterface import ControllerInterfaceError

class WatlowF4T(ControllerInterface):
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
        cond_event_toggle (bool): True = toggled, False = momentary (default=False)
        limits (list(bool)): list of slots where limit controllers are installed (default=[5])
        loop_event (list(int)): list of events #'s that enable/disble loops (default=[0,2,0,0])
        cascade_event (list(int)): list of events #'s that enbl/dis casc.lps(default=[0,0,0,0])
        cascade_ctl_event (list(int)): list of event#'s enbl/dis casc. mode (default=[0,0,0,0])
        waits (list(str)): Configuration for the 4 waitfor inputs each index can be::
            "A" -- Analog
            "D" -- Digital
            "" -- Off(default x4)
        time_zone (None): Not currently used
        run_module (int): The module that the "Chamber Running" output is on (default=1)
        run_io (int): The output of the run_module that indicates chamber running (default=1)
        alarms (int): The number of alarms that the controller has (default=6)
        profiles (bool): If True the controller supports profiles(programs) (default=False)
        lock (RLock): The locking method to use when accessing the controller (default=RLock())
    '''

    def __init__(self, **kwargs):
        self.iwatlow_val_dict, self.client, self.loops, self.cascades = None, None, None, None
        self.init_common(**kwargs)
        self.cond_event = kwargs.get('cond_event', 9)
        self.cond_event_toggle = kwargs.get('cond_event_toggle', False)

        #list of limits needs to be supplied 1,2,3,4,5,6 are posible
        self.limits = kwargs.get('limits', [5])

        #list of events that may enable or disable a loop index 0=loop1, events=1-8 0=not used
        self.loop_event = kwargs.get('loop_event', [0, 0, 0, 0])

        #list of events that may enable or disable a cascade loop
        self.cascade_event = kwargs.get('cascade_event', [0, 0, 0, 0])

        #list of events that may enable or dsiable simple setpoint mode on a cascade loop
        self.cascade_ctl_event = kwargs.get('cascade_ctl_event', [0, 0, 0, 0])

        # waits 1-4 A= analog wait, D= digital wait
        self.waits = kwargs.get('waits', ['', '', '', ''])
        self.time_zone = kwargs.get('time_zone', None)
        self.run_module = kwargs.get('run_module', 1)
        self.run_io = kwargs.get('run_io', 1)
        self.events = 8

        #these are detectable from the part number (call process_partno())
        self.alarms = kwargs.get('alarms', 6)
        self.profiles = kwargs.get('profiles', False)
        self.named_loop_map_list = kwargs.get('loop_names', [])

        self.__update_loop_map()
        self.watlow_val_dict = {
            1:'2', 2:'3', 3:'50Hz', 4:'60Hz', 9:'ambientError',
            10:'auto', 11:'b', 13: 'both', 15:'C', 17:'closeOnAlarm',
            22:'current', 23:'d', 24:'deviationAlarm', 26:'e', 27:'end', 28:'error',
            30:'F', 31:'factory', 32:'fail', 34:'fixedTimeBase', 37:'high', 39:'hours',
            40:'hundredths', 44:'inputDryContact', 46:'j', 47:'hold', 48:'k', 49:'latching',
            53:'low', 54:'manual', 56:'millivolts', 57:'minutes', 58:'n', 59:'no',
            60: 'nonLatching', 61:'none', 62:'off', 63:'on', 65:'open', 66:'openOnAlarm',
            68:'output',
            73:'power', 75:'process', 76:'processAlarm',
            80:'r', 81:'ramprate', 84:'s', 85:'setPoint', 87:'soak', 88:'startup',
            93:'t', 94:'tenths', 95:'thermocouple', 96:'thousandths',
            100:'user', 103:'variableTimeBase', 104:'volts', 105:'whole', 106:'yes',
            108:'silenceAlarms',
            112:'milliamps', 113:'rtd100ohm', 114:'rtd1000ohm', 116:'jump',
            127:'shorted', 129:'clear',
            138:'ok', 139:'badCalibrationData',
            140:'measurementError', 141:'rtdError', 142:'analogInput', 146:'pause', 147:'resume',
            148:'terminate', 149: 'running',
            155:'1kpotentiometer',
            160:'heatPower', 161:'coolPower',
            180:'custom',
            193:'inputVoltage',
            204:'ignore',
            240:'math', 241:'processValue', 242:'setPointClosed', 243:'setPointOpen',
            245:'variable', 246:'notsourced',
            251:'notStarted', 252:'complete', 253: 'terminated',
            1037:'counts',
            1276:'electrical',
            1360:'10k', 1361:'20k', 1375:'add',
            1423:'mathError', 1448:'5k', 1449:'40k', 1451:'curveA', 1452:'curveB', 1453:'curveC',
            1456:'up', 1457:'down',
            1532:'specialFunctionOutput1', 1533:'specialFunctionOutput2',
            1534:'specialFunctionOutput3', 1535:'specialFunctionOutput4',
            1538:'%RH', 1540:'absoluteTemperature', 1541:'relativeTemperature', 1542:'wait',
            1557:'nc',
            1617:'stale', 1667:'safe',
            1740:'encoder', 1770:'edit', 1771:'insert', 1772:'delete', 1779:'profileNumber',
            1782: 'start', 1783: 'timedStart',
            1794:'cascadeHeatPower', 1795:'cascadeCoolPower', 1796:'cascadePower',
            1797:'cascadeSetPointClosed', 1798:'cascadeSetPointOpen',
            1927:'instant', 1928:'ramptime', 1964:'above', 1965:'below',
            10001:'condition'
        }

    def inv_watlow_val_dict(self, key):
        '''
        Get the key by a given value from the dictionary self.watlowValDict

        Args:
            key (str): The value to find the key for in self.watlowValDict
        Returns:
            Str
        '''
        try:
            return self.iwatlow_val_dict[key]
        except Exception:
            self.iwatlow_val_dict = {v: k for k, v in list(self.watlow_val_dict.items())}
            return self.iwatlow_val_dict[key]

    def __update_loop_map(self):
        '''
        update the loop map.
        '''
        self.loop_map = [{'type':'cascade', 'num':j+1} for j in range(self.cascades)]
        self.loop_map += [{'type':'loop', 'num':j+1} for j in range(self.loops)]
        if len(self.named_loop_map_list) == len(self.loop_map):
            self.named_loop_map = {name:i for i, name in enumerate(self.named_loop_map_list)}

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

    def mod_to_float(self, val):
        '''
        Convert unsigned ints from modbus to a float expects list of length=2.
        '''
        return round(struct.unpack('f', struct.pack('HH', val[0], val[1]))[0], 1)

    #required (ABC) items

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
        Interact directly with the controller

        Args:
            command (str): A modbus packet PDU (ie function code + data)
        Returns:
            str. The raw modbus response from the controller.
        '''
        return self.client.interact(command)

    @exclusive
    def get_datetime(self):
        dtl = self.client.read_holding(14664, 12)
        return datetime.datetime(
            hour=dtl[0],
            minute=dtl[2],
            second=dtl[4],
            month=dtl[6],
            day=dtl[8],
            year=dtl[10]
        )

    @exclusive
    def set_datetime(self, value):
        self.client.write_holding(14664, [value.hour])
        self.client.write_holding(14666, [value.minute])
        self.client.write_holding(14668, [value.second])
        self.client.write_holding(14670, [value.month])
        self.client.write_holding(14672, [value.day])
        self.client.write_holding(14674, [value.year])

    @exclusive
    def get_refrig(self):
        raise NotImplementedError

    @exclusive
    def set_refrig(self, value):
        raise NotImplementedError

    @exclusive
    def get_loop_sp(self, N):
        self.__range_check(N, 1, self.loops)
        return {'constant': self.client.read_holding_float(2782+(N-1)*160)[0],
                'current': self.client.read_holding_float(2810+(N-1)*160)[0]}

    @exclusive
    def set_loop_sp(self, N, value):
        value = value['constant'] if isinstance(value, dict) else value
        self.__range_check(N, 1, self.loops)
        self.client.write_holding_float(2782+(N-1)*160, value)

    @exclusive
    def get_loop_pv(self, N):
        reg = 2820+(N-1)*160
        self.__range_check(N, 1, self.loops)
        return {'air': self.client.read_holding_float(reg)[0]}

    @exclusive
    def set_loop_range(self, N, value):
        self.__range_check(N, 1, self.loops)
        self.client.write_holding_float(2776+(N-1)*160, value['max'])
        self.client.write_holding_float(2774+(N-1)*160, value['min'])

    @exclusive
    def get_loop_range(self, N):
        self.__range_check(N, 1, self.loops)
        return {'max':self.client.read_holding_float(2776+(N-1)*160)[0],
                'min':self.client.read_holding_float(2774+(N-1)*160)[0]}

    @exclusive
    def get_loop_en(self, N):
        self.__range_check(N, 1, self.loops)
        cmd = self.watlow_val_dict[self.client.read_holding(2814+(N-1)*160, 1)[0]] != 'off'
        if self.loop_event[N-1] != 0:
            eve = self.get_event(self.loop_event[N-1], exclusive=False)['constant']
            if self.run_module:
                running = self.__read_io(self.run_module, self.run_io, exclusive=False)
            else:
                running = False
            return {'constant': eve, 'current': eve if running else cmd}
        else:
            return {'constant': True, 'current': cmd}


    @exclusive
    def set_loop_en(self, N, value):
        self.__range_check(N, 1, self.loops)
        value = value['constant'] if isinstance(value, dict) else value
        if self.watlow_val_dict[self.client.read_holding(2730+(N-1)*160, 1)[0]] == 'off' and value:
            self.client.write_holding(2730+(N-1)*160, 10)
        if self.loop_event[N-1] != 0:
            self.set_event(self.loop_event[N-1], value, exclusive=False)

    @exclusive
    def get_loop_units(self, N):
        self.__range_check(N, 1, self.loops)
        try:
            act_num = self.loop_map.index({'type':'loop', 'num':N}) + 1
            return self.__profile_units(act_num, exclusive=False)
        except ControllerInterfaceError:
            return "ERROR"

    @exclusive
    def set_loop_mode(self, N, value):
        self.__range_check(N, 1, self.loops)
        value = value['constant'] if isinstance(value, dict) else value
        if value in ['Off', 'OFF', 'off']:
            self.set_loop_en(N, False, exclusive=False)
        elif value in ['On', 'ON', 'on']:
            self.set_loop_en(N, True, exclusive=False)
        elif value in ['Auto', 'AUTO', 'auto']:
            self.set_loop_en(N, True, exclusive=False)
            self.client.write_holding(2730+(N-1)*160, 10)
        elif value in ['Manual', 'MANUAL', 'manual']:
            self.set_loop_en(N, True, exclusive=False)
            self.client.write_holding(2730+(N-1)*160, 54)
        else:
            raise ValueError('mode must be "Off" or "Auto" or "Manual" or "On"')

    @exclusive
    def get_loop_mode(self, N):
        self.__range_check(N, 1, self.loops)
        tdict = {62:'Off', 10:'Auto', 54:'Manual'}
        lpen = self.get_loop_en(N, exclusive=False)
        if lpen['constant']:
            con = tdict[self.client.read_holding(2730+(N-1)*160, 1)[0]]
        else:
            con = 'Off'
        if lpen['current']:
            curmode = tdict[self.client.read_holding(2814+(N-1)*160, 1)[0]]
            cur = curmode if curmode != 'Off' else 'Auto'
        else:
            cur = 'Off'
        return {'current': cur, 'constant': con}

    def get_loop_modes(self, N):
        self.__range_check(N, 1, self.loops)
        if self.loop_event[N-1] != 0:
            return ['Off', 'Auto', 'Manual']
        else:
            return ['Auto', 'Manual']

    @exclusive
    def get_loop_power(self, N):
        self.__range_check(N, 1, self.loops)
        return {'constant':self.client.read_holding_float(2784+(N-1)*160)[0],
                'current':self.client.read_holding_float(2808+(N-1)*160)[0]}

    @exclusive
    def set_loop_power(self, N, value):
        self.__range_check(N, 1, self.loops)
        if isinstance(value, dict):
            value = value['constant']
        self.client.write_holding_float(2784+(N-1)*160, value)

    @exclusive
    def get_cascade_sp(self, N):
        self.__range_check(N, 1, self.cascades)
        air = self.client.read_holding_float(4188+(N-1)*200)[0]
        prod = self.client.read_holding_float(4190+(N-1)*200)[0]
        return {'constant':self.client.read_holding_float(4042+(N-1)*200)[0],
                'current':prod if self.get_cascade_ctl(N, exclusive=False)['current'] else air,
                'air':air,
                'product':prod}

    @exclusive
    def set_cascade_sp(self, N, value):
        self.__range_check(N, 1, self.cascades)
        value = value['constant'] if isinstance(value, dict) else value
        constreg = 4042+(N-1)*200
        self.client.write_holding_float(constreg, value)

    @exclusive
    def get_cascade_pv(self, N):
        self.__range_check(N, 1, self.cascades)
        return {'product': self.client.read_holding_float(4180+(N-1)*200)[0],
                'air': self.client.read_holding_float(4182+(N-1)*200)[0]}

    @exclusive
    def get_cascade_range(self, N):
        self.__range_check(N, 1, self.cascades)
        return {'max':self.client.read_holding_float(4036+(N-1)*200)[0],
                'min':self.client.read_holding_float(4034+(N-1)*200)[0]}

    @exclusive
    def set_cascade_range(self, N, value):
        self.__range_check(N, 1, self.cascades)
        self.client.write_holding_float(4036+(N-1)*200, value['max'])
        self.client.write_holding_float(4034+(N-1)*200, value['min'])

    @exclusive
    def get_cascade_en(self, N):
        self.__range_check(N, 1, self.cascades)
        cmd = self.watlow_val_dict[self.client.read_holding(4012+(N-1)*200, 1)[0]] != 'off'
        if self.cascade_event[N-1] != 0:
            eve = self.get_event(self.cascade_event[N-1], exclusive=False)['constant']
            if self.run_module:
                running = self.__read_io(self.run_module, self.run_io, exclusive=False)
            else:
                running = False
            return {'constant': eve, 'current': eve if running else cmd}
        else:
            return {'constant': True, 'current': cmd}

    @exclusive
    def set_cascade_en(self, N, value):
        self.__range_check(N, 1, self.cascades)
        value = value['constant'] if isinstance(value, dict) else value
        if self.watlow_val_dict[self.client.read_holding(4010+(N-1)*200, 1)[0]] == 'off' and value:
            self.client.write_holding(4010+(N-1)*200, 10)
        if self.cascade_event[N-1] != 0:
            self.set_event(self.cascade_event[N-1], value, exclusive=False)

    @exclusive
    def get_cascade_units(self, N):
        self.__range_check(N, 1, self.cascades)
        try:
            act_num = self.loop_map.index({'type':'cascade', 'num':N}) + 1
            return self.__profile_units(act_num, exclusive=False)
        except ControllerInterfaceError:
            return "ERROR"

    @exclusive
    def set_cascade_mode(self, N, value):
        self.__range_check(N, 1, self.cascades)
        value = value['constant'] if isinstance(value, dict) else value
        if value in ['Off', 'OFF', 'off']:
            self.set_cascade_en(N, False, exclusive=False)
        elif value in ['On', 'ON', 'on']:
            self.set_cascade_en(N, True, exclusive=False)
        elif value in ['Auto', 'AUTO', 'auto']:
            self.set_cascade_en(N, True, exclusive=False)
            self.client.write_holding(4010+(N-1)*200, 10)
        elif value in ['Manual', 'MANUAL', 'manual']:
            self.set_cascade_en(N, True, exclusive=False)
            self.client.write_holding(4010+(N-1)*200, 54)
        else:
            raise ValueError('mode must be "Off" or "Auto" or "Manual" or "On"')

    @exclusive
    def get_cascade_mode(self, N):
        self.__range_check(N, 1, self.cascades)
        tdict = {62:'Off', 10:'Auto', 54:'Manual'}
        lpen = self.get_cascade_en(N, exclusive=False)
        if lpen['constant']:
            con = tdict[self.client.read_holding(4010+(N-1)*200, 1)[0]]
        else:
            con = 'Off'
        if lpen['current']:
            curmode = tdict[self.client.read_holding(4012+(N-1)*200, 1)[0]]
            cur = curmode if curmode != 'Off' else 'Auto'
        else:
            cur = 'Off'
        return {'current':cur, 'constant':con}

    def get_cascade_modes(self, N):
        self.__range_check(N, 1, self.cascades)
        if self.cascade_event[N-1] != 0:
            return ['Off', 'Auto', 'Manual']
        else:
            return ['Auto', 'Manual']

    @exclusive
    def get_cascade_ctl(self, N):
        self.__range_check(N, 1, self.cascades)
        cmod = self.client.read_holding(4200+(N-1)*200, 1)[0] == 62
        if self.cascade_ctl_event[N-1] != 0:
            return self.get_event(self.cascade_ctl_event[N-1], exclusive=False)
        else:
            cmod = self.client.read_holding(4200+(N-1)*200, 1)[0] == 62
            return {'constant': cmod, 'current': cmod}

    @exclusive
    def set_cascade_ctl(self, N, value):
        self.__range_check(N, 1, self.cascades)
        value = value['constant'] if isinstance(value, dict) else value
        if self.client.read_holding(4200+(N-1)*200, 1)[0] == 63 and value:
            self.client.write_holding(4200+(N-1)*200, 62)
        if self.cascade_ctl_event[N-1] != 0:
            self.set_event(self.cascade_ctl_event[N-1], value, exclusive=False)

    @exclusive
    def get_cascade_deviation(self, N):
        self.__range_check(N, 1, self.cascades)
        return {'positive': self.client.read_holding_float(4170+(N-1)*200)[0],
                'negative': self.client.read_holding_float(4168+(N-1)*200)[0]}

    @exclusive
    def set_cascade_deviation(self, N, value):
        self.__range_check(N, 1, self.cascades)
        self.client.write_holding_float(4168+(N-1)*200, 0-abs(value['negative']))
        self.client.write_holding_float(4170+(N-1)*200, value['positive'])

    @exclusive
    def get_cascade_power(self, N):
        self.__range_check(N, 1, self.cascades)
        return {'constant':self.client.read_holding_float(4044+(N-1)*200)[0],
                'current':self.client.read_holding_float(4178+(N-1)*200)[0]}

    @exclusive
    def set_cascade_power(self, N, value):
        self.__range_check(N, 1, self.cascades)
        if isinstance(value, dict):
            value = value['constant']
        self.client.write_holding_float(4044+(N-1)*200, value)

    @exclusive
    def get_event(self, N):
        #62=0ff, 63=on
        #      prof1  prof2  prof3  prof4  prof5  prof6  prof7  prof8  key1  key2  key3  key4
        reg = [16594, 16596, 16598, 16600, 16822, 16824, 16826, 16828, 6844, 6864, 6884, 6904][N-1]
        self.__range_check(N, 1, 12)
        val = self.watlow_val_dict[self.client.read_holding(reg, 1)[0]] == 'on'
        return {'current':val, 'constant':val}

    @exclusive
    def set_event(self, N, value):
        #62=0ff, 63=on
        #      prof1  prof2  prof3  prof4  prof5  prof6  prof7  prof8  key1  key2  key3  key4
        reg = [16594, 16596, 16598, 16600, 16822, 16824, 16826, 16828, 6844, 6864, 6884, 6904][N-1]
        kpress = 6850 +(N-8-1)*20 #down=1457, #up = 1456
        self.__range_check(N, 1, 12)
        value = value['constant'] if isinstance(value, dict) else value
        if N <= 8:
            if value:
                self.client.write_holding(reg, self.inv_watlow_val_dict('on'))
            else:
                self.client.write_holding(reg, self.inv_watlow_val_dict('off'))
        elif value:
            self.client.write_holding(kpress, self.inv_watlow_val_dict('down'))
        else:
            self.client.write_holding(kpress, self.inv_watlow_val_dict('up'))

    @exclusive
    def get_status(self):
        prgmstate = self.client.read_holding(16568, 1)[0]
        if prgmstate == 149:
            return "Program Running"
        elif prgmstate == 146:
            return "Program Paused"
        elif prgmstate == 1783:
            if self.__read_io(self.run_module, self.run_io, exclusive=False):
                return "Constant (Program Calendar Start)"
            else:
                return "Standby (Program Calendar Start)"
        elif not self.get_alarm_status(exclusive=False)['active']:
            if self.__read_io(self.run_module, self.run_io, exclusive=False):
                return "Constant"
            else:
                return "Standby"
        else:
            return "Alarm"

    @exclusive
    def get_alarm_status(self):
        aalms = []
        ialms = []
        for i in range(0, self.alarms):
            if self.client.read_holding(1356+100*i, 1)[0] in [88, 61, 12]:
                ialms.append(i+1)
            else:
                aalms.append(i+1)
        for i in self.limits:
            state = self.watlow_val_dict[self.client.read_holding(11250+(i-1)*60, 1)[0]] == 'error'
            cerror = self.watlow_val_dict[self.client.read_holding(11288+(i-1)*60, 1)[0]] != 'none'
            status = self.watlow_val_dict[self.client.read_holding(11264+60*(i-1), 1)[0]] == 'fail'
            if state or cerror or status:
                aalms.append(20+i)
            else:
                ialms.append(20+i)
        return {'active': aalms, 'inactive': ialms}

    @exclusive
    def const_start(self):
        status = self.get_status(exclusive=False)
        if "Program" in status:
            self.client.write_holding(16566, self.inv_watlow_val_dict('terminate'))
            time.sleep(0.5)
        #io is actual on/off switch
        if not self.__read_io(self.run_module, self.run_io, exclusive=False):
            self.set_event(self.cond_event, True, exclusive=False)

        #we can be "running" while in standby (standby only means loop 1 active mode is off)
        if "Standby" in status and self.cascades == 0:
            self.set_loop_en(1, True, exclusive=False)
        elif "Standby" in status:
            self.set_cascade_en(1, True, exclusive=False)

    @exclusive
    def stop(self):
        #status = self.get_status(exclusive=False)
        if self.__read_io(self.run_module, self.run_io, exclusive=False):
            if self.cond_event_toggle:
                self.set_event(self.cond_event, False, exclusive=False)
            else:
                self.set_event(self.cond_event, True, exclusive=False)

    @exclusive
    def prgm_start(self, N, step):
        self.__range_check(N, 1, 40)
        if step > self.get_prgm_steps(N, exclusive=False):
            raise ControllerInterfaceError(f'Program #{N} does not have step #{step}')
        if self.get_status(exclusive=False).find("Program") >= 0:
            self.client.write_holding(16566, self.inv_watlow_val_dict('terminate'))
            time.sleep(2)
        self.client.write_holding(16558, N) #profile to start
        self.client.write_holding(16560, step) #step to start
        self.client.write_holding(16562, self.inv_watlow_val_dict('start')) #start the profile

    @exclusive
    def prgm_pause(self):
        self.client.write_holding(16566, self.inv_watlow_val_dict('pause'))

    @exclusive
    def prgm_resume(self):
        #none(61),pause(146),terminate(148)
        self.client.write_holding(16564, self.inv_watlow_val_dict('resume'))

    @exclusive
    def prgm_next_step(self):
        program = self.get_prgm_cur(exclusive=False)
        nextstep = self.get_prgm_cstep(exclusive=False) + 1
        self.const_start(exclusive=False)
        time.sleep(1)
        self.prgm_start(program, nextstep, exclusive=False)

    @exclusive
    def get_prgm_counter(self):
        return []

    @exclusive
    def get_prgm_cur(self):
        return self.client.read_holding(16588, 1)[0]

    @exclusive
    def get_prgm_cstep(self):
        return self.client.read_holding(16590, 1)[0]

    @exclusive
    def get_prgm_cstime(self):
        data = self.client.read_holding(16622, 5)
        return "%d:%02d:%02d" % (data[4], data[2], data[0])

    @exclusive
    def get_prgm_time(self, pgm=None):
        data = self.client.read_holding(16570, 3)
        return "%d:%02d:00" % (data[2], data[0])

    @exclusive
    def get_prgm_name(self, N):
        reg = 16886+(N-1)*40
        self.__range_check(N, 1, 40)
        if not self.profiles:
            raise ControllerInterfaceError("This watlow does not impliment profiles")
        return self.client.read_holding_string(reg, 20)

    @exclusive
    def get_prgm_steps(self, N):
        self.client.write_holding(18888, N)
        return self.client.read_holding(18920, 1)[0]

    def set_prgm_name(self, N, value):
        raise NotImplementedError

    @exclusive
    def get_prgms(self):
        return [{'number':i, 'name':self.get_prgm_name(i, exclusive=False)} for i in range(1, 41)]

    @exclusive
    def get_prgm(self, N):
        def event_mod(vals, event):
            '''Get event from events/gs register block'''
            event -= 1
            if event < 4:
                return self.watlow_val_dict[vals[8+event*2]]
            else:
                return self.watlow_val_dict[vals[24+(event-4)*2]]
        if N == 0:
            return self.__get_prgm_empty()
        self.__range_check(N, 1, 40)
        if not self.profiles:
            raise ControllerInterfaceError("This watlow does not impliment profiles")
        self.client.write_holding(18888, N) #set active profile
        step_count = self.client.read_holding(18920, 1)[0] #get the number of steps in the profile
        if not step_count > 0:
            raise ControllerInterfaceError(f'Profile {N} does not exist.')
        prgm_dict = {'name':self.client.read_holding_string(18606, 20),
                     'log':self.client.read_holding(19038, 1)[0] == 106}
        #is wait a valid step type
        haswaits = self.waits[0] != '' or self.waits[1] != ''
        haswaits = haswaits or self.waits[2] != '' or self.waits[3] != ''
        prgm_dict['haswaits'] = haswaits
        prgm_dict['hasenables'] = sum(self.loop_event + self.cascade_event) > 0
        ranges, gsd, steps = [], [], []
        for i in range(self.loops + self.cascades):
            tmap = self.loop_map[i]
            gsd.append({'value':self.client.read_holding_float(19086+i*2)[0]})
            if tmap['type'] == 'loop':
                ranges.append(self.get_loop_range(tmap['num'], exclusive=False))
            else:
                ranges.append(self.get_cascade_range(tmap['num'], exclusive=False))
        for i in range(step_count):
            ldata, wdata = [], []
            step_type = self.watlow_val_dict[self.client.read_holding(19094+170*i, 1)[0]]
            sdata = {'type':step_type} #step type
            if step_type in ['soak', 'ramptime', 'instant']: # this step has duration.
                duration = self.client.read_holding(19096+170*i, 6)
                sdata['duration'] = {
                    'hours':duration[0],
                    'minutes':duration[2],
                    'seconds':duration[4]
                }
            else:
                sdata['duration'] = {'hours':0, 'minutes':0, 'seconds':0}
            if step_type in ['instant', 'ramptime']:
                params = self.client.read_holding(19114+170*i, 8) #targets
            if step_type == 'ramprate':
                params = self.client.read_holding(19106+170*i, 16) #rates and targets
            if step_type == 'end':
                params = self.client.read_holding(19170+i*170, 7) #endmodes

            #get all guaranteed soak enables and events
            gse_event = self.client.read_holding(19138+170*i, 32)

            for j in range(self.cascades + self.loops):
                tmap = self.loop_map[j]
                if tmap['type'] == 'loop':
                    enable_event = self.loop_event[tmap['num']-1]
                else:
                    enable_event = self.cascade_event[tmap['num']-1]
                clp = ranges[j].copy()
                clp.update({
                    'mode':'',
                    'gsoak':False,
                    'target':0.0,
                    'rate':0.0,
                    'showEnable': False,
                    'isCascade': False,
                    'cascade': False
                })
                if step_type == 'ramprate':
                    clp['target'] = self.mod_to_float(params[8+j*2:10+j*2])
                    clp['rate'] = self.mod_to_float(params[j*2:2+j*2])
                elif step_type in ['instant', 'ramptime']:
                    clp['target'] = self.mod_to_float(params[j*2:2+j*2])
                elif step_type == 'end':
                    if params[j*2] == 100:
                        clp['mode'] = 'user'
                    elif params[j*2] == 62:
                        clp['mode'] = 'off'
                    else:
                        clp['mode'] = 'hold'
                    clp['enable'] = True if enable_event == 0 or params[j*2] != 62 else False
                #if stepType in ['instant','ramptime','ramprate','soak']:
                clp['gsoak'] = gse_event[j*2] == 63
                clp['showEnable'] = enable_event != 0
                clp['enable'] = True
                if enable_event != 0:
                    clp['enable'] = event_mod(gse_event, enable_event) == 'on'
                if tmap['type'] == 'cascade':
                    clp['isCascade'] = True
                    clp['cascade'] = event_mod(gse_event,
                                               self.cascade_ctl_event[tmap['num']-1]) == 'on'
                ldata.append(clp)
            sdata['loops'] = ldata
            wdraw = self.client.read_holding(19122+i*170, 16)
            for j in range(4):
                if self.waits[j]:
                    cwt = wdraw[j*4]
                    cws = self.mod_to_float(wdraw[2+j*4:4+j*4])
                    wts = self.watlow_val_dict[cwt]
                    wdata.append({'number':j+1, 'condition':wts, 'value':cws})
            sdata['waits'] = wdata
            jraw = self.client.read_holding(19102+i*170, 3)
            sdata.update({'jstep':jraw[0], 'jcount':jraw[2]})
            sdata['events'] = [{'number':j+1, 'value':event_mod(gse_event, j+1)} for j in range(8)]
            steps.append(sdata)
        prgm_dict['steps'] = steps
        prgm_dict['gs_dev'] = gsd
        return prgm_dict

    @exclusive
    def set_prgm(self, N, prgm):
        def event_number(event_number, event_value):
            '''Set event from events/gs register block'''
            if event_number < 5:
                self.client.write_holding(19146+offset+(event_number-1)*2,
                                          self.inv_watlow_val_dict(event_value))
            else:
                self.client.write_holding(19162+offset+(event_number-5)*2,
                                          self.inv_watlow_val_dict(event_value))
        self.client.write_holding(18888, N) #set active profile
        self.client.write_holding(18890, 1375) #Set mode Add program
        self.client.write_holding_string(18606, prgm['name'])#set program name
        self.client.write_holding(19038, 106 if prgm['log'] else 59) #set log mode
        for i, val in enumerate(prgm['gs_dev']): #set guarenteed soak deviations
            self.client.write_holding_float(19086+i*2, val['value'])
        for stnm, stp in enumerate(prgm['steps']):
            offset = stnm*170
            #step type
            self.client.write_holding(19094+offset, self.inv_watlow_val_dict(stp['type']))
            for val in stp['events']:
                event_number(val['number'], val['value'])
            if stp['type'] == 'jump':
                self.client.write_holding(19102+offset, stp['jstep']) #jump step target
                self.client.write_holding(19104+offset, stp['jcount']) #jump count
            if stp['type'] == 'wait':
                for cwt in stp['waits']:
                     # wait condition
                    self.client.write_holding(19122+offset+(cwt['number']-1)*4,
                                              self.inv_watlow_val_dict(cwt['condition']))
                     # wait value
                    self.client.write_holding_float(19124+offset+(cwt['number']-1)*4, cwt['value'])
            if stp['type'] in ['soak', 'instant', 'ramptime', 'ramprate', 'end']:
                for i, clp in enumerate(stp['loops']):
                    cmap = self.loop_map[i]
                    if stp['type'] == 'ramprate': #write ramp rate
                        self.client.write_holding_float(19106+offset+i*2, clp['rate'])
                    if stp['type'] in ['ramprate', 'ramptime', 'instant']: #write target value
                        self.client.write_holding_float(19114+offset+i*2, clp['target'])
                    if stp['type'] == 'end': #write end mode
                        self.client.write_holding(19170+offset+i*2,
                                                  self.inv_watlow_val_dict(clp['mode']))
                    if stp['type'] != 'end': # guarenteed soak
                        self.client.write_holding(19138+offset+i*2,
                                                  63 if clp['gsoak'] else 62)
                        if cmap['type'] == 'loop':
                            lpevt = self.loop_event[cmap['num']-1]
                        else:
                            lpevt = self.cascade_event[cmap['num']-1]
                        if lpevt > 0:
                            event_number(lpevt, 'on' if clp['enable'] else 'off')
                        if cmap['type'] == 'cascade' and self.cascade_ctl_event[cmap['num']-1] > 0:
                            event_number(self.cascade_ctl_event[cmap['num']-1],
                                         'on' if clp['cascade'] else 'off')
            else:
                for evt in self.loop_event + self.cascade_event + self.cascade_ctl_event:
                    if evt > 0:
                        event_number(evt, 'nc')
            if stp['type'] in ['soak', 'instant', 'ramptime']:
                self.client.write_holding(19100+offset, stp['duration']['seconds'])
                self.client.write_holding(19098+offset, stp['duration']['minutes'])
                self.client.write_holding(19096+offset, stp['duration']['hours'])
            #set condition event to on unless its an end step with both loops off.
            if self.cond_event > 0 and self.cond_event <= 8:
                run = True
                if 'loops' in stp and 'mode' in stp['loops'][0]:
                    run = False
                    for mod in stp['loops']:
                        if mod['mode'] != 'off':
                            run = True
                event_number(self.loop_event[i], 'on' if run else 'off')

    @exclusive
    def prgm_delete(self, N):
        self.__range_check(N, 1, 40)
        if not self.profiles:
            raise ControllerInterfaceError("This watlow does not impliment profiles")
        try:
            self.client.write_holding(18888, N) #set active profile
            self.client.write_holding(18890, self.inv_watlow_val_dict('delete')) #delete profile
        except ModbusError as exp:
            exp.message = f'Cannot delete program. (original message: {exp.message})'
            raise # something else went wrong pass the exception on up.


    @exclusive
    def process_controller(self, update=True):
        prtnum = self.client.read_holding_string(16, 15)

        if update:
            #profile & function blocks (p/n digit 7)
            if prtnum[6] == 'B':
                self.profiles = False
                self.alarms = 8
            elif prtnum[6] == 'C':
                self.profiles = False
                self.alarms = 14
            elif prtnum[6] == 'D':
                self.profiles = True
                self.alarms = 6
            elif prtnum[6] == 'E':
                self.profiles = True
                self.alarms = 8
            elif prtnum[6] == 'F':
                self.profiles = True
                self.alarms = 14
            else: #(pn[6] == 'A')
                self.profiles = False
                self.alarms = 6
            #control algorithms (p/n digit 12)
            if prtnum[11] == '2':
                self.loops = 2
                self.cascades = 0
            elif prtnum[11] == '3':
                self.loops = 3
                self.cascades = 0
            elif prtnum[11] == '4':
                self.loops = 4
                self.cascades = 0
            elif prtnum[11] == '5':
                self.loops = 0
                self.cascades = 0
            elif prtnum[11] == '6':
                self.loops = 0
                self.cascades = 1
            elif prtnum[11] == '7':
                self.loops = 1
                self.cascades = 1
            elif prtnum[11] == '8':
                self.loops = 2
                self.cascades = 1
            elif prtnum[11] == '9':
                self.loops = 3
                self.cascades = 1
            elif prtnum[11] == 'A':
                self.loops = 0
                self.cascades = 2
            elif prtnum[11] == 'B':
                self.loops = 1
                self.cascades = 2
            elif prtnum[11] == 'C':
                self.loops = 2
                self.cascades = 2
            else: #(pn[11] == '1')
                self.loops = 1
                self.cascades = 0
            self.__update_loop_map()
            self.limits = []
            for i in range(6):
                try:
                    self.client.read_holding(11250+60*i)
                    self.limits.append(i+1)
                except ModbusError:
                    pass
            if len(self.limits):
                prtnum += 'w/ %d limits' % len(self.limits)
        return prtnum

    @exclusive
    def get_network_settings(self):
        raise NotImplementedError

    @exclusive
    def set_network_settings(self, value):
        if value:
            self.__set_message(1, value.get('message', 'Espec Server Hosted:'), exclusive=False)
            self.__set_message(2, value.get('host', 'NO_HOST_SPECIFIED!'), exclusive=False)
            self.__set_message(3, value.get('address', 'Network Not Up'), exclusive=False)
            self.__set_message(4, value.get('datetime'), exclusive=False)
        else:
            self.__set_message(1, exclusive=False)
            self.__set_message(2, exclusive=False)
            self.__set_message(3, exclusive=False)
            self.__set_message(4, exclusive=False)

    #F4T only interface items
    @exclusive
    def __read_io(self, module, iopt):
        '''
        Read IO state. Will throw modbus exception code 4 if io does not exist
        module = module number 1-6.
        io = io device, depends on the installed card (high density io has 1-6)
        '''
        #       mod1   mod2   mod3   mod4   mod5   mod6 (io 1, add 40 for the next io point)
        oreg = [33718, 33958, 34198, 34438, 34678, 34918]
        if module is not None and iopt is not None:
            self.__range_check(module, 1, 6)
            self.__range_check(iopt, 1, 6)
            try:
                tval = self.client.read_holding(oreg[module-1]+(iopt-1)*40, 1)[0]
                return self.watlow_val_dict[tval] == 'on'
            except ModbusError as exc:
                raise ModbusError(4, exc.message + " (IO point does not exist)")

    @exclusive
    def __get_message(self, num):
        '''
        Get Message N from the controller
        '''
        self.__range_check(num, 1, 4)
        return self.client.read_holding_string(37548+(num-1)*160)

    @exclusive
    def __set_message(self, num, value=None):
        '''
        Set message N of the controller
        '''
        self.__range_check(num, 1, 4)
        if value is not None:
            self.client.write_holding_string(37548+(num-1)*160, value)
            self.client.write_holding(37546+(num-1)*160, self.inv_watlow_val_dict('yes')) #show?
        else:
            self.client.write_holding(37546+(num-1)*160, self.inv_watlow_val_dict('no')) #show?

    @exclusive
    def __profile_units(self, num):
        '''
        Get the units for the profile loops pv/sp
        '''
        if not self.profiles:
            raise ControllerInterfaceError("Profile support is required to read units.")
        reg = 16536 + (num-1)*2
        profpv = self.client.read_holding(reg, 1)[0]
        try:
            tlist = ['absoluteTemperature', 'relativeTemperature', 'notsourced']
            if self.watlow_val_dict[profpv] in tlist:
                tval = self.client.read_holding(14080 if self.interface == "RTU" else 6730, 1)[0]
                return '\xb0%s' % self.watlow_val_dict[tval]
            else:
                return '%s' % self.watlow_val_dict[profpv]
        except LookupError:
            return 'ERROR'

    def __get_prgm_empty(self):
        '''
        create a empty null program
        '''
        haswaits = self.waits[0] != '' or self.waits[1] != ''
        haswaits = haswaits or self.waits[2] != '' or self.waits[3] != ''
        gsd, ldata, evd, wdata = [], [], [], []
        for _ in range(self.loops):
            gsd.append({'value':3.0})
        for j in range(self.loops + self.cascades):
            lpdata = {'target':0, 'rate':0, 'mode':'', 'gsoak': False, 'cascade': False,
                      'isCascade': self.loop_map[j]['type'] == 'cascade'}
            if self.loop_map[j]['type'] == 'cascade':
                lpdata.update({
                    'enable': self.cascade_event[j] == 0,
                    'showEnable': self.cascade_event[j] != 0
                })
            else:
                lpdata.update({
                    'enable': self.loop_event[j - self.cascades] == 0,
                    'showEnable': self.loop_event[j - self.cascades] != 0
                })
            ldata.append(lpdata)
        hidden_events = self.loop_event + self.cascade_event + self.cascade_ctl_event
        hidden_events.append(self.cond_event)
        for j in range(8):
            if j+1 not in hidden_events:
                evd.append({'value':False, 'number':j+1})
        for j in range(4):
            if self.waits[j]:
                wdata.append({'number':j+1, 'condition':'none', 'value':0})
        steps = [{
            'type':'instant',
            'duration':{'hours':0, 'minutes':0, 'seconds':0},
            'loops':ldata,
            'events':evd,
            'waits':wdata,
            'jstep':0,
            'jcount':0
        }]
        return {
            'controllerType':'WatlowF4T',
            'name':'',
            'log':False,
            'gs_dev':gsd,
            'steps':steps,
            'haswaits':haswaits
        }

    def get_operation_modes(self):
        if self.cond_event is None:
            return ['constant', 'program']
        else:
            return ['standby', 'constant', 'program']
