import sys, traceback
from ChamberConnectLibrary.Espec import Espec
from ChamberConnectLibrary.WatlowF4T import WatlowF4T

try:
    args = {'interface':sys.argv[2],
            'serialport':sys.argv[3],
            'host':sys.argv[3],
            'baudrate':int(sys.argv[4]) if len(sys.argv) == 5 else 9600}
    ctlr = Espec(**args) if sys.argv[1] == 'Espec' else WatlowF4T(**args)
    ctlr.process_controller()
    ctlr.self_test(ctlr.loops+ctlr.cascades,ctlr.cascades)
except:
    traceback.print_exc()

    print '\nThe test could not be run try:'
    print '\ntest.py controller interface ipORserialport [baudrate]'
    print '\tcontroller: "Espec" or "WatlowF4T"'
    print '\tinterface: "Serial": Serial connection when "controller" is "Espec".'
    print '\t           "RTU":Serial connection when "controller" is "WatlowF4T"'
    print '\t           "TCP":TCP connection'
    print '\t"hostORserialport": hostname for TCP, or serial port for RTU/Serial'
    print '\t"baudrate": The baudrate for RTU/Serial, optional(default=9600)'