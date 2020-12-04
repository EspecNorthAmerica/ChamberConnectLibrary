'''
Copyright (C) Espec North America, INC. - All Rights Reserved
Written by Myles Metzler mmetzler@espec.com, Feb. 2016
Partial modbus implimantation for communicating with watlow controllers (input/holding registers only)

Updated:
Modified by Paul Nong-Laolam  pnong-laolam@espec.com, Oct 2020
The original source code written for Python 2.7.x by Myles Metzler has been modified 
to support Python 3. Code has been completely tested on Python 3.5.3 and Python 3.6.8. 
'''
#pylint: disable=W0703
import socket
import struct
import time
import collections
import serial, os
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
            rval = (self.interact(packet)).decode('utf-8', 'replace')

        except ModbusError:
            if self.retry:
                rval = (self.interact(packet)).decode('utf-8', 'replace')
            else:
                raise

        print ('\n67: self._decode_packet(rval, packet) = {}'.format(self._decode_packet(rval, packet)))
        #yy = input('=>Press enter to continue...')

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

        str2 = '\n85: struct.upackt() ='
        print ('84: print self.read_input(register, count): {}'.format(vals))
        print ( str2 + ' {}'.format([struct.unpack('h', struct.pack('H', val))[0] for val in vals]))
        #yy = input('=>Press [ENTER]...')

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

        print ('\n102: val = {}\nfidx = {}\nsidx = {}'.format(rval, fidx,sidx))
        print ('103: {}'.format([
            round(struct.unpack('f', struct.pack('HH', val[i+fidx], val[i+sidx]))[0], 1)
            for i in range(0, count*2, 2)
        ]))
        #yy = input('=>Press [ENTER]...')

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

        print ('\n125: {}'.format(val))
        #yy = input('=>Press [ENTER]...')

        rstring = ""
        for char in val:
            if char is not 0:
                rstring = rstring + chr(char)

        print ('\n133: {}'.format(rstring))
        #yy = input('=>Press [ENTER]...')

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

        print ('\n149: Checking packet value & type: \n   Value = {}\n   Type = {}'.format(packet,type(packet)))
        #yy = input('=>Press [ENTER]...')

        try:
            rval = self.interact(packet)

            print ('\n155: "self.interact(packet)" = {}'.format(rval))
            #yy = input('=>Press [ENTER]...')

        except ModbusError:
            if self.retry:
                rval = (self.interact(packet)).decode('utf-8', 'replace')

                print ('\n162: "self.interact(packet)" = {}'.format(rval))
                #yy = input('=>Press [ENTER]...')

            else:
                raise

        print ('\n168: "self.interact(packet)" = {}'.format(self._decode_packet(rval, packet)))
        #yy = input('=>Press [ENTER]...')

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

        str2 = '\n186: "[struct.unpack(\'h\', struct.pack(\'H\', val))[0] for val in vals]"'
        print ('185: Value of "self.read_holding(register, count)" = {}'.format(vals))
        print (str2 + ' = {}'.format([struct.unpack('h', struct.pack('H', val))[0] for val in vals]))
        #yy = input('=>Press [ENTER]...')

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

        print ('\n202: print "self.read_holding(register, count*2)" = {}'.format(val))
        #yy = input('=>Press [ENTER]...')

        fidx, sidx = (0, 1) if self.low_word_first else (1, 0) # read reg 0, then reg 1 

        print ('\n207: Register 1 = {}; register 2 = {}'.format(fidx, sidx))
        print ('208: Value read from register = {}'.format([
            round(struct.unpack('f', struct.pack('HH', val[i+fidx], val[i+sidx]))[0], 1)
            for i in range(0, count*2, 2)
        ]))
        #yy = input('=>Press [ENTER]...')
        

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

        # start probe block
        print ('\n232: print "self.read_holding(register, count)" = {}'.format(val))
        #yy = input('=>Press [ENTER]...')
        # end of probe block
        rstring = ""
        for char in val:
            if char is not 0:
                rstring = rstring + chr(char)

        # start probe block
        print ('\n241: {}'.format(rstring))
        #yy = input('=>Press [ENTER]...')
        # end of probe block

        return rstring

    def write_holding(self, register, value):
        '''
        Write to holding 16bit register(s), accepts single values or lists of values
        Args:
            register (int): register(s) to write to
            value (int or list(int)): value(s) to write,
        '''
        packettype = 16 if isinstance(value, collections.Iterable) else 6
        packet = self._make_packet(packettype, register, value)

        print ('\n257: packettype = {}'.format(packettype))
        print ('258: packet = {}'.format(packet))
        #yy = input('=>Press [ENTER]...')
        try:
            rval = (self.interact(packet)).decode('utf-8', 'replace')

            print ('\n263: {}'.format(rval))
            #yy = input('=>Press [ENTER]...')

        except ModbusError:
            if self.retry:
                rval = (self.interact(packet)).decode('utf-8', 'replace')
            else:
                raise

        print ('\n272: doce_packet = {}'.format(self._decode_packet(rval, packet)))
        #yy = input('=>Press [ENTER]...')

        self._decode_packet(rval, packet)

    def write_holding_signed(self, register, value):
        '''
        Write to signed 16bit holding register(s), accepts single values or lists of values
        Args:
            register (int): register(s) to write to
            value (int or list(int)): value(s) to write,
        '''
        if isinstance(value, collections.Iterable):
            value = [0xFFFF & val for val in value]
        else:
            value = 0xFFFF & value #trim to 16bit signed int
        self.write_holding(register.encode('ascii', 'ignore'), value.encode('ascii', 'ignore'))

        print ('\n290: Max Hex value = {}'.format(value))
        print ('291: register holding = {}'.format(self.write_holding(register, value)))
        #yy = input('=>Press [ENTER]...')

    def write_holding_float(self, register, value):
        '''
        Write floating point values to the controller
        Args:
            register (int): first register to write to, 2 float value will be written.
            value (float or list(float)): vlaue(s) to write to
        '''
        if isinstance(value, collections.Iterable):
            packval = []
            for val in value:
                packval += self._pack32('f', val)
        else:
            packval = self._pack32('f', value)
        self.write_holding(register.encode('ascii', 'ignore'), packval.encode('ascii', 'ignore'))

        print ('\309: package value = {}'.format(packval))
        print ('310: "self.write_holding(register, packval)" = {}'.format(self.write_holding(register, packval)))
        #yy = input('=>Press [ENTER]...')

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

        print ('\n327: mods = {}'.format(mods))
        print ('328: mods.extend = {}'.format(mods.extend([padder]*length)))
        print ('329: "self.write_holding(register, mods[0:length])" = {}'.format(self.write_holding(register, mods[0:length])))
        #yy = input('=>Press [ENTER]...')

    def interact(self, packet):
        '''Interact with the physical interface'''
        raise NotImplementedError('ModbusTCP or ModbusRTU must be used not Modbus class')

    def read_item(self, **kwargs):
        '''
            Read paramter from the controller.
            
            kwargs:
                register: int (relative register value, required)
                address: int
                type: string (holding/holding_signed/holding_float/holding_string/input/input_signed/input_float/input_string)
                count: int (only applies to string only)
                low_word_first: bool (word order for 32 bit values)
                scalar: int (factor that read value will be devided by)
            returns:
                dict: ex: {'register':2782, 'address':1, 'type':'holding_float', 'count':1, 
                                                                         'low_word_first':True, 'scalar':1, 'value':50.0}
        '''
        print ('351: "self.read_items([kwargs])[0]" = {}'.format(self.read_items([kwargs])[0]))
        #yy = input('=>Press [ENTER]...')

        return self.read_items([kwargs])[0]

    def read_items(self, items):
        '''
            Read parameters from the controller using a list of arguments for each parameter
            params:
                list: ex: [{'register':2782, 'address':1, 'type':'holding_float', 'count':1, 'low_word_first':True, 'scalar':1}]
            returns:
                list: ex: [{'register':2782, 'address':1, 'type':'holding_float', 'count':1, 'low_word_first':True, 
                                                                                                      'scalar':1, 'value':50.0}]
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

        print ('\n376: Packet cmd passed from call function:\n{}'.format(items))
        #yy=input('=>Press [ENTER]...')

        for itm in items:
            self.address = itm.get('address', self.address)
            self.low_word_first = itm.get('low_word_first', self.low_word_first)
            func = itm.get('type', 'holding')
            vals = types[func](itm['register'], itm.get('count', 1))

            print ('\n385:\n  Modbus addr = {}\n  low_word_first = {}\n  type = {}\n  Value read from F4T = {}'
                                                     .format(self.address, self.low_word_first, func, vals ))
            #yy = input('=>Press [ENTER]...')         

            if 'string' in func:
                itm['value'] = vals

                print ('\n392: if string found in type = {}'.format(itm['value']))
                #yy = input('=>Press [ENTER]...')         

            elif isinstance(vals, list):
                for val in vals:
                    if 'scalar' in itm and itm['scalar'] != 1:
                        val = float(val) / itm['scalar']
                itm['value'] = vals if len(vals) > 1 else vals[0]

        print ('\n401: Result before yielding to main:\n{}\n\n'.format(items))
 
        return items

    def _pack32(self, format, value):
        pval = struct.unpack('HH', struct.pack(format, value))

        print ('\n408: pre process = {}'.format(pval))
        print ('409: post process = {}'.format(list(pval) if self.low_word_first else [pval[1], pval[0]]))
        #yy=input('=>Press [ENTER]...')

        return list(pval) if self.low_word_first else [pval[1], pval[0]]

    def _make_packet(self, function, register, args):
        '''Make modbus request packet.'''
        if function in [3, 4, 6]:
            mod_rqst_pkt = struct.pack('>BBHH', self.address, function, register, args)

            str2 = '\n419: struct.pack (addr, func, reg, arg) into bytes: '
            print (str2 + ' = {}'.format(mod_rqst_pkt))
            #yy=input('=>Press [ENTER]...')

            return mod_rqst_pkt
        elif function == 16:
            margs = [self.address, function, register, len(args), len(args)*2] + list(args)
            mod_rqst_pkt = struct.pack('>BBHHB%dH' % len(args), *margs)
            print ('\n427: "struct.pack" = {}'.format(struct.pack('>BBHHB%dH' % len(args), *margs)))
            #yy=input('=>Press [ENTER]...')
            return mod_rqst_pkt
        else:
            raise NotImplementedError("Supplied modbus function code is not supported.")

    def _decode_packet(self, packet, spacket):
        '''Decode the modbus request packet.'''
        fcode = struct.unpack('>B', bytes([packet[1]]))[0]
        addr = struct.unpack('>B', bytes([packet[0]]))[0]

        print ('\n438: "struct.unpack(">B", packet[1])[0]" = {}'.format(fcode))
        print ('439: "struct.unpack(">B", packet[0])[0]" = {}'.format(addr))
        #yy=input('=>Press [ENTER]...')
        if self.address != addr:

            shex = ":".join("{:02x}".format(ord(c) for c in spacket))       # unmod, tested
            rhex = ":".join("{:02x}".format(ord(c) for c in packet))        # unmod, tested 

            print ('\n446: Print ":".join("{:02x}".format(ord(c) for c in spacket)) = {}'.format(shex))
            print ('447: Print ":".join("{:02x}".format(ord(c) for c in packet)) = {}'.format(rhex))
            #yy=input('=>Press [ENTER]...')

            raise ModbusError('Address error; Sent={}, Recieved={}'.format(shex, rhex))

        if fcode > 127:
            ecode = struct.unpack(">B", bytes([packet[2]]))[0]
            ttp = (ecode, self.error_messages.get(ecode, 'Unknown error code'))

            print ('\n456: struct.unpack(">B", packet[2])[0] = {}'.format(ecode))
            print ('457: (ecode, self.error_messages.get(ecode, \'Unknown error code\')) = {}'.format(ttp))
            #yy=input('=>Press [ENTER]...')

            raise ModbusError('Modbus Error: Exception code = %d(%s)' % ttp)

        if fcode in [3, 4]: #Read input/holding register(s)
            cnt = struct.unpack(">B", bytes([packet[2]]))[0]/2
            print ('\n464: "struct.unpack(">%dH" % cnt, packet[3:])" = {}'.format(struct.unpack(">%dH" % cnt, packet[3:])))
            #yy=input('=>Press [ENTER]...')
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

        print ('\n515: Verifying raw data packet:\n  value = {}; length = {}'.format(data, len(data)))
        print ('516: Elements in bytes and value:') 
        for k in data: print ('   byte = {}    value = {}'.format(bytes([k]), k))
        #yy = input('=>Press [ENTER]...')

        for i in data:
            crc ^= i     # Python 3 stores CRC strings in bytes 
         
            print ('\n523: "crc ^= i" = {}'.format(crc))
            #yy = input('=>Press [ENTER]...')

            for _ in range(8):
                tmp = crc & 1
                print ('528: crc & 1 = {}'.format(tmp))
                crc = crc >> 1
                print ('530: crc >> 1 = {}'.format(crc))
                if tmp:
                    crc ^= 0xA001    # crc = crc ^ 0xA001

                print ('\n534: Value of "crc ^= 0xA001" = {}'.format(crc))

        print ('\n536: (((crc % 256) << 8) + (crc >> 8)) = {}'.format(((crc % 256) << 8) + (crc >> 8)))
        #yy = input('=>Press [ENTER]....')
        return ((crc % 256) << 8) + (crc >> 8) #swap byte order

    def interact(self, packet):

        print ('\n542: Packet passed from read_holding method: {}'.format(packet))
        #yy=input('=>Press [ENTER]...') 

        crc = struct.pack('>H', self._calc_crc(packet))

        print ('\n547: CRC: string = {}, length = {}, type = {}, value = {},{}'.format(crc, len(crc), type(crc), crc[0], crc[1]))
        #yy=input('=>Press [ENTER]...') 

        self.serial.write(packet + crc)
        time.sleep(self.pause)
        head = self.serial.read(2)

        print ('\n554: self.serial.write(packet + crc) = {}'.format(self.serial.write(packet + crc)))
        print ('555: send sleep time to ctlr >> time.sleep(self.pause) = {}'.format(time.sleep(self.pause)))
        #yy=input ('=>Press [ENTER]...') 

        if len(head) == 0:
            raise ModbusError("The slave device did not respond.")

        raddress = struct.unpack('>B', bytes([head[0]]))[0] 
        fcode = struct.unpack('>B', bytes([head[1]]))[0]

        print ('\n564: Type: {}'.format(type(head)))
        print ('565: Result of "struct.unpack(>B, head[0])[0]" = {}'.format(raddress))
        print ('566: Result of "struct.unpack(>B, head[1])[0]" = {}'.format(fcode))
        #yy=input ('=>Press [ENTER]...') 

        if fcode == 16 or fcode == 6:
            body = self.serial.read(4)

            print ('\n571: if fcode = 16 or 6, print: {}'.format(body))
            print ('572: Result of "struct.unpack(>B, head[1])[0]" = {}'.format(fcode))
            #yy=input ('=>Press [ENTER]...') 

        elif fcode == 3:
            body = self.serial.read(1)

            print ('\n579: if fcode = 3, self.serial.read(1) = {}'.format(body))

            body += self.serial.read(struct.unpack('>B', body)[0])

            print ('583: Byte value of "self.serial.read(struct.unpack(\'>B\', body)[0])" = {}'.format(body))
            #yy=input('=>Press [ENTER]...') 
    
        elif fcode > 127:
            body = self.serial.read(1)

            print ('\n589: if fcode = 127, print: {}'.format(body))
            #yy=input('=>Press [ENTER]...') 

        else:
            raise NotImplementedError("Only modbus function codes 3,6,16 are implimented.")

        rcrc = struct.unpack('>H', self.serial.read(2))[0]
        ccrc = self._calc_crc(head+body)

        print ('\n698: If fcode is none other, "struct.unpack(\'>H\', self.serial.read(2))[0]]" = {}'.format(rcrc))
        print ('599: "self._calc_crc(head+body)" = {}'.format(ccrc))
        #yy=input('=>Press [ENTER]...') 

        if self.address != raddress:
            shex = ":".join(["{:02x}".format(ord(c)) for c in packet+crc])
            rhex = ":".join(["{:02x}".format(ord(c)) for c in head+body+rcrc])

            print ('\n606: shex = {}'.format(shex))
            print ('607: rhex = {}'.format(rhex))

            raise ModbusError('Address error; Sent={}, Recieved={}'.format(shex, rhex))

        if rcrc != ccrc:
            shex = ":".join(["{:02x}".format(ord(c)) for c in packet+crc])
            rhex = ":".join(["{:02x}".format(ord(c)) for c in head+body+rcrc])

            print ('\n615: shex = {}'.format(shex))
            print ('616: rhex = {}'.format(rhex))

            raise ModbusError("CRC error; Sent=%s, Recieved=%s" % (shex, rhex))

        print ('\n620: Result of: head + body = {} + {} = {}'.format(head, body, head + body))
        #yy = input('=>Press [ENTER]...')

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
        #self.socket.settimeout(timeout)
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
            raise ModbusError("MBAP length error; expected:6, got:%s (%r)" % ttp)

        mbap = struct.unpack('>3H', mbap_raw)
        body = self.socket.recv(mbap[2])

        if mbap[0] != self.packet_id:
            ttp = (self.packet_id, mbap[0], mbap_raw)
            raise ModbusError("MBAP id error; expected:%r, got:%r (%r)" % ttp)
        #self.packet_id = self.packet_id + 1 if self.packet_id < 65535 else 0
        return body

if __name__ == '__main__':
    '''
    This main program can make two separate calls based on the modified code below.
    It can make a method call to ModbusRTU module using the serial communication 
    protocol; or it can make a call to ModbusTCP module using the TCP protocol. 

    Test programmer will need to make this change in the following lines of code. 
    Default call is: ModbusRTU. For TCP usage, programmer must manually edit the 
    TCP IP address found on the F4T controller.  
    '''
    pkt = [
        { 'register':2942, 
          'address':1, 
          'type':'holding_float', 
          'count':1, 
          'low_word_first':True, 
          'scalar':1 }
    ]
    os.system('clear') 
    print ('Order of execution and method call...')

    # calling ModbusTCP module for TCP communication
    # tested on: Python 3.6.8 and Python 3.5.x 
    #
    # calling ModbusRTU module for serial communication 
    tst = ModbusRTU(1, 3, baud=38400, low_word_first=True)

    #addr, host = '192.168.0.194', '192.168.0.194'
    #addr, host = '10.30.200.232', '10.30.200.232'
    #addr, host = '10.30.100.56', '10.30.100.56'
    #tst = ModbusTCP(addr, host, low_word_first=True)

    tmp = tst.read_items(pkt)

    #print (tmp) 
    #for i in tmp:
    #    print('{}\n'.format(i)) # pylint: disable=E1601, here
