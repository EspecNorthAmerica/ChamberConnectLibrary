# Initialization  
Examples on setting up the instantiating the correct class for a chamber.

* **Watlow F4T based chambers**  
    The examples shown below are for benchtop chambers (model #'s: BT?-???).
    The Watlow F4T is highly configurable and the library requires some basic configurations to match that.
    All Espec North America chambers using a F4T follow the same design standard when possible;
    meaining that the constructor calls shown below should work on any temp/humidity chamber.

    ```python
    from chamberconnectlibrary.watlowf4t import WatlowF4T

    #example interface_params for RS232/RS485 on port 7 (windows) Modbus address=1
    interface_params = {'interface':'RTU', 'baudrate':38400, serialport:'//./COM7', 'adr':1}

    #example interface_params for RS232/RS485 on ttyUSB0 (linux) Modbus address=1
    interface_params = {'interface':'RTU', 'baudrate':38400, serialport:'/dev/ttyUSB0', 'adr':1}

    #example interface_params for a TCP connection to 10.30.100.55
    interface_params = {'interface':'TCP', 'host':10.30.100.55}

    #example for temp only chamber (BTU-??? or BTZ-???)
    controller = WatlowF4T(
        alarms=8, # the number of available alarms
        profiles=True, # the controller has programming
        loops=1, # the number of control loops (ie temperature)
        cond_event=9, # the event that enables/disables conditioning
        cond_event_toggle=False, # is the condition momentary(False), or maintained(True)
        run_module=1, # The io module that has the chamber run output
        run_io=1, # The run output on the mdoule that has the chamber run out put
        limits=[5], # A list of modules that contain limit type cards.
        **interface_params
    )

    #example for temp/humidity chamber (BTL-??? or BTX-???)
    controller = WatlowF4T(
        alarms=8, # the number of available alarms
        profiles=True, # the controller has programming
        loops=2, # the number of control loops (ie temperature)
        cond_event=9, # the event that enables/disables conditioning (9 is key 1)
        cond_event_toggle=False, # is the condition momentary(False), or maintained(True)
        run_module=1, # The io module that has the chamber run output
        run_io=1, # The run output on the mdoule that has the chamber run out put
        limits=[5], # A list of modules that contain limit type cards.
        loop_event=[0,2,0,0], # A list of event #'s that enable/disable a control loop
        **interface_params
    )

    #example for temp only chamber with Product temperature control (aka "PTCON" or "cascade") (BTU-??? or BTZ-???)
    controller = WatlowF4T(
        alarms=8, # the number of available alarms
        profiles=True, # the controller has programming
        loops=0, # the number of control loops (ie temperature)
        cond_event=9, # the event that enables/disables conditioning
        cond_event_toggle=False, # is the condition momentary(False), or maintained(True)
        run_module=1, # The io module that has the chamber run output
        run_io=1, # The run output on the mdoule that has the chamber run out put
        limits=[5], # A list of modules that contain limit type cards.
        cascades=1, # the number of cascade loops (ie temperature with PTCON)
        cascade_ctl_event=[7,0,0,0] # the event that enables PTCON
        **interface_params
    )

    #example for temp/humidity chamber with Product temperature control (aka "PTCON" or "cascade") (BTL-??? or BTX-???)
    controller = WatlowF4T(
        alarms=8, # the number of available alarms
        profiles=True, # the controller has programming
        loops=1, # the number of control loops (ie temperature)
        cond_event=9, # the event that enables/disables conditioning (9 is key 1)
        cond_event_toggle=False, # is the condition momentary(False), or maintained(True)
        run_module=1, # The io module that has the chamber run output
        run_io=1, # The run output on the mdoule that has the chamber run out put
        limits=[5], # A list of modules that contain limit type cards.
        loop_event=[0,2,0,0], # A list of event #'s that enable/disable a control loop
        cascades=1, # the number of cascade loops (ie temperature with PTCON)
        cascade_ctl_event=[7,0,0,0] # the event that enables PTCON
        **interface_params
    )
    ```
* **P300/SCP-220 based chambers**  
    The vast majority of chambers sold by Espec North America use one of these controllers.
    The setup for these controllers is much simpler.

    ```python
    from chamberconnectlibrary.espec import Espec

    #example interface_params for RS232/RS485 on port 7 (windows) RS485 address = 1
    interface_params = {'interface':'Serial', 'baudrate':19200, serialport:'//./COM7', 'adr':1}

    #example interface_params for RS232/RS485 on ttyUSB0 (linux) RS485 address = 1
    interface_params = {'interface':'Serial', 'baudrate':19200, serialport:'/dev/ttyUSB0', 'adr':1}

    #example interface_params for a TCP connection to 10.30.100.55
    interface_params = {'interface':'TCP', 'host':10.30.100.55}

    #when connecting to a P300:
    controller_type = 'P300'
    
    #when connecting to a SCP220:
    controller_type = 'SCP220'

    #example for temp only chamber
    controller = Espec(ctrl_type=controller_type, loops=1, **interface_params)

    #example for temp/humidity chamber
    controller = Espec(ctrl_type=controller_type, loops=2, **interface_params)

    #example for temp only chamber w/ product temperature control (aka PTCON)
    controller = Espec(ctrl_type=controller_type, loops=0, cascades=1, **interface_params)

    #example for temp/humidity chamber w/ product temperature control (aka PTCON)
    controller = Espec(ctrl_type=controller_type, loops=1, cascades=1, **interface_params)

    #or the library can figure it out automatically:
    controller = Espec(ctrl_type=controller_type, **interface_params)
    controller.process_controller()
    ```
* **Watlow F4 based chambers**  
    This controller is for legacy chambers; there are no design standards so exact Examples
    are not possible.

    ```python
    from chamberconnectlibrary.watlowf4 import WatlowF4

    #example interface_params for RS232/RS485 on port 7 (windows) Modbus address=1
    interface_params = {'interface':'RTU', 'baudrate':38400, serialport:'//./COM7', 'adr':1}

    #example interface_params for RS232/RS485 on ttyUSB0 (linux) Modbus address=1
    interface_params = {'interface':'RTU', 'baudrate':38400, serialport:'/dev/ttyUSB0', 'adr':1}

    #example interface_params for a TCP connection to 10.30.100.55
    interface_params = {'interface':'TCP', 'host':10.30.100.55}

    #example for temp only chamber (BTU-??? or BTZ-???)
    controller = WatlowF4(
        profiles=True,
        loops=2, # 1 or 2 for temp only or temp/humidity respectively
        loop_event=[0, 8], # event 8 was generally used for enabling humidity (loop 2)
        cond_event=7, # no condition event is available on most f4 based ENA chambers.
        limits=[1], # A list of external inputs used for alarms/limits, most ENA chambers used DI#1 for an alarm
        **interface_params
    )
    ```

# Getter Functions  
Functions used to retrieve information from the controller.


## get_loop(N, loop_type, &ast;param_list=None)
Get parameters for a loop from a given list (or all if no list is provided)
* **Arguments**:
    * **N** (int): The loop number (1-4)
    * **loop_type** (str): The loop type, possible values:
        * `"cascade"`: A cascade control loop
        * `"loop"`: A standard control loop.
    * **&ast;param_list** (list(str) or list(list(str))): The list of parameters to read,
    it may be positional arguments or a single list ie:  
    `get_loop_byname('temp', ['setpoint', 'range'])` == `get_loop_byname('temp', 'setpoint', 'range')`  
    valid items:  
        * `"setpoint"`: The target temp/humi/altitude/etc of the control loop
        * `"processvalue"`: The current conditions inside the chamber
        * `"range"`: The settable range for the "setpoint"
        * `"enable"`: Weather the loop is on or off
        * `"units"`: The units of the "setpoint" or "processvalue" parameters
        * `"mode"`: The current control status of the loop
        * `"power"`: The current output power of the loop
        * `"deviation"`: (type="cascade" only) The allowable difference between air/prod.
        * `"enable_cascade"`: (type="cascade" only) Enable or disable cascade type control
* **Returns**:  
    A dictionary containing a key for each item in the `param_list` argument.  
    Example return value for when `param_list=None`:

    ```python
    {
        "setpoint":{"constant":float, "current":float, "air":float, "product":float}, # "product"/"air" only w/ type="cascade"
        "processvalue":{"air":float, "product":float}, # "product" only w/ type="cascade"
        "range":{"min":float, "max":float},
        "enable":{"constant":bool, "current":bool},
        "units":str,
        "mode":str,
        "power":{"constant": float, "current": float},
        "deviation":{"positive": float, "negative": float}, # only w/ type="cascade"
        "enable_cascade":{"constant":bool, "current":bool}, # only w/ type="cascade"
    }
    ```

* **Example**:  
    `controller.get_loop(1, 'loop')`

## get_loop_byname(name, &ast;param_list)
Get parameters for a loop from a given list (or all if no list is provided)
* **Arguments**:
    * **name** (str): name of the loop setup during init
    * ***param_list** (list(str) or list(list(str))): The list of parameters to read,
    it may be positional arguments or a single list ie:  
    `get_loop_byname('temp', ['setpoint', 'range'])` == `get_loop_byname('temp', 'setpoint', 'range')`  
    valid items:
        * `"setpoint"`: The target temp/humi/altitude/etc of the control loop
        * `"processvalue"`: The current conditions inside the chamber
        * `"range"`: The settable range for the "setpoint"
        * `"enable"`: Weather the loop is on or off
        * `"units"`: The units of the "setpoint" or "processvalue" parameters
        * `"mode"`: The current control status of the loop
        * `"power"`: The current output power of the loop
        * `"deviation"`: (type="cascade" only) The allowable difference between air/prod.
        * `"enable_cascade"`: (type="cascade" only) Enable or disable cascade type control
* **Returns**:  
    A dictionary containing a key for each item in the `param_list` argument.  
    Example return value for when `param_list=None`:

    ```python
    {
        "setpoint":{"constant":float, "current":float, "air":float, "product":float}, # "product"/"air" only w/ type="cascade"
        "processvalue":{"air":float, "product":float}, # "product" only w/ type="cascade"
        "range":{"min":float, "max":float},
        "enable":{"constant":bool, "current":bool},
        "units":str,
        "mode":str,
        "power":{"constant": float, "current": float},
        "deviation":{"positive": float, "negative": float}, # only w/ type="cascade"
        "enable_cascade":{"constant":bool, "current":bool}, # only w/ type="cascade"
    }
    ```

* **Example**:  
    `controller.get_loop('temp')`

## get_operation(pgm=None)
Get the complete operation status of the chamber.
* **Arguments**:
    * **pgm** (dict): Optional. The currently executing program; used to speed up calculating
    the time until program end.
* **Returns**:  
    A dictionary containing the current status of the chamber.  
    Example while running a program:

    ```python
    {
        "mode":str, # possible values:'program'/'constant'/'standby'/'off'/'alarm'/'paused'
        "status":str, # a more verbose version of mode, generally used user displays.
        "program": {
            'number':int,
            'step':int,
            'time_remaining':str, # format= "1234:59:59" ie "HOURS:MINUTES:SECONDS" or "ERROR: reason"
            'step_time_remaining':str, # format= "1234:59:59" ie "HOURS:MINUTES:SECONDS",
            'name':str,
            'steps':int
        },
        "alarm":None # or a list of integers ie: [1, 2]
    }
    ```

* **Example**:  
    `controller.get_operation()`

## get_program(N)
Read an entire program from the controller.
* **Arguments**:
    * **N** (int): The program number
* **Returns**:  
    A dictionary containing the desired program.  
    The dictionary will vary by controller and configuration of the controller.
* **Example**:  
    `my_program = controller.get_program(1)`

## get_program_list()
Get a list of all available programs on the controller.
* **Arguments**: None
* **Returns**:  
    The list available programs by name and number.  
    Example results:

    ```python
    [{"number":int, "name":str}] #length up to 40
    ```
* **Example**:
    `my_program_list = controller.get_program_list()`

## get_program_details(N)
Get the name and number of steps of a program..
* **Arguments**:
    * **N** (int): The program number.
* **Returns**:  
    A dictionary containing the program number, name, and step count  
    Example results:

    ```python
    {"number":int, "name":str, "steps":int}
    ```
* **Example**:  
    `my_program_details = controller.get_program_details(1)`

## get_datetime()
Get the date and time from the controller.
* **Arguments**: None
* **Returns**:  
    The current time as a `datetime.datetime` object
* **Example**:  
    `my_datetime = controller.get_datetime()`

## get_refrig()
Get the constant settings for the refigeration system.
* **Arguments**: None
* **Returns**:  
    The constant settings that are used by the constant setpoint.  
    Example results:

    ```python
    {"mode":string,"setpoint":int}
    ```
* **Raises**:  
    This function will raise a `NotImplementedError` on all controllers classes except `Espec`.
* **Example**:  
    `my_refrig = controller.get_refrig()`

## get_event(N)
Get the state of a programmable output.
* **Arguments**:
    * **N** (int): The number of the output to read.
* **Returns**:  
    A dictionary containing both the constant mode settings and the current value of the output.  
    Example results:  

    ```python
    {"constant":bool, "current":bool}
    ```
* **Example**:  
    `my_event = controller.get_event(1)`

# Setter Functions  
Functions used to write information to the controller.

## set_loop(N, loop_type, param_list=None, &ast;&ast;kwargs)
Set the parameters for control loop.
* **Arguments**:
    * **N** (int): The loop number (1-4).
    * **loop_type** (str): The loop type, acceptible values:
        * `cascade` A cascade control loop.
        * `loop` A standard control loop.
    * **param_list** (dict(dict)): The items to set.  
    Keys other than the ones shown below will be ignored.
    Where a param_list is `{'my_key':{'constant':my_value}}` then `{'my_key':my_value}` is also valid.  
    
    ```python
    {
        'setpoint': {'constant':double},
        'range': {'min': float, 'max': float},
        'enable': {'constant':bool},
        'power': {'constant':double},
        'deviation': {'positive':float, 'negative':float},
        'enable_cascade': {'constant':bool}
    }
    ```
    * **&ast;&ast;kwargs**: list of items to set (same as param_list)
* **Returns**: None
* **Example**:  
    `controller.set_loop(1, 'loop', {'setpoint':50.0})`

## set_loop_byname(name, param_list=None, &ast;&ast;kwargs)
Set the parameters for a named control loop.
* **Arguments**:
    * **name** (int): name of the loop to read.
    * **param_list** (dict(dict)): The items to set.  
    Keys other than the ones shown below will be ignored.
    Where a param_list is `{'my_key':{'constant':my_value}}` then `{'my_key':my_value}` is also valid.  
    
    ```python
    {
        'setpoint': {'constant':double},
        'range': {'min': float, 'max': float},
        'enable': {'constant':bool},
        'power': {'constant':double},
        'deviation': {'positive':float, 'negative':float},
        'enable_cascade': {'constant':bool}
    }
    ```
    * **&ast;&ast;kwargs**: list of items to set (same as param_list)
* **Returns**: None
* **Example**:  
    `controller.set_loop_byname('temp', 'setpoint'=50.0)`

## set_operation(mode, **kwargs)
Change to operation mode of the chamber (start a program/run constant/pause or resume a program/stop)
* **Arguments**:
    * **mode** (str): The mode to run, possible values:
        * `standby`: Stop the chamber from running.
        * `off`: Stop the chamber from running.
        * `constant`: Start the configured constant mode
        * `program`: Run a program.
        * `program_pause`: Pause the running program.
        * `program_resume`: Resume the paused program.
        * `program_advance`: Force the program to the next step.
    * **kwargs**: key word arguments accepted:
        * **program** (int or dict): the program # to run, or a dict: `{'number':int, 'step': int}`
        * **step** (int): the step # to start the given program on (if program an int) (default=1)
* **Returns**: None
* **Example**:  
    `controller.set_operation('constant')`

## set_program(N, value)
Write a program to the controller (None = delete the program)
* **Arguments**:
    * **N** (int): The number of the program to write.
    * **value** (dict or None): The program to write to the controller, `None` deletes the program
* **Returns**: None
* **Example**:  
    `controller.set_program(1, my_program)`

## set_datetime(value)
Write the date/time to the controller.
* **Arguments**:
    * **value** (datetime.datetime): The new datetime to write to the controller
* **Returns**: None
* **Example**:  
    `controller.datetime(datetime.now())`

## set_refrig(value)
Write the constant refrigeration mode to the controller (espec.py based controllers only).
* **Arguments**:
    * **value** (dict): The parameters for the refrig system.  
    ```python
    {
        'mode': str, # "off" or "manual" or "auto"
        'setpoint': int # 20 or 50 or 100
    }
    ```
* **Returns**: None
* **Example**:  
    `controller.set_refrig({'mode':'auto', 'setpoint':0})`

## set_event(N, value)
Write the constant digital output state to the controller.
* **Arguments**:
    * **N** (int): The number of the output (typically 1-12 or 1-8)
    * **value** (bool): The new constant output state (True = on)
* **Returns**: None
* **Example**:  
    `controller.set_event(1, True)`
