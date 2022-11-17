'''
examples of using the chamberconnectlibrary
'''
import pprint
import time
from chamberconnectlibrary.watlowf4t import WatlowF4T
from chamberconnectlibrary.watlowf4 import WatlowF4
from chamberconnectlibrary.espec import Espec

LOOP_NAMES = ['Temperature', 'Humidity']

CONTROLLER = Espec(
    interface='Serial',
    serialport='//./COM10',
    baudrate=19200,
    loop_names=LOOP_NAMES
)
# CONTROLLER = WatlowF4(
#     interface='RTU',
#     serialport='//./COM7',
#     baudrate=19200,
#     loop_names=LOOP_NAMES
# )
# CONTROLLER = WatlowF4T(
#     interface='TCP',
#     host='10.30.100.138',
#     loop_names=LOOP_NAMES
# )
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

for _ in range(100):
    print ('\nsample')
    stm = time.time()
    lookup = {'cascade':[], 'loop':[]}
    lookup['loop'].append({'name':'Temperature', 'id': 1, 'number': 1})
    lookup['loop'].append({'name':'Humidity', 'id': 2, 'number': 2})
    params = {'get_loops':True, 'get_status':True, 'get_alarms':True, 'get_program_status':True, 'get_program_list':True, 'get_refrig':True}
    params['get_events'] = [{'N':i+1, 'name':'TS#%d'%(i+1)} for i in range(8)]
    smpl = CONTROLLER.sample(lookup, **params)
    print(f'--- {(time.time() - stm)} seconds ---')
    print(smpl)
