import os
import time
from chamberconnectlibrary.especinteract import EspecSerial

chb = EspecSerial(port=9, baud=19200)

def interact_wrap(cmd):
	format_str = '"%s","%s"'
	alt_format_str = '"%s","=""%s"""'
	if cmd != 'delay':
		try:
			res = chb.interact(cmd)
		except Exception, e:
			res = str(e)
		res = res.replace('"', '""')
		if '"' in res:
			return format_str % (cmd, res)
		else:
			return alt_format_str % (cmd, res)
	else:
		time.sleep(1)
		return '"delay","slept for 1 sec"'

read_commands_old = [
	'ROM?', 'ROM?, DISP', 'ROM?, CONT',
	'DATE?',
	'TIME?',
	'SRQ?',
	'MASK?',
	'TIMER ON?',
	'TIMER USE?',
]
read_commands_old += ['TIMER LIST?, %d' % i for i in range(3)]
read_commands_old += [
	'ALARM?',
	'KEYPROTECT?',
	'TYPE?',
	'MODE?', 'MODE?, DETAIL',
	'MON?', 'MON?, DETAIL',
	'TEMP?',
	'HUMI?',
	'SET?',
	'REF?',
	'RELAY?',
]
read_commands_old += ['CONSTANT SET?, %s' % p for p in ['TEMP', 'HUMI', 'REF', 'RELAY', 'PTC']]
read_commands_old += [
	'%?',
	'PRGM MON?',
	'PRGM SET?',
	'PRGM USE?, RAM',
	'PRGM USE?, RAM:1', #MAY NEED TO LOOK AT MORE THAN JUST PROGRAM 1?
	'PRGM DATA?, RAM:1', 'PRGM DATA?, RAM:1, STEP1', 'PRGM DATA?, RAM:1, DETAIL',
	'SYSTEM SET?, PTS', 'SYSTEM SET?, PTC', 'SYSTEM SET?, PTCOPT',
	'MON PTC?',
	'SET PTC?',
	'PTC?',
	'PRGM DATA PTC?, RAM:1', 'PRGM DATA PTC?, RAM:1, STEP1', 'PRGM DATA PTC?, RAM:1, DETAIL',
	'RUN PRGM MON?', 'RUN PRGM?'
]

write_commands_old = [
	#'DATE, 17. 9/20',
	#'TIME, 15:00:00',
	'MASK, 01000000',
	'SRQ,RESET',
]
write_commands_old += ['TIMER ERASE, NO%d' % i for i in range(3)]
write_commands_old += [
	'TIMER WRITE, NO0, 10:00, CONSTANT',
	'TIMER WRITE, NO1, MODE1, 17.9/20, 23:00, CONSTANT', 'TIMER WRITE, NO1, MODE2, SAT, 23:00, CONSTANT', 'TIMER WRITE, NO1, MODE3, 23:00, CONSTANT',
	'TIMER WRITE, NO2, MODE1, 17.9/20, 23:00, STANDBY', 'TIMER WRITE, NO2, MODE2, SAT, 23:00, STANDBY', 'TIMER WRITE, NO2, MODE3, 23:00, STANDBY'
]
write_commands_old += ['TIMER, %s, %d' % (m, i) for i in range(3) for m in ['ON', 'OFF']]
write_commands_old += [
	'KEYPROTECT, ON', 'KEYPROTECT, OFF',
	'POWER, ON', 'POWER, OFF',
	'TEMP, S1.0 H100.0 L-40.0',
	'HUMI, S85 H100 L0',
	'SET, REF9',
	'RELAY, ON, 1,2', 'RELAY, OFF, 3, 4',
	'PRGM, RUN, RAM:1, STEP1', 'delay', 'PRGM, PAUSE', 'delay', 'PRGM, CONTINUE', 'PRGM, ADVANCE', 'PRGM, END, HOLD',
]
write_commands_old += ['MODE, %s' % m for m in ['OFF', 'STANDBY', 'CONSTANT', 'RUN1']]
write_commands_old += [
	'PRGM ERASE, RAM:2',
	"PRGM DATA WRITE, PGM2, EDIT START",
	"PRGM DATA WRITE, PGM2, STEP1, TEMP10.0, TIME1:00",
	"PRGM DATA WRITE, PGM2, STEP2, HUMI100, TIME1:00",
	"PRGM DATA WRITE, PGM2, COUNT, A(1. 2. 10)",
	"PRGM DATA WRITE, PGM2, NAME, SAMPLE-1",
	"PRGM DATA WRITE, PGM2, END, CONSTANT",
	"PRGM DATA WRITE, PGM2, EDIT END",
	"RUN PRGM, TEMP10.0 GOTEMP23.0 HUMI85 GOHUMI100 TIME1:00",
	"TEMP PTC, PTCON, DEVP10.0, DEVN-10.0",
	#"PTC, 150.0, -40.0, 1.0, 36.0, 2.0, 0.0, 0.0"
]


read_commands_new = ['CONSTANT SET?, AIR']
read_commands_new += ['CONSTANT SET?, %s, C%d' % (p, i) for i in range(1,4) for p in ['AIR', 'TEMP', 'HUMI', 'REF', 'RELAY', 'PTC']]
read_commands_new += [
	'MODE?, DETAIL, CONSTANT',
	'MON?, DETAIL, CONSTANT',
	'AIR?',
	'PRGM DATA?, RAM:1, CONSTANT',
	'PRGM DATA?, RAM:1, STEP1, AIR',
	'PRGM DATA PTC?, RAM:1, CONSTANT',
	'PRGM DATA PTC?, RAM:1, STEP1, AIR',
	'RUN PRGM?, AIR',
]
read_commands_new += ['TIMER LIST?, %d, CONSTANT' % i for i in range(3)]

write_commands_new = ['MODE, CONSTANT, C%d' % i for i in range(1, 4)]
write_commands_new += ['TEMP, S1.0 H100.0 L-40.0, C%d' % i for i in range(1, 4)]
write_commands_new += ['HUMI, S85 H100 L0, C%d' % i for i in range(1, 4)]
write_commands_new += ['RELAY, ON, 1,2, C%d' % i for i in range(1, 4)]
write_commands_new += ['RELAY, OFF, 3,4, C%d' % i for i in range(1, 4)]
write_commands_new += ['SET, REF9, C%d' % i for i in range(1, 4)]
write_commands_new += ['TEMP PTC, PTCON, DEVP10.0, DEVN-10.0, C%d' % i for i in range(1, 4)]
write_commands_new += ['AIR, 5, C%d' % i for i in range(1, 4)]
write_commands_new += [
	"PRGM DATA WRITE, PGM3, EDIT START",
	"PRGM DATA WRITE, PGM3, STEP1, TEMP10.0, TIME1:00, AIR2",
	"PRGM DATA WRITE, PGM3, STEP2, HUMI100, TIME1:00, AIR3",
	"PRGM DATA WRITE, PGM3, COUNT, A(1. 2. 10)",
	"PRGM DATA WRITE, PGM3, NAME, SAMPLE-1",
	"PRGM DATA WRITE, PGM3, END, CONSTANT2",
	"PRGM DATA WRITE, PGM3, EDIT END",
	"RUN PRGM, TEMP10.0 GOTEMP23.0 HUMI85 GOHUMI100 TIME1:00 AIR4",
	'PRGM, RUN, RAM:1, STEP1', 'delay', "PRGM, END, CONST3",
	'TIMER WRITE, NO1, MODE1, 17.9/20, 23:00, CONSTANT1', 'TIMER WRITE, NO1, MODE2, SAT, 23:00, CONSTANT2', 'TIMER WRITE, NO1, MODE3, 23:00, CONSTANT3',
]


stime = time.time()
filename = 'test.csv'
with open(filename, 'w') as f:
	f.write('old read commands\n')
	for command in read_commands_old:
		f.write(interact_wrap(command) + '\n')
	f.write('\nnew read commands\n')
	for command in read_commands_new:
		f.write(interact_wrap(command) + '\n')
	f.write('\nold write commands\n')
	for command in write_commands_old:
		f.write(interact_wrap(command) + '\n')
	f.write('\nnew write commands\n')
	for command in write_commands_new:
		f.write(interact_wrap(command) + '\n')
print time.time() - stime
os.system('start ' + filename)