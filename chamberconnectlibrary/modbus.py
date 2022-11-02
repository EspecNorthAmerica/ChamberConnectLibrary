'''
Copyright (C) Espec North America, INC. - All Rights Reserved
Written by Myles Metzler mmetzler@espec.com, Feb. 2016
Partial modbus implimantation for communicating with watlow controllers (input/holding registers only)

Updated: Oct 2020, 2022
Modified and updated for Python 3.6+ by Paul Nong-Laolam  <pnong-laolam@espec.com>

Note: The original source code written for Python 2.7.x by Myles Metzler 
      To set this library available for Python 3, the entire set of source codes
      have been updated to support Python 3. 

      Some changes were made within the Python 3 itself and this code as updated 
      to reflect those changes. 

      Code has been completely tested on Python 3.6.8 and Python 3.7.3. 

Updated: July 2022
        -- bug fixes and modifications to run on Python 3.6.8 and above 
        -- completely tested on Python 3.9+ 
'''
#pylint: disable=W0703
import socket
import struct
import time
import collections
import serial, os

try:
    collectionsAbc = collections.abc 
except AttributeError:
    collectionsAbc = collections 

class ModbusError(Exception):
    '''Generic Modbus exception.'''
    pass

class Modbus(object):
    '''
    A subset of a modbus master library, only impliments modbus functions:
    3: Read Holding Register(s)
    4: Read Input Register(s)
    6: Write Holding Register
    16: Write Multiple Holding Registers
    '''
    
    def __init__(self, address, *args, **kwargs):
        self.low_word_first = kwargs.get('low_word_first', True)
        self.retry = kwargs.get('retry', False)
        self.address = address
        self.error_messages = {
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

    def read_input(self, register, count=1):
        '''
        Read input register(s)
        Args:
            register (int): The modbus register to read
            count (int): The number of modbus registers to read (defaul=1)
        Returns:
            list. unsigned 16bit integers
        '''
        # setting raw package 
        packet = self._make_packet(4, register, count)

        try:
            rval = self.interact(packet)

        except ModbusError:
            if self.retry:
                rval = self.interact(packet)
            else:
                raise

        return self._decode_packet(rval, packet)

    def read_input_signed(self, register, count=1):
        '''
        Read some signed short(s)
        Args:
            register (int): The modbus register to read
            count (int): The number of modbus registers to read (default=1)
        Returns:
            list. signed 16bit integers
        '''
        vals = self.read_input(register, count)

        return [struct.unpack('h', struct.pack('H', val))[0] for val in vals]

    def read_input_float(self, register, count=1):
        '''
        Read some floating point values from 2 adjacent modbus registers
        Args:
            register (int): the first register to start reading at.
            count (int): the number of floats to read (2*count will actually be read)
        Returns:
            list. 32bit floats
        '''
        val = self.read_input(register, count*2)
        fidx, sidx = (0, 1) if self.low_word_first else (1, 0)

        return [
            round(struct.unpack('f', struct.pack('HH', val[i+fidx], val[i+sidx]))[0], 1)
            for i in range(0, count*2, 2)
        ]

    def read_input_string(self, register, count):
        '''
        Read a string
        Args:
            register (int): The register to start reading from
            count(int): The number of registers to read (length of string)
        Returns:
            str
        '''
        val = self.read_input(register, count)

        rstring = ""
        for char in val:
            if char is not 0:
                rstring = rstring + chr(char)

        return rstring

    def read_holding(self, register, count=1):
        '''
        Read holding register(s)
        Args:
            register (int): The modbus register to read
            count (int): The number of modbus registers to read (default=1)
        Returns:
            list. unsigned 16bit integers
        '''
        packet = self._make_packet(3, register, count)

        try:
            rval = self.interact(packet) # call def interact(self,pkt)   <line 593> 

        except ModbusError:
            if self.retry:
                rval = self.interact(packet)

            else:
                raise

        return self._decode_packet(rval, packet)

    def read_holding_signed(self, register, count=1):
        '''
        Read some signed short(s)
        Args:
            register (int): The modbus register to read
            count (int): The number of modbus registers to read (default=1)
        Returns:
            list. signed 16bit integers
        '''
        vals = self.read_holding(register, count)

        return [struct.unpack('h', struct.pack('H', val))[0] for val in vals]

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

        fidx, sidx = (0, 1) if self.low_word_first else (1, 0) # read reg 0, then reg 1 

        return [
            round(struct.unpack('f', struct.pack('HH', val[i+fidx], val[i+sidx]))[0], 1)
            for i in range(0, count*2, 2)
        ]

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
        Write to holding 16bit register(s), accepts single values or lists of values
        Args:
            register (int): register(s) to write to
            value (int or list(int)): value(s) to write,
        '''
        packettype = 16 if isinstance(value, collectionsAbc.Iterable) else 6
        packet = self._make_packet(packettype, register, value)

        try:
            rval = self.interact(packet)

        except ModbusError:
            if self.retry:
                rval = self.interact(packet)
                #rval = (self.interact(packet)).decode('utf-8', 'replace')
            else:
                raise

        self._decode_packet(rval, packet)

    def write_holding_signed(self, register, value):
        '''
        Write to signed 16bit holding register(s), accepts single values or lists of values
        Args:
            register (int): register(s) to write to
            value (int or list(int)): value(s) to write,
        '''
        if isinstance(value, collectionsAbc.Iterable):
            value = [0xFFFF & val for val in value]
        else:
            value = 0xFFFF & value #trim to 16bit signed int
        self.write_holding(register, value)

    def write_holding_float(self, register, value):
        '''
        Write floating point values to the controller
        Args:
            register (int): first register to write to, 2 float value will be written.
            value (float or list(float)): vlaue(s) to write to
        '''
        if isinstance(value, collectionsAbc.Iterable):
            packval = []
            for val in value:
                packval += self._pack32('f', val)
        else:
            packval = self._pack32('f', value)

        self.write_holding(register, packval)
        #self.write_holding(register, [x.encode() for x in packval])

    def write_holding_string(self, register, value, length=20, padder=0):
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
        mods.extend([padder]*length)
        self.write_holding(register.encode('ascii', 'ignore'), (mods[0:length]).encode('ascii', 'ignore'))

    def interact(self, packet):
        '''Interact with the physical interface'''
        raise NotImplementedError('ModbusTCP or ModbusRTU must be used not Modbus class')

    def read_item(self, **kwargs):
        '''
            Read paramter from the controller.

            kwargs:
                register: int (relative register value, required)
                address: int
                type: string (holding/holding_signed/holding_float/holding_string/input/
                                                                       input_signed/input_float/input_string)
                count: int (only applies to string only)
                low_word_first: bool (word order for 32 bit values)
                scalar: int (factor that read value will be devided by)
            returns:
                dict: ex: {'register':2782, 'address':1, 'type':'holding_float', 
                           'count':1, 'low_word_first':True, 'scalar':1, 'value':50.0}
        '''

        return self.read_items([kwargs])[0]

    def read_items(self, items):
        '''
            Read parameters from the controller using a list of arguments for each parameter
            params:
                list: ex: [{'register':2782, 'address':1, 'type':'holding_float', 
                                         'count':1, 'low_word_first':True, 'scalar':1}]
            returns:
                list: ex: [{'register':2782, 'address':1, 'type':'holding_float', 
                                         'count':1, 'low_word_first':True, 'scalar':1, 'value':50.0}]
        '''
        types = {
            'holding': self.read_holding,
            'holding_signed': self.read_holding_signed,
            'holding_float': self.read_holding_float,
            'holding_string': self.read_holding_string,
            'input': self.read_input,
            'input_signed': self.read_input_signed,
            'input_float': self.read_input_float,
            'input_string': self.read_input_string
        }

        for itm in items:
            self.address = itm.get('address', self.address)
            self.low_word_first = itm.get('low_word_first', self.low_word_first)
            func = itm.get('type', 'holding')
            vals = types[func](itm['register'], itm.get('count', 1)) # goes to **_make_packet()** 

            if 'string' in func:
                itm['value'] = vals

            elif isinstance(vals, list):
                for val in vals:
                    if 'scalar' in itm and itm['scalar'] != 1:
                        val = float(val) / itm['scalar']
                itm['value'] = vals if len(vals) > 1 else vals[0]

        # return items to caller
        #print (f'\n428:Result summary: \n{items}\n\n')

        return items

    def _pack32(self, format, value):
        pval = struct.unpack('HH', struct.pack(format, value))

        return list(pval) if self.low_word_first else [pval[1], pval[0]]

    def _make_packet(self, function, register, args):
        '''Make modbus request packet.'''
        if function in [3, 4, 6]:
            mod_rqst_pkt = struct.pack('>BBHH', self.address, function, register, args)
            return mod_rqst_pkt
        elif function == 16:
            margs = [self.address, function, register, len(args), len(args)*2] + list(args)
            mod_rqst_pkt = struct.pack('>BBHHB%dH' % len(args), *margs)
            return mod_rqst_pkt
        else:
            raise NotImplementedError("Supplied modbus function code is not supported.")

    def _decode_packet(self, packet, spacket):
        '''Decode the modbus request packet.'''
        fcode = struct.unpack('>B', bytes([packet[1]]))[0]
        addr = struct.unpack('>B', bytes([packet[0]]))[0]

        if self.address != addr:

            shex = ":".join("{:02x}".format(ord(c) for c in spacket))       # unmod, tested
            rhex = ":".join("{:02x}".format(ord(c) for c in packet))        # unmod, tested

            raise ModbusError(f'Address error; Sent={shex}, Received={rhex}')

        if fcode > 127:
            ecode = struct.unpack(">B", bytes([packet[2]]))[0]
            ttp = (ecode, self.error_messages.get(ecode, 'Unknown error code'))

            raise ModbusError(f'Modbus Error: Exception code = {ttp}(%s)')

        if fcode in [3, 4]: #Read input/holding register(s)
            cnt = struct.unpack(">B", bytes([packet[2]]))[0]/2

            return struct.unpack(">%dH" % cnt, packet[3:])
        elif fcode == 6:
            pass #nothing is required
        elif fcode == 16:
            pass #nothing required
        else:
            raise NotImplementedError("Supplied modbus function code is not supported.")

class ModbusRTU(Modbus):
    '''
    A subset of a modbus RTU master library, only impliments modbus functions:
    3: Read Holding Register(s)
    4: Read Input Register(s)
    6: Write Holding Register
    16: Write Multiple Holding Registers
    '''
    def __init__(self, address, port, **kwargs):
        super(ModbusRTU, self).__init__(address, port, **kwargs)
        #watlow suggests using 0.012 char send time for buads greater than 19200
        databits, stopbits = kwargs.get('databits', 8), kwargs.get('stopbits', 1)
        baud = kwargs.get('baud', 38400)
        port='/dev/ttyUSB0'   # set for testing: TO BE COMMENTED OUT FOR PRODUCTION 
        # calculated pause time does not work on the Watlow F4T, using watlow recomended delay...
        #self.pause = 3.5 * (((databits + stopbits + 2)/ baud) if baud < 19200 else 0.012)
        self.pause = 0.03
        self.serial = serial.Serial(
            port=port,
            baudrate=baud,
            bytesize=databits,
            parity=kwargs.get('parity', 'N'),
            stopbits=stopbits,
            timeout=kwargs.get('timeout', 3)
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
    def _calc_crc(self, data):
        '''
        calculate the CRC16
        '''
        crc = 0xFFFF

        # set to test in Python 3+ environment; remove for production 
        #for k in data: print ('   byte = {}    value = {}'.format(bytes([k]), k))

        for i in data:
            crc ^= i     # NOTES: Python 3 stores CRC strings in bytes

            #print (f'\n564: "crc ^= i" = {crc}')     # remove for production 

            for _ in range(8):
                tmp = crc & 1

                #print (f'\n570: crc & 1 = {tmp}')    # remove for production

                crc = crc >> 1

                #print ('\n575: crc >> 1 = {crc}')    # remove for production 

                if tmp:
                    crc ^= 0xA001    # crc = crc ^ 0xA001

                # set for testing in Python 3+ environment; remove for production 
                #print (f'\n534: Value of "crc ^= 0xA001" = {crc}')

        #print (f'\n584: (((crc % 256) << 8) + (crc >> 8)) = {(((crc % 256) << 8) + (crc >> 8))}')
        # remove or comment out after testing.

        return ((crc % 256) << 8) + (crc >> 8) #swap byte order

    def interact(self, packet):

        crc = struct.pack('>H', self._calc_crc(packet))

        self.serial.write(packet + crc)
        time.sleep(self.pause)
        head = self.serial.read(2)

        if len(head) == 0:
            raise ModbusError("The slave device did not respond.")

        raddress = struct.unpack('>B', bytes([head[0]]))[0]
        fcode = struct.unpack('>B', bytes([head[1]]))[0]

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
        ccrc = self._calc_crc(head+body)

        if self.address != raddress:
            shex = ":".join(["{:02x}".format(ord(c)) for c in packet+crc])
            rhex = ":".join(["{:02x}".format(ord(c)) for c in head+body+rcrc])

            raise ModbusError(f'Address error; Sent={shex}, Recieved={rhex}')

        if rcrc != ccrc:
            shex = ":".join(["{:02x}".format(ord(c)) for c in packet+crc])
            rhex = ":".join(["{:02x}".format(ord(c)) for c in head+body+rcrc])

            raise ModbusError(f'CRC error; Sent={shex}, Recieved={rhex}')

        return head + body

class ModbusTCP(Modbus):
    '''
    A subset of a modbus TCP master library, only impliments modbus functions:
    3: Read Holding Register(s)
    4: Read Input Register(s)
    6: Write Holding Register
    16: Write Multiple Holding Registers
    '''
    def __init__(self, address, host, port=502, **kwargs):
        super(ModbusTCP, self).__init__(address, host, **kwargs)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(5.0)
        self.socket.setblocking(True)
        self.socket.connect((host, port))
        self.packet_id = 1
        time.sleep(0.1)

    def __del__(self):
        self.close()

    def close(self):
        '''
        Close the tcp socket.
        '''
        self.socket.close()
        time.sleep(0.1)

    def _make_mbap(self, length):
        '''
        make the modbus mbap
        '''
        return struct.pack(">3H", self.packet_id, 0, length)

    def interact(self, packet):
        '''
        interact with the slave device
        '''
        self.socket.send(self._make_mbap(len(packet)) + packet)
        mbap_raw = self.socket.recv(6)


        if len(mbap_raw) == 0:
            raise ModbusError("The controller did not respond to the request (MBAP length = 0)")

        if len(mbap_raw) != 6:
            ttp = (len(mbap_raw), mbap_raw)
            raise ModbusError(f'MBAP length error; expected:6, got:{ttp} (%r)')

        mbap = struct.unpack('>3H', mbap_raw)
        body = self.socket.recv(mbap[2])

        if mbap[0] != self.packet_id:
            ttp = (self.packet_id, mbap[0], mbap_raw)
            raise ModbusError(f'MBAP id error; expected:%r, got:{ttp} (%r)')
        #self.packet_id = self.packet_id + 1 if self.packet_id < 65535 else 0
        return body

if __name__ == "__main__":
    '''main program for texting local functions
       no local functions needed for testing...
    '''
    # pass 
    # no tests on local functions warranted
    # refer to sample programs in build/scripts-3.7 folder
    pass

