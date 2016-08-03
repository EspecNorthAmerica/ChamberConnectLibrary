'''
Handle the actual communication with Espec Corp. Controllers

:copyright: (C) Espec North America, INC.
:license: MIT, see LICENSE for more details.
'''
import serial, socket

class EspecError(Exception):
    '''Generic Espec Corp controller error'''
    pass

class EspecSerial:
    '''handles low level communication to espec corp controllers via serial (RS232/485)'''
    def __init__(self, port, baud=9600, parity='N', databits=8, stopbits=1, timeout=1, address=1, delimeter='\r\n'):
        self.address = address
        self.delimeter = delimeter
        self.serial = serial.Serial(port=port,baudrate=baud,bytesize=databits,parity=parity,stopbits=stopbits,timeout=timeout)
    def __del__(self):
        try:
            self.close()
        except:
            pass
    def close(self):
        self.serial.close()
    def interact(self,message):
        message = message.encode('ascii','ignore')
        self.serial.write('%d,%s%s'%(self.address,message,self.delimeter))
        recv = ''
        while recv[0-len(self.delimeter):] != self.delimeter:
            rbuff = self.serial.read(1)
            if len(rbuff) == 0:
                raise EspecError('The chamber did not respond in time')
            recv += rbuff
        if recv.startswith('NA:'):
            raise EspecError('EspecError: command:"%s" genarated Error:"%s"' % (message,recv[3:0-len(self.delimeter)]))
        return recv[:-1*len(self.delimeter)]
            
class EspecTCP:
    '''handles low level communication to espec corp controllers via serial TCP'''
    def __init__(self,host,port=10001,timeout=5,address=1,delimeter='\r\n'):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(True)
        self.socket.connect((host,port))
        self.address = address
        self.delimeter = delimeter
    def __del__(self):
        try:
            self.close()
        except:
            pass
    def close(self):
        self.socket.close()
    def interact(self,message):
        self.socket.send('%d,%s%s'%(self.address,message,self.delimeter))
        recv = ''
        while recv[0-len(self.delimeter):] != self.delimeter:
            recv += self.socket.recv(1)
        if recv.startswith('NA:'):
            raise EspecError('EspecError: command:"%s" genarated Error:"%s"' % (message,recv[3:0-len(self.delimeter)]))
        return recv[:-2]