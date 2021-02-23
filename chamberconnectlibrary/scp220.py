'''
A direct implimentation of the SCP220's communication interface.

:copyright: (C) Espec North America, INC.
:license: MIT, see LICENSE for more details.
'''
from .p300 import P300

class SCP220(P300):
    '''
    SCP220 communication basic implimentation

    Args:
        interface (str): The interface type to connect to: "Serial" or "TCP"
    Kwargs:
        serialport (str/int): The serial port to connect to when interface="Serial"
        baudrate (int): The baud rate to connect at when interface="Serial"
        address (int): The RS485 address of the chamber to connect to.
        host (str): The IP address or hostname of the chamber when interface="TCP"
    '''

    def __init__(self, interface, **kwargs):
        super(SCP220, self).__init__(interface, **kwargs)
        self.ramprgms = 20

    def read_constant_ptc(self):
        temp = super(SCP220, self).read_constant_ptc()
        temp['deviation']['negative'] = 0 - temp['deviation']['negative']
        return temp

    def read_constant_ref(self):
        temp = super(SCP220, self).read_constant_ref()
        if temp['mode'] not in ['manual', 'off']:
            temp['mode'] = 'auto'
        return temp

    def read_temp_ptc(self):
        temp = super(SCP220, self).read_temp_ptc()
        tsp = temp['setpoint']
        tsp['air'], tsp['product'] = tsp['product'], tsp['air']
        temp['deviation']['negative'] = 0 - temp['deviation']['negative']
        return temp

    def read_mode(self, detail=False):
        return super(SCP220, self).read_mode(False)

    def read_mon(self, detail=False):
        return super(SCP220, self).read_mon(False)

    def read_ip_set(self):
        raise NotImplementedError

    def write_ip_set(self, address, mask, gateway):
        raise NotImplementedError

    def read_prgm_data_detail(self, pgmnum):
        raise NotImplementedError

    def read_prgm_data_ptc_detail(self, pgmnum):
        raise NotImplementedError

    def write_prgm_data_step(self, pgmnum, **pgmstep):
        if 'temperature' in pgmstep:
            if 'deviation' in pgmstep['temperature']:
                pgmstep['temperature']['deviation']['negative'] = abs(
                    pgmstep['temperature']['deviation']['negative']
                )
        super(SCP220, self).write_prgm_data_step(pgmnum, **pgmstep)

    def read_prgm_data_ptc_step(self, pgmnum, pgmstep):
        tmp = super(SCP220, self).read_prgm_data_ptc_step(pgmnum, pgmstep)
        ttmp = tmp['temperature']['deviation']
        ttmp['negative'] = 0 - ttmp['negative']
        return tmp

    def write_temp_ptc(self, enable, positive, negative):
        super(SCP220, self).write_temp_ptc(enable, positive, abs(negative))

    def read_prgm(self, pgmnum, with_ptc=False):
        if pgmnum > 30:
            raise ValueError('pgmnum must be 0-30')
        tmp = super(SCP220, self).read_prgm(pgmnum, with_ptc)
        tmp.pop('tempDetail', None)
        tmp.pop('humiDetail', None)
        return tmp
