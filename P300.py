'''
Copyright (C) Espec North America, INC. - All Rights Reserved
Written by Myles Metzler mmetzler@espec.com, April 2016

Simple implimentations of all commands the P300 supports
'''
from EspecInteract import *
import re

def tryfloat(val,default):
    try:
        return float(val)
    except:
        return default

class P300:
    '''P300 communications basic implimentation'''

    def __init__(self,interface, **kwargs):
        self.reflookup = {'REF0':{'mode':'off','setpoint':0},
                          'REF1':{'mode':'manual','setpoint':20},
                          'REF3':{'mode':'manual','setpoint':50},
                          'REF6':{'mode':'manual','setpoint':100},
                          'REF9':{'mode':'auto','setpoint':0}}
        if interface == 'Serial':
            self.ctlr = EspecSerial(kwargs['serialport'],kwargs['baudrate'],kwargs.get('parity','N'),
                                    kwargs.get('databits',8),kwargs.get('stopbits',1),kwargs.get('timeout',1),
                                    kwargs.get('address',1),kwargs.get('delimeter','\r\n'))
        else:
            self.ctlr = EspecTCP(kwags['host'],kwargs.get('port',10001),kwargs.get('timeout',1),kwargs.get('address',1),kwargs.get('delimeter','\r\n'))

    def __del__(self):
        self.cleanup()

    def cleanup(self):
        try: self.ctlr.close()
        except: pass

    def interact(self, message):
        '''Read a responce from the controller
        params:
            message: the command to write
        returns:
            string: response'''
        return self.ctlr.interact(message)

    def read_rom(self, display=False):
        '''Get the rom version of the controller
        params:
            display: If true get the controllers display rom
        returns:
            rom version as a string'''
        return self.ctlr.interact('ROM?%s' % (',DISP' if display else ''))

    def read_date(self):
        '''Get the date from the controller
        returns:
            {"year":int,"month":int,"day":int}'''
        rsp = self.ctlr.interact('DATE?').split('.')
        date = [rsp[0]] + rsp[1].split('/')
        return {'year':2000+int(date[0]),'month':int(date[1]),'day':int(date[2])}

    def read_time(self):
        '''Get the time from the controller
        returns:
            {"hour":int,"minute":int,"second":int}'''
        time = self.ctlr.interact('TIME?').split(':')
        return {'hour':int(time[0]),'minute':int(time[1]),'second':int(time[2])}

    def read_srq(self):
        '''Read the SRQ status
        returns:
            {"alarm":boolean,"single_step_done":boolean,"state_change":boolean,"GPIB":boolean}'''
        srq = list(self.ctlr.interact('SRQ?'))
        return {'alarm':srq[1]=='1','single_step_done':srq[2]=='1','state_change':srq[3]=='1','GPIB':srq[6]=='1'}

    def read_mask(self):
        '''Read the SRQ mask
        returns:
            {"alarm":boolean,"single_step_done":boolean,"state_change":boolean,"GPIB":boolean}'''
        mask = list(self.ctlr.interact('MASK?'))
        return {'alarm':mask[1]=='1','single_step_done':mask[2]=='1','state_change':mask[3]=='1','GPIB':mask[6]=='1'}

    def read_timerOn(self):
        '''Return a list of valid timers by number
        returns:
            [int]'''
        rsp = self.ctlr.interact('TIMER ON?').split(',')
        return [int(t) for t in rsp[1:]]

    def read_timerUse(self):
        '''Return the number of each set timer
        returns:
            [int]'''
        rsp = self.ctlr.interact('TIMER USE?').split(',')
        return [int(t) for t in rsp[1:]]

    def read_timerListQuick(self):
        '''Read the timer settings for the quick timer(timer 0)
        returns:
            {"mode":string,"time":{"hour":int,"minute":int},"pgmnum":int,"pgmstep":int}
            "mode"="STANDBY" or "OFF" or "CONSTANT" or "RUN"
            "pgmnum" and "pgmstep" only present when mode=="RUN"'''
        parsed = re.search(r'(\w+)(?:,RAM:(\d+),STEP(\d+))?,(\d+):(\d+)',self.ctlr.interact('TIMER LIST?,0'))
        ret = {'mode':parsed.group(1),'time':{'hour':int(parsed.group(4)),'minute':int(parsed.group(5))}}
        if parsed.group(1) == 'RUN':
            ret.update({'pgmnum':int(parsed.group(2)),'pgmstep':int(parsed.group(3))})
        return ret

    def read_timerListStart(self):
        '''Read the timer settings for the start timer (timer 1)
        returns:
            {"repeat":string,"time":{"hour":int,"minute":int},"mode":string","date":{"month":int,"day":int,"year":int},"day":string,"pgmnum":int,"pgmstep":int}
            "repeat"="once" or "weekly" or "daily"
            "mode"="CONSTANT" or "RUN"
            "date" only present when "repeat"=="once"
            "pgmnum" and "step" only present when "mode"=="RUN"
            "days" only present when "repeat"=="weekly"'''
        rsp = self.ctlr.interact('TIMER LIST?,1')
        parsed = re.search(r'1,MODE(\d)(?:,(\d+).(\d+)/(\d+))?(?:,([A-Z/]+))?,(\d+):(\d+),(\w+)(?:,RAM:(\d+),STEP(\d+))?',rsp)
        ret = {'repeat':['once','weekly','daily'][int(parsed.group(1))-1],
               'time':{'hour':int(parsed.group(6)),'minute':int(parsed.group(7))},
               'mode':parsed.group(8)}
        if parsed.group(2): ret['date'] = {'year':2000+int(parsed.group(2)),'month':int(parsed.group(3)),'day':int(parsed.group(4))}
        if parsed.group(5): ret['days'] = parsed.group(5).split('/')
        if parsed.group(9): ret.update({'pgmnum':int(parsed.group(9)),'pgmstep':int(parsed.group(10))})
        return ret

    def read_timerListStop(self):
        '''Read the timer settings for the start timer (timer 1)
        returns:
            {"repeat":string,"time":{"hour":int,"minute":int},"mode":string","date":{"month":int,"day":int,"year":int},"day":string}
            "repeat"="once" or "weekly" or "daily"
            "mode"="STANDBY" or "OFF"
            "date" only present when "repeat"=="once"
            "days" only present when "repeat"=="weekly"'''
        rsp = self.ctlr.interact('TIMER LIST?,2')
        parsed = re.search(r'2,MODE(\d)(?:,(\d+).(\d+)/(\d+))?(?:,([A-Z]+))?,(\d+):(\d+),(\w+)',rsp)
        ret = {'repeat':['once','weekly','daily'][int(parsed.group(1))-1],
               'time':{'hour':int(parsed.group(6)),'minute':int(parsed.group(7))},
               'mode':parsed.group(8)}
        if parsed.group(2): ret['date'] = {'year':2000+int(parsed.group(2)),'month':int(parsed.group(3)),'day':int(parsed.group(4))}
        if parsed.group(5): ret['days'] = parsed.group(5).split('/')
        return ret

    def read_alarm(self):
        '''Return a list of active alarm codes, an empty list if no alarms.
        returns:
            [int]'''
        rsp = self.ctlr.interact('ALARM?').split(',')
        return [int(t) for t in rsp[1:]]

    def read_keyprotect(self):
        '''Returns the key protection state(prevents a user from changing the settings of the controller).
        returns:
            True if protection is enabled False if not'''
        return self.ctlr.interact('KEYPROTECT?') == 'ON'

    def read_type(self):
        '''Returns the type of sensor(s) connected to the controller, type of controller, max temperature
        returns:
            {"drybulb":string,"wetbulb":string,"controller":string,"tempmax":float
            "wetbulb" only present if chamber has humidity'''
        rsp = self.ctlr.interact('TYPE?').split(',')
        if len(rsp) == 4:
            return {'drybulb':rsp[0],'wetbulb':rsp[1],'controller':rsp[2],'tempmax':float(rsp[3])}
        else:
            return {'drybulb':rsp[0],'controller':rsp[1],'tempmax':float(rsp[2])}

    def read_mode(self,detail=False):
        '''Return the chamber operation state.
        params:
            detail: boolean, when True get additional details about the operation mode of the chamber
        returns:
            detail=Faslse: string "OFF" or "STANDBY" or "CONSTANT" or "RUN"
            detail=True: string "OFF" or "STANDBY" or "CONSTANT" or "RUN" or "RUN PAUSE" or "RUN END HOLD" or "RMT RUN" or "RMT RUN PAUSE" or "RMT RUN END HOLD"'''
        return self.ctlr.interact('MODE?%s' % (',DETAIL' if detail else ''))

    def read_mon(self,detail=False):
        '''Returns the conditions inside the chamber
        params:
            detail: boolean, when True "mode" parameter has additional details
        returns:
            {"temperature":float,"humidity":float,"mode":string,"alarms":int}
            "humidity": only presetn if chamber has humidity
            "mode": see read_mode for valid parameters (with and without detail flag).'''
        rsp = self.ctlr.interact('MON?%s' % (',DETAIL' if detail else '')).split(',')
        if len(rsp) == 4:
            return {'temperature':float(rsp[0]),'humidity':float(rsp[1]),'mode':rsp[2],'alarms':int(rsp[3])}
        else:
            return {'temperature':float(rsp[0]),'mode':rsp[1],'alarms':int(rsp[2])}

    def read_temp(self):
        '''Returns the temperature parameters
        returns:
            {"processvalue":float,"setpoint":float,"enable":boolean(always True),"range":{"max":float,"min":float}}'''
        rsp = self.ctlr.interact('TEMP?').split(',')
        return {'processvalue':float(rsp[0]),'setpoint':float(rsp[1]),'enable':True,'range':{'max':float(rsp[2]),'min':float(rsp[3])}}

    #have raise a special error about not being avaiable on non humditity chambers?
    def read_humi(self):
        '''Returns the humidity parameters
        returns:
            {"processvalue":float,"setpoint":float,"enable":boolean,"range":{"max":float,"min":float}}'''
        rsp = self.ctlr.interact('HUMI?').split(',')
        try:
            hsp = float(rsp[1])
            en = True
        except:
            hsp = 0
            en = False
        return {'processvalue':float(rsp[0]),'setpoint':hsp,'enable':en,'range':{'max':float(rsp[2]),'min':float(rsp[3])}}

    def read_set(self):
        '''returns the regrigeration capacity set point of the chamber
        returns:
            {"mode":string,"setpoint":int}
            "mode": "off" or "manual" or "auto"
            "setpoint: 20 or 50 or 100 (percent cooling power)'''
        return self.reflookup.get(self.ctlr.interact('SET?'),{'mode':'manual','setpoint':0})

    def read_ref(self):
        '''returns the state of the compressors on the system
        returns:
            [boolean] 0=high stage, 1=low stage'''
        rsp = self.ctlr.interact('REF?').split(',')
        if len(rsp) == 3:
            return [rsp[1]=='ON1',rsp[2]=='ON2']
        else:
            return [rsp[1]=='ON1']

    #cannot be checked with a p300 with stopped plc...
    def read_relay(self):
        '''returns the status of each relay(time signal)
        returns:
            [boolean] len=12'''
        rsp = self.ctlr.interact('RELAY?').split(',')
        return [str(i) in rsp[1:] for i in range(1,13)]

    def read_htr(self):
        '''returns the heater outputs
        returns:
            {"dry":flaot,"wet":float}
            "wet" is only present with humidity chambers'''
        rsp = self.ctlr.interact('%?').split(',')
        if len(rsp) == 3:
            return {'dry':float(rsp[1]),'wet':float(rsp[2])}
        else:
            return {'dry':float(rsp[1])}

    def read_constantTemp(self):
        '''Get the constant settings for the temperature loop
        returns:
            {"setpoint":float,"enable":True}'''
        rsp = self.ctlr.interact('CONSTANT SET?,TEMP').split(',')
        return {'setpoint':float(rsp[0]),'enable':rsp[1]=='ON'}

    def read_constantHumi(self):
        '''Get the constant settings for the humidity loop
        returns:
            {"setpoint":float,"enable":boolean}'''
        rsp = self.ctlr.interact('CONSTANT SET?,HUMI').split(',')
        return {'setpoint':float(rsp[0]),'enable':rsp[1]=='ON'}

    def read_constantRef(self):
        '''Get the constant settings for the refigeration system
        returns:
            {"mode":string,"setpoint":int}
            '''
        rsp = self.ctlr.interact('CONSTANT SET?,REF')
        try:
            return {'mode':'manual','setpoint':float(rsp)}
        except:
            return {'mode':rsp.lower(),'setpoint':0}

    def read_constantRelay(self):
        '''Get the constant settings for the relays(time signals)
        returns:
            [int]'''
        rsp = self.ctlr.interact('CONSTANT SET?,RELAY').split(',')
        return [str(i) in rsp[1:] for i in range(1,13)]

    def read_constantPtc(self):
        '''Get the constant settings for product temperature control
        returns:
            {"enable":boolean,"deviation":{"positive":float,"negative":float}}'''
        rsp = self.ctlr.interact('CONSTANT SET?,PTC').split(',')
        return {'enable': rsp[0] == 'ON', 'deviation': {'positive':float(rsp[1]),'negative':float(rsp[2])}}

    def read_prgmMon(self):
        '''get the status of the running program
        returns:
            {"pgmstep":int,"temperature":float,"humidity":float,"time":{"hour":int,"minute":int},"counter_a":int,"counter_b":int}
            "humidity" is only present on chambers with humidity
            "counter_?" is the cycles remaining'''
        rsp = self.ctlr.interact('PRGM MON?').split(',')
        if len(rsp) == 6:
            time = rsp[3].split(':')
            return {'pgmstep':int(rsp[0]),'temperature':float(rsp[1]),'humidity':tryfloat(rsp[2],0),
                    'time':{'hour':int(time[0]),'minute':int(time[1])},'counter_a':int(rsp[4]),'counter_b':int(rsp[5])}
        else:
            time = rsp[2].split(':')
            return {'pgmstep':int(rsp[0]),'temperature':float(rsp[1]),
                    'time':{'hour':int(time[0]),'minute':int(time[1])},'counter_a':int(rsp[3]),'counter_b':int(rsp[4])}

    def read_prgmSet(self):
        '''get the name,number and end mode of the current program
        returns:
            {"number":int,"name":string,"end":string}
            "end"="OFF" or "STANDBY" or "CONSTANT" or "HOLD" or "RUN"'''
        rsp = self.ctlr.interact('PRGM SET?')
        parsed = re.search(r'RAM:(\d+),([^,;]+),END\((\w+)\)',rsp)
        return {'number':int(parsed.group(1)),'name':parsed.group(2),'end':parsed.group(3)}

    def read_prgmUse(self):
        '''get the id number for each program on the controller as a list
        returns:
            [int]'''
        rsp = self.ctlr.interact('PRGM USE?,RAM').split(',')
        return [str(i) in rsp[1:] for i in range(1,41)]

    def read_prgmUseNum(self, pgmnum):
        '''get the name and creation date of a specific program
        params:
            pgmnum: the program to read
        returns:
            {"name":string,"date":{"year":int,"month":int,"day":int}}'''
        rsp = self.ctlr.interact('PRGM USE?,RAM:%d'%pgmnum).split(',')
        date = re.search(r'(\d+).(\d+)/(\d+)',rsp[1])
        return {'name':rsp[0],'date':{'year':2000+int(date.group(1)),'month':int(date.group(2)),'day':int(date.group(3))}}

    def read_prgmData(self,pgmnum):
        '''get the parameters for a given program
        params:
            pgmnum: int, the program to get
        returns:
            {"steps":int,"name":string,"end":string,"counter_a":{"start":int,"end":int,"cycles":int},"counter_b":{"start":int,"end":int,"cycles":int}}
            "END"="OFF" or "CONSTANT" or "STANDBY" or "RUN"'''
        return self.parse_prgmData(self.ctlr.interact('PRGM DATA?,RAM:%d'%pgmnum))

    def read_prgmDataDetail(self,pgmnum):
        '''get the conditions a program will start with and its operational range
        params:
            pgmnum: int, the program to get
        returns:
            {"temperature":{"range":{"max":float,"min":float},"mode":string,"setpoint":float},"humidity":{"range":{"max":float,"min":float},"mode":string,"setpoint":float}'''
        return self.parse_prgmDataDetail(self.ctlr.interact('PRGM DATA?,RAM:%d,DETAIL'%(pgmnum)))

    def read_prgmDataStep(self,pgmnum,pgmstep):
        '''get a programs step parameters
        params:
            pgmnum: int, the program to read from
            pgmstep: int, the step to read from
        returns:
            {"number":int,"time":{"hour":int,"minute":int},"paused":boolean,"granty":boolean,"refrig":{"mode":string,"setpoint":int},
             "temperature":{"setpoint":float,"ramp":boolean},"humidity":{"setpoint":float,"enable":boolean,"ramp":boolean},"relay":[int]}'''
        return self.parse_prgmDataStep(self.ctlr.interact('PRGM DATA?,RAM:%d,STEP%d'%(pgmnum,pgmstep)))

    def read_systemSet(self,arg='PTCOPT'):
        '''return controller product monitor and or control configuration (if this returns C or MC w/ default options you have PTCON)
        params:
            arg: what to read options are: "PTCOPT","PTC","PTS"
        returns:
            string'''
        if arg in ['PTCOPT','PTC','PTC']:
            return self.ctlr.interact('SYSTEM SET?,%s'%arg)
        else:
            raise ValueError('arg must be one of the following: "PTCOPT","PTC","PTS"')

    def read_monPtc(self):
        '''Returns the conditions inside the chamber, including PTCON (dont call this on chambers without PTCON)
        returns:
            {"temperature":{"product":float,"air":float},"humidity":float,"mode":string,"alarms":int}
            "humidity" is present only on humidity chambers'''
        rsp = self.ctlr.interact('MON PTC?').split(',')
        if len(rsp) == 5:
            return {'temperature':{'product':float(rsp[0]),'air':float(rsp[1])},'humidity':float(rsp[2]),'mode':rsp[3],'alarms':int(rsp[4])}
        else:
            return {'temperature':{'product':float(rsp[0]),'air':float(rsp[1])},'mode':rsp[2],'alarms':int(rsp[3])}

    def read_tempPtc(self):
        '''returns the temperature paramers including product temp control settings
        returns:
            {"enable":boolean,"enable_cascade":boolean,"deviation":{"positive":float,"negative":float},
             "processvalue":{"air":float,"product":float},"setpoint":{"air":float,"product":float}}'''
        rsp = self.ctlr.interact('TEMP PTC?').split(',')
        return {'enable':True,'enable_cascade':rsp[0] == 'ON','deviation':{'positive':tryfloat(rsp[5],0),'negative':tryfloat(rsp[6],0)},
                'processvalue':{'air':tryfloat(rsp[2],0),'product':tryfloat(rsp[1],0)},'setpoint':{'air':tryfloat(rsp[3],0),'product':tryfloat(rsp[4],0)}}

    def read_setPtc(self):
        '''get the product temperature control parameters (on/off, deviation settings)
        returns:
            {"enable_cascade":boolean,"deviation":{"positive":float,"negative":float}}'''
        rsp = self.ctlr.interact('SET PTC?').split(',')
        return {'enable_cascade':rsp[0] == 'ON','deviation':{'positive':tryfloat(rsp[1],0),'negative':tryfloat(rsp[2],0)}}

    def read_ptc(self):
        '''get the product temperature control parameters (range,p,i,filter,opt1,opt2)
        returns:
            {"range":{"max":float,"min":float},"p":float,"filter":float,"i":float,"opt1":0.0,"opt2":0.0}'''
        rsp = self.ctlr.interact('PTC?').split(',')
        return {'range':{'max':float(rsp[0]),'min':float(rsp[1])},'p':float(rsp[2]),'filter':float(rsp[3]),'i':float(rsp[4]),'opt1':float(rsp[5]),'opt2':float(rsp[6])}

    def read_prgmDataPtc(self,pgmnum):
        '''get the parameters for a given program that includes ptc
        params:
            pgmnum: int, the program to get
        returns:
            {"steps":int,"name":string,"end":string,"counter_a":{"start":int,"end":int,"cycles":int},"counter_b":{"start":int,"end":int,"cycles":int}}
            "END"="OFF" or "CONSTANT" or "STANDBY" or "RUN"'''
        return self.parse_prgmData(self.ctlr.interact('PRGM DATA PTC?,RAM:%d'%pgmnum))

    def read_prgmDataPtcDetail(self,pgmnum):
        '''get the conditions a program will start with and its operational range including ptc
        params:
            pgmnum: int, the program to get
        returns:
            {"temperature":{"range":{"max":float,"min":float},"mode":string,"setpoint":float},"humidity":{"range":{"max":float,"min":float},"mode":string,"setpoint":float}'''
        return self.parse_prgmDataDetail(self.ctlr.interact('PRGM DATA PTC?,RAM:%d,DETAIL'%(pgmnum)))

    def read_prgmDataPtcStep(self,pgmnum,pgmstep):
        '''get a programs step parameters including ptc
        params:
            pgmnum: int, the program to read from
            pgmstep: int, the step to read from
        returns:
            {"number":int,"time":{"hour":int,"minute":int},"paused":boolean,"granty":boolean,"refrig":{"mode":string,"setpoint":int},
             "temperature":{"setpoint":float,"ramp":boolean,"enable_cascade":boolean,"deviation":{"positive":float,"negative":float}},
             "humidity":{"setpoint":float,"enable":boolean,"ramp":boolean},"relay":[int]}'''
        return self.parse_prgmDataStep(self.ctlr.interact('PRGM DATA PTC?,RAM:%d,STEP%d'%(pgmnum,pgmstep)))

    def read_runPrgmMon(self):
        '''Get the state of the remote program being run
        returns:
            {"pgmstep":int,"temperature":float,"humidity":float,"time":{"hours":int,"minutes":int},"counter":int}
            "humidity" is present only on humidity chambers'''
        rsp = self.ctlr.interact('RUN PRGM MON?').split(',')
        if len(rsp) == 5:
            time = rsp[3].split(':')
            return {'pgmstep':int(rsp[0]),'temperature':float(rsp[1]),'humidity':float(rsp[2]),'time':{'hours':int(time[0]),'minutes':int(time[1])},'counter':int(rsp[4])}
        else:
            time = rsp[2].split(':')
            return {'pgmstep':int(rsp[0]),'temperature':float(rsp[1]),'time':{'hours':int(time[0]),'minuets':int(time[1])},'counter':int(rsp[3])}

    #not tested
    def read_runPrgm(self):
        '''get the settings for the remote program being run
        returns:
            {"temperature":{"start":float,"end":float},"humidity":{"start":float,"end":float},
             "time":{"hours":int,"minutes":int},"refrig":{"mode":string,"setpoint":}}'''
        rsp = self.ctlr.interact('RUN PRGM?')
        parsed = re.search(r'TEMP([0-9.-]+) GOTEMP([0-9.-]+)(?: HUMI(\d+) GOHUMI(\d+))? TIME(\d+):(\d+) (\w+)(?: RELAYON,([0-9,]+))?',rsp)
        ret = {'temperature':{'start':float(parsed.group(1)),'end':float(parsed.group(2))},
               'time':{'hours':int(parsed.group(5)),'minutes':int(parsed.group(6))},
               'refrig':self.reflookup.get(parsed.group(7),{'mode':'manual','setpoint':0})}
        if parsed.group(3):
            ret['humidity'] = {'start':float(parsed.group(3)),'end':float(parsed.group(4))}
        if parsed.group(8):
            relays = parsed.group(8).split(',')
            base['relay'] = [str(i) in relays for i in range(1,13)]
        else:
            base['relay'] = [False for i in range(1,13)]

    def read_IPSet(self):
        '''Read the configured IP address of the controller'''
        return dict(zip(['address','mask','gateway'],self.ctlr.interact('IPSET?').split(',')))

    #--- write methods --- write methods --- write methods --- write methods --- write methods --- write methods --- write methods --- write methods --- write methods --- write methods ---
    def write_date(self,year,month,day):
        '''write a new date to the controller
        params:
            year: int,2007-2049
            month: int,1-12
            day: int,1-31'''
        cyear = (year - 2000) if year > 2000 else year
        self.ctlr.interact('DATE,%d.%d/%d' %(cyear,month,day))

    def write_time(self,hour,minute,second):
        '''write a new time to the controller
        params:
            hour: int,0-23
            minute: int,0-59
            second: int,0-59'''
        self.ctlr.interact('TIME,%d:%d:%d' %(hour,minute,second))

    def write_mask(self,alarm=False,single_step_done=False,state_change=False,GPIB=False):
        '''write the srq mask
        params:
            alarm,single_step_done,state_change,GPIB: boolean'''
        self.ctlr.interact('MASK,0%d%d%d00%d0' %(int(alarm),int(single_step_done),int(state_change),int(GPIB)))

    def write_srq(self):
        '''reset the srq register'''
        self.ctlr.interact('SRQ,RESET')

    def write_timerWriteQuick(self,mode,time,pgmnum=None,pgmstep=None):
        '''write the quick timer parameters to the controller(timer 0)
        params:
            mode: string, "STANDBY" or "OFF" or "CONSTANT" or "RUN"
            time: {"hour":int,"minute":int}, the time to wait
            pgmnum: int, program to run if mode=="RUN"
            pgmstep: int, program step to run if mode=="RUN"'''
        cmd = 'TIMER WRITE,NO0,%d:%d,%s' %(time['hour'],time['minute'],mode)
        if mode == 'RUN': cmd = '%s,RAM:%d,STEP%d' % (cmd,pgmnum,pgmstep)
        self.ctlr.interact(cmd)

    def write_timerWriteStart(self,repeat,time,mode,date=None,days=None,pgmnum=None,pgmstep=None):
        '''write the start timer parameters to the controller (timer 1)
        params:
            repeat: string, "once" or "weekly" or "daily"
            time: {"hour":int,"minute":int}, the time of day to start the chamber
            mode: string, "CONSTANT" or "RUN"
            date: {"month":int,"day":int,"year":int}, date to start chamber on when repeat=="once"
            days: [string], the day to start the chamber on when repeat=="weekly" (first 3 letters all caps)
            pgmnum: int,
            pgmstep: int, only present when "mode"=="RUN"'''
        cmd = 'TIMER WRITE,NO1,MODE%d' % {'once':1,'weekly':2,'daily':3}[repeat]
        if repeat == 'once':
            cmd = '%s,%d.%d/%d' % (cmd,date['year']-2000,date['month'],date['day'])
        elif repeat == 'weekly':
            cmd = '%s,%s' % (cmd, '/'.join(days))
        cmd = '%s,%d:%d,%s' % (cmd,time['hour'],time['minute'],mode)
        if mode == 'RUN':
            cmd = '%s,RAM:%d,STEP%d' % (cmd,pgmnum,pgmstep)
        self.ctlr.interact(cmd)

    def write_timerWriteStop(self,repeat,time,mode,date=None,days=None,):
        '''write the stop timer parameters to the controller (timer 2)
        params:
            repeat: string, "once" or "weekly" or "daily"
            time: {"hour":int,"minute":int}, the time of day to start the chamber
            mode: string, "STANDBY" or "OFF"
            date: {"month":int,"day":int,"year":int}, date to start chamber on when repeat=="once"
            days: [string], the day to start the chamber on when repeat=="weekly" (first 3 letters all caps)'''
        cmd = 'TIMER WRITE,NO2,MODE%d' % {'once':1,'weekly':2,'daily':3}[repeat]
        if repeat == 'once':
            cmd = '%s,%d.%d/%d' % (cmd,date['year']-2000,date['month'],date['day'])
        elif repeat == 'weekly':
            cmd = '%s,%s' % (cmd, '/'.join(days))
        cmd = '%s,%d:%d,%s' % (cmd,time['hour'],time['minute'],mode)
        self.ctlr.interact(cmd)

    def write_timerErase(self,timer):
        '''erase the give timer
        params:
            timer: string, "quick" or "start" or "stop"'''
        self.ctlr.interact('TIMER ERASE,NO%d' % ({'quick':0,'start':1,'stop':2}[timer]))

    def write_timer(self,timer,run):
        '''set the run mode of a give timer
        params:
            timer: string, "quick" or "start" or "stop"
            run: boolean, True=turn timer on, False=turn timer off'''
        self.ctlr.interact('TIMER,%s,%d' %('ON' if run else 'OFF',{'quick':0,'start':1,'stop':2}[timer]))

    def write_keyprotect(self,enable):
        '''enable/disable change and operation protection
        params:
            enable: boolean True=protection on, False=protection off'''
        self.ctlr.interact('KEYPROTECT,%s' % ('ON' if enable else 'off'))

    def write_power(self,on):
        '''turn on the chamber power
        params:
            on: boolean True=start constant1, False=Turn contoller off)'''
        self.ctlr.interact('POWER,%s' % ('ON' if on else 'off'))

    def write_temp(self,enable=True,setpoint=None,max=None,min=None,range=None):
        '''update the temperature parameters
        params:
            setpoint: float
            max: float
            min: float
            range: {"max":float,"min":float} this dictionary may be used to set max/min if params max/min are None'''
        actsp = (' S%0.1f' % setpoint) if setpoint else ''
        actmx = (' H%0.1f' % max) if max else (' H%0.1f' % range['max']) if range else ''
        actmn = (' L%0.1f' % min) if min else (' L%0.1f' % range['min']) if range else ''
        self.ctlr.interact('TEMP,%s%s%s' % (actsp,actmx,actmn))

    def write_humi(self,enable=True,setpoint=None,max=None,min=None,range=None):
        '''update the humidity parameters
        params:
            enable: boolean
            setpoint: float
            max: float
            min: float
            range: {"max":float,"min":float} this dictionary may be used to set max/min if params max/min are None'''
        actsp = (' S%0.1f' % setpoint) if setpoint else ''
        actmx = (' H%0.1f' % max) if max else (' H%0.1f' % range['max']) if range else ''
        actmn = (' L%0.1f' % min) if min else (' L%0.1f' % range['min']) if range else ''
        self.ctlr.interact('HUMI,%s%s%s' % (actsp if enable else 'SOFF',actmx,actmn))

    def write_set(self,mode,setpoint=0):
        '''Set the constant setpoints refrig mode
        params:
            mode: string,"off" or "manual" or "auto"
            setpoint: int,20 or 50 or 100'''
        self.ctlr.interact('SET,%s' % self.encode_refrig(mode,setpoint))

    def write_relay(self,relays):
        '''set each relay(time signal)
        params:
            relays: [boolean] True=turn relay on, False=turn relay off, None=do nothing'''
        vals = self.parse_relays(relays)
        if len(vals['on']) > 0:
            self.ctlr.interact('RELAY,ON,%s' % ','.join(str(v) for v in vals['on']))
        if len(vals['off']) > 0:
            self.ctlr.interact('RELAY,OFF,%s' % ','.join(str(v) for v in vals['off']))

    def write_prgmRun(self,pgmnum,pgmstep):
        '''runs a program at the given step
        params:
            pgmnum: int, program to run
            prgmstep: int, step to run'''
        self.ctlr.interact('PRGM,RUN,RAM:%d,STEP%d' % (pgmnum,pgmstep))

    def write_prgmPause(self):
        '''pause a running program.'''
        self.ctlr.interact('PRGM,PAUSE')

    def write_prgmContinue(self):
        '''resume execution of a paused program'''
        self.ctlr.interact('PRGM,CONTINUE')

    def write_prgmAdvance(self):
        '''skip to the next step of a running program'''
        self.ctlr.interact('PRGM,ADVANCE')

    def write_prgmEnd(self,mode="STANDBY"):
        '''stop the running program
        params:
            mode: string, the mode to run in place of the program must be: "HOLD"/"CONST"/"OFF"/"STANDBY"(default)'''
        if mode in ["HOLD","CONST","OFF","STANDBY"]:
            self.ctlr.interact('PRGM,END,%s' % mode)
        else:
            raise ValueError('"mode" must be "HOLD"/"CONST"/"OFF"/"STANDBY"')

    def write_modeOff(self):
        '''turn the controller screen off'''
        self.ctlr.interact('MODE,OFF')

    def write_modeStandby(self):
        '''stop operation(STANDBY)'''
        self.ctlr.interact('MODE,STANDBY')

    def write_modeConstant(self):
        '''run constant setpoint 1'''
        self.ctlr.interact('MODE,CONSTANT')

    def write_modeRun(self,pgmnum):
        '''run a program given by number
        params:
            pgmnum: int, the program to run'''
        self.ctlr.interact('MODE,RUN%d' % pgmnum)

    def write_prgmDataEdit(self, pgmnum, mode, overwrite=False):
        '''start/stop/cancel program editing on a new or exising program
        params:
            pgmnum: int, the program to start/stop/cancel editing on
            mode: string, "START" or "END" or "CANCEL"
            overwrite: boolean, when true programs/steps may be overwritten'''
        self.ctlr.interact('PRGM DATA WRITE, PGM%d, %s %s' % (pgmnum,'OVER WRITE' if overwrite else 'EDIT',mode))

    def write_prgmDataDetails(self,pgmnum,**pgmdetail):
        '''write the various program wide parameters to the controller
        params:
            pgmnum: int, the program being written or edited
            pgmdetail: the program details see write_prgmDataDetail for parameters'''
        if 'name' in pgmdetail:
            self.ctlr.interact('PRGM DATA WRITE, PGM%d, NAME,%s' % (pgmnum,pgmdetail['name']))
        if 'counter_a' in pgmdetail and pgmdetail['counter_a']['cycles'] > 0:
            tmp = 'PRGM DATA WRITE, PGM%d, COUNT,A(%d.%d.%d)' % ((pgmnum,pgmdetail['counter_a']['start'],pgmdetail['counter_a']['end'],pgmdetail['counter_a']['cycles']))
            if 'counter_b' in pgmdetail and pgmdetail['counter_b']['cycles'] > 0:
                tmp = '%s,B(%d.%d.%d)' % (tmp,pgmdetail['counter_b']['start'],pgmdetail['counter_b']['end'],pgmdetail['counter_b']['cycles'])
            self.ctlr.interact(tmp)
        if 'counter_b' in pgmdetail and not 'counter_a' in pgmdetail and pgmdetail['counter_b']['cycles'] > 0:
            self.ctlr.interact('PRGM DATA WRITE, PGM%d, COUNT,B(%d.%d.%d)' % ((pgmnum,pgmdetail['counter_b']['start'],pgmdetail['counter_b']['end'],pgmdetail['counter_b']['cycles'])))
        if 'end' in pgmdetail:
            self.ctlr.interact('PRGM DATA WRITE, PGM%d, END,%s' % (pgmnum,pgmdetail['end'] if pgmdetail['end'] != 'RUN' else 'RUN,PTN%s' % pgmdetail['next_prgm']))
        if 'tempDetail' in pgmdetail:
            if 'range' in pgmdetail['tempDetail']:
                self.ctlr.interact('PRGM DATA WRITE, PGM%d, HTEMP,%0.1f' % (pgmnum,pgmdetail['tempDetail']['range']['max']))
                self.ctlr.interact('PRGM DATA WRITE, PGM%d, LTEMP,%0.1f' % (pgmnum,pgmdetail['tempDetail']['range']['min']))
            if 'mode' in pgmdetail['tempDetail']:
                self.ctlr.interact('PRGM DATA WRITE, PGM%d, PRE MODE, TEMP,%s' % (pgmnum,pgmdetail['tempDetail']['mode']))
            if 'setpoint' in pgmdetail['tempDetail'] and pgmdetail['tempDetail']['mode'] == 'SV':
                self.ctlr.interact('PRGM DATA WRITE, PGM%d, PRE TSV,%0.1f' % (pgmnum,pgmdetail['tempDetail']['setpoint']))
        if 'humiDetail' in pgmdetail:
            if 'range' in pgmdetail['humiDetail']:
                self.ctlr.interact('PRGM DATA WRITE, PGM%d, HHUMI,%0.0f' % (pgmnum,pgmdetail['humiDetail']['range']['max']))
                self.ctlr.interact('PRGM DATA WRITE, PGM%d, LHUMI,%0.0f' % (pgmnum,pgmdetail['humiDetail']['range']['min']))
            if 'mode' in pgmdetail['humiDetail']:
                self.ctlr.interact('PRGM DATA WRITE, PGM%d, PRE MODE, HUMI,%s' % (pgmnum,pgmdetail['humiDetail']['mode']))
            if 'setpoint' in pgmdetail['humiDetail'] and pgmdetail['humiDetail']['mode'] == 'SV':
                self.ctlr.interact('PRGM DATA WRITE, PGM%d, PRE HSV,%0.0f' % (pgmnum,pgmdetail['humiDetail']['setpoint']))

    def write_prgmDataStep(self,pgmnum,**pgmstep):
        '''write a program step to the controller
        params:
            pgmnum: int, the program being written/edited
            pgmstep: the program parameters, see read_prgmDataStep for parameters'''
        cmd = 'PRGM DATA WRITE, PGM%d, STEP%d' % (pgmnum, pgmstep['number'])
        if 'time' in pgmstep:
            cmd = '%s,TIME%d:%d' % (cmd,pgmstep['time']['hour'],pgmstep['time']['minute'])
        if 'paused' in pgmstep:
            cmd = '%s,PAUSE %s' % (cmd,'ON' if pgmstep['paused'] else 'OFF')
        if 'refrig' in pgmstep:
            cmd = '%s,%s' % (cmd, self.encode_refrig(**pgmstep['refrig']))
        if 'granty' in pgmstep:
            cmd = '%s,GRANTY %s' % (cmd, 'ON' if pgmstep['granty'] else 'OFF')
        if 'temperature' in pgmstep:
            if 'setpoint' in pgmstep['temperature']:
                cmd = '%s,TEMP%0.1f' % (cmd,pgmstep['temperature']['setpoint'])
            if 'ramp' in pgmstep['temperature']:
                cmd = '%s,TRAMP%s' % (cmd,'ON' if pgmstep['temperature']['ramp'] else 'OFF')
            if 'enable_cascade' in pgmstep['temperature']:
                cmd = '%s,PTC%s' % (cmd, 'ON' if pgmstep['temperature']['enable_cascade'] else 'OFF')
            if 'deviation' in pgmstep['temperature']:
                cmd = '%s,DEVP%0.1f,DEVN%0.1f' % (cmd,pgmstep['temperature']['deviation']['positive'],pgmstep['temperature']['deviation']['negative'])
        if 'humidity' in pgmstep:
            if 'setpoint' in pgmstep['humidity']:
                cmd = '%s,HUMI%s' % (cmd,('%0.0f' % pgmstep['humidity']['setpoint']) if pgmstep['humidity']['enable'] else 'OFF')
            if 'ramp' in pgmstep['humidity']:
                cmd = '%s,HRAMP%s' % (cmd,'ON' if pgmstep['humidity']['ramp'] else 'OFF')
        if 'relay' in pgmstep:
            rlys = self.parse_relays(pgmstep['relay'])
            if rlys['on']:
                cmd = '%s,RELAY ON%s' % (cmd,'.'.join(str(v) for v in rlys['on']))
            if rlys['off']:
                cmd = '%s,RELAY OFF%s' % (cmd,'.'.join(str(v) for v in rlys['off']))
        self.ctlr.interact(cmd)

    def write_prgmErase(self,pgmnum):
        '''erase a program
        params:
            pgmnum: int, the program to erase'''
        self.ctlr.interact('PRGM ERASE,RAM:%d'%pgmnum)

    def write_runPrgm(self,temp,hour,minute,gotemp=None,humi=None,gohumi=None,relays=None):
        '''Run a remote program (single step program)
        params:
            temp: float, temperature to use at the start of the step
            hour: int, # of hours to run the step
            minute: int, # of minutes to run the step
            gotemp: float, temperature to end the step at(optional for ramping)
            humi: float, the humidity to use at the start of the step (optional)
            gohumi: float, the humidity to end the steap at (optional for ramping)
            relays: [boolean], True= turn relay on, False=turn relay off, None=Do nothing (optional)'''
        cmd = 'RUN PRGM, TEMP%0.1f TIME%d:%d' % (temp,hour,minute)
        if gotemp:
            cmd = '%s GOTEMP%0.1f' % (cmd,gotemp)
        if humi:
            cmd = '%s HUMI%0.0f' % (cmd,humi)
        if gohumi:
            cmd = '%s GOHUMI%0.0f' % (cmd,gohumi)
        rlys = self.parse_relays(relays) if relays else {'on':None,'off':None}
        if rlys['on']:
            cmd = '%s RELAYON,%s' % (cmd,','.join(str(v) for v in rlys['on']))
        if rlys['off']:
            cmd = '%s RELAYOFF,%s' % (cmd,','.join(str(v) for v in rlys['off']))
        self.ctlr.interact(cmd)

    def write_tempPtc(self,enable,positive,negative):
        '''set product temperature control settings
        params:
            enable: boolean, True(on)/False(off)
            positive: float, maximum positive deviation
            negative: float, maximum negative deviation'''
        self.ctlr.interact('TEMP PTC, PTC%s, DEVP%0.1f, DEVN%0.1f' % ('ON' if enable else 'OFF',positive,negative))

    def write_ptc(self,range,p,filter,i,opt1=0,opt2=0):
        '''write product temp control parameters to controller
        params:
            range: {"max":float,"min":float}, allowable range of operation
            p: float, P parameter of PID
            i: float, I parameter of PID
            filter: float, filter value
            opt1,opt2 not used set to 0.0'''
        self.ctlr.interact('PTC,%0.1f,%0.1f,%0.1f,%0.1f,%0.1f,%0.1f,%0.1f' % (range['max'],range['min'],p,filter,i,opt1,opt2))

    def write_IPSet(self,address,mask,gateway):
        '''Write the IP address configuration to the controller'''
        self.ctlr.interact('IPSET,%s,%s,%s'%(address,mask,gateway))

    # --- helpers etc --- helpers etc --- helpers etc --- helpers etc --- helpers etc --- helpers etc --- helpers etc --- helpers etc --- helpers etc --- helpers etc ---
    def parse_prgmDataStep(self,arg):
        parsed = re.search(r'(\d+),TEMP([0-9.-]+),TEMP RAMP (\w+)(?:,PTC (\w+))?(?:,HUMI([^,]+)(?:,HUMI RAMP (\w+))?)?,TIME(\d+):(\d+),GRANTY (\w+),(\w+)(?:,RELAY ON([0-9.]+))?,PAUSE (\w+)(?:,DEVP([0-9.-]+),DEVN([0-9.-]+))?',arg)
        base = {'number':int(parsed.group(1)),
                'time':{'hour':int(parsed.group(7)),
                        'minute':int(parsed.group(8))},
                'paused':parsed.group(12) == 'ON',
                'granty':parsed.group(9) == 'ON',
                'refrig':self.reflookup.get(parsed.group(10),{'mode':'manual','setpoint':0}),
                'temperature':{'setpoint':float(parsed.group(2)),
                               'ramp':parsed.group(3) == 'ON'}}
        if parsed.group(5):
            base['humidity'] = {'setpoint':tryfloat(parsed.group(5),0.0),'enable':parsed.group(5) != ' OFF','ramp':parsed.group(6) == 'ON'}
        if parsed.group(4):
            base['temperature'].update({'enable_cascade':parsed.group(4) == 'ON','deviation': {'positive':float(parsed.group(13)),'negative':float(parsed.group(14))}})
        if parsed.group(11):
            relays = parsed.group(11).split('.')
            base['relay'] = [str(i) in relays for i in range(1,13)]
        else:
            base['relay'] = [False for i in range(1,13)]
        return base

    def parse_prgmDataDetail(self,arg):
        parsed = re.search(r'([0-9.-]+),([0-9.-]+),(?:(\d+),(\d+),)?TEMP(\w+)(?:,([0-9.-]+))?(?:,HUMI(\w+)(?:,(\d+))?)?',arg)
        ret = {'tempDetail':{'range':{'max':float(parsed.group(1)),'min':float(parsed.group(2))},'mode':parsed.group(5),'setpoint':parsed.group(6)}}
        if parsed.group(3):
            ret['humiDetail'] = {'range':{'max':float(parsed.group(3)),'min':float(parsed.group(4))},'mode':parsed.group(7),'setpoint':parsed.group(8)}
        return ret

    #currently not parsing the patern number on endmode run
    def parse_prgmData(self,arg):
        parsed = re.search(r'(\d+),<([^,;]+)>,COUNT,A\((\d+).(\d+).(\d+)\),B\((\d+).(\d+).(\d+)\),END\(([a-zA-Z0-9:]+)\)',arg)
        return {'steps':int(parsed.group(1)),'name':parsed.group(2),'end':parsed.group(9) if 'RUN' not in parsed.group(9) else parsed.group(9)[:3],
                'next_prgm':int('0' if 'RUN' not in parsed.group(9) else parsed.group(9)[4:]),
                'counter_a':{'start':int(parsed.group(3)),'end':int(parsed.group(4)),'cycles':int(parsed.group(5))},
                'counter_b':{'start':int(parsed.group(6)),'end':int(parsed.group(7)),'cycles':int(parsed.group(8))}}

    def read_prgm(self, pgmnum,withPtc=False):
        '''read an entire program helper method'''
        if pgmnum > 0 and pgmnum <= 40:
            pgm = self.read_prgmDataPtc(pgmnum) if withPtc else self.read_prgmData(pgmnum)
            pgm.update(self.read_prgmDataPtcDetail(pgmnum) if withPtc else self.read_prgmDataDetail(pgmnum))
            pgm['steps'] = [self.read_prgmDataPtcStep(pgmnum,i) if withPtc else self.read_prgmDataStep(pgmnum,i) for i in range(1,pgm['steps']+1)]
        elif pgmnum == 0:
            pgm = {'counter_a':{'cycles':0,'end':0,'start':0},'counter_b':{'cycles':0,'end':0,'start':0},
                      'end':'OFF','name':'','next_prgm':0,'tempDetail':{'mode':'OFF','setpoint':None,'range':self.read_temp()['range']},
                      'steps':[{'granty':False,'number':1,'paused':False,'refrig':{'mode':'auto','setpoint':0},'time':{'hour':1,'minute':0},
                               'relay':[False for i in range(12)], 'temperature':{'ramp':False,'setpoint':0.0}}]}
            if withPtc:
                pgm['steps'][0]['temperature'].update({'deviation':self.read_tempPtc()['deviation'],'enable_cascade':False})
            try:
                pgm['humiDetail'] = {'mode':'OFF','setpoint':None,'range':self.read_humi()['range']}
                pgm['steps'][0]['humidity'] = {'enable':False,'ramp':False,'setpoint':0.0}
            except: pass
        else:
            raise valueError('pgmnum must be 0-40')
        return pgm

    def write_prgm(self, pgmnum, program):
        '''write an entire program helper method (must use same program format as read_prgm)'''
        self.write_prgmDataEdit(pgmnum,'START')
        try:
            self.write_prgmDataDetails(pgmnum, **program)
            for num,step in enumerate(program['steps']):
                step['number'] = num+1 #ensure the step number is sequential
                self.write_prgmDataStep(pgmnum,**step)
            self.write_prgmDataEdit(pgmnum,'END')
        except:
            self.write_prgmDataEdit(pgmnum,'CANCEL')
            raise

    def encode_refrig(self,mode,setpoint):
        if mode =='off':
            act = 'REF0'
        elif mode == 'auto':
            act = 'REF9'
        elif mode == 'manual':
            if setpoint == 0:
                act = 'REF0'
            elif setpoint == 20:
                act = 'REF1'
            elif setpoint == 50:
                act = 'REF3'
            elif setpoint == 100:
                act = 'REF6'
            else:
                raise ValueError('parameter "setpoint" must be one of the following: 20/50/100')
        else:
            raise ValueError('parameter "mode" must be one of the following: "off"/"manual"/"auto"')
        return act

    def parse_relays(self,relays):
        ret = {'on':[],'off':[]}
        for i,val in enumerate(relays):
            if val is not None:
                if val:
                    ret['on'].append(i+1)
                else:
                    ret['off'].append(i+1)
        return ret

