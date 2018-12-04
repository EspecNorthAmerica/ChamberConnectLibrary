'''
Handle the actual communication with Espec Corp. Controllers

:copyright: (C) Espec North America, INC.
:license: MIT, see LICENSE for more details.
'''
#pylint: disable=W0703
import socket
import serial
import time
from controllerinterface import ControllerInterfaceError

ERROR_DESCIPTIONS = {
    'CMD ERR':'Unrocognized command',
    'ADDR ERR':'Bad address',
    'CONT NOT READY-1':'Chamber does not support PTCON/Humidity',
    'CONT NOT READY-2':'Chamber is not running a program',
    'CONT NOT READY-3':'Command not supported by this controller',
    'CONT NOT READY-4':'Keys may not be locked while controller is off',
    'CONT NOT READY-5':'Specified time signal is not enabled',
    'DATA NOT READY':'Specified program does not exist',
    'PARA ERR':'Parameter missing or unrecognizable',
    'DATA OUT OF RANGE':'Data not with in valid range',
    'PROTECT ON':'Controller data protection is anabled via hmi',
    'PRGM WRITE ERR-1':'Program slot is read only',
    'PRGM WRITE ERR-2':'Not in program edit/overwrite mode',
    'PRGM WRITE ERR-3':'Edit request not allowed not in edit mode',
    'PRGM WRITE ERR-4':'A program is already being edited',
    'PRGM WRITE ERR-5':'A program is already being edited',
    'PRGM WRITE ERR-6':'Not in overwrite mode',
    'PRGM WRITE ERR-7':'Cannot edit program other thant the one in edit mode',
    'PRGM WRITE ERR-8':'Steps must be entered in order',
    'PRGM WRITE ERR-9':'Invalid counter configuration',
    'PRGM WRITE ERR-10':'Cannot edit a running program',
    'PRGM WRITE ERR-11':'Missing data for counter or end mode',
    'PRGM WRITE ERR-12':'Program is being edited on hmi',
    'PRGM WRITE ERR-13':'Invalid step data',
    'PRGM WRITE ERR-14':'Cannot set exposure time while ramp control is on.',
    'PRGM WRITE ERR-15':'Humidity must be enabled for humidity ramo mode',
    'INVALID REQ':'Unsupported function',
    'CHB NOT READY':'Could not act on given command.'
}

class EspecError(ControllerInterfaceError):
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
                errmsg = recv[3:0-len(self.delimeter)]
                msg = 'EspecError: command:"%s" genarated Error:"%s"(%s)' % (
                    message, errmsg, ERROR_DESCIPTIONS.get(errmsg, 'missing description')
                )
                raise EspecError(msg)
            recvs.append(recv[:-1*len(self.delimeter)])
        return recvs if len(recvs) > 1 else recvs[0]

class EspecTCP(object):
    '''
    Handles low level communication to espec corp controllers via serial TCP
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
            errmsg = recv[3:0-len(self.delimeter)]
            msg = 'EspecError: command:"%s" genarated Error:"%s"(%s)' % (
                message, errmsg, ERROR_DESCIPTIONS.get(errmsg, 'missing description')
            )
            raise EspecError(msg)
        return recv[:-2]
