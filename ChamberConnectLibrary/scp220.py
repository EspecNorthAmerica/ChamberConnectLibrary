'''
A direct implimentation of the SCP220's communication interface.

:copyright: (C) Espec North America, INC.
:license: MIT, see LICENSE for more details.
'''
from p300 import P300

class SCP220(P300):
    '''SCP220 communication basic implimentation'''

    def __init__(self, interface, **kwargs):
        super(SCP220, self).__init__(interface, **kwargs)
        self.ramprgms = 20

    def read_temp_ptc(self):
        '''returns the temperature paramers including product temp control settings
        returns:
            {
                "enable":boolean,
                "enable_cascade":boolean,
                "deviation":{"positive":float ,"negative":float},
                "processvalue":{"air":float, "product":float},
                "setpoint":{"air":float, "product":float}
            }'''
        temp = super(SCP220, self).read_temp_ptc()
        tsp = temp['setpoint']
        tsp['air'], tsp['product'] = tsp['product'], tsp['air']
        return temp

    def read_mode(self, detail=False):
        '''Return the chamber operation state.
        params:
            detail: boolean, Not used on the SCP-220
        returns:
            detail=Faslse: string "OFF" or "STANDBY" or "CONSTANT" or "RUN"'''
        return super(SCP220, self).read_mode(False)

    def read_mon(self, detail=False):
        '''Returns the conditions inside the chamber
        params:
            detail: boolean, Not used on the SCP-220
        returns:
            {"temperature":float, "humidity":float, "mode":string,"alarms":int}
            "humidity": only present if chamber has humidity
            "mode": string "OFF" or "STANDBY" or "CONSTANT" or "RUN"'''
        return super(SCP220, self).read_mon(False)

    def read_ip_set(self):
        '''Read the configured IP address of the controller'''
        raise NotImplementedError

    def write_ip_set(self, address, mask, gateway):
        '''Write the IP address configuration to the controller'''
        raise NotImplementedError

    def read_prgm_data_detail(self, pgmnum):
        '''Get program data details'''
        raise NotImplementedError
