'''
Handle the actual communication with Espec Corp. Controllers

:copyright: (C) Espec North America, INC.
:license: MIT, see LICENSE for more details.
'''
#pylint: disable=W0703
import socket       # initialize and open socket
import serial       # initialize and open the port
import time         # load time library 

class EspecError(Exception):
    '''
    Generic Espec Corp controller error
    '''
    pass

class EspecSerial(object):
    '''
    Handles low level communication to espec corp controllers via serial (RS232/485)
    '''
    def __init__(self, **kwargs):
        self.address = kwargs.get('address', None)
        self.delimeter = kwargs.get('delimeter', '\r\n')
        self.serial = serial.Serial(
            port=kwargs.get('port'),
            baudrate=kwargs.get('baud', 9600),
            bytesize=kwargs.get('databits', 8),
            parity=kwargs.get('parity', 'N'),
            stopbits=kwargs.get('stopbits', 1),
            timeout=kwargs.get('timeout', 3)
        )

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def close(self):
        '''
        Close the connection the the chamber
        '''
        self.serial.close()

    def interact(self, message):
        '''
        Send a message to the chamber and get its response

        params:
            message: the message to send (str)
        returns:
            string: response from the chamber
        raises:
            EspecError
        '''
        if not isinstance(message, (list, tuple)):
            message = [message]
        recvs = []
        for msg in message:
            msg = msg.encode('ascii', 'ignore')
            if self.address:
                self.serial.write('%d,%s%s'%(self.address, msg, self.delimeter))
            else:
                self.serial.write('%s%s' % (msg, self.delimeter))
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
            recvs.append(recv[:-1*len(self.delimeter)])
        return recvs if len(recvs) > 1 else recvs[0]"

class EspecTCP(object):
    '''
    Handles low level communication to espec corp controllers via serial TCP

    P300 does not have TCP/IP communication port; however, in order to connect to 
    web controller, it will need a serial-to-tcp/ip adaptor to send information
    and publish over to the web. Thus, this section is for that purpose. 
    '''
    def __init__(self, **kwargs):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(True)
        self.socket.connect((kwargs.get('host'), kwargs.get('port', 10001)))
        self.address = kwargs.get('address', None)
        self.delimeter = kwargs.get('delimeter', '\r\n')

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def close(self):
        '''
        Close the connection the the chamber
        '''
        self.socket.close()
        time.sleep(0.1)

    def interact(self, message):
        '''
        Send a message to the chamber and get its response

        params:
            message: the message to send (str)
        returns:
            string: response from the chamber
        raises:
            EspecError
        '''
        message = message.encode('ascii', 'ignore')
        # TCP forwarder doesnt handle address properly so we are ignoring it.
        # if self.address:
        #     self.socket.send('%d,%s%s'%(self.address, message, self.delimeter))
        # else:
        #     self.socket.send('%s%s'%(message, self.delimeter))
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
 
