'''
Upper level interface for the Watlow F4T controller

:copyright: (C) Espec North America, INC.
:license: MIT, see LICENSE for more details.
'''
#from pymodbus.client.sync import ModbusTcpClient as ModbusClient
import time, datetime, traceback
from modbus import *
from struct import *
from controllerabstract import CtlrProperty, ControllerInterfaceError, exclusive

class WatlowF4T(CtlrProperty):
    '''
    A class for interfacing with Watlow F4T
    '''

    def __init__(self,**kwargs):
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
            loops (int): The number of control loops the controller has (default=1)
            cascades (int): The number of cascade control loops the controller has (default=0)
            cond_event (int): The number of the event that will turn the controller on/off (default=0(disabled))
            cond_event_toggle (bool): When True the cond_event is toggled, when False the event is momentary (default=False)
            limits (list(bool)): A list of slots that limit controllers are installed in (default=[5])
            loop_event (list(int)): A list of events #'s that turns control loops on/off (default=[0,2,0,0])
            cascade_event (list(int)): A list of events #'s that turns cascade control loops on/off (default=[0,0,0,0])
            cascade_ctl_event (list(int)): A list of events that will enable/disable simple setpoint mode on a the cascade control loops (default=[0,0,0,0])
            waits (list(str)): Configuration for the 4 waitfor inputs on the profile engine each index can be::
                "A" -- Analog
                "D" -- Digital
                "" -- Off(default x4)
            time_zone (None): Not currently used
            run_module (int): The module that the "Chamber Running" output is on (default=1)
            run_io (int): The output of the run_module that the "Chamber Running" output is on (default=1)
            alarms (int): The number of alarms that the controller has (default=6)
            profiles (bool): If True the controller supports profiles(programs) (default=False)
            lock (RLock): The locking method to use when accessing the controller (default=RLock())
        
        Returns:
            None
        '''
        self.init_common(**kwargs)
        self.cond_event = kwargs.get('cond_event',9)
        self.cond_event_toggle = kwargs.get('cond_event_toggle',False)
        self.limits = kwargs.get('limits',[5]) #list of limits needs to be supplied 1,2,3,4,5,6 are posible
        self.loop_event = kwargs.get('loop_event',[0,2,0,0]) #list of events that may enable or disable a loop index 0=loop1, events=1-8 0=not used
        self.cascade_event = kwargs.get('cascade_event',[0,0,0,0]) #list of events that may enable or disable a cascade loop
        self.cascade_ctl_event = kwargs.get('cascade_ctl_event',[0,0,0,0]) #list of events that may enable or dsiable simple setpoint mode on a cascade loop
        self.waits = kwargs.get('waits',['','','','']) # waits 1-4 A= analog wait, D= digital wait
        self.time_zone = kwargs.get('time_zone',None)
        self.run_module = kwargs.get('run_module',1)
        self.run_io = kwargs.get('run_io',1)
        self.events = 8

        #these are detectable from the part number (call process_partno())
        self.alarms = kwargs.get('alarms',6)
        self.profiles = kwargs.get('profiles',False)

        self.update_profile_loop_map()
        self.watlowValDict = {1:'2', 2:'3', 3:'50Hz', 4:'60Hz', 9:'ambientError',
                              10:'auto', 11:'b', 13: 'both', 15:u'C', 17:'closeOnAlarm',
                              22:'current',  23:'d', 24:'deviationAlarm', 26:'e', 27:'end', 28:'error',
                              30:'F', 31:'factory', 32:'fail', 34:'fixedTimeBase', 37:'high', 39:'hours',
                              40:'hundredths',  44:'inputDryContact',  46:'j', 47:'hold', 48:'k', 49:'latching',
                              53:'low', 54:'manual', 56:'millivolts', 57:'minutes', 58:'n', 59:'no',
                              60: 'nonLatching', 61:'none', 62:'off', 63:'on', 65:'open', 66:'openOnAlarm', 68:'output',
                              73:'power', 75:'process', 76:'processAlarm',
                              80:'r', 81:'ramprate', 84:'s', 85:'setPoint', 87:'soak', 88:'startup',
                              93:'t', 94:'tenths', 95:'thermocouple', 96:'thousandths',
                              100:'user',103:'variableTimeBase', 104:'volts', 105:'whole', 106:'yes', 108:'silenceAlarms',
                              112:'milliamps', 113:'rtd100ohm', 114:'rtd1000ohm', 116:'jump',
                              127:'shorted', 129:'clear',
                              138:'ok', 139:'badCalibrationData',
                              140:'measurementError', 141:'rtdError', 142:'analogInput', 146:'pause', 147:'resume', 148:'terminate', 149: 'running',
                              155:'1kpotentiometer',
                              160:'heatPower', 161:'coolPower',
                              180:'custom',
                              193:'inputVoltage',
                              204:'ignore',
                              240:'math', 241:'processValue', 242:'setPointClosed', 243:'setPointOpen', 245:'variable', 246:'notsourced',
                              251:'notStarted', 252:'complete', 253: 'terminated',
                              1037:'counts',
                              1276:'electrical',
                              1360:'10k', 1361:'20k', 1375:'add',
                              1423:'mathError', 1448:'5k', 1449:'40k', 1451:'curveA', 1452:'curveB', 1453:'curveC', 1456:'up', 1457:'down',
                              1532:'specialFunctionOutput1', 1533:'specialFunctionOutput2', 1534:'specialFunctionOutput3', 1535:'specialFunctionOutput4',
                              1538:'%RH', 1540:'absoluteTemperature', 1541:'relativeTemperature', 1542:'wait', 1557:'nc',
                              1617:'stale',1667:'safe',
                              1740:'encoder', 1770:'edit',  1771:'insert', 1772:'delete', 1779:'profileNumber', 1782: 'start', 1783: 'timedStart',
                              1794:'cascadeHeatPower', 1795:'cascadeCoolPower', 1796:'cascadePower', 1797:'cascadeSetPointClosed', 1798:'cascadeSetPointOpen',
                              1927:'instant', 1928:'ramptime', 1964:'above', 1965:'below',
                              10001:'condition'}

    def invWatlowValDict(self,key):
        '''
        Get the key by a given value from the dictionary self.watlowValDict

        Args:
            key (str): The value to find the key for in self.watlowValDict

        Returns:
            Str
        '''
        try:
            return self.iwatlowValDict[key]
        except:
            self.iwatlowValDict = {v: k for k, v in self.watlowValDict.items()}
            return self.iwatlowValDict[key]

    def update_profile_loop_map(self):
        '''
        update the loop map.
        '''
        self.profile_loop_map = [{'type':'cascade','num':j+1} for j in range(self.cascades)]
        self.profile_loop_map += [{'type':'loop','num':j+1} for j in range(self.loops)]

    def range_check(self, val, min, max):
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
        if (max < min or val < min or val > max):
            raise ValueError("Index is not within bounds or bounds are not valid")

    def mod_to_float(self,val):
        '''
        Convert unsigned ints from modbus to a float expects list of length=2.
        '''
        return round(unpack('f',pack('HH',val[0], val[1]))[0],1)

    def float_to_mod(self,val):
        '''
        Convert a float to a 2 element list of unsigned ints for modbus.
        '''
        return unpack('HH',pack('f',val))

    def mod_to_string(self,val):
        '''
        Convert unsigned ints from modbus to a string.
        '''
        str = ""
        for x in val:
            if x is not 0:
                str = str + chr(x)
        return str

    def string_to_mod(self,val,len=20):
        '''
        Convert a string into unsigned ints for modbus.
        len= (20) The final length of the int list if string is short 0 will be appended, longer gets cut.
        '''
        mods = [ord(c) for c in val]
        mods.extend([0]*len)
        return mods[0:len]

    #required (ABC) items

    def connect(self):
        '''
        connect to the controller using the paramters provided on class initialization
        '''
        self.client = modbusRTU(self.adr,self.serialport,self.baudrate) if self.interface == "RTU" else modbusTCP(self.adr,self.host)

    def close(self):
        '''
        close the connection to the controller
        '''
        self.client.close()

    @exclusive
    def raw(self,command):
        '''
        Interact directly with the controller

        Args:
            command (str): A modbus packet PDU (ie function code + data), TCP/RTU specific packet requirements will be managed automatically

        Returns:
            str. The raw modbus response from the controller.
        '''
        return self.client.interact(command)

    @exclusive
    def get_register(self,register,type='short',count=1,**kwargs):
        '''
        Read a specific modbus register of a specified type directly from the controller

        Args:
            register (int): The modbus register to read.
            type (str): The data type of the register::
                "short" -- 16bit integer (default)
                "long" -- 32bit integer
                "float" -- 32bit floating point
                "string" -- String up to 20 characters in length (2char per register)
            count (int): The number of registers to read (length of type is takein into account)

        Returns:
            list(int),list(float),string.

        Raises:
            ValueError
        '''
        count = count*2 if type == 'long' or type == 'float' else count
        vals = self.client.readHolding(register,count)
        if type == 'string':
            return self.mod_to_string(vals)
        elif type == 'long':
            i = 0
            lvals = []
            while i < len(vals):
                lvals.append(pack('HH',vals[i],vals[i+1]))
                i += 2
            return lvals
        elif type == 'float':
            i = 0
            fvals = []
            while i < len(vals):
                fvals.append(round(unpack('f',pack('HH',vals[i], vals[i+1]))[0],1))
                i += 2
            return fvals
        elif type == 'short':
            return vals
        else:
            raise ValueError('"%s" is not a supported register type' % type)

    @exclusive
    def set_register(self,register,value,type='short',**kwargs):
        '''
        write a specific modbus register of a specified type directly to the controller

        Args:
            register (int): The modbus register to write too.
            type (str): The data type of the register::
                "short" -- 16bit integer (default)
                "long" -- 32bit integer
                "float" -- 32bit floating point
                "string" -- String up to 20 characters in length (2char per register)
            value (int,float,str): The value to write to the controller

        Returns:
            None.

        Raises:
            ValueError
        '''
        if type == 'string':
            self.client.writeHolding(register, self.string_to_mod(value))
        elif type == 'long':
            self.client.writeHolding(register, struct.pack('HH',int(value)))
        elif type == 'float':
            self.client.writeHolding(register, self.float_to_mod(float(value)))
        elif type == 'short':
            self.client.writeHolding(register, struct.unpack('H',struct.pack('h',int(value))))
        else:
            raise ValueError('"%s" is not a supported register type' % type)

    @exclusive
    def get_datetime(self):
        '''
        Get the datetime from the controller.

        Returns:
            datetime. The current time as a datetime.datetime object
        '''
        d = self.client.readHolding(14664, 12)
        return datetime.datetime(hour = d[0],minute = d[2],second = d[4],month = d[6],day = d[8],year = d[10])

    @exclusive
    def set_datetime(self,value):
        '''
        Set the datetime of the controller.

        Args:
            value (datetime.datetime): The new datetime for the controller.
        '''
        self.client.writeHolding(14664, [value.hour])
        self.client.writeHolding(14666, [value.minute])
        self.client.writeHolding(14668, [value.second])
        self.client.writeHolding(14670, [value.month])
        self.client.writeHolding(14672, [value.day])
        self.client.writeHolding(14674, [value.year])

    @exclusive
    def get_loop(self,N,type,list=None):
        '''
        Get all parameters for a loop from a given list.

        Args:
            N (int): The loop number (1-4).
            type (str): The loop type::
                "cascade" -- A cascade control loop.
                "loop" -- A standard control loop.
            list (list(str)): The list of parameters to read defaults::
                "setpoint" -- The target temp/humi/altitude/etc of the control loop
                "processvalue" -- The current conditions inside the chamber
                "range" -- The settable range for the "setpoint"
                "enable" -- Weather the loop is on or off
                "units" -- The units of the "setpoint" or "processvalue" parameters
                "mode" -- The current control status of the loop
                "power" -- The current output power of the loop
                "deviation" -- (type="cascade" only) The ammount the air temperature is allowed to deviate from the product.
                "enable_cascade" -- (type="cascade" only) Enable or disable cascade type control (faster product change rates)

        Returns:
            dict. The dictionary contains a key for each item in the list argument::
                "setpoint" -- {"constant":float,"current":float}
                "processvalue" -- {"air":float,"product":float} (product present only with type="cascade")
                "range" -- {"min":float,"max":float}
                "enable" -- {"constant":bool,"current":bool}
                "units" -- str
                "mode" -- str('Off' or 'Auto' or 'Manual')
                "deviation" -- {"positive": float, "negative": float}
                "enable_cascade" -- {"constant":bool,"current":bool}
                "power" -- {"constant": float, "current": float}
        '''
        loopFunctions = {'cascade':{'setpoint':self.get_cascade_sp,'setPoint':self.get_cascade_sp,'setValue':self.get_cascade_sp,
                                    'processvalue':self.get_cascade_pv,'processValue':self.get_cascade_pv,
                                    'range':self.get_cascade_range,
                                    'enable':self.get_cascade_en,
                                    'units':self.get_cascade_units,
                                    'mode':self.get_cascade_mode,
                                    'deviation':self.get_cascade_deviation,
                                    'enable_cascade':self.get_cascade_ctl,
                                    'power': self.get_cascade_power},
                            'loop':{'setpoint':self.get_loop_sp,'setPoint':self.get_loop_sp,'setValue':self.get_loop_sp,
                                    'processvalue':self.get_loop_pv,'processValue':self.get_loop_pv,
                                    'range':self.get_loop_range,
                                    'enable':self.get_loop_en,
                                    'units':self.get_loop_units,
                                    'mode':self.get_loop_mode,
                                    'power':self.get_loop_power}}
        if list is None:
            list = loopFunctions[type].keys()
            list = [x for x in list if x not in ['setPoint','setValue','processValue']]
        return {key:loopFunctions[type][key](N,exclusive=False) if key in loopFunctions[type] else 'invalid key' for key in list}

    @exclusive
    def set_loop(self,N,type,list):
        '''
        Set all parameters for a loop from a given list.

        Args:
            N (int): The loop number (1-4).
            type (str): The loop type::
                "cascade" -- A cascade control loop.
                "loop" -- A standard control loop.
            list (dict(dict)): The possible keys and there values::
                "setpoint" -- The target temp/humi/altitude/etc of the control loop
                "range" -- The settable range for the "setpoint"
                "enable" -- turn the control loop on or off
                "power" -- set the manual power of the control loop
                "deviation" -- (type="cascade" only) The ammount the air temperature is allowed to deviate from the product.
                "enable_cascade" -- (type="cascade" only) Enable or disable cascade type control (faster product change rates)

        Returns:
            None

        Raises:
            ModbusError
        '''
        loopFunctions = {'cascade':{'setpoint':self.set_cascade_sp,'setPoint':self.set_cascade_sp,'setValue':self.set_cascade_sp,
                                    'range':self.set_cascade_range,
                                    'enable':self.set_cascade_en,
                                    'deviation':self.set_cascade_deviation,
                                    'enable_cascade':self.set_cascade_ctl,
                                    'mode':self.set_cascade_mode,
                                    'power':self.set_cascade_power},
                            'loop':{'setpoint':self.set_loop_sp,'setPoint':self.set_loop_sp,'setValue':self.set_loop_sp,
                                    'range':self.set_loop_range,
                                    'enable':self.set_loop_en,
                                    'mode':self.set_loop_mode,
                                    'power':self.set_loop_power}}
        #mode must be done first
        if 'mode' in list:
            loopFunctions[type]['mode'](exclusive=False,N=N,value=list.pop('mode'))
        for k,v in list.items():
            try: loopFunctions[type][k](exclusive=False,N=N,value=v)
            except KeyError: pass

    @exclusive
    def get_loop_sp(self, N, constant=None):
        '''
        Get the setpoint of a control loop.

        Args:
            N (int): The number for the control loop
            constant (bool): Read the constant or current setpoint, None=Both (default=None)
        
        Returns:
            dict(float): constant=None
            float: constant=bool

        Raises:
            ValueError, ModbusError
        '''
        self.range_check(N,1,self.loops)
        if constant is None:
            return {'constant': self.mod_to_float(self.client.readHolding(2782+(N-1)*160, 2)),
                    'current': self.mod_to_float(self.client.readHolding(2810+(N-1)*160, 2))}
        if constant is True:
            return self.mod_to_float(self.client.readHolding(2782+(N-1)*160, 2))
        if constant is False:
            return self.mod_to_float(self.client.readHolding(2810+(N-1)*160, 2))
        raise ValueError('constant must be a bool or None')
    
    @exclusive
    def set_loop_sp(self, N, value):
        '''
        Set the setpoint of the control loop.

        Args:
            N (int): The number for the control loop
            value (float): The new setpoint

        Returns:
            None

        Raises:
            ValueError, ModbusError
        '''
        value = value['constant'] if type(value) is dict else value
        self.range_check(N,1,self.loops)
        constreg = 2782+(N-1)*160
        self.client.writeHolding(constreg, self.float_to_mod(value))

    @exclusive
    def get_loop_pv(self, N, product=None):
        '''
        Get the process value of a loop.

        Args:
            N (int): The number for the control loop
            product (bool): Read the product temperature (not valid) or the air temperature if None get both (default=None)
        
        Returns:
            dict(float). product=None
            float. product=bool

        Raises:
            ValueError
        '''
        reg = 2820+(N-1)*160
        self.range_check(N,1,self.loops)
        if product is None:
            return {'air': self.mod_to_float(self.client.readHolding(reg, 2))}
        if product is False:
            return self.mod_to_float(self.client.readHolding(reg, 2))
        return ValueError('product must be None or False.')

    @exclusive
    def set_loop_range(self,N,value):
        self.range_check(N,1,self.loops)
        self.client.writeHolding(2776+(N-1)*160, self.float_to_mod(value['max']))
        self.client.writeHolding(2774+(N-1)*160, self.float_to_mod(value['min']))

    @exclusive
    def get_loop_range(self,N):
        self.range_check(N,1,self.loops)
        return {'max':self.mod_to_float(self.client.readHolding(2776+(N-1)*160, 2)),
                'min':self.mod_to_float(self.client.readHolding(2774+(N-1)*160, 2))}

    @exclusive
    def get_loop_en(self,N):
        self.range_check(N,1,self.loops)
        cm = self.watlowValDict[self.client.readHolding(2814+(N-1)*160, 1)[0]] != 'off'
        eve = self.get_event(self.loop_event[N-1],exclusive=False)['constant'] if self.loop_event[N-1] != 0 else True
        return {'constant': eve, 'current': cm}

    @exclusive
    def set_loop_en(self,N,value):
        self.range_check(N,1,self.loops)
        value = value['constant'] if type(value) is dict else value
        if self.watlowValDict[self.client.readHolding(2730+(N-1)*160, 1)[0]] == 'off' and value:
            self.client.writeHolding(2730+(N-1)*160, 10)
        if self.loop_event[N-1] != 0:
            self.set_event(self.loop_event[N-1],value,exclusive=False)

    @exclusive
    def get_loop_units(self, N):
        self.range_check(N,1,self.loops)
        try:
            return self.profile_units(self.profile_loop_map.index({'type':'loop','num':N}) + 1, exclusive=False)
        except ControllerInterfaceError:
            return "ERROR"

    @exclusive
    def set_loop_mode(self, N, value):
        self.range_check(N,1,self.loops)
        if value in ['Off','OFF','off']:
            self.set_loop_en(N,False,exclusive=False)
        elif value in ['On','ON','on']:
            self.set_loop_en(N,True,exclusive=False)
        elif value in ['Auto','AUTO','auto']:
            self.set_loop_en(N,True,exclusive=False)
            self.client.writeHolding(2730+(N-1)*160,10)
        elif value in ['Manual','MANUAL','manual']:
            self.set_loop_en(N,True,exclusive=False)
            self.client.writeHolding(2730+(N-1)*160,54)
        else:
            raise ValueError('mode must be "Off"/"Auto"/"Manual"/"On" ("On" = set_loop_en(N,True) recieved: ' + value)

    @exclusive
    def get_loop_mode(self, N):
        '''Returns loop state'''
        self.range_check(N,1,self.loops)
        if self.get_loop_en(N,exclusive=False)['constant']:
            return {62:'Off',10:'Auto',54:'Manual'}[self.client.readHolding(2730+(N-1)*160, 1)[0]]
        else:
            return 'Off'

    @exclusive
    def get_loop_power(self, N, constant=None):
        self.range_check(N,1,self.loops)
        if constant is None:
            return {'constant': self.mod_to_float(self.client.readHolding(2784+(N-1)*160, 2)),
                    'current': self.mod_to_float(self.client.readHolding(2808+(N-1)*160, 2))}
        elif constant is True:
            return self.mod_to_float(self.client.readHolding(2784+(N-1)*160, 2))
        elif constant is False:
            return self.mod_to_float(self.client.readHolding(2808+(N-1)*160, 2))
        raise ValueError('constant must be a bool or None')

    @exclusive
    def set_loop_power(self, N, value):
        self.range_check(N,1,self.loops)
        if type(value) is dict:
            value = value['constant']
        self.client.writeHolding(2784+(N-1)*160, self.float_to_mod(value))


    @exclusive
    def get_cascade_sp(self,N):
        self.range_check(N,1,self.cascades)
        constreg = 4042+(N-1)*200
        reg = 4042+(N-1)*200
        cur = self.mod_to_float(self.client.readHolding(reg, 2))
        return {'constant':self.mod_to_float(self.client.readHolding(constreg, 2)) if reg != constreg else cur,
                'current':cur,
                'air':self.mod_to_float(self.client.readHolding(4188+(N-1)*200, 2)),
                'product':self.mod_to_float(self.client.readHolding(4190+(N-1)*200, 2))}

    @exclusive
    def set_cascade_sp(self,N,value):
        self.range_check(N,1,self.cascades)
        value = value['constant'] if type(value) is dict else value
        constreg = 4042+(N-1)*200
        self.client.writeHolding(constreg, self.float_to_mod(value))
        
    @exclusive
    def get_cascade_pv(self, N):
        '''Read the process values of the loop, product=outer, air=inner'''
        self.range_check(N,1,self.cascades)
        return {'product': self.mod_to_float(self.client.readHolding(4180+(N-1)*200,2)),
                'air': self.mod_to_float(self.client.readHolding(4182+(N-1)*200,2))}

    @exclusive
    def get_cascade_range(self,N):
        self.range_check(N,1,self.cascades)
        return {'max':self.mod_to_float(self.client.readHolding(4036+(N-1)*200, 2)),
                'min':self.mod_to_float(self.client.readHolding(4038+(N-1)*200, 2))}

    @exclusive
    def set_cascade_range(self,N,value): 
        self.range_check(N,1,self.cascades)
        self.client.writeHolding(4036+(N-1)*200, self.float_to_mod(value['max']))
        self.client.writeHolding(4038+(N-1)*200, self.float_to_mod(value['min']))   

    @exclusive
    def get_cascade_en(self,N):
        self.range_check(N,1,self.cascades)
        cm = self.watlowValDict[self.client.readHolding(4012+(N-1)*200, 1)[0]] != 'off'
        eve = self.get_event(self.cascade_event[N-1],exclusive=False) if self.cascade_event[N-1] != 0 else True
        return {'constant': eve, 'current': cm}

    @exclusive
    def set_cascade_en(self,N,value):
        self.range_check(N,1,self.cascades)
        value = value['constant'] if type(value) is dict else value
        if self.watlowValDict[self.client.readHolding(4010+(N-1)*200, 1)[0]] == 'off' and value:
            self.client.writeHolding(4010+(N-1)*200, 10)
        if self.cascade_event[N-1] != 0:
            self.set_event(self.cascade_event[N-1],value,exclusive=False)

    @exclusive
    def get_cascade_units(self,N):
        self.range_check(N,1,self.cascades)
        try:
            return self.profile_units(self.profile_loop_map.index({'type':'cascade','num':N}) + 1, exclusive=False)
        except ControllerInterfaceError:
            return "ERROR"

    @exclusive
    def set_cascade_mode(self, N, value):
        self.range_check(N,1,self.cascades)
        if value in ['Off','OFF','off']:
            self.set_cascade_en(N,False,exclusive=False)
        elif value in ['On','ON','on']:
            self.set_cascade_en(N,True,exclusive=False)
        elif value in ['Auto','AUTO','auto']:
            self.set_cascade_en(N,True,exclusive=False)
            self.client.writeHolding(4010+(N-1)*200,10)
        elif value in ['Manual','MANUAL','manual']:
            self.set_cascade_en(N,True,exclusive=False)
            self.client.writeHolding(4010+(N-1)*200,54)
        else:
            raise ValueError('mode must be "Off"/"Auto"/"Manual"/"On" ("On" = set_cascade_en(N,True) recieved: ' + value)

    @exclusive
    def get_cascade_mode(self, N):
        '''Returns loop state'''
        self.range_check(N,1,self.cascades)
        if self.get_cascade_en(N,exclusive=False):
            return {62:'Off',10:'Auto',54:'Manual'}[self.client.readHolding(4010+(N-1)*200, 1)[0]]
        else:
            return 'Off'

    @exclusive
    def get_cascade_ctl(self,N):
        self.range_check(N,1,self.cascades)
        cm = self.client.readHolding(4200+(N-1)*200, 1)[0] == 62
        eve = True
        if (self.cascade_ctl_event[N-1] != 0):
            return self.get_event(self.cascade_ctl_event[N-1],exclusive=False)
        else:
            cm = self.client.readHolding(4200+(N-1)*200, 1)[0] == 62
            return {'constant': cm, 'current': cm}

    @exclusive
    def set_cascade_ctl(self,N,value):
        self.range_check(N,1,self.cascades)
        value = value['constant'] if type(value) is dict else value
        if (self.client.readHolding(4200+(N-1)*200, 1)[0] == 63 and value):
            self.client.writeHolding(4200+(N-1)*200, 62)
        if (self.cascade_ctl_event[N-1] != 0):
            self.set_event(self.cascade_ctl_event[N-1],value,exclusive=False)

    @exclusive
    def get_cascade_deviation(self,N):
        self.range_check(N,1,self.cascades)
        return {'positive': self.mod_to_float(self.client.readHolding(4170+(N-1)*200,2)),
                'negative': self.mod_to_float(self.client.readHolding(4168+(N-1)*200,2))}

    @exclusive
    def set_cascade_deviation(self,N,value):
        self.range_check(N,1,self.cascades)
        self.client.writeHolding(4168+(N-1)*200, self.float_to_mod(0-abs(value['negative'])))
        self.client.writeHolding(4170+(N-1)*200, self.float_to_mod(value['positive']))

    @exclusive
    def get_cascade_power(self, N, constant=None):
        self.range_check(N,1,self.cascades)
        if constant is None:
            return {'constant': self.mod_to_float(self.client.readHolding(4044+(N-1)*200, 2)),
                    'current': self.mod_to_float(self.client.readHolding(4178+(N-1)*200, 2))}
        elif constant is True:
            return self.mod_to_float(self.client.readHolding(4044+(N-1)*200, 2))
        elif constant is False:
            return self.mod_to_float(self.client.readHolding(4178+(N-1)*200, 2))
        raise ValueError('constant must be a bool or None')

    @exclusive
    def set_cascade_power(self, N, value):
        self.range_check(N,1,self.cascades)
        if type(value) is dict:
            value = value['constant']
        self.client.writeHolding(4044+(N-1)*200, self.float_to_mod(value))

    @exclusive
    def get_event(self,N):
        #62=0ff, 63=on
        #        prof1  prof2  prof3  prof4  prof5  prof6  prof7  prof8  key1  key2  key3  key4
        rereg = [16594, 16596, 16598, 16600, 16822, 16824, 16826, 16828, 6844, 6864, 6884, 6904][N-1]
        kpress = 6850 +(N-8-1)*20 #down=1457, #up = 1456
        self.range_check(N,1,12)
        val = self.watlowValDict[self.client.readHolding(rereg, 1)[0]] == 'on'
        return {'current':val,'constant':val}

    @exclusive
    def set_event(self,N,value):
        #62=0ff, 63=on
        #        prof1  prof2  prof3  prof4  prof5  prof6  prof7  prof8  key1  key2  key3  key4
        rereg = [16594, 16596, 16598, 16600, 16822, 16824, 16826, 16828, 6844, 6864, 6884, 6904][N-1]
        kpress = 6850 +(N-8-1)*20 #down=1457, #up = 1456
        self.range_check(N,1,12)
        value = value['constant'] if type(value) is dict else value
        if N <= 8:
            self.client.writeHolding(rereg, (self.invWatlowValDict('on') if value else self.invWatlowValDict('off')))
        else:
            self.client.writeHolding(kpress, (self.invWatlowValDict('down') if value else self.invWatlowValDict('up')))



    @exclusive
    def get_status(self):
        '''Return controller state: "Alarm","Standby","Constant","Program (Run/Paused/Calander Start)"'''
        prgmstate = self.client.readHolding(16568, 1)[0]
        if (prgmstate == 149):
            return "Program Running"
        elif (prgmstate == 146):
            return "Program Paused"
        elif (prgmstate == 1783):
            return "%s (Program Calendar Start)" % "Constant" if self.read_io(self.run_module,self.run_io,exclusive=False) else "Standby"
        elif not self.get_alarm_status(exclusive=False)['active']:
            return "Constant" if self.read_io(self.run_module,self.run_io,exclusive=False) else "Standby"
        else:
            return "Alarm"

    @exclusive
    def get_alarm_status(self):
        '''Returns a list of active alarms (1-14), alarms 20+ are limits'''
        aalms = []
        ialms = []
        for i in range(0,self.alarms):
            if self.client.readHolding(1356+100*i, 1)[0] in [88,61,12]:
                ialms.append(i+1)
            else:
                aalms.append(i+1)
        for i in self.limits:
            state = self.watlowValDict[self.client.readHolding(11250+(i-1)*60, 1)[0]] == 'error'
            error = self.watlowValDict[self.client.readHolding(11288+(i-1)*60, 1)[0]] != 'none'
            status = self.watlowValDict[self.client.readHolding(11264+60*(i-1), 1)[0]] == 'fail'
            if (state or error or status):
                aalms.append(20+i)
            else:
                ialms.append(20+i)
        return {'active': aalms, 'inactive': ialms}

    @exclusive
    def const_start(self):
        '''Run constant mode, regardless of what the controller was doing.'''
        status = self.get_status(exclusive=False)
        if "Program" in status:
            self.client.writeHolding(16566, self.invWatlowValDict('terminate'))
            time.sleep(0.5)
        if not self.read_io(self.run_module,self.run_io,exclusive=False): #io is actual on/off switch
            self.set_event(self.cond_event,True,exclusive=False)
        if "Standby" in status: #we can be "running" while in standby (standby only means loop 1 active mode is off)
            self.set_loop_en(1,True,exclusive=False)

    @exclusive
    def stop(self):
        '''Stop all operation.'''
        status = self.get_status(exclusive=False)
        if self.read_io(self.run_module,self.run_io,exclusive=False):
            if self.cond_event_toggle:
                self.set_event(self.cond_event,False,exclusive=False)
            else:
                self.set_event(self.cond_event,True,exclusive=False)

    @exclusive
    def prgm_start(self, N, step):
        '''Start profile N at step'''
        self.range_check(N,1,40)
        if step > self.get_prgm_steps(N,exclusive=False):
            raise ControllerInterfaceError("Program #%d does not have step #%d." % (N,step))
        if (self.get_status(exclusive=False).find("Program") >= 0):
            self.client.writeHolding(16566, self.invWatlowValDict('terminate'))
            time.sleep(2)
        self.client.writeHolding(16558, N) #profile to start
        self.client.writeHolding(16560, step) #step to start
        self.client.writeHolding(16562, self.invWatlowValDict('start')) #start the profile
    
    @exclusive
    def prgm_pause(self):
        '''pause the current profile'''
        self.client.writeHolding(16566, self.invWatlowValDict('pause'))

    @exclusive
    def prgm_resume(self):
        '''resume a paused profile'''
        #none(61),pause(146),terminate(148)
        self.client.writeHolding(16564, self.invWatlowValDict('resume'))

    @exclusive
    def prgm_next_step(self):
        program = self.get_prgm_cur(exclusive=False)
        nextstep = self.get_prgm_cstep(exclusive=False) + 1
        self.const_start(exclusive=False)
        time.sleep(1)
        self.prgm_start(program,nextstep,exclusive=False)

    @exclusive
    def get_prgm_cur(self):
        '''get the current profile number'''
        return self.client.readHolding(16588, 1)[0]

    @exclusive
    def get_prgm_cstep(self):
        '''get the current step of the current profile'''
        return self.client.readHolding(16590, 1)[0]

    @exclusive
    def get_prgm_cstime(self):
        '''current step time remaining'''
        data = self.client.readHolding(16622, 5)
        return "%d:%02d:%02d" % (data[4], data[2], data[0])

    @exclusive
    def get_prgm_time(self, pgm=None):
        '''time until program end'''
        data = self.client.readHolding(16570, 3)
        return "%d:%02d:00" % (data[2], data[0])

    @exclusive
    def get_prgm_name(self, N):
        '''Get the name of program N'''
        reg = 16886+(N-1)*40
        self.range_check(N,1,40)
        if not self.profiles:
            raise ControllerInterfaceError("This watlow does not impliment profiles")
        return self.mod_to_string(self.client.readHolding(reg, 20))

    @exclusive
    def get_prgm_steps(self, N):
        '''Get the number of steps in a program'''
        self.client.writeHolding(18888, N)
        return self.client.readHolding(18920, 1)[0]

    @exclusive
    def get_prgms(self):
        '''Get a list of all programs on the controller [number,name,steps]'''
        return [{'number':i,'name':self.get_prgm_name(i,exclusive=False)} for i in range(1,41)]

    @exclusive
    def get_prgm(self, N):
        def eventMod(vals,event):
            event -= 1
            if event < 4:
                return self.watlowValDict[vals[8+event*2]]
            else:
                return self.watlowValDict[vals[24+(event-4)*2]]
        if N == 0:
            return self.get_prgm_empty()
        self.range_check(N,1,40)
        if not self.profiles:
            raise ControllerInterfaceError("This watlow does not impliment profiles")
        self.client.writeHolding(18888, N) #set active profile
        step_count = self.client.readHolding(18920, 1)[0] #get the number of steps in the profile
        if not (step_count > 0):
            raise ControllerInterfaceError("Profile %d does not exist." % N)
        prgmDict = {'name':self.mod_to_string(self.client.readHolding(18606, 20)),
                    'log':self.client.readHolding(19038, 1)[0] == 106}
        haswaits = self.waits[0] != '' or self.waits[1] != '' or self.waits[2] != '' or self.waits[3] != '' #is wait a valid step type
        prgmDict['haswaits'] = haswaits
        prgmDict['hasenables'] = sum(self.loop_event + self.cascade_event)>0
        ranges,gsd,steps = [],[],[]
        for i in range(self.loops + self.cascades):
            map = self.profile_loop_map[i]
            gsd.append({'value': self.mod_to_float(self.client.readHolding(19086+i*2, 2))})
            ranges.append(self.get_loop_range(map['num'], exclusive=False) if map['type'] == 'loop' else self.get_cascade_range(map['num'], exclusive=False))
        for i in range(step_count):
            ld,wd,evd = [],[],[]
            stepType = self.watlowValDict[self.client.readHolding(19094+170*i, 1)[0]]
            sd = {'type':stepType} #step type
            if stepType in ['soak','ramptime','instant']: # this step has duration.
                duration = self.client.readHolding(19096+170*i, 6)
                sd['duration'] = {'hours':duration[0],'minutes':duration[2],'seconds':duration[4]}
            else:
                sd['duration'] = {'hours':0,'minutes':0,'seconds':0}
            if stepType in ['instant','ramptime']:
                params = self.client.readHolding(19114+170*i, 8) #targets
            if stepType == 'ramprate':
                params = self.client.readHolding(19106+170*i, 16) #rates and targets
            if stepType == 'end':
                params = self.client.readHolding(19170+i*170, 7) #endmodes

            gse_event = self.client.readHolding(19138+170*i, 32) #get all guaranteed soak enables and events

            for j in range(self.cascades + self.loops):
                map = self.profile_loop_map[j]
                enable_event = self.loop_event[map['num']-1] if map['type'] == 'loop' else self.cascade_event[map['num']-1]
                lp = ranges[j].copy()
                lp.update({'mode':'','gsoak':False,'target':0.0,'rate':0.0,'showEnable': False,'isCascade': False, 'cascade': False})
                if stepType == 'ramprate':
                    lp['target'] = self.mod_to_float(params[8+j*2:10+j*2])
                    lp['rate'] = self.mod_to_float(params[j*2:2+j*2])
                elif stepType in ['instant','ramptime']:
                    lp['target'] = self.mod_to_float(params[j*2:2+j*2])
                elif stepType == 'end':
                    lp['mode'] = 'user' if params[j*2] == 100 else 'off' if params[j*2] == 62 else 'hold'
                    lp['enable'] = True if enable_event == 0 or params[j*2] != 62 else False
                #if stepType in ['instant','ramptime','ramprate','soak']:
                lp['gsoak'] = gse_event[j*2] == 63
                lp['showEnable'] = enable_event != 0
                lp['enable'] = True if enable_event == 0 else eventMod(gse_event,enable_event) == 'on'
                if map['type'] == 'cascade':
                    lp['isCascade'] = True
                    lp['cascade'] = eventMod(gse_event,self.cascade_ctl_event[map['num']-1]) == 'on'
                ld.append(lp)
            sd['loops'] = ld
            wdraw = self.client.readHolding(19122+i*170, 16)
            for j in range(4):
                if self.waits[j]:
                    wt = wdraw[j*4]
                    ws = self.mod_to_float(wdraw[2+j*4:4+j*4])
                    wts = self.watlowValDict[wt]
                    wd.append({'number':j+1,'condition':wts,'value':ws})
            sd['waits'] = wd
            jraw = self.client.readHolding(19102+i*170, 3)
            sd.update({'jstep':jraw[0],'jcount':jraw[2]})
            sd['events'] = [{'number':j+1,'value':eventMod(gse_event,j+1)} for j in range(8)]
            steps.append(sd)
        prgmDict['steps'] = steps
        prgmDict['gs_dev'] = gsd
        return prgmDict

    @exclusive
    def set_prgm(self,N,prgm):
        '''write to program N'''
        def eventMod(eventNumber,eventValue):
            if eventNumber < 5: self.client.writeHolding(19146+offset+(eventNumber-1)*2, self.invWatlowValDict(eventValue))
            else: self.client.writeHolding(19162+offset+(eventNumber-5)*2, self.invWatlowValDict(eventValue))
        self.client.writeHolding(18888, N) #set active profile
        self.client.writeHolding(18890, 1375) #Set mode Add program
        self.client.writeHolding(18606, self.string_to_mod(prgm['name'])) #set program name
        self.client.writeHolding(19038, 106 if prgm['log'] else 59) #set log mode
        for i,val in enumerate(prgm['gs_dev']): #set guarenteed soak deviations
            self.client.writeHolding(19086+i*2, self.float_to_mod(val['value']))
        for stnm,stp in enumerate(prgm['steps']):
            offset = stnm*170
            self.client.writeHolding(19094+offset, self.invWatlowValDict(stp['type'])) #step type
            for val in stp['events']:
                print 'step:%d, event#:%d, state:%s' % (stnm, val['number'],val['value'])
                eventMod(val['number'],val['value'])
            if stp['type'] == 'jump':
                self.client.writeHolding(19102+offset, stp['jstep']) #jump step target
                self.client.writeHolding(19104+offset, stp['jcount']) #jump count
            if stp['type'] == 'wait':
                for wt in stp['waits']:
                    self.client.writeHolding(19122+offset+(wt['number']-1)*4, self.invWatlowValDict(wt['condition'])) # wait condition
                    self.client.writeHolding(19124+offset+(wt['number']-1)*4, self.float_to_mod(wt['value'])) # wait value
            if stp['type'] in ['soak','instant','ramptime','ramprate','end']:
                for i,lp in enumerate(stp['loops']):
                    map = self.profile_loop_map[i]
                    if stp['type'] == 'ramprate': #write ramp rate
                        self.client.writeHolding(19106+offset+i*2, self.float_to_mod(lp['rate']))
                    if stp['type'] in ['ramprate','ramptime','instant']: #write target value
                        self.client.writeHolding(19114+offset+i*2, self.float_to_mod(lp['target']))
                    if stp['type'] == 'end': #write end mode
                        #if lp['mode'] == 'off' and (self.loop_event[map['num']-1] if map['type'] == 'loop' else self.cascade_event[map['num']-1]) > 0:
                        #    eventMod(self.loop_event[map['num']-1],'off')
                        self.client.writeHolding(19170+offset+i*2, self.invWatlowValDict(lp['mode']))
                    if stp['type'] != 'end':
                        self.client.writeHolding(19138+offset+i*2, 63 if lp['gsoak'] else 62) # guarenteed soak
                        lpevt = self.loop_event[map['num']-1] if map['type'] == 'loop' else self.cascade_event[map['num']-1]
                        if lpevt > 0:
                            eventMod(lpevt,'on' if lp['enable'] else 'off')
                        if map['type'] == 'cascade' and self.cascade_ctl_event[map['num']-1] > 0:
                            eventMod(self.cascade_ctl_event[map['num']-1],'on' if lp['cascade'] else 'off')
            else:
                for ev in self.loop_event + self.cascade_event + self.cascade_ctl_event:
                    if ev > 0: eventMod(ev,'nc')
            if stp['type'] in ['soak','instant','ramptime']:
                self.client.writeHolding(19100+offset, stp['duration']['seconds']) #duration seconds
                self.client.writeHolding(19098+offset, stp['duration']['minutes']) #duration mins
                self.client.writeHolding(19096+offset, stp['duration']['hours']) #duration hours
            if self.cond_event > 0 and self.cond_event <= 8: #set condition event to on unless its an end step with both loops off.
                run = True
                if 'loops' in stp and 'mode' in stp['loops'][0]:
                    run = False
                    for md in stp['loops']:
                        if md['mode'] != 'off': run = True
                eventMod(self.loop_event[i],'on' if run else 'off')

    @exclusive
    def prgm_delete(self,N):
        self.range_check(N,1,40)
        if not self.profiles:
            raise ControllerInterfaceError("This watlow does not impliment profiles")
        try:
            self.client.writeHolding(18888, N) #set active profile
            self.client.writeHolding(18890, self.invWatlowValDict('delete')) #delete profile
        except ModbusError, e:
            if 'Exception code = 4' in e.message:
                pass # the program does not exist consume the exception
            else:
                raise # something else went wrong pass the exception on up.

    @exclusive
    def sample(self, lookup=None):
        loops = []
        for map in self.profile_loop_map:
            items = ['setpoint','processvalue','enable']
            if map['type'] == 'cascade': items.append('enable_cascade')
            lp = lookup[map['type']][map['num']-1].copy() if lookup else {}
            lp.update(self.get_loop(map['num'],map['type'],items,exclusive=False))
            loops.append(lp)
        return {'datetime':self.get_datetime(exclusive=False),'loops':loops,'status':self.get_status(exclusive=False)}

    @exclusive
    def process_controller(self, update=True):
        '''Lookup the F4T part number and determine: qty loops/cascade loops, qty alarms, profiling capability.
        Returns: part number'''
        pn = self.mod_to_string(self.client.readHolding(16, 15))

        if update: 
            #profile & function blocks (p/n digit 7)
            if (pn[6] == 'B'):
                self.profiles = False
                self.alarms = 8
            elif (pn[6] == 'C'):
                self.profiles = False
                self.alarms = 14
            elif (pn[6] == 'D'):
                self.profiles = True
                self.alarms = 6
            elif (pn[6] == 'E'):
                self.profiles = True
                self.alarms = 8
            elif (pn[6] == 'F'):
                self.profiles = True
                self.alarms = 14
            else: #(pn[6] == 'A')
                self.profiles = False
                self.alarms = 6
            #control algorithms (p/n digit 12)
            if (pn[11] == '2'):
                self.loops = 2
                self.cascades = 0
            elif (pn[11] == '3'):
                self.loops = 3
                self.cascades = 0
            elif (pn[11] == '4'):
                self.loops = 4
                self.cascades = 0
            elif (pn[11] == '5'):
                self.loops = 0
                self.cascades = 0
            elif (pn[11] == '6'):
                self.loops = 0
                self.cascades = 1
            elif (pn[11] == '7'):
                self.loops = 1
                self.cascades = 1
            elif (pn[11] == '8'):
                self.loops = 2
                self.cascades = 1
            elif (pn[11] == '9'):
                self.loops = 3
                self.cascades = 1
            elif (pn[11] == 'A'):
                self.loops = 0
                self.cascades = 2
            elif (pn[11] == 'B'):
                self.loops = 1
                self.cascades = 2
            elif (pn[11] == 'C'):
                self.loops = 2
                self.cascades = 2
            else: #(pn[11] == '1')
                self.loops = 1
                self.cascades = 0
            self.update_profile_loop_map()
        return pn

    @exclusive
    def get_networkSettings(self):
        raise NotImplementedError()

    @exclusive
    def set_networkSettings(self,value):
        if value:
            self.set_message(1,value.get('message','Espec Server Hosted:'),exclusive=False)
            self.set_message(2,value.get('host','NO_HOST_SPECIFIED!'),exclusive=False)
            self.set_message(3,value.get('address','Network Not Up'),exclusive=False)
        else:
            self.set_message(1,exclusive=False)
            self.set_message(2,exclusive=False)
            self.set_message(3,exclusive=False)

    #F4T only interface items
    @exclusive
    def read_io(self, module, io):
        '''Read IO state. Will throw modbus exception code 4 if io does not exist
        module = module number 1-6.
        io = io device, depends on the installed card (high density io has 1-6)'''
        #       mod1   mod2   mod3   mod4   mod5   mod6 (io 1, add 40 for the next io point)
        oreg = [33718, 33958, 34198, 34438, 34678, 34918]
        if module is not None and io is not None:
            self.range_check(module,1,6)
            self.range_check(io,1,6)
            try:
                return (self.watlowValDict[self.client.readHolding(oreg[module-1]+(io-1)*40, 1)[0]] == 'on')
            except ModbusError as e:
                raise ModbusError(4,e.message + " (IO point does not exist)")

    @exclusive
    def get_message(self,N):
        self.range_check(N,1,4)
        return self.mod_to_string(self.client.readHolding(37548+(N-1)*160))

    @exclusive
    def set_message(self,N,value=None):
        self.range_check(N,1,4)
        if value is not None:
            self.client.writeHolding(37548+(N-1)*160, self.string_to_mod(value))
            self.client.writeHolding(37546+(N-1)*160, self.invWatlowValDict('yes')) #show?
        else:
            self.client.writeHolding(37546+(N-1)*160, self.invWatlowValDict('no')) #show?

    @exclusive
    def profile_units(self, N):
        '''Get the units for the profile loops pv/sp, the profile_loop# may not be the same as the loop#'''
        if not self.profiles:
            raise ControllerInterfaceError("This watlow does not impliment profiles, profiles are required to read loop units")
        reg = 16536 + (N-1)*2
        profpv = self.client.readHolding(reg, 1)[0]
        try:
            if self.watlowValDict[profpv] in ['absoluteTemperature','relativeTemperature','notsourced']:
                return u'\xb0%s' % self.watlowValDict[self.client.readHolding(14080 if self.interface == "RTU" else 6730, 1)[0]]
            else:
                return u'%s' % self.watlowValDict[profpv]
        except LookupError:
            return u'ERROR'

    def get_prgm_empty(self):
        '''create a empty null program'''
        haswaits = self.waits[0] != '' or self.waits[1] != '' or self.waits[2] != '' or self.waits[3] != ''
        gsd,ld,evd,wd = [],[],[],[]
        for i in range(self.loops):
            gsd.append({'value':3.0})
        for j in range(self.loops + self.cascades):
            lp = {'target':0,'rate':0,'mode':'','gsoak': False, 'cascade': False,
                  'enable': True if self.loop_event[j] == 0 else False,
                  'showEnable': False if self.loop_event[j] == 0 else True,
                  'isCascade': self.profile_loop_map[j]['type'] == 'cascade'}
            ld.append(lp)
        hidden_events = self.loop_event + self.cascade_event + self.cascade_ctl_event
        hidden_events.append(self.cond_event)
        for j in range(8):
            if j+1 not in hidden_events:
                evd.append({'value':False,'number':j+1})
        for j in range(4):
            if self.waits[j]:
                wd.append({'number':j+1,'condition':'none','value':0})
        steps = [{'type':'instant','duration':{'hours':0,'minutes':0,'seconds':0},'loops':ld,'events':evd,'waits':wd,'jstep':0,'jcount':0}]
        return {'controllerType':'WatlowF4T','name':'','log':False,'gs_dev':gsd,'steps':steps,'haswaits':haswaits}

if __name__ == '__main__':
    print 'running self test'
    ctlr = WatlowF4T(interface='RTU',serialport='\\.\COM4',baudrate=38400)
    ctlr.process_controller()
    ctlr.self_test(ctlr.loops,ctlr.cascades)