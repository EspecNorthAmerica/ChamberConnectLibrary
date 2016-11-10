#!/usr/bin/python
'''
A simple command line program that calls all functions supported by the
chamberconnectlibrary.

:copyright: (C) Espec North America, INC.
:license: MIT, see LICENSE for more details.
'''
#pylint: disable=W0703

import sys
import traceback
from chamberconnectlibrary.espec import Espec
from chamberconnectlibrary.watlowF4T import WatlowF4T

def main(**kwargs):
    '''Try each command given a set of parameters'''
    ctlr_type = kwargs.pop('controller', None)
    if ctlr_type == 'Espec' or ctlr_type == 'EspecP300':
        ctlr = Espec(**kwargs)
    elif ctlr_type == 'EspecSCP220':
        ctlr = Espec(ctlrType='SCP220', **kwargs)
    else:
        ctlr = WatlowF4T(**kwargs)
    ctlr.process_controller()
    ctlr.self_test(ctlr.loops+ctlr.cascades, ctlr.cascades)

if __name__ == '__main__':
    try:
        main(
            controller=sys.argv[1],
            interface=sys.argv[2],
            serialport=sys.argv[3],
            host=sys.argv[3],
            baudrate=int(sys.argv[4]) if len(sys.argv) == 5 else 9600
        )
    except Exception:
        traceback.print_exc()

        print '\nThe test could not be run try:'
        print '\nchamberconnectlibrary_test controller interface ipORserialport [baudrate]'
        print '\tcontroller: "Espec"/"EspecP300" or "EspecSCP220" or "WatlowF4T"'
        print '\tinterface: "Serial": Serial connection when "controller" is "Espec".'
        print '\t           "RTU":Serial connection when "controller" is "WatlowF4T"'
        print '\t           "TCP":TCP connection'
        print '\t"hostORserialport": hostname for TCP, or serial port for RTU/Serial'
        print '\t"baudrate": The baudrate for RTU/Serial, optional(default=9600)'
