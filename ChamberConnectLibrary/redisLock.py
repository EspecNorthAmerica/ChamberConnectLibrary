'''
An exclusive lock for talking to controllers using redis.

:copyright: (C) Espec North America, INC.
:license: MIT, see LICENSE for more details.
'''
import redis, time

class LockTimeout(BaseException):
    pass

class Lock(object):
    def __init__(self, redis, key, expires=120, timeout=60):
        self.key = key
        self.timeout = timeout
        self.expires = expires
        self.redis = redis
    def __enter__(self):
        timeout = self.timeout
        while timeout >= 0:
            expires = time.time() + self.expires + 0.1
            if self.redis.setnx(self.key, expires):
                return
            cv = self.redis.get(self.key)
            if cv and float(cv) < time.time() and self.redis.getset(self.key, expires) == cv:
                return
            timeout -= 0.1
            time.sleep(0.1)
        raise LockTimeout("Timeout waiting for lock")
    def __exit__(self, exc_type, exc_value, traceback):
        self.redis.delete(self.key)

def exclusive(func):
    def wrapper(self,*args,**kwargs):
        if kwargs.get('exclusive',True):
            with Lock(self.redis,'%s-lock' % (self.serialport if self.interface == "RTU" else self.host)):
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