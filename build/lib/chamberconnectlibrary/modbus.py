'''
Copyright (C) Espec North America, INC. - All Rights Reserved
Written by Myles Metzler mmetzler@espec.com, Feb. 2016

Partial modbus implimantation for communicating with watlow controllers (holding registers only)
'''
import serial, socket, struct, time

class ModbusError(Exception):
    '''Generic Modbus exception.'''
    pass

class modbus:
    '''A subset of a modbus master library, only impliments modbus functions:
     3: Read Holding Register(s)
     6: Write Holding Register
     16: Write Multiple Holding Registers'''
    errorMessages = {1: 'Illegal Function',
                     2: 'Illegal Data Address',
                     3: 'Illegal Data Value',
                     4: 'Slave Device Failure',
                     5: 'Acknowledge',
                     6: 'Slave Device Busy',
                     7: 'Negative Acknowledge',
                     8: 'Memory Parity Error',
                     10:'Gateway Path Unavalable',
                     11:'Gateway Target Device Failed To Respond'}


    def readHolding(self,register,count=1):
        '''
        Read holding register(s)

        Args:
            register (int): The modbus register to read
            count (int): The number of modbus registers to read (default=1)

        Returns:
            tuple. 16bit integers
        '''
        packet = self.makePacket(3,register,count)
        rval = self.interact(packet)
        return self.decodePacket(rval, packet)

    def readFloat(self, register, count=1):
        '''
        Read some floating point values from 2 adjacent modbus registers

        Args:
            register (int): the first register to start reading at.
            count (int): the number of floats to read (2*count will actually be read)

        Returns:
            tuple. 32bit floats
        '''
        val = readHolding(self,register,count*2)
        return [round(unpack('f',pack('HH',val[i], val[i+1]))[0],1) for i in range(0,count*2,2)]

    def readString(self,register,count):
        '''
        Read a string

        Args:
            register (int): The register to start reading from
            count(int): The number of registers to read (length of string)

        Returns:
            str
        '''
        val = readHolding(self,register,count)
        str = ""
        for x in val:
            if x is not 0:
                str = str + chr(x)
        return str

    def writeHolding(self,register,value):
        '''
        Write to holding register(s), accepts single values or lists of values

        Args:
            register (int): register(s) to write to
            value (int or list(int)): value(s) to write,

        Return:
            None
        '''
        packet = self.makePacket(16 if type(value) in [list,tuple] else 6,register,value)
        rval = self.interact(packet)
        self.decodePacket(rval, packet)

    def writeFloat(self, register, value):
        '''
        Write floating point values to the controller

        Args:
            register (int): first register to write to, 2 float value will be written.
            value (float or list(float)): vlaue(s) to write to

        Return:
            None
        '''
        if type(value) in [list,tuple]:
            self.writeHolding(''.join([unpack('HH',pack('f',val)) for val in value]))
        else:
            self.writeHolding(unpack('HH',pack('f',value)))

    def writeString(self, register, value, length=20):
        '''
        Write a string to the controller

        Args:
            register (int): first register to wrote to
            value (str): The string to write
            length (int): The string will be padded or truncated to this length.

        Return:
            None
        '''
        mods = [ord(c) for c in val]
        mods.extend([0]*length)
        self.writeHolding(register,mods[0:length])

    def interact(self,packet):
        '''Interact with the physical interface'''
        raise NotImplementedError("Do not use this class directly, instead instantiate modbusTCP or modbusRTU")

    def makePacket(self,function,register,args):
        '''Make modbus request packet.'''
        if function == 3:
            return struct.pack(">BBHH",self.address,function,register,args)
        elif function == 6:
            return struct.pack(">BBHH",self.address,function,register,args)
        elif function == 16:
            data = struct.pack(">BBHHB",self.address,function,register,len(args),len(args)*2)
            for v in args:
                data += struct.pack(">H",v)
            return data
        else:
            raise NotImplementedError("Only modbus function codes 3,6,16 are implimented.")

    def decodePacket(self,packet, spacket):
        '''Decode the modbus request packet.'''
        fc = struct.unpack(">B",packet[1])[0]
        addr = struct.unpack(">B",packet[0])[0]
        if self.address != addr:
            sendHex = ":".join("{:02x}".format(ord(c) for c in spacket))
            recHex = ":".join("{:02x}".format(ord(c) for c in packet))
            raise ModbusError("Address error; Sent=%s, Recieved=%s" % (sendHex, recHex))
        if fc > 127:
            excCode = struct.unpack(">B",packet[2])[0]
            raise ModbusError("Modbus Error: Exception code = %d(%s)" % (excCode, self.errorMessages.get(excCode,'Unknown error code')))

        if fc == 3: #Read holding register(s)
            cnt = struct.unpack(">B",packet[2])[0]/2
            return struct.unpack(">%dH"%cnt,packet[3:])
        elif fc == 6:
            pass #nothing is required
        elif fc == 16:
            pass #nothing required
        else:
            raise NotImplementedError("Only modbus function codes 3,6,16 are implimented.")

class modbusRTU(modbus):
    def __init__(self, address, port, baud=9600, parity='N', databits=8, stopbits=1, timeout=1):
        self.address = address
        self.pause = 3.5 * (((databits + stopbits + 2)/ baud) if baud < 19200 else 0.012) #watlow suggests using 0.012 char send time for buads greater than 19200
        self.serial = serial.Serial(port=port,baudrate=baud,bytesize=databits,parity=parity,stopbits=stopbits,timeout=timeout)

    def __del__(self):
        try:
            self.close()
        except:
            pass

    def close(self):
        self.serial.close()

    def calc_crc(self,data):
        '''calculate the CRC16'''
        crc = 0xFFFF
        for i in data:
            crc = crc ^ ord(i)        
            for j in xrange(8):
                tmp = crc & 1
                crc = crc >> 1
                if tmp:
                    crc = crc ^ 0xA001
        return ((crc % 256) << 8) + (crc >> 8) #swap byte order

    def check_crc(self,data,crc):
        crc = (crc[0] << 8) + crc[1]
        if (crc != self.calc_crc(data)):
            raise ModbusError("The CRCs do not match.")

    def interact(self,packet):
        crc = struct.pack(">H",self.calc_crc(packet))
        self.serial.write(packet + crc)
        time.sleep(self.pause)
        head = self.serial.read(2)
        if len(head) == 0:
            raise ModbusError("The slave device did not respond.")
        raddress = struct.unpack('>B', head[0])[0]
        fc = struct.unpack('>B',head[1])[0]
        if fc == 16 or fc == 6:
            body = self.serial.read(4)
        elif fc == 3:
            body = self.serial.read(1)
            body += self.serial.read(struct.unpack('>B',body)[0])
        elif fc > 127:
            body = self.serial.read(1)
        else:
            raise NotImplementedError("Only modbus function codes 3,6,16 are implimented.")
        rcrc = struct.unpack('>H',self.serial.read(2))[0]
        ccrc = self.calc_crc(head+body)
        if self.address != raddress:
            sendHex = ":".join(["{:02x}".format(ord(c)) for c in (packet+crc)])
            recHex = ":".join(["{:02x}".format(ord(c)) for c in (head+body+rcrc)])
            raise ModbusError("Address error; Sent=%s, Recieved=%s" % (sendHex, recHex))
        if rcrc != ccrc:
            sendHex = ":".join(["{:02x}".format(ord(c)) for c in (packet+crc)])
            recHex = ":".join(["{:02x}".format(ord(c)) for c in (head+body+rcrc)])
            raise ModbusError("CRC error; Sent=%s, Recieved=%s" % (sendHex, recHex))
        return head + body

class modbusTCP(modbus):
    def __init__(self,address,host,port=502,timeout=5):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.socket.settimeout(timeout)
        self.socket.setblocking(True)
        self.socket.connect((host,port))
        self.id = 1
        self.address = address

    def __del__(self):
        self.close()

    def close(self):
        self.socket.close()

    def makeMBAP(self,length):
        return struct.pack(">3H",self.id,0,length)

    def interact(self,packet):
        self.sendHex = ":".join(["{:02x}".format(ord(c)) for c in packet])
        self.socket.send(self.makeMBAP(len(packet)) + packet)
        mbap_raw = self.socket.recv(6)
        if len(mbap_raw) == 0:
            raise ModbusError("The controller did not respond to the request (MBAP length = 0)")
        if len(mbap_raw) != 6:
            raise ModbusError("MBAP length error; expected:6, got:%s (%r)" % (len(mbap_raw),mbap_raw))
        mbap = struct.unpack('>3H',mbap_raw)
        body = self.socket.recv(mbap[2])
        if mbap[0] != self.id:
            raise ModbusError("MBAP id error; expected:%r, got:%r (%r)" % (self.id, mbap[0], mbap_raw))
        #self.id = self.id + 1 if self.id < 65536 else 0
        return body

def float_to_mod(val):
    '''Convert a float to a 2 element list of unsigned ints for modbus_tk.'''
    return struct.unpack('HH',struct.pack('f',val))

if __name__ == '__main__':
    mb = modbusRTU(1,'\\.\COM4',38400)
    #mb = modbusTCP(1,"10.30.100.112")
    print mb.readHolding(1328)
    mb.writeHolding(2782,float_to_mod(110))
    mb.writeHolding(16594,63)
