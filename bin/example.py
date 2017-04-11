'''
examples of using the chamberconnectlibrary
'''
from chamberconnectlibrary.watlowf4 import WatlowF4

LOOP_NAMES = ['Temperature', 'Humidity']

CONTROLLER = WatlowF4(
    interface='RTU',
    serialport='//./COM7',
    baudrate=19200,
    loop_names=LOOP_NAMES
)
print CONTROLLER.process_controller()

print '\ncascade loops:'
for i in range(CONTROLLER.cascades):
    print CONTROLLER.get_loop(i+1, 'cascade', ['processvalue', 'setpoint'])

print '\nloops:'
for i in range(CONTROLLER.loops):
    print CONTROLLER.get_loop(i+1, 'loop', 'processvalue', 'setpoint')

print '\nnamed loops:'
for name in LOOP_NAMES:
    print CONTROLLER.get_loop(name, ['processvalue', 'setpoint'])

for name in LOOP_NAMES:
    print CONTROLLER.set_loop(name, setpoint=60.0)

print '\noperations:'
print CONTROLLER.get_operation()
CONTROLLER.set_operation('standby')

print '\nEvents:'
for i in range(8):
    print CONTROLLER.get_event(i+1)
