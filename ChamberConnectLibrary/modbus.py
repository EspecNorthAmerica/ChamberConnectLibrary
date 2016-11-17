'''
Copyright (C) Espec North America, INC. - All Rights Reserved
Written by Myles Metzler mmetzler@espec.com, Feb. 2016

Partial modbus implimantation for communicating with watlow controllers (holding registers only)
'''
#pylint: disable=W0703
import socket
import struct
import time
import serial
import collections

class ModbusError(Exception):
    '''Generic Modbus exception.'''
    pass

class Modbus(object):
    '''
    A subset of a modbus master library, only impliments modbus functions:
    3: Read Holding Register(s)
    6: Write Holding Register
    16: Write Multiple Holding Registers
    '''
    errorMessages = {
        1: 'Illegal Function',
        2: 'Illegal Data Address',
        3: 'Illegal Data Value',
        4: 'Slave Device Failure',
        5: 'Acknowledge',
        6: 'Slave Device Busy',
        7: 'Negative Acknowledge',
        8: 'Memory Parity Error',
        10:'Gateway Path Unavalable',
        11:'Gateway Target Device Failed To Respond'
    }
    address = 1


    def read_holding(self, register, count=1):
        '''
        Read holding register(s)

        Args:
            register (int): The modbus register to read
            count (int): The number of modbus registers to read (default=1)

        Returns:
            list. 16bit integers
        '''
        packet = self.make_packet(3, register, count)
        rval = self.interact(packet)
        return self.decode_packet(rval, packet)

    def read_holding_float(self, register, count=1):
        '''
        Read some floating point values from 2 adjacent modbus registers

        Args:
            register (int): the first register to start reading at.
            count (int): the number of floats to read (2*count will actually be read)

        Returns:
            list. 32bit floats
        '''
        val = self.read_holding(register, count*2)
        return [round(struct.unpack('f', struct.pack('HH', val[i], val[i+1]))[0], 1)
                for i in range(0, count*2, 2)]

    def read_holding_string(self, register, count):
        '''
        Read a string

        Args:
            register (int): The register to start reading from
            count(int): The number of registers to read (length of string)

        Returns:
            str
        '''
        val = self.read_holding(register, count)
        rstring = ""
        for char in val:
            if char is not 0:
                rstring = rstring + chr(char)
        return rstring

    def write_holding(self, register, value):
        '''
        Write to holding register(s), accepts single values or lists of values

        Args:
            register (int): register(s) to write to
            value (int or list(int)): value(s) to write,
        '''
        packettype = 16 if isinstance(value, collections.Iterable) else 6
        packet = self.make_packet(packettype, register, value)
        rval = self.interact(packet)
        self.decode_packet(rval, packet)

    def write_holding_float(self, register, value):
        '''
        Write floating point values to the controller

        Args:
            register (int): first register to write to, 2 float value will be written.
            value (float or list(float)): vlaue(s) to write to
        '''
        if isinstance(value, collections.Iterable):
            packval = ''.join([struct.unpack('HH', struct.pack('f', val)) for val in value])
        else:
            packval = struct.unpack('HH', struct.pack('f', value))
        self.write_holding(register, packval)

    def write_holding_string(self, register, value, length=20):
        '''
        Write a string to the controller

        Args:
            register (int): first register to wrote to
            value (str): The string to write
            length (int): The string will be padded or truncated to this length.

        Return:
            None
        '''
        mods = [ord(c) for c in value]
        mods.extend([0]*length)
        self.write_holding(register, mods[0:length])

    def interact(self, packet):
        '''Interact with the physical interface'''
        raise NotImplementedError

    def make_packet(self, function, register, args):
        '''Make modbus request packet.'''
        if function == 3:
            return struct.pack(">BBHH", self.address, function, register, args)
        elif function == 6:
            return struct.pack(">BBHH", self.address, function, register, args)
        elif function == 16:
            data = struct.pack(">BBHHB", self.address, function, register, len(args), len(args)*2)
            for val in args:
                data += struct.pack(">H", val)
            return data
        else:
            raise NotImplementedError("Only modbus function codes 3,6,16 are implimented.")

    def decode_packet(self, packet, spacket):
        '''Decode the modbus request packet.'''
        fcode = struct.unpack(">B", packet[1])[0]
        addr = struct.unpack(">B", packet[0])[0]
        if self.address != addr:
            shex = ":".join("{:02x}".format(ord(c) for c in spacket))
            rhex = ":".join("{:02x}".format(ord(c) for c in packet))
            raise ModbusError("Address error; Sent=%s, Recieved=%s" % (shex, rhex))
        if fcode > 127:
            ecode = struct.unpack(">B", packet[2])[0]
            ttp = (ecode, self.errorMessages.get(ecode, 'Unknown error code'))
            raise ModbusError('Modbus Error: Exception code = %d(%s)' % ttp)

        if fcode == 3: #Read holding register(s)
            cnt = struct.unpack(">B", packet[2])[0]/2
            return struct.unpack(">%dH" % cnt, packet[3:])
        elif fcode == 6:
            pass #nothing is required
        elif fcode == 16:
            pass #nothing required
        else:
            raise NotImplementedError("Only modbus function codes 3,6,16 are implimented.")

class ModbusRTU(Modbus):
    '''
    A subset of a modbus RTU master library, only impliments modbus functions:
    3: Read Holding Register(s)
    6: Write Holding Register
    16: Write Multiple Holding Registers
    '''

    def __init__(self, address, port, **kwargs):
        self.address = address
        #watlow suggests using 0.012 char send time for buads greater than 19200
        databits, stopbits = kwargs.get('databits', 8), kwargs.get('stopbits', 1)
        baud = kwargs.get('baud', 9600)
        self.pause = 3.5 * (((databits + stopbits + 2)/ baud) if baud < 19200 else 0.012)
        self.serial = serial.Serial(
            port=port,
            baudrate=baud,
            bytesize=databits,
            parity=kwargs.get('parity', 'N'),
            stopbits=stopbits,
            timeout=kwargs.get('timeout', 1)
        )

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def close(self):
        '''
        Close the serial port.
        '''
        self.serial.close()

    def __calc_crc(self, data):
        '''
        calculate the CRC16
        '''
        crc = 0xFFFF
        for i in data:
            crc = crc ^ ord(i)
            for j in xrange(8):
                tmp = crc & 1
                crc = crc >> 1
                if tmp:
                    crc = crc ^ 0xA001
        return ((crc % 256) << 8) + (crc >> 8) #swap byte order

    def __check_crc(self, data, crc):
        '''
        check a given set of data against a given crc value
        '''
        crc = (crc[0] << 8) + crc[1]
        if crc != self.__calc_crc(data):
            raise ModbusError("The CRCs do not match.")

    def interact(self, packet):
        crc = struct.pack(">H", self.__calc_crc(packet))
        self.serial.write(packet + crc)
        time.sleep(self.pause)
        head = self.serial.read(2)
        if len(head) == 0:
            raise ModbusError("The slave device did not respond.")
        raddress = struct.unpack('>B', head[0])[0]
        fcode = struct.unpack('>B', head[1])[0]
        if fcode == 16 or fcode == 6:
            body = self.serial.read(4)
        elif fcode == 3:
            body = self.serial.read(1)
            body += self.serial.read(struct.unpack('>B', body)[0])
        elif fcode > 127:
            body = self.serial.read(1)
        else:
            raise NotImplementedError("Only modbus function codes 3,6,16 are implimented.")
        rcrc = struct.unpack('>H', self.serial.read(2))[0]
        ccrc = self.__calc_crc(head+body)
        if self.address != raddress:
            shex = ":".join(["{:02x}".format(ord(c)) for c in packet+crc])
            rhex = ":".join(["{:02x}".format(ord(c)) for c in head+body+rcrc])
            raise ModbusError("Address error; Sent=%s, Recieved=%s" % (shex, rhex))
        if rcrc != ccrc:
            shex = ":".join(["{:02x}".format(ord(c)) for c in packet+crc])
            rhex = ":".join(["{:02x}".format(ord(c)) for c in head+body+rcrc])
            raise ModbusError("CRC error; Sent=%s, Recieved=%s" % (shex, rhex))
        return head + body

class ModbusTCP(Modbus):
    '''
    A subset of a modbus TCP master library, only impliments modbus functions:
    3: Read Holding Register(s)
    6: Write Holding Register
    16: Write Multiple Holding Registers
    '''

    def __init__(self, address, host, port=502, timeout=5):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.socket.settimeout(timeout)
        self.socket.setblocking(True)
        self.socket.connect((host, port))
        self.packet_id = 1
        self.address = address

    def __del__(self):
        self.close()

    def close(self):
        '''
        Close the tcp socket.
        '''
        self.socket.close()

    def __make_mbap(self, length):
        '''
        make the modbus mbap
        '''
        return struct.pack(">3H", self.packet_id, 0, length)

    def interact(self, packet):
        #self.shex = ":".join(["{:02x}".format(ord(c)) for c in packet])
        self.socket.send(self.__make_mbap(len(packet)) + packet)
        mbap_raw = self.socket.recv(6)
        if len(mbap_raw) == 0:
            raise ModbusError("The controller did not respond to the request (MBAP length = 0)")
        if len(mbap_raw) != 6:
            ttp = (len(mbap_raw), mbap_raw)
            raise ModbusError("MBAP length error; expected:6, got:%s (%r)" % ttp)
        mbap = struct.unpack('>3H', mbap_raw)
        body = self.socket.recv(mbap[2])
        if mbap[0] != self.packet_id:
            ttp = (self.packet_id, mbap[0], mbap_raw)
            raise ModbusError("MBAP id error; expected:%r, got:%r (%r)" % ttp)
        #self.packet_id = self.packet_id + 1 if self.packet_id < 65536 else 0
        return body
