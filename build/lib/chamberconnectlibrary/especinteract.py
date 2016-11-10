'''
Handle the actual communication with Espec Corp. Controllers

:copyright: (C) Espec North America, INC.
:license: MIT, see LICENSE for more details.
'''
import socket
import serial

class EspecError(Exception):
    '''Generic Espec Corp controller error'''
    pass

class EspecSerial(object):
    '''handles low level communication to espec corp controllers via serial (RS232/485)'''
    def __init__(self, port, **kwargs):
        self.address = kwargs.get('address', None)
        self.delimeter = kwargs.get('delimeter', '\r\n')
        self.serial = serial.Serial(
            port=port,
            baudrate=kwargs.get('baud', 9600),
            bytesize=kwargs.get('databits', 8),
            parity=kwargs.get('parity', 'N'),
            stopbits=kwargs.get('stopbits', 8),
            timeout=kwargs.get('timeout', 1)
        )

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def close(self):
        '''Close the connection the the chamber'''
        self.serial.close()

    def interact(self, message):
        '''Send a message to the chamber and get its response
        params:
            message: the message to send (str)
        returns:
            string: response from the chamber
        raises:
            EspecError'''
        message = message.encode('ascii', 'ignore')
        if self.address:
            self.serial.write('%d,%s%s'%(self.address, message, self.delimeter))
        else:
            self.serial.write('%s%s' % (message, self.delimeter))
        recv = ''
        while recv[0-len(self.delimeter):] != self.delimeter:
            rbuff = self.serial.read(1)
            if len(rbuff) == 0:
                raise EspecError('The chamber did not respond in time')
            recv += rbuff
        if recv.startswith('NA:'):
            msg = 'EspecError: command:"%s" genarated Error:"%s"' % (
                message, recv[3:0-len(self.delimeter)]
            )
            raise EspecError(msg)
        return recv[:-1*len(self.delimeter)]

class EspecTCP(object):
    '''handles low level communication to espec corp controllers via serial TCP'''
    def __init__(self, host, **kwargs):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(True)
        self.socket.connect((host, kwargs.get('port', 10001)))
        self.address = kwargs.get('address', None)
        self.delimeter = kwargs.get('delimeter', '\r\n')

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def close(self):
        '''Close the connection the the chamber'''
        self.socket.close()

    def interact(self, message):
        '''Send a message to the chamber and get its response
        params:
            message: the message to send (str)
        returns:
            string: response from the chamber
        raises:
            EspecError'''
        if self.address:
            self.socket.send('%d,%s%s'%(self.address, message, self.delimeter))
        else:
            self.socket.send('%s%s'%(message, self.delimeter))
        recv = ''
        while recv[0-len(self.delimeter):] != self.delimeter:
            recv += self.socket.recv(1)
        if recv.startswith('NA:'):
            msg = 'EspecError: command:"%s" generated Error:"%s"' % (
                message, recv[3:0-len(self.delimeter)]
            )
            raise EspecError(msg)
        return recv[:-2]
