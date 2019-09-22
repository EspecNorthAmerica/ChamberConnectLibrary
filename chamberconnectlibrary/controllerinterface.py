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
import inspect

class ControllerInterfaceError(Exception):
    '''Exception that is thrown when a there is a problem communicating with a controller'''
    pass

def exclusive(func):
    '''Lock the physical interface for the function call'''
    def wrapper(self, *args, **kwargs):
        '''Lock the physical interface for the function call'''
        if kwargs.pop('exclusive', True):
            with self.lock:
                auto_connect = self.client is None
                try:
                    if auto_connect:
                        self.connect()
                    return func(self, *args, **kwargs)
                finally:
                    try:
                        if auto_connect:
                            self.close()
                    except Exception:
                        pass
        else:
            try:
                del kwargs['exclusive']
            except Exception:
                pass
            return func(self, *args, **kwargs)
    return wrapper

class ControllerInterface(metaclass=ABCMeta):
    '''Abstract class for a controller implimentation of the chamberconnectlibrary'''

    loop_map = []
    named_loop_map = {}

    def init_common(self, **kwargs):
        '''Setup properties of all controllers of the chamberconnectlibrary'''
        self.client = None
        self.host = kwargs.get('host')
        self.interface = kwargs.get('interface')
        self.adr = kwargs.get('adr', 1)
        self.serialport = kwargs.get('serialport')
        self.baudrate = kwargs.get('baudrate')
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
            {"mode":string, "setpoint":float}
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

    @exclusive
    def get_loop(self, identifier, *args):
        '''
        Get all parameters for a loop from a given list.
        There are four different ways to call this method; all methods return the same data:

        get_loop(str(identifier), *str(parameters))
            Args:
                identifier (str): The name of the loop.
                parameters (list(string)): The list of parameters to get from the loop, (see below)

        get_loop(str(identifier), [str(parameters)])
            Args:
                identifier (str): The name of the loop.
                parameters (list(string)): The list of parameters to get from the loop, (see below)

        get_loop(int(identifier), str(loop_type), *str(parameters))
            Args:
                identifier (str): The name of the loop.
                loop_type (str): The type of loop to be accessed ("loop" or "cascade")
                parameters (list(string)): The list of parameters to get from the loop, (see below)

        get_loop(int(identifier), str(loop_type), [str(parameters)])
            Args:
                identifier (str): The name of the loop.
                loop_type (str): The type of loop to be accessed ("loop" or "cascade")
                parameters (list(string)): The list of parameters to get from the loop, (see below)

        parameters:
            The following is a list of available parameters as referenced by each call type:
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
        loop_functions = {
            'cascade':{
                'setpoint':self.get_cascade_sp,
                'setPoint':self.get_cascade_sp,
                'setValue':self.get_cascade_sp,
                'processvalue':self.get_cascade_pv,
                'processValue':self.get_cascade_pv,
                'range':self.get_cascade_range,
                'enable':self.get_cascade_en,
                'units':self.get_cascade_units,
                'mode':self.get_cascade_mode,
                'deviation':self.get_cascade_deviation,
                'enable_cascade':self.get_cascade_ctl,
                'power': self.get_cascade_power
            },
            'loop':{
                'setpoint':self.get_loop_sp,
                'setPoint':self.get_loop_sp,
                'setValue':self.get_loop_sp,
                'processvalue':self.get_loop_pv,
                'processValue':self.get_loop_pv,
                'range':self.get_loop_range,
                'enable':self.get_loop_en,
                'units':self.get_loop_units,
                'mode':self.get_loop_mode,
                'power':self.get_loop_power
            }
        }

        if isinstance(identifier, str):
            my_loop_map = self.loop_map[self.named_loop_map[identifier]]
            loop_number = my_loop_map['num']
            loop_type = my_loop_map['type']
            param_list = args if len(args) > 0 else None
        elif isinstance(identifier, int) and len(args) >= 1:
            loop_number = identifier
            loop_type = args[0]
            param_list = args[1:] if len(args) > 1 else None
        else:
            raise ValueError(
                'invalid argument format, call w/: '
                'get_loop(int(identifier), str(loop_type), *args) or '
                'get_loop(str(identifier), *args), *args are optional.'
            )

        if param_list is None:
            param_list = list(loop_functions[loop_type].keys())
            excludes = ['setPoint', 'setValue', 'processValue']
            param_list = [x for x in param_list if x not in excludes]
        elif len(param_list) >= 1 and \
             (isinstance(param_list[0], list) or isinstance(param_list[0], tuple)):
            param_list = param_list[0]
        ret = {}
        for key in param_list:
            try:
                ret[key] = loop_functions[loop_type][key](loop_number, exclusive=False)
            except KeyError:
                ret[key] = None
            except NotImplementedError:
                ret[key] = None
        return ret

    @exclusive
    def set_loop(self, identifier, loop_type='loop', param_list=None, **kwargs):
        '''
        Set all parameters for a loop from a given list.

        Args:
            identifier (int or str): The loop number, or the name of the loop
            loop_type (str): The loop type (disregarded when identifier is a str)::
                "cascade" -- A cascade control loop.
                "loop" -- A standard control loop (default).
            param_list (dict(dict)): The parameters to update as a dictionary::
                see kwargs for possible keys/values
            kwargs (dict): The parameters to update as key word arguments, param_list overrides::
                "setpoint" -- The target temp/humi/altitude/etc of the control loop
                "range" -- The settable range for the "setpoint"
                "enable" -- turn the control loop on or off
                "power" -- set the manual power of the control loop
                "mode" -- set the control mode of the control loop
                "deviation" -- (type="cascade" only) The allowable difference between air/prod.
                "enable_cascade" -- (type="cascade" only) Enable or disable cascade type control
        Returns:
            None
        '''
        loop_functions = {
            'cascade':{
                'setpoint':self.set_cascade_sp,
                'setPoint':self.set_cascade_sp,
                'setValue':self.set_cascade_sp,
                'range':self.set_cascade_range,
                'enable':self.set_cascade_en,
                'deviation':self.set_cascade_deviation,
                'enable_cascade':self.set_cascade_ctl,
                'mode':self.set_cascade_mode,
                'power':self.set_cascade_power
            },
            'loop':{
                'setpoint':self.set_loop_sp,
                'setPoint':self.set_loop_sp,
                'setValue':self.set_loop_sp,
                'range':self.set_loop_range,
                'enable':self.set_loop_en,
                'mode':self.set_loop_mode,
                'power':self.set_loop_power
            }
        }
        if param_list is None:
            param_list = kwargs
        if isinstance(identifier, str):
            my_loop_map = self.loop_map[self.named_loop_map[identifier]]
            loop_number = my_loop_map['num']
            loop_type = my_loop_map['type']
        elif isinstance(identifier, int):
            loop_number = identifier
        else:
            raise ValueError(
                'invalid argument format, call w/: '
                'set_loop(int(identifier), str(loop_type), **kwargs) or '
                'get_loop(str(identifier), **kwargs)'
            )

        #mode must be done first
        if 'mode' in param_list:
            loop_functions[loop_type]['mode'](
                exclusive=False,
                N=loop_number,
                value=param_list.pop('mode')
            )
        for key, val in list(param_list.items()):
            try:
                loop_functions[loop_type][key](
                    exclusive=False,
                    N=loop_number,
                    value=val
                )
            except KeyError:
                pass
            except NotImplementedError:
                pass

    @exclusive
    def get_operation(self, pgm=None):
        '''
        Get the complete operation status of the chamber (excludes control loops and events).

        Args:
            pgm (dict): A cached version of the running program, if None it will be retrieved.
        Returns:
            dict::
                "mode" -- str('program' or 'constant' or 'standby' or 'off' or 'alarm' or 'paused')
                "status" -- str(varies by controller; more detailed/format'd version of "mode" key)
                "program" --
                "alarm" -- [int] list of active alarms by number, empty list if no alarms
        '''
        status = self.get_status(exclusive=False)
        ret = {'status': status}
        if 'Paused' in status:
            ret['mode'] = 'program_pause'
        elif status.startswith('Prog'):
            ret['mode'] = 'program'
        elif status.startswith('Const'):
            ret['mode'] = 'constant'
        elif status.startswith('Stand'):
            ret['mode'] = 'standby'
        elif status == 'Off':
            ret['mode'] = 'off'
        elif status == 'Alarm':
            ret['mode'] = 'alarm'
        else:
            ret['mode'] = 'ERROR'

        if 'Program' in status:
            pnum = self.get_prgm_cur(exclusive=False)
            ret['program'] = {
                'number':pnum,
                'step':self.get_prgm_cstep(),
                'time_remaining':self.get_prgm_time(pgm, exclusive=False),
                'step_time_remaining':self.get_prgm_cstime(exclusive=False),
                'name':self.get_prgm_name(pnum, exclusive=False),
                'steps':self.get_prgm_steps(pnum, exclusive=False),
                'cycles':self.get_prgm_counter(exclusive=False)
            }
        else:
            ret['program'] = None

        if status == 'Alarm':
            ret['alarms'] = self.get_alarm_status(exclusive=False)['active']
        else:
            ret['alarms'] = None

        return ret


    @exclusive
    def set_operation(self, mode, **kwargs):
        '''
        Update the controllers operation mode (ie run a program, stop, constant etc)

        Args:
            mode (string): The mode to run:
                'standby' or 'off': Stop the chamber from running
                'constant': Start the configured constant mode
                'program': run a program
                'program_pause': pause the running program
                'program_resume': resume the paused program
                'program_advance': force the program to the next step.
        kwargs:
            program (int or dict): the program # to run, valid dict: {'number':int, 'step': int}
            step (int): the step # to start the program on. (Default=1)
        Returns:
            dict::
                "mode" -- str('program' or 'constant' or 'standby' or 'off' or 'alarm' or 'paused')
                "status" -- str(varies by controller; more detailed/format'd version of "mode" key)
                "program" --
                "alarm" -- [int] list of active alarms by number, empty list if no alarms
        '''
        if mode in ['standby', 'off']:
            self.stop(exclusive=False)
        elif mode == 'constant':
            self.const_start(exclusive=False)
        elif mode == 'program':
            if isinstance(kwargs['program'], dict):
                self.prgm_start(
                    kwargs['program']['number'],
                    kwargs['program'].get('step', 1),
                    exclusive=False
                )
            else:
                self.prgm_start(kwargs['program'], kwargs.get('step', 1), exclusive=False)
        elif mode == 'program_pause':
            self.prgm_pause(exclusive=False)
        elif mode == 'program_resume':
            self.prgm_resume(exclusive=False)
        elif mode == 'program_advance':
            self.prgm_next_step(exclusive=False)
        else:
            raise ValueError('unsupported mode parameter')

    @exclusive
    def get_program(self, N):
        '''
        Get a program (alias for get_prgm)

        Args:
            N (int): The program number
        Returns:
            dict (format varies from controller to controller)
        '''
        return self.get_prgm(N, exclusive=False)

    @exclusive
    def set_program(self, N, value):
        '''
        Set a program (alias for set_prgm)

        Args:
            N (int): The program number
            value (dict): The program to write to the controller, None erases the given program
        '''
        if value is None:
            return self.prgm_delete(N, exclusive=False)
        else:
            return self.set_prgm(N, value, exclusive=False)

    @exclusive
    def get_program_list(self):
        '''
        Get a list of all programs on the chamber. (alias for get_prgms)

        Returns:
            [{"number":int, "name":str}]
        '''
        return self.get_prgms(exclusive=False)

    @exclusive
    def get_program_details(self, N):
        '''
        Get the name and number of steps of a program.

        Args:
            N (int): The program number
        Returns:
            {"number":int, "name":str, "steps":int}
        '''
        return {
            'number':N,
            'name':self.get_prgm_name(N, exclusive=False),
            'steps':self.get_prgm_steps(N, exclusive=False)
        }

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
    def get_loop_modes(self, N):
        '''
        Get the available modes for a loop

        Args:
            N (int): The number of the loop
        Returns:
            string: list of control modes
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
    def get_cascade_modes(self, N):
        '''
        Get the available modes for a cascade loop

        Args:
            N (int): The number of the loop
        Returns:
            string: list of control modes
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
            {"constant":bool, "current":bool}
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
    def get_prgm_counter(self):
        '''
        Get the status of the jump step/counter

        Returns:
            [{'name':str, 'start':int, 'end':int, 'cycles':int, 'remaining':int}]
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

    @exclusive
    def sample(self, lookup=None, **kwargs):
        '''
        Take a sample for data logging, gets datetime, mode, and sp/pv on all loops

        kwargs:
            get_loops (bool): If true get loop status (Default=True)
            get_status (bool): If true get controller operation status. (Default=True)
            get_alarms (bool): If true get the controller alarms status. (Default=False)
            get_program_status (bool): If true get information about the running progam. (Default=False)
            get_events (list or dict): A list of events to get the current status of (Default=None)
            get_program_list (bool): get a list of programs on the controller. (Default=False)
            get_refrig (bool): If true get the controller refrig mode. (Default=False)
        Returns:
            {"datetime":datetime.datetime, "loops":[{varies}], "status":str}
        '''
        ret = {'datetime':self.get_datetime(exclusive=False)}
        if kwargs.get('get_loops', True):
            ret['loops'] = []
            for tmap in self.loop_map:
                items = ['setpoint', 'processvalue', 'enable', 'mode', 'power', 'units', 'range']
                if tmap['type'] == 'cascade':
                    items += ['enable_cascade', 'deviation']
                if lookup:
                    lkps = [lkp for lkp in lookup[tmap['type']] if lkp['number'] == tmap['num']]
                    lpdata = lkps[0].copy() if lookup else {}
                    lpdata.update(self.get_loop(tmap['num'], tmap['type'], items, exclusive=False))
                    ret['loops'].append(lpdata)
        if kwargs.get('get_status', True) or kwargs.get('get_program_status', False):
            ret['status'] = self.get_status(exclusive=False)
        if kwargs.get('get_alarms', False):
            ret['alarms'] = self.get_alarm_status(exclusive=False)
        if kwargs.get('get_program_status', False) and self.profiles:
            if ret['status'].startswith('Program') and 'Remote' not in ret['status']:
                cpn = self.get_prgm_cur(exclusive=False)
                ret['program_status'] = {
                    'number':cpn,
                    'name':self.get_prgm_name(cpn, exclusive=False),
                    'step':self.get_prgm_cstep(exclusive=False),
                    'time_step':self.get_prgm_cstime(exclusive=False),
                    'time_total':self.get_prgm_time(kwargs.get('running_program'), exclusive=False),
                    'counters':self.get_prgm_counter(exclusive=False)
                }
            else:
                ret['program_status'] = {p:None for p in ['number', 'name', 'step', 'time_step', 'time_total', 'counters']}
        if kwargs.get('get_program_list', False) and self.profiles:
            ret['program_list'] = self.get_prgms(exclusive=False)
        if kwargs.get('get_events', None):
            if isinstance(kwargs['get_events'][0], dict):
                events = kwargs['get_events']
            else:
                events = [{'N':i} for i in kwargs['get_events']]
            for event in events:
                event['status'] = self.get_event(event['N'], exclusive=False)
            ret['events'] = events
        if kwargs.get('get_refrig', False):
            try:
                ret['refrig'] = self.get_refrig(exclusive=False)
            except NotImplementedError:
                ret['refrig'] = None
        return ret

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
    def get_network_settings(self):
        '''
        Get the network settings from the controller (if controller supports)

        Returns:
            {"address":str, "mask":str, "gateway":str, "message":str, "host":str}
        '''
        pass

    @abstractmethod
    def set_network_settings(self, value):
        '''
        Set the network settings of the controller (if controller supports)

        Args:
            value ({"address":str, "mask":str, "gateway":str, "message":str, "host":str}): Settings
        '''
        pass

    def get_operation_modes(self):
        '''
        Get the supported operation modes for this controller.

        Returns:
            ["standby","constant","program"] or ["constant","program"]
        '''
        return ['standby', 'constant', 'program']

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
            print('\n'.join(['\t' + l for l in trce.split('\n')]))

        print('process_controller():')
        try:
            print('\t%r' % self.process_controller())
        except Exception:
            print_exception(traceback.format_exc())

        print('get_datetime:')
        try:
            print('\t%r' % self.get_datetime())
        except Exception:
            print_exception(traceback.format_exc())

        print('set_datetime:')
        try:
            self.set_datetime(self.get_datetime())
            print('\tok')
        except Exception:
            print_exception(traceback.format_exc())

        print('get_operation:')
        try:
            print('\t%r' % self.get_operation())
        except Exception:
            print_exception(traceback.format_exc())

        for lpi in range(loops):
            i = lpi + 1
            print('get_loop_sp(%d):' % i)
            try:
                print('\t%r' % self.get_loop_sp(i))
            except Exception:
                print_exception(traceback.format_exc())
            print('set_loop_sp(%d):' %i)
            try:
                self.set_loop_sp(i, self.get_loop_sp(i)['constant'])
                print('\tok')
            except Exception:
                print_exception(traceback.format_exc())

            print('get_loop_pv(%d):' % i)
            try:
                print('\t%r' % self.get_loop_pv(i))
            except Exception:
                print_exception(traceback.format_exc())

            print('get_loop_range(%d):' % i)
            try:
                print('\t%r' % self.get_loop_range(i))
            except Exception:
                print_exception(traceback.format_exc())
            print('set_loop_range(%d):' %i)
            try:
                self.set_loop_range(i, self.get_loop_range(i))
                print('\tok')
            except Exception:
                print_exception(traceback.format_exc())

            print('get_loop_en(%d):' % i)
            try:
                print('\t%r' % self.get_loop_en(i))
            except Exception:
                print_exception(traceback.format_exc())
            print('set_loop_en(%d):' %i)
            try:
                self.set_loop_en(i, self.get_loop_en(i)['constant'])
                print('\tok')
            except Exception:
                print_exception(traceback.format_exc())

            print('get_loop_units(%d):' % i)
            try:
                print('\t%r' % self.get_loop_units(i))
            except Exception:
                print_exception(traceback.format_exc())

            print('get_loop_mode(%d):' % i)
            try:
                print('\t%r' % self.get_loop_mode(i))
            except Exception:
                print_exception(traceback.format_exc())

            print('get_loop_power(%d):' % i)
            try:
                print('\t%r' % self.get_loop_power(i))
            except Exception:
                print_exception(traceback.format_exc())

        for csi in range(cascades):
            i = csi + 1
            print('get_cascade_sp[%d]:' % i)
            try:
                print('\t%r' % self.get_cascade_sp(i))
            except Exception:
                print_exception(traceback.format_exc())
            print('set_cascade_sp(%d):' %i)
            try:
                self.set_cascade_sp(i, self.get_cascade_sp(i)['constant'])
                print('\tok')
            except Exception:
                print_exception(traceback.format_exc())

            print('get_cascade_pv(%d):' % i)
            try:
                print('\t%r' % self.get_cascade_pv(i))
            except Exception:
                print_exception(traceback.format_exc())

            print('get_cascade_range(%d):' % i)
            try:
                print('\t%r' % self.get_cascade_range(i))
            except Exception:
                print_exception(traceback.format_exc())
            print('set_cascade_range[%d]:' %i)
            try:
                self.set_cascade_range(i, self.get_cascade_range(i))
                print('\tok')
            except Exception:
                print_exception(traceback.format_exc())

            print('get_cascade_en[%d]:' % i)
            try:
                print('\t%r' % self.get_cascade_en(i))
            except Exception:
                print_exception(traceback.format_exc())
            print('set_cascade_en(%d):' %i)
            try:
                self.set_cascade_en(i, self.get_cascade_en(i)['constant'])
                print('\tok')
            except Exception:
                print_exception(traceback.format_exc())

            print('get_cascade_units(%d):' % i)
            try:
                print('\t%r' % self.get_cascade_units(i))
            except Exception:
                print_exception(traceback.format_exc())

            print('get_cascade_mode(%d):' % i)
            try:
                print('\t%r' % self.get_cascade_mode(i))
            except Exception:
                print_exception(traceback.format_exc())

            print('get_cascade_ctl(%d):' % i)
            try:
                print('\t%r' % self.get_cascade_ctl(i))
            except Exception:
                print_exception(traceback.format_exc())
            print('set_cascade_ctl(%d):' %i)
            try:
                self.set_cascade_ctl(i, self.get_cascade_ctl(i))
                print('\tok')
            except Exception:
                print_exception(traceback.format_exc())

            print('get_cascade_deviation(%d):' % i)
            try:
                print('\t%r' % self.get_cascade_deviation(i))
            except Exception:
                print_exception(traceback.format_exc())
            print('set_cascade_deviation(%d):' %i)
            try:
                self.set_cascade_deviation(i, self.get_cascade_deviation(i))
                print('\tok')
            except Exception:
                print_exception(traceback.format_exc())

        for i in range(1, 13):
            print('get_event(%d):' % i)
            try:
                print('\t%r' % self.get_event(i))
            except Exception:
                print_exception(traceback.format_exc())
            print('set_event(%d):' %i)
            try:
                self.set_event(i, self.get_event(i)['current'])
                print('\tok')
            except Exception:
                print_exception(traceback.format_exc())

        print('get_status:')
        try:
            print('\t%r' % self.get_status())
        except Exception:
            print_exception(traceback.format_exc())

        print('get_alarm_status:')
        try:
            print('\t%r' % self.get_alarm_status())
        except Exception:
            print_exception(traceback.format_exc())

        print('get_prgm_cur:')
        try:
            print('\t%r' % self.get_prgm_cur())
        except Exception:
            print_exception(traceback.format_exc())

        print('get_prgm_cstep:')
        try:
            print('\t%r' % self.get_prgm_cstep())
        except Exception:
            print_exception(traceback.format_exc())

        print('get_prgm_cstime:')
        try:
            print('\t%r' % self.get_prgm_cstime())
        except Exception:
            print_exception(traceback.format_exc())

        print('get_prgm_time:')
        try:
            print('\t%r' % self.get_prgm_time())
        except Exception:
            print_exception(traceback.format_exc())

        for i in range(1, 6): #do 5 programs only
            print('get_prgm_name(%d):' % i)
            try:
                print('\t%r' % self.get_prgm_name(i))
            except Exception:
                print_exception(traceback.format_exc())

            print('get_prgm_steps(%d):' % i)
            try:
                print('\t%r' % self.get_prgm_steps(i))
            except Exception:
                print_exception(traceback.format_exc())

        print('get_prgms:')
        try:
            print('\t%r' % self.get_prgms())
        except Exception:
            print_exception(traceback.format_exc())

        print('get_prgm(1):')
        try:
            print('\t%r' % self.get_prgm(1))
        except Exception:
            print_exception(traceback.format_exc())
        print('set_prgm(1):')
        try:
            self.set_prgm(2, self.get_prgm(1))
            print('\tok')
        except Exception:
            print_exception(traceback.format_exc())

        print('get_network_settings:')
        try:
            print('\t%r' % self.get_network_settings())
        except Exception:
            print_exception(traceback.format_exc())
        print('set_network_settings:')
        try:
            self.set_network_settings(self.get_network_settings())
            print('\tok')
        except Exception:
            print_exception(traceback.format_exc())

        print('call const_start():')
        try:
            self.const_start()
            time.sleep(5)
            print('\tok')
        except Exception:
            print_exception(traceback.format_exc())

        print('call stop():')
        try:
            self.stop()
            time.sleep(5)
            print('\tok')
        except Exception:
            print_exception(traceback.format_exc())

        print('call prgm_start(1,1):')
        try:
            self.prgm_start(1, 1)
            time.sleep(5)
            print('\tok')
        except Exception:
            print_exception(traceback.format_exc())

        print('call prgm_pause():')
        try:
            self.prgm_pause()
            time.sleep(5)
            print('\tok')
        except Exception:
            print_exception(traceback.format_exc())

        print('call prgm_resume():')
        try:
            self.prgm_resume()
            time.sleep(5)
            print('\tok')
        except Exception:
            print_exception(traceback.format_exc())

        print('call sample():')
        try:
            print('\t%r' % self.sample())
        except Exception:
            print_exception(traceback.format_exc())

        print('Testing Complete')
