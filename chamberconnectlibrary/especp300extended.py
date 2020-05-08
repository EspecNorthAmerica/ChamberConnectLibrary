'''
Upper level interface for Espec Corp. SCP220 Controllers

:copyright: (C) Espec North America, INC.
:license: MIT, see LICENSE for more details.
'''
from chamberconnectlibrary.p300extended import P300Extended
from chamberconnectlibrary.especp300 import EspecP300, exclusive

class EspecP300Extended(EspecP300):
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
        super(EspecP300Extended, self).__init__(**kwargs)
        self.connect_args['enable_air_speed'] = kwargs.get('enable_air_speed', False)

    def connect(self):
        self.client = P300Extended(self.interface, **self.connect_args)

    @exclusive
    def get_air_speed(self):
        return {
            'current':self.client.read_air()['selected'],
            'constant':self.client.read_constant_air()['selected']
        }

    @exclusive
    def get_air_speeds(self):
        return self.client.read_air()['options']

    @exclusive
    def set_air_speed(self, value):
        self.client.write_air(value)
