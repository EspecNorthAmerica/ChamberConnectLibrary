#!/usr/bin/python

import sys, traceback
from chamberconnectlibrary.espec import Espec
from chamberconnectlibrary.watlowF4T import WatlowF4T

def main(**kwargs):
    ctlrType = kwargs.pop('controller', None)
    ctlr = Espec(**kwargs) if ctlrType == 'Espec'  else WatlowF4T(**kwargs)
    ctlr.process_controller()
    ctlr.self_test(ctlr.loops+ctlr.cascades,ctlr.cascades)
    
if __name__ == '__main__':
    try:
        args = {'controller':sys.argv[1],
                'interface':sys.argv[2],
                'serialport':sys.argv[3],
                'host':sys.argv[3],
                'baudrate':int(sys.argv[4]) if len(sys.argv) == 5 else 9600}
        main(**args)
    except:
        traceback.print_exc()

        print '\nThe test could not be run try:'
        print '\nchamberconnectlibrary_test controller interface ipORserialport [baudrate]'
        print '\tcontroller: "Espec" or "WatlowF4T"'
        print '\tinterface: "Serial": Serial connection when "controller" is "Espec".'
        print '\t           "RTU":Serial connection when "controller" is "WatlowF4T"'
        print '\t           "TCP":TCP connection'
        print '\t"hostORserialport": hostname for TCP, or serial port for RTU/Serial'
        print '\t"baudrate": The baudrate for RTU/Serial, optional(default=9600)'