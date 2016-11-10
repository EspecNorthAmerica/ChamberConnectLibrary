'''
Common interface for all All ChamberConnectLibrary upper level interfaces

:copyright: (C) Espec North America, INC.
:license: MIT, see LICENSE for more details.
'''
from abc import ABCMeta, abstractmethod
import traceback, time #needed for debug only...
from threading import RLock

class ControllerInterfaceError(Exception):
    pass

def exclusive(func):
    def wrapper(self,*args,**kwargs):
        if kwargs.get('exclusive',True):
            with self.lock:
                try:
                    try: del kwargs['exclusive']
                    except: pass
                    self.connect()
                    return func(self,*args,**kwargs)
                finally:
                    try:
                        self.close()
                        if self.interface == "TCP": time.sleep(0.1) #forcefully slow down connection cycles
                    except: pass
        else:
            try: del kwargs['exclusive']
            except: pass
            return func(self,*args,**kwargs)
    return wrapper

class itemproperty(object):
    '''copyright Ian Kelly, MIT licensed from http://code.activestate.com/recipes/577703-item-properties/
    an implimentation of the python property class with support for index/keys'''
    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        if doc is None and fget is not None and hasattr(fget, "__doc__"):
            doc = fget.__doc__
        self._get = fget
        self._set = fset
        self._del = fdel
        self.__doc__ = doc

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            return bounditemproperty(self, instance)

    def __set__(self, instance, value):
        raise AttributeError("can't set attribute")

    def __delete__(self, instance):
        raise AttributeError("can't delete attribute")

    def getter(self, fget):
        return itemproperty(fget, self._set, self._del, self.__doc__)

    def setter(self, fset):
        return itemproperty(self._get, fset, self._del, self.__doc__)

    def deleter(self, fdel):
        return itemproperty(self._get, self._set, fdel, self.__doc__)


class bounditemproperty(object):
    '''copyright Ian Kelly, MIT licensed from http://code.activestate.com/recipes/577703-item-properties/'''
    def __init__(self, item_property, instance):
        self.__item_property = item_property
        self.__instance = instance

    def __getitem__(self, key):
        fget = self.__item_property._get
        if fget is None:
            raise AttributeError("unreadable attribute item")
        return fget(self.__instance, key)

    def __setitem__(self, key, value):
        fset = self.__item_property._set
        if fset is None:
            raise AttributeError("can't set attribute item")
        fset(self.__instance, key, value)

    def __delitem__(self, key):
        fdel = self.__item_property._del
        if fdel is None:
            raise AttributeError("can't delete attribute item")
        fdel(self.__instance, key)

class CtlrProperty:
    __metaclass__ = ABCMeta

    def init_common(self,**kwargs):
        self.client = None
        self.host = kwargs.get('host',"10.30.100.90")
        self.interface = kwargs.get('interface',"TCP")
        self.adr = kwargs.get('adr',1)
        self.serialport = kwargs.get('serialport', 4-1) #zero indexed COM4 = 3
        self.baudrate = kwargs.get('baudrate',19200)
        self.loops = kwargs.get('loops',1)
        self.cascades = kwargs.get('cascades',0)
        self.lock = kwargs.get('lock',RLock())

    @abstractmethod
    def get_datetime(self):
        '''
        Get the controllers date & time (datetime.datetime)
        '''
        pass
    @abstractmethod
    def set_datetime(self,value):
        '''
        Set the controllers (datetime.datetime)
        '''
        pass

    @abstractmethod
    def get_loop_sp(self,N):
        '''
        Get the setpoint of loop N
        '''
        pass
    @abstractmethod
    def set_loop_sp(self,N,value): pass
    @abstractmethod
    def get_loop_pv(self,N): pass
    @abstractmethod
    def get_loop_range(self,N): pass
    @abstractmethod
    def set_loop_range(self,N,value): pass
    @abstractmethod
    def get_loop_en(self,N): pass
    @abstractmethod
    def set_loop_en(self,N,value): pass
    @abstractmethod
    def get_loop_units(self,N): pass
    @abstractmethod
    def get_loop_mode(self,N): pass
    @abstractmethod
    def set_loop_mode(self,N,value): pass

    def get_loop_power(self,N): raise NotImplementedError
    def set_loop_power(self,N,value): raise NotImplementedError

    @abstractmethod
    def get_cascade_sp(self,N): pass
    @abstractmethod
    def set_cascade_sp(self,N,value): pass
    @abstractmethod
    def get_cascade_pv(self,N): pass
    @abstractmethod
    def get_cascade_range(self,N): pass
    @abstractmethod
    def set_cascade_range(self,N,value): pass
    @abstractmethod
    def get_cascade_en(self,N): pass
    @abstractmethod
    def set_cascade_en(self,N): pass
    @abstractmethod
    def get_cascade_units(self,N): pass
    @abstractmethod
    def get_cascade_mode(self,N): pass
    @abstractmethod
    def set_cascade_mode(self,N,value): pass
    @abstractmethod
    def get_cascade_ctl(self,N): pass
    @abstractmethod
    def set_cascade_ctl(self,N,value): pass
    @abstractmethod
    def get_cascade_deviation(self,N): pass
    @abstractmethod
    def set_cascade_deviation(self,N,value): pass
    
    def get_cascade_power(self,N): raise NotImplementedError
    def set_cascade_power(self,N,value): raise NotImplementedError

    @abstractmethod
    def get_event(self,N): pass
    @abstractmethod
    def set_event(self,N): pass
    @abstractmethod
    def get_status(self): pass
    @abstractmethod
    def get_alarm_status(self): pass

    @abstractmethod
    def const_start(self): pass
    @abstractmethod
    def stop(self): pass
    @abstractmethod
    def prgm_start(self,N,step): pass
    @abstractmethod
    def prgm_pause(self): pass
    @abstractmethod
    def prgm_resume(self): pass
    @abstractmethod
    def prgm_next_step(self): pass

    @abstractmethod
    def get_prgm_cur(self): pass
    @abstractmethod
    def get_prgm_cstep(self): pass
    @abstractmethod
    def get_prgm_cstime(self): pass
    @abstractmethod
    def get_prgm_time(self, pgm=None): pass

    @abstractmethod
    def get_prgm_name(self,N): pass
    #@abstractmethod #not all controllers can support this so we are not forcing the overwrite
    def set_prgm_name(self,N,value): raise NotImplementedError
    @abstractmethod
    def get_prgm_steps(self,N): pass
    @abstractmethod
    def get_prgms(self): pass
    @abstractmethod
    def get_prgm(self,N): pass
    @abstractmethod
    def set_prgm(self,N,value): pass

    @abstractmethod
    def prgm_delete(self,N): pass
    @abstractmethod
    def sample(self): pass
    @abstractmethod
    def process_controller(self): pass
    
    @abstractmethod
    def get_networkSettings(self): pass
    @abstractmethod
    def set_networkSettings(self): pass

    #properties
    datetime = property(lambda self: self.get_datetime(),
                        lambda self, value: self.set_datetime(value),
                        doc='datetime object representing the datetime of the controller')

    loop_sp = itemproperty(lambda self,N: self.get_loop_sp(N),
                           lambda self,N,value: self.set_loop_sp(N,value),
                           doc='setpoint of the specified loop')
    loop_pv = itemproperty(lambda self,N: self.get_loop_pv(N),
                           doc='process value of the loop')
    loop_range = itemproperty(lambda self,N: self.get_loop_range(N),
                              lambda self,N,value: self.set_loop_range(N,value),
                              doc='allowable operation range of the specified loop')
    loop_en = itemproperty(lambda self,N: self.get_loop_en(N),
                           lambda self,N,value: self.set_loop_en(N,value),
                           doc='enable/disable signal of the specified loop')
    loop_units = itemproperty(lambda self,N: self.get_loop_units(N),
                              doc='units of the specified loop')
    loop_mode = itemproperty(lambda self,N: self.get_loop_mode(N),
                             lambda self,N,value: self.set_loop_mode(N,value),
                             doc='get the mode of the specified loop')

    cascade_sp = itemproperty(lambda self,N: self.get_cascade_sp(N),
                              lambda self,N,value: self.set_cascade_sp(N,value),
                              doc='setpoint of the specified cascade(PTCON) loop')
    cascade_pv = itemproperty(lambda self,N: self.get_cascade_pv(N),
                              doc='process value of the cascade(PTCON) loop')
    cascade_range = itemproperty(lambda self,N: self.get_cascade_range(N),
                                 lambda self,N,value: self.set_cascade_range(N,value),
                                 doc='allowable setpoint range of the cascade(PTCON) loop')
    cascade_en = itemproperty(lambda self,N: self.get_cascade_en(N),
                              lambda self,N,value: self.set_cascade_en(N,value),
                              doc='enable/disable signal of the cascade(PTCON) loop')
    cascade_units = itemproperty(lambda self,N: self.get_cascade_units(N),
                                 doc='units of the cascade(PTCON) loop')
    cascade_mode = itemproperty(lambda self,N: self.get_cascade_mode(N),
                                lambda self,N,value: self.set_cascade_mode(N,value),
                                doc='get the mode of the cascade(PTCON) loop')
    cascade_ctl = itemproperty(lambda self,N: self.get_cascade_ctl(N),
                               lambda self,N,value: self.set_cascade_ctl(N,value),
                               doc='enable/disable signal for cascade(PTCON) control mode')
    cascade_deviation = itemproperty(lambda self,N: self.get_cascade_deviation(N),
                                     lambda self,N,value: self.set_cascade_deviation(N,value),
                                     doc='over under temperature range when cascade(PTCON) is operating')

    event = itemproperty(lambda self,N: self.get_event(N),
                         lambda self,N,value: self.set_event(N,value),
                         doc='Time signal/relay/event status/enable/disable')
    status = property(lambda self: self.get_status(),
                      doc='The controller run status')
    alarm_status = property(lambda self: self.get_alarm_status(),
                            doc='get a list of active alarms by code')

    prgm_cur = property(lambda self: self.get_prgm_cur(),
                        doc='Get the number of the currently executing program')
    prgm_cstep = property(lambda self: self.get_prgm_cstep(),
                          doc='Get the current step of the currently executing program')
    prgm_cstime = property(lambda self: self.get_prgm_cstime(),
                           doc='Get the time remaing of the current step of the current program')
    prgm_time = property(lambda self: self.get_prgm_time(),
                         doc='Get remaining execution time of the current program')
    prgm_name = itemproperty(lambda self,N: self.get_prgm_name(N),
                             lambda self,N,value: self.set_prgm_name(N,value),
                             doc='The name of the given program')
    prgm_steps = itemproperty(lambda self,N: self.get_prgm_steps(N),
                              doc='Get the number of steps in a program')
    prgms = property(lambda self: self.get_prgms(),
                     doc='A list of all programs and there names')
    prgm = itemproperty(lambda self,N: self.get_prgm(N),
                        lambda self,N,value: self.set_prgm(N,value),
                        doc='programs on the controller')

    networkSettings = property(lambda self: self.get_networkSettings(),
                               lambda self,value: self.set_networkSettings(value),
                               doc='network settings displayed by the controller')

    def self_test(self,loops,cascades):
        '''preform a self test on all functions'''

        def print_exception(trce):
            print '\n'.join(['\t' + l for l in trce.split('\n')])

        print 'call process_controller():'
        try:
            print '\t%r' % self.process_controller()
        except:
            print_exception(traceback.format_exc())

        print 'read datetime:'
        try:
            print '\t%r' % self.datetime
        except:
            print_exception(traceback.format_exc())

        print 'write datetime:'
        try:
            self.datetime = self.datetime
            print '\tok'
        except:
            print_exception(traceback.format_exc())

        for i in range(1,loops+1):
            print 'read loop_sp[%d]:' % i
            try:
                print '\t%r' % self.loop_sp[i]
            except:
                print_exception(traceback.format_exc())
            print 'write loop_sp[%d]:' %i
            try: 
                self.loop_sp[i] = self.loop_sp[i]['constant']
                print '\tok'
            except:
                print_exception(traceback.format_exc())

            print 'read loop_pv[%d]:' % i
            try:
                print '\t%r' % self.loop_pv[i]
            except:
                print_exception(traceback.format_exc())

            print 'read loop_range[%d]:' % i
            try:
                print '\t%r' % self.loop_range[i]
            except:
                print_exception(traceback.format_exc())
            print 'write loop_range[%d]:' %i
            try: 
                self.loop_range[i] = self.loop_range[i]
                print '\tok'
            except:
                print_exception(traceback.format_exc())

            print 'read loop_en[%d]:' % i
            try:
                print '\t%r' % self.loop_en[i]
            except:
                print_exception(traceback.format_exc())
            print 'write loop_en[%d]:' %i
            try: 
                self.loop_en[i] = self.loop_en[i]['constant']
                print '\tok'
            except:
                print_exception(traceback.format_exc())

            print 'read loop_units[%d]:' % i
            try:
                print '\t%r' % self.loop_units[i]
            except:
                print_exception(traceback.format_exc())

            print 'read loop_mode[%d]:' % i
            try:
                print '\t%r' % self.loop_mode[i]
            except:
                print_exception(traceback.format_exc())

        for i in range(1,cascades+1):
            print 'read cascade_sp[%d]:' % i
            try:
                print '\t%r' % self.cascade_sp[i]
            except:
                print_exception(traceback.format_exc())
            print 'write cascade_sp[%d]:' %i
            try: 
                self.cascade_sp[i] = self.cascade_sp[i]['constant']
                print '\tok'
            except: print_exception(traceback.format_exc())

            print 'read cascade_pv[%d]:' % i
            try:
                print '\t%r' % self.cascade_pv[i]
            except:
                print_exception(traceback.format_exc())

            print 'read cascade_range[%d]:' % i
            try:
                print '\t%r' % self.cascade_range[i]
            except:
                print_exception(traceback.format_exc())
            print 'write cascade_range[%d]:' %i
            try: 
                self.cascade_range[i] = self.cascade_range[i]
                print '\tok'
            except:
                print_exception(traceback.format_exc())

            print 'read cascade_en[%d]:' % i
            try:
                print '\t%r' % self.cascade_en[i]
            except:
                print_exception(traceback.format_exc())
            print 'write cascade_en[%d]:' %i
            try: 
                self.cascade_en[i] = self.cascade_en[i]['constant']
                print '\tok'
            except:
                print_exception(traceback.format_exc())

            print 'read cascade_units[%d]:' % i
            try:
                print '\t%r' % self.cascade_units[i]
            except:
                print_exception(traceback.format_exc())

            print 'read cascade_mode[%d]:' % i
            try:
                print '\t%r' % self.cascade_mode[i]
            except:
                print_exception(traceback.format_exc())

            print 'read cascade_ctl[%d]:' % i
            try:
                print '\t%r' % self.cascade_ctl[i]
            except:
                print_exception(traceback.format_exc())
            print 'write cascade_ctl[%d]:' %i
            try: 
                self.cascade_ctl[i] = self.cascade_ctl[i]
                print '\tok'
            except:
                print_exception(traceback.format_exc())

            print 'read cascade_deviation[%d]:' % i
            try:
                print '\t%r' % self.cascade_deviation[i]
            except:
                print_exception(traceback.format_exc())
            print 'write cascade_deviation[%d]:' %i
            try: 
                self.cascade_deviation[i] = self.cascade_deviation[i]
                print '\tok'
            except:
                print_exception(traceback.format_exc())

        for i in range(1,13):
            print 'read event[%d]:' % i
            try:
                print '\t%r' % self.event[i]
            except:
                print_exception(traceback.format_exc())
            print 'write event[%d]:' %i
            try: 
                self.event[i] = self.event[i]['current']
                print '\tok'
            except:
                print_exception(traceback.format_exc())

        print 'read status:'
        try:
            print '\t%r' % self.status
        except:
            print_exception(traceback.format_exc())

        print 'read alarm_status:'
        try:
            print '\t%r' % self.alarm_status
        except:
            print_exception(traceback.format_exc())

        print 'read prgm_cur:'
        try:
            print '\t%r' % self.prgm_cur
        except:
            print_exception(traceback.format_exc())

        print 'read prgm_cstep:'
        try:
            print '\t%r' % self.prgm_cstep
        except:
            print_exception(traceback.format_exc())

        print 'read prgm_cstime:'
        try:
            print '\t%r' % self.prgm_cstime
        except:
            print_exception(traceback.format_exc())

        print 'read prgm_time:'
        try:
            print '\t%r' % self.prgm_time
        except:
            print_exception(traceback.format_exc())

        for i in range(1,6): #do 5 programs only
            print 'read prgm_name[%d]:' % i
            try:
                print '\t%r' % self.prgm_name[i]
            except:
                print_exception(traceback.format_exc())

            print 'read prgm_steps[%d]:' % i
            try:
                print '\t%r' % self.prgm_steps[i]
            except:
                print_exception(traceback.format_exc())

        print 'read prgms:'
        try:
            print '\t%r' % self.prgms
        except:
            print_exception(traceback.format_exc())

        print 'read prgm[1]:'
        try:
            print '\t%r' % self.prgm[1]
        except:
            print_exception(traceback.format_exc())
        print 'write prgm[1]:'
        try: 
            self.prgm[1] = self.prgm[1]
            print '\tok'
        except:
            print_exception(traceback.format_exc())

        print 'read networkSettings:'
        try:
            print '\t%r' % self.networkSettings
        except:
            print_exception(traceback.format_exc())
        print 'write networkSettings:'
        try: 
            self.networkSettings = self.networkSettings
            print '\tok'
        except:
            print_exception(traceback.format_exc())

        print 'call const_start():'
        try:
            self.const_start()
            time.sleep(5)
            print '\tok'
        except:
            print_exception(traceback.format_exc())

        print 'call stop():'
        try:
            self.stop()
            time.sleep(5)
            print '\tok'
        except:
            print_exception(traceback.format_exc())

        print 'call prgm_start(1,1):'
        try:
            self.prgm_start(1,1)
            time.sleep(5)
            print '\tok'
        except:
            print_exception(traceback.format_exc())

        print 'call prgm_pause():'
        try:
            self.prgm_pause()
            time.sleep(5)
            print '\tok'
        except:
            print_exception(traceback.format_exc())

        print 'call prgm_resume():'
        try:
            self.prgm_resume()
            time.sleep(5)
            print '\tok'
        except:
            print_exception(traceback.format_exc())

        print 'call sample():'
        try:
            print '\t%r' % self.sample()
        except:
            print_exception(traceback.format_exc())

        print 'Testing Complete'
