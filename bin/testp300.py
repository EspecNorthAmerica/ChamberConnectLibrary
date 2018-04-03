'''
examples of using the chamberconnectlibrary

This program will only test the control and response of the 
P300. The purpose is to study its control and response in order
to implement and add new features to support the new series. 

'''
import pprint, time 
from chamberconnectlibrary.espec import Espec

LOOP_NAMES = ['Temperature', 'Humidity']

CONTROLLER = Espec(
    interface='Serial',
    serialport='//./COM3',
    baudrate=19200,
    loop_names=LOOP_NAMES
)

for _ in range(10):
    print '\nsample'
    stm = time.time()
    lookup = {'cascade':[], 'loop':[]}
    lookup['loop'].append({'name':'Temperature', 'id': 1, 'number': 1})
    lookup['loop'].append({'name':'Humidity', 'id': 2, 'number': 2})
    params = {
	     'get_loops':True, 
		 'get_status':True, 
		 'get_alarms':True, 
		 'get_program_status':True, 
		 'get_program_list':True, 
		 'get_refrig':True
    }
    params['get_events'] = [{'N':i+1, 'name':'TS#%d'%(i+1)} for i in range(8)]
    smpl = CONTROLLER.sample(lookup, **params)
    print("--- %s seconds ---" % (time.time() - stm))
    print(smpl)
