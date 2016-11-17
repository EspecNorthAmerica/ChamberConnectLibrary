'''
Common interface for all All ChamberConnectLibrary upper level interfaces

:copyright: (C) Espec North America, INC.
:license: MIT, see LICENSE for more details.
'''
#pylint: disable=W0703,W0201,R0902,W0232,R0904,C0103
from abc import ABCMeta, abstractmethod
from threading import RLock
import traceback
import time

class ControllerInterfaceError(Exception):
    '''Exception that is thrown when a there is a problem communicating with a controller'''
    pass

def exclusive(func):
    '''Lock the physical interface for the function call'''
    def wrapper(self, *args, **kwargs):
        '''Lock the physical interface for the function call'''
        if kwargs.get('exclusive', True):
            with self.lock:
                try:
                    try:
                        del kwargs['exclusive']
                    except Exception:
                        pass
                    self.connect()
                    return func(self, *args, **kwargs)
                finally:
                    try:
                        self.close()
                        if self.interface == "TCP":
                            time.sleep(0.1) #forcefully slow down connection cycles
                    except Exception:
                        pass
        else:
            try:
                del kwargs['exclusive']
            except Exception:
                pass
            return func(self, *args, **kwargs)
    return wrapper

class ItemProperty(object):
    '''copyright Ian Kelly, MIT licensed from
    http://code.activestate.com/recipes/577703-item-properties/
    an implimentation of the python property class with support for index/keys'''
    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        if doc is None and fget is not None and hasattr(fget, "__doc__"):
            doc = fget.__doc__
        self._get = fget
        self._set = fset
        self._del = fdel
        self.__doc__ = doc

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            return BoundItemProperty(self, instance)

    def __set__(self, instance, value):
        raise AttributeError("can't set attribute")

    def __delete__(self, instance):
        raise AttributeError("can't delete attribute")

    def getter(self, fget):
        '''Call the getter function'''
        return ItemProperty(fget, self._set, self._del, self.__doc__)

    def setter(self, fset):
        '''Call the settier function'''
        return ItemProperty(self._get, fset, self._del, self.__doc__)

    def deleter(self, fdel):
        '''Call the deleter'''
        return ItemProperty(self._get, self._set, fdel, self.__doc__)


class BoundItemProperty(object):
    '''copyright Ian Kelly, MIT licensed from
    http://code.activestate.com/recipes/577703-item-properties/'''
    def __init__(self, item_property, instance):
        self.__item_property = item_property
        self.__instance = instance

    def __getitem__(self, key):
        fget = self.__item_property._get
        if fget is None:
            raise AttributeError("unreadable attribute item")
        return fget(self.__instance, key)

    def __setitem__(self, key, value):
        fset = self.__item_property._set
        if fset is None:
            raise AttributeError("can't set attribute item")
        fset(self.__instance, key, value)

    def __delitem__(self, key):
        fdel = self.__item_property._del
        if fdel is None:
            raise AttributeError("can't delete attribute item")
        fdel(self.__instance, key)

class CtlrProperty:
    '''Abstract class for a controller implimentation of the chamberconnectlibrary'''
    __metaclass__ = ABCMeta

    def init_common(self, **kwargs):
        '''Setup properties of all controllers of the chamberconnectlibrary'''
        self.client = None
        self.host = kwargs.get('host', "10.30.100.90")
        self.interface = kwargs.get('interface', "TCP")
        self.adr = kwargs.get('adr', 1)
        self.serialport = kwargs.get('serialport', 4-1) #zero indexed COM4 = 3
        self.baudrate = kwargs.get('baudrate', 19200)
        self.loops = kwargs.get('loops', 1)
        self.cascades = kwargs.get('cascades', 0)
        self.lock = kwargs.get('lock', RLock())

    @abstractmethod
    def get_datetime(self):
        '''
        Get the datetime from the controller.

        Returns:
            datetime. The current time as a datetime.datetime object
        '''
        pass

    @abstractmethod
    def set_datetime(self, value):
        '''
        Set the datetime of the controller.

        Args:
            value (datetime.datetime): The new datetime for the controller.
        '''
        pass

    @abstractmethod
    def get_refrig(self):
        '''
        Get the constant settings for the refigeration system

        returns:
            {"mode":string,"setpoint":int}
        '''
        pass

    @abstractmethod
    def set_refrig(self, value):
        '''
        Set the constant setpoints refrig mode

        params:
            mode: string,"off" or "manual" or "auto"
            setpoint: int,20 or 50 or 100
        '''
        pass

    @abstractmethod
    def get_loop(self, N, loop_type, param_list=None):
        '''
        Get all parameters for a loop from a given list.

        Args:
            N (int): The loop number (1-4).
            loop_type (str): The loop type::
                "cascade" -- A cascade control loop.
                "loop" -- A standard control loop.
            param_list (list(str)): The list of parameters to read defaults::
                "setpoint" -- The target temp/humi/altitude/etc of the control loop
                "processvalue" -- The current conditions inside the chamber
                "range" -- The settable range for the "setpoint"
                "enable" -- Weather the loop is on or off
                "units" -- The units of the "setpoint" or "processvalue" parameters
                "mode" -- The current control status of the loop
                "power" -- The current output power of the loop
                "deviation" -- (type="cascade" only) The allowable difference between air/prod.
                "enable_cascade" -- (type="cascade" only) Enable or disable cascade type control
        Returns:
            dict. The dictionary contains a key for each item in the list argument::
                "setpoint" -- {"constant":float,"current":float}
                "processvalue" -- {"air":float,"product":float} ("product" only w/ type="cascade")
                "range" -- {"min":float,"max":float}
                "enable" -- {"constant":bool,"current":bool}
                "units" -- str
                "mode" -- str('Off' or 'Auto' or 'Manual')
                "deviation" -- {"positive": float, "negative": float}
                "enable_cascade" -- {"constant":bool,"current":bool}
                "power" -- {"constant": float, "current": float}
        '''
        pass

    @abstractmethod
    def set_loop(self, N, loop_type, param_list):
        '''
        Set all parameters for a loop from a given list.

        Args:
            N (int): The loop number (1-4).
            loop_type (str): The loop type::
                "cascade" -- A cascade control loop.
                "loop" -- A standard control loop.
            param_list (dict(dict)): The possible keys and there values::
                "setpoint" -- The target temp/humi/altitude/etc of the control loop
                "range" -- The settable range for the "setpoint"
                "enable" -- turn the control loop on or off
                "power" -- set the manual power of the control loop
                "deviation" -- (type="cascade" only) The allowable difference between air/prod.
                "enable_cascade" -- (type="cascade" only) Enable or disable cascade type control
        '''
        pass

    @abstractmethod
    def get_loop_sp(self, N):
        '''
        Get the setpoint of a control loop.

        Args:
            N (int): The number for the control loop
            constant (bool): Read the constant or current setpoint, None=Both (default=None)
        Returns:
            {"constant":float, "current":float}
        Raises:
            ValueError
        '''
        pass

    @abstractmethod
    def set_loop_sp(self, N, value):
        '''
        Set the setpoint of the control loop.

        Args:
            N (int): The number for the control loop
            value (float): The new setpoint
        Returns:
            None
        Raises:
            ValueError
        '''
        pass

    @abstractmethod
    def get_loop_pv(self, N):
        '''
        Get the process value of a loop.

        Args:
            N (int): The number for the control loop
            product (bool): True=(not valid), False=air temp, None=both (default=None)
        Returns:
            dict(float). product=None
            float. product=bool
        Raises:
            ValueError
        '''
        pass

    @abstractmethod
    def get_loop_range(self, N):
        '''
        Get the valid setpoint range of a loop

        Args:
            N (int): The number of the loop
        Returns:
            {"min": float, "max": float}
        '''
        pass

    @abstractmethod
    def set_loop_range(self, N, value):
        '''
        Set the valid setpoint range of a loop

        Args:
            N (int): The number of the loop
            value: ({"min": float, "max": float}): The range
        '''
        pass

    @abstractmethod
    def get_loop_en(self, N):
        '''
        Get the enable/disable state of a loop

        Args:
            N (int): The number of the loop
        Returns:
            {"constant": bool, "current": bool}
        '''
        pass

    @abstractmethod
    def set_loop_en(self, N, value):
        '''
        Set the enable/disable state of a loop

        Args:
            N (int): The number of the loop
            value (bool): True = loop is running
        '''
        pass

    @abstractmethod
    def get_loop_units(self, N):
        '''
        Get the units for a loop

        Args:
            N (int): The number of the loop
        Returns:
            string
        '''
        pass

    @abstractmethod
    def get_loop_mode(self, N):
        '''
        Get the control mode for a loop

        Args:
            N (int): The number of the loop
        Returns:
            string: The control mode (varies by controller)
        '''
        pass

    @abstractmethod
    def set_loop_mode(self, N, value):
        '''
        Get the control mode for a loop

        Args:
            N (int): The number of the loop
            value (bool): The control mode (varies by controller)
        '''
        pass

    @abstractmethod
    def get_loop_power(self, N):
        '''
        Get the output power(%) for a loop

        Args:
            N (int): The number of the loop
        Returns:
            {"constant": float, "current": float}
        '''
        pass

    @abstractmethod
    def set_loop_power(self, N, value):
        '''
        Set the output power(%) for a loop

        Args:
            N (int): The number of the loop
            value (float): The output power
        '''
        pass

    @abstractmethod
    def get_cascade_sp(self, N):
        '''
        Get the setpoint for a cascade loop

        Args:
            N (int): The number of the loop
        Returns:
            {"constant":float, "current":float, "air":float, "product":float}
        '''
        pass

    @abstractmethod
    def set_cascade_sp(self, N, value):
        '''
        Get the setpoint for a cascade loop

        Args:
            N (int): The number of the loop
            value (float): The setpoint
        '''
        pass

    @abstractmethod
    def get_cascade_pv(self, N):
        '''
        Get the process value for a cascade loop

        Args:
            N (int): The number of the loop
        Returns:
            {"product":float, "air":float}
        '''
        pass

    @abstractmethod
    def get_cascade_range(self, N):
        '''
        Get the valid setpoint range for a cascade loop

        Args:
            N (int): The number of the loop
        Returns:
            {"min":float, "max":float}
        '''
        pass

    @abstractmethod
    def set_cascade_range(self, N, value):
        '''
        Set the valid setpoint range for a cascade loop

        Args:
            N (int): The number of the loop
            value ({"min":float, "max":float}): The range
        '''
        pass

    @abstractmethod
    def get_cascade_en(self, N):
        '''
        Get the enable/disable state for a cascade loop

        Args:
            N (int): The number of the loop
        Returns:
            {"constant":bool, "current":bool}
        '''
        pass

    @abstractmethod
    def set_cascade_en(self, N, value):
        '''
        Set the enable/disable state for a cascade loop

        Args:
            N (int): The number of the loop
            value (bool): True = loop running
        '''
        pass

    @abstractmethod
    def get_cascade_units(self, N):
        '''
        Get the units for a cascade loop

        Args:
            N (int): The number of the loop
        Returns:
            str: The loop units
        '''
        pass

    @abstractmethod
    def get_cascade_mode(self, N):
        '''
        Get the control mode for a cascade loop

        Args:
            N (int): The number of the loop
        Returns:
            str: The control mode
        '''
        pass

    @abstractmethod
    def set_cascade_mode(self, N, value):
        '''
        Set the control mode for a cascade loop

        Args:
            N (int): The number of the loop
            value (str): The control mode
        '''
        pass

    @abstractmethod
    def get_cascade_ctl(self, N):
        '''
        Get enable/disable of cascade mode for a cascade loop

        Args:
            N (int): The number of the loop
        Returns:
            {"constant":bool, "current":bool}
        '''
        pass

    @abstractmethod
    def set_cascade_ctl(self, N, value):
        '''
        Set enable/disable of cascade mode for a cascade loop

        Args:
            N (int): The number of the loop
            value (bool): True = when cascade mode is enabled
        '''
        pass

    @abstractmethod
    def get_cascade_deviation(self, N):
        '''
        Get allowable product to air deviation for a cascade loop

        Args:
            N (int): The number of the loop
        Returns:
            {"positive":float, "negative":float}
        '''
        pass

    @abstractmethod
    def set_cascade_deviation(self, N, value):
        '''
        Set allowable product to air deviation for a cascade loop

        Args:
            N (int): The number of the loop
            value ({"positive": float, "negative": float}): The deviations
        '''
        pass

    @abstractmethod
    def get_cascade_power(self, N):
        '''
        Get the output power for a cascade loop

        Args:
            N (int): The number of the loop
        Returns:
            {"constant":float, "current":float}
        '''
        pass

    @abstractmethod
    def set_cascade_power(self, N, value):
        '''
        Set the output power for a cascade loop

        Args:
            N (int): The number of the loop
            value (float): The output power %
        '''
        pass

    @abstractmethod
    def get_event(self, N):
        '''
        Get the state of a programmable output

        Args:
            N (int): The number of the output
        Returns:
            {"constant":float, "current":float}
        '''
        pass

    @abstractmethod
    def set_event(self, N, value):
        '''
        Set the state of a programmable output

        Args:
            N (int): The number of the output
            value (bool): the output state True = on
        '''
        pass

    @abstractmethod
    def get_status(self):
        '''
        Get the chamber status.

        Returns:
            str: The chamber status
        '''
        pass

    @abstractmethod
    def get_alarm_status(self):
        '''
        Get the chamber alarms status.

        Returns:
            {"active":[int], "inactive":[int]}
        '''
        pass

    @abstractmethod
    def const_start(self):
        '''
        Start the constant mode of the chamber
        '''
        pass

    @abstractmethod
    def stop(self):
        '''
        Start operation of the chamber.
        '''
        pass

    @abstractmethod
    def prgm_start(self, N, step):
        '''
        Start a program on the chamber

        Args:
            N (int): The number of the program to start.
            step (int): The step to start the program on.
        '''
        pass

    @abstractmethod
    def prgm_pause(self):
        '''
        Pause the running program.
        '''
        pass

    @abstractmethod
    def prgm_resume(self):
        '''
        Resume the paused program.
        '''
        pass

    @abstractmethod
    def prgm_next_step(self):
        '''
        Skip to the next step of the running program.
        '''
        pass

    @abstractmethod
    def get_prgm_cur(self):
        '''
        Get the number of the running program

        Returns:
            int: The running program
        '''
        pass

    @abstractmethod
    def get_prgm_cstep(self):
        '''
        Get the current step of the running program.

        Returns:
            int: The current step of the running program
        '''
        pass

    @abstractmethod
    def get_prgm_cstime(self):
        '''
        Get the remaining time of the current step of the running program

        Returns:
            str: HH:MM:SS
        '''
        pass

    @abstractmethod
    def get_prgm_time(self, pgm=None):
        '''
        Get the time until the running program ends.

        Args:
            pgm (dict): The current program cache (optional,speeds up some controllers)
        Returns:
            str: HH:MM
        '''
        pass

    @abstractmethod
    def get_prgm_name(self, N):
        '''
        Get the name of a given program.

        Args:
            N (int): The program to get the name of
        Returns:
            str: The program name
        '''
        pass

    @abstractmethod
    def set_prgm_name(self, N, value):
        '''
        Set the name of a givem program

        Args:
            N (int): The program to set the name of
            value (str): The new name for the program
        '''
        pass

    @abstractmethod
    def get_prgm_steps(self, N):
        '''
        Get the total number of steps in a program

        Args:
            N (int): The program number
        Returns:
            int: The total number of steps
        '''
        pass

    @abstractmethod
    def get_prgms(self):
        '''
        Get a list of all programs on the chamber.

        Returns:
            [{"number":int, "name":str}]
        '''
        pass

    @abstractmethod
    def get_prgm(self, N):
        '''
        Get a program

        Args:
            N (int): The program number
        Returns:
            dict (format varies from controller to controller)
        '''
        pass

    @abstractmethod
    def set_prgm(self, N, value):
        '''
        Set a program

        Args:
            N (int): The program number
            value (dict): The program to write to the controller
        '''
        pass

    @abstractmethod
    def prgm_delete(self, N):
        '''
        Delete a program

        Args:
            N (int): The program number
        '''
        pass

    @abstractmethod
    def sample(self, lookup=None):
        '''
        Take a sample for data logging, gets datetime, mode, and sp/pv on all loops

        Returns:
            {"datetime":datetime.datetime, "loops":[{varies}], "status":str}
        '''
        pass

    @abstractmethod
    def process_controller(self, update=True):
        '''
        Read the controllers "part number" and setup the class as best as possible using it.

        Args:
            update (bool): When true update the classes configuration (default=True)
        Returns:
            str: The "part number"
        '''
        pass

    @abstractmethod
    def get_networkSettings(self):
        '''
        Get the network settings from the controller (if controller supports)

        Returns:
            {"address":str, "mask":str, "gateway":str, "message":str, "host":str}
        '''
        pass

    @abstractmethod
    def set_networkSettings(self, value):
        '''
        Set the network settings of the controller (if controller supports)

        Args:
            value ({"address":str, "mask":str, "gateway":str, "message":str, "host":str}): Settings
        '''
        pass

    #properties
    datetime = property(lambda self: self.get_datetime(),
                        lambda self, value: self.set_datetime(value),
                        doc='datetime object representing the datetime of the controller')

    loop_sp = ItemProperty(lambda self, N: self.get_loop_sp(N),
                           lambda self, N, value: self.set_loop_sp(N, value),
                           doc='setpoint of the specified loop')
    loop_pv = ItemProperty(lambda self, N: self.get_loop_pv(N),
                           doc='process value of the loop')
    loop_range = ItemProperty(lambda self, N: self.get_loop_range(N),
                              lambda self, N, value: self.set_loop_range(N, value),
                              doc='allowable operation range of the specified loop')
    loop_en = ItemProperty(lambda self, N: self.get_loop_en(N),
                           lambda self, N, value: self.set_loop_en(N, value),
                           doc='enable/disable signal of the specified loop')
    loop_units = ItemProperty(lambda self, N: self.get_loop_units(N),
                              doc='units of the specified loop')
    loop_mode = ItemProperty(lambda self, N: self.get_loop_mode(N),
                             lambda self, N, value: self.set_loop_mode(N, value),
                             doc='get the mode of the specified loop')
    loop_power = ItemProperty(lambda self, N: self.get_loop_power(N),
                              lambda self, N, value: self.set_loop_power(N, value),
                              doc='get/set the output power of a secified loop')

    cascade_sp = ItemProperty(lambda self, N: self.get_cascade_sp(N),
                              lambda self, N, value: self.set_cascade_sp(N, value),
                              doc='setpoint of the specified cascade(PTCON) loop')
    cascade_pv = ItemProperty(lambda self, N: self.get_cascade_pv(N),
                              doc='process value of the cascade(PTCON) loop')
    cascade_range = ItemProperty(lambda self, N: self.get_cascade_range(N),
                                 lambda self, N, value: self.set_cascade_range(N, value),
                                 doc='allowable setpoint range of the cascade(PTCON) loop')
    cascade_en = ItemProperty(lambda self, N: self.get_cascade_en(N),
                              lambda self, N, value: self.set_cascade_en(N, value),
                              doc='enable/disable signal of the cascade(PTCON) loop')
    cascade_units = ItemProperty(lambda self, N: self.get_cascade_units(N),
                                 doc='units of the cascade(PTCON) loop')
    cascade_mode = ItemProperty(lambda self, N: self.get_cascade_mode(N),
                                lambda self, N, value: self.set_cascade_mode(N, value),
                                doc='get the mode of the cascade(PTCON) loop')
    cascade_power = ItemProperty(lambda self, N: self.get_cascade_power(N),
                                 lambda self, N, value: self.set_cascade_power(N, value),
                                 doc='get/set the output power of a cascade(PTCON) loop')
    cascade_ctl = ItemProperty(lambda self, N: self.get_cascade_ctl(N),
                               lambda self, N, value: self.set_cascade_ctl(N, value),
                               doc='enable/disable signal for cascade(PTCON) control mode')
    cascade_deviation = ItemProperty(lambda self, N: self.get_cascade_deviation(N),
                                     lambda self, N, value: self.set_cascade_deviation(N, value),
                                     doc='over/under temp range when cascade(PTCON) is operating')

    event = ItemProperty(lambda self, N: self.get_event(N),
                         lambda self, N, value: self.set_event(N, value),
                         doc='Time signal/relay/event status/enable/disable')
    status = property(lambda self: self.get_status(),
                      doc='The controller run status')
    alarm_status = property(lambda self: self.get_alarm_status(),
                            doc='get a list of active alarms by code')

    prgm_cur = property(lambda self: self.get_prgm_cur(),
                        doc='Get the number of the currently executing program')
    prgm_cstep = property(lambda self: self.get_prgm_cstep(),
                          doc='Get the current step of the currently executing program')
    prgm_cstime = property(lambda self: self.get_prgm_cstime(),
                           doc='Get the time remaing of the current step of the current program')
    prgm_time = property(lambda self: self.get_prgm_time(),
                         doc='Get remaining execution time of the current program')
    prgm_name = ItemProperty(lambda self, N: self.get_prgm_name(N),
                             lambda self, N, value: self.set_prgm_name(N, value),
                             doc='The name of the given program')
    prgm_steps = ItemProperty(lambda self, N: self.get_prgm_steps(N),
                              doc='Get the number of steps in a program')
    prgms = property(lambda self: self.get_prgms(),
                     doc='A list of all programs and there names')
    prgm = ItemProperty(lambda self, N: self.get_prgm(N),
                        lambda self, N, value: self.set_prgm(N, value),
                        doc='programs on the controller')

    networkSettings = property(lambda self: self.get_networkSettings(),
                               lambda self, value: self.set_networkSettings(value),
                               doc='network settings displayed by the controller')

    def self_test(self, loops, cascades):
        '''
        preform a self test on all functions

        Args:
            loops (int): The number of standard control loops
            cascades (int): The number of cascade control loops
        '''

        def print_exception(trce):
            '''
            Format an Exception for printing
            '''
            print '\n'.join(['\t' + l for l in trce.split('\n')])

        print 'call process_controller():'
        try:
            print '\t%r' % self.process_controller()
        except Exception:
            print_exception(traceback.format_exc())

        print 'read datetime:'
        try:
            print '\t%r' % self.datetime
        except Exception:
            print_exception(traceback.format_exc())

        print 'write datetime:'
        try:
            self.datetime = self.datetime
            print '\tok'
        except Exception:
            print_exception(traceback.format_exc())

        for i in range(1, loops+1):
            print 'read loop_sp[%d]:' % i
            try:
                print '\t%r' % self.loop_sp[i]
            except Exception:
                print_exception(traceback.format_exc())
            print 'write loop_sp[%d]:' %i
            try:
                self.loop_sp[i] = self.loop_sp[i]['constant']
                print '\tok'
            except Exception:
                print_exception(traceback.format_exc())

            print 'read loop_pv[%d]:' % i
            try:
                print '\t%r' % self.loop_pv[i]
            except Exception:
                print_exception(traceback.format_exc())

            print 'read loop_range[%d]:' % i
            try:
                print '\t%r' % self.loop_range[i]
            except Exception:
                print_exception(traceback.format_exc())
            print 'write loop_range[%d]:' %i
            try:
                self.loop_range[i] = self.loop_range[i]
                print '\tok'
            except Exception:
                print_exception(traceback.format_exc())

            print 'read loop_en[%d]:' % i
            try:
                print '\t%r' % self.loop_en[i]
            except Exception:
                print_exception(traceback.format_exc())
            print 'write loop_en[%d]:' %i
            try:
                self.loop_en[i] = self.loop_en[i]['constant']
                print '\tok'
            except Exception:
                print_exception(traceback.format_exc())

            print 'read loop_units[%d]:' % i
            try:
                print '\t%r' % self.loop_units[i]
            except Exception:
                print_exception(traceback.format_exc())

            print 'read loop_mode[%d]:' % i
            try:
                print '\t%r' % self.loop_mode[i]
            except Exception:
                print_exception(traceback.format_exc())

            print 'read loop_power[%d]:' % i
            try:
                print '\t%r' % self.loop_power[i]
            except Exception:
                print_exception(traceback.format_exc())

        for i in range(1, cascades+1):
            print 'read cascade_sp[%d]:' % i
            try:
                print '\t%r' % self.cascade_sp[i]
            except Exception:
                print_exception(traceback.format_exc())
            print 'write cascade_sp[%d]:' %i
            try:
                self.cascade_sp[i] = self.cascade_sp[i]['constant']
                print '\tok'
            except Exception:
                print_exception(traceback.format_exc())

            print 'read cascade_pv[%d]:' % i
            try:
                print '\t%r' % self.cascade_pv[i]
            except Exception:
                print_exception(traceback.format_exc())

            print 'read cascade_range[%d]:' % i
            try:
                print '\t%r' % self.cascade_range[i]
            except Exception:
                print_exception(traceback.format_exc())
            print 'write cascade_range[%d]:' %i
            try:
                self.cascade_range[i] = self.cascade_range[i]
                print '\tok'
            except Exception:
                print_exception(traceback.format_exc())

            print 'read cascade_en[%d]:' % i
            try:
                print '\t%r' % self.cascade_en[i]
            except Exception:
                print_exception(traceback.format_exc())
            print 'write cascade_en[%d]:' %i
            try:
                self.cascade_en[i] = self.cascade_en[i]['constant']
                print '\tok'
            except Exception:
                print_exception(traceback.format_exc())

            print 'read cascade_units[%d]:' % i
            try:
                print '\t%r' % self.cascade_units[i]
            except Exception:
                print_exception(traceback.format_exc())

            print 'read cascade_mode[%d]:' % i
            try:
                print '\t%r' % self.cascade_mode[i]
            except Exception:
                print_exception(traceback.format_exc())

            print 'read cascade_ctl[%d]:' % i
            try:
                print '\t%r' % self.cascade_ctl[i]
            except Exception:
                print_exception(traceback.format_exc())
            print 'write cascade_ctl[%d]:' %i
            try:
                self.cascade_ctl[i] = self.cascade_ctl[i]
                print '\tok'
            except Exception:
                print_exception(traceback.format_exc())

            print 'read cascade_deviation[%d]:' % i
            try:
                print '\t%r' % self.cascade_deviation[i]
            except Exception:
                print_exception(traceback.format_exc())
            print 'write cascade_deviation[%d]:' %i
            try:
                self.cascade_deviation[i] = self.cascade_deviation[i]
                print '\tok'
            except Exception:
                print_exception(traceback.format_exc())

        for i in range(1, 13):
            print 'read event[%d]:' % i
            try:
                print '\t%r' % self.event[i]
            except Exception:
                print_exception(traceback.format_exc())
            print 'write event[%d]:' %i
            try:
                self.event[i] = self.event[i]['current']
                print '\tok'
            except Exception:
                print_exception(traceback.format_exc())

        print 'read status:'
        try:
            print '\t%r' % self.status
        except Exception:
            print_exception(traceback.format_exc())

        print 'read alarm_status:'
        try:
            print '\t%r' % self.alarm_status
        except Exception:
            print_exception(traceback.format_exc())

        print 'read prgm_cur:'
        try:
            print '\t%r' % self.prgm_cur
        except Exception:
            print_exception(traceback.format_exc())

        print 'read prgm_cstep:'
        try:
            print '\t%r' % self.prgm_cstep
        except Exception:
            print_exception(traceback.format_exc())

        print 'read prgm_cstime:'
        try:
            print '\t%r' % self.prgm_cstime
        except Exception:
            print_exception(traceback.format_exc())

        print 'read prgm_time:'
        try:
            print '\t%r' % self.prgm_time
        except Exception:
            print_exception(traceback.format_exc())

        for i in range(1, 6): #do 5 programs only
            print 'read prgm_name[%d]:' % i
            try:
                print '\t%r' % self.prgm_name[i]
            except Exception:
                print_exception(traceback.format_exc())

            print 'read prgm_steps[%d]:' % i
            try:
                print '\t%r' % self.prgm_steps[i]
            except Exception:
                print_exception(traceback.format_exc())

        print 'read prgms:'
        try:
            print '\t%r' % self.prgms
        except Exception:
            print_exception(traceback.format_exc())

        print 'read prgm[1]:'
        try:
            print '\t%r' % self.prgm[1]
        except Exception:
            print_exception(traceback.format_exc())
        print 'write prgm[1]:'
        try:
            self.prgm[1] = self.prgm[1]
            print '\tok'
        except Exception:
            print_exception(traceback.format_exc())

        print 'read networkSettings:'
        try:
            print '\t%r' % self.networkSettings
        except Exception:
            print_exception(traceback.format_exc())
        print 'write networkSettings:'
        try:
            self.networkSettings = self.networkSettings
            print '\tok'
        except Exception:
            print_exception(traceback.format_exc())

        print 'call const_start():'
        try:
            self.const_start()
            time.sleep(5)
            print '\tok'
        except Exception:
            print_exception(traceback.format_exc())

        print 'call stop():'
        try:
            self.stop()
            time.sleep(5)
            print '\tok'
        except Exception:
            print_exception(traceback.format_exc())

        print 'call prgm_start(1,1):'
        try:
            self.prgm_start(1, 1)
            time.sleep(5)
            print '\tok'
        except Exception:
            print_exception(traceback.format_exc())

        print 'call prgm_pause():'
        try:
            self.prgm_pause()
            time.sleep(5)
            print '\tok'
        except Exception:
            print_exception(traceback.format_exc())

        print 'call prgm_resume():'
        try:
            self.prgm_resume()
            time.sleep(5)
            print '\tok'
        except Exception:
            print_exception(traceback.format_exc())

        print 'call sample():'
        try:
            print '\t%r' % self.sample()
        except Exception:
            print_exception(traceback.format_exc())

        print 'Testing Complete'
