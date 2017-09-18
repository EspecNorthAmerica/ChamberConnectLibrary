'''
examples of using the chamberconnectlibrary
'''
import pprint
import time
from chamberconnectlibrary.watlowf4t import WatlowF4T
from chamberconnectlibrary.watlowf4 import WatlowF4
from chamberconnectlibrary.espec import Espec

LOOP_NAMES = ['Temperature', 'Humidity']

# CONTROLLER = Espec(
#     interface='Serial',
#     serialport='//./COM10',
#     baudrate=19200,
#     loop_names=LOOP_NAMES
# )
# CONTROLLER = WatlowF4(
#     interface='RTU',
#     serialport='//./COM7',
#     baudrate=19200,
#     loop_names=LOOP_NAMES
# )
CONTROLLER = WatlowF4T(
    interface='TCP',
    host='10.30.100.138',
    loop_names=LOOP_NAMES
)
# CONTROLLER = WatlowF4T(
#     interface='RTU',
#     serialport='//./COM4',
#     baudrate=38400,
#     loop_names=LOOP_NAMES
# )
print CONTROLLER.process_controller()

# print '\ncascade loops:'
# for i in range(CONTROLLER.cascades):
#     print CONTROLLER.get_loop(i+1, 'cascade', ['processvalue', 'setpoint'])

# print '\nloops:'
# for i in range(CONTROLLER.loops):
#     print CONTROLLER.get_loop(i+1, 'loop', 'processvalue', 'setpoint')

# print '\nnamed loops:'
# for name in LOOP_NAMES:
#     print CONTROLLER.get_loop(name, ['processvalue', 'setpoint'])

# for name in LOOP_NAMES:
#     print CONTROLLER.set_loop(name, setpoint=60.0)

# print '\noperations:'
# print CONTROLLER.get_operation()
# CONTROLLER.set_operation('standby')

# print '\nEvents:'
# for i in range(8):
#     print CONTROLLER.get_event(i+1)

print '\nsample'
stm = time.time()
smpl = CONTROLLER.sample(get_alarms=True, get_program_status=True, get_events=[i+1 for i in range(8)], get_program_list=True, get_refrig=True)
print("--- %s seconds ---" % (time.time() - stm))
pprint.pprint(smpl)
