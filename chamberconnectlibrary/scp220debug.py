'''
Copyright (C) Espec North America, INC. - All Rights Reserved
Written by Myles Metzler mmetzler@espec.com, Dec. 2017

SCP220 debug port handler.
'''
import struct
import serial

class SCP220DebugError(Exception):
    '''generic error'''
    pass

class SCP220Debug(object):
    '''
    A class used to communicate with an SCP220's debug port
    '''

    __CODE_STX = 0x02
    __CODE_ETX = 0x03

    #??1
    __DT_CLS_VER1 = 0x01
    __DT_CLS_VER2 = 0x02
    __DT_CLS_DB = 0x03
    __DT_CLS_SEQ = 0x04
    __DT_CLS_DISP1 = 0x05
    __DT_CLS_DISP2 = 0x06
    __DT_CLS_SYS = 0x07
    __DT_CLS_HARD = 0x08

    #??2
    __DT_REQ_DTL_CNCT = 0x01
    __DT_REQ_DTL_DL = 0x02
    __DT_REQ_DTL_DEV_MON = 0x11
    __DT_REQ_DTL_LDR_MON = 0x12

    #??3
    __DT_RES_DTL = 0x80
    __MAX_DATA_LEN = 2048

    DATA_TYPES = {
        'char':1, 'b_bit':2, 'uchar':2, 'int':3, 'short':3, 'ushort':4, 'w_bit':4, 'uint':4, 'long':5,
        'ulong':6, 'ptr':6, 'float':7, 'int2':8, 'long2':9, 'int3':10, 'long3':11
    }

    __BAUDS = [256000, 128000, 56000, 38400, 28800, 19200, 14400, 9600, 4800, 2400, 1200, 600, 300, 110]

    def __init__(self, **kwargs):
        self.sequence_number = 0
        baud = kwargs.get('baud', 9600)
        while (self.__BAUDS[self.sequence_number] != baud):
            self.sequence_number += 1
        self.serial = serial.Serial(
            port=kwargs.get('port'),
            baudrate=baud,
            bytesize=kwargs.get('databits', 8),
            parity=kwargs.get('parity', 'N'),
            stopbits=kwargs.get('stopbits', 1),
            timeout=kwargs.get('timeout', 3)
        )
        self.serial.flush()
        self.__test_packet()


    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


    def __message_to_list(self, itm):
        return [self.DATA_TYPES[itm['datatype']], itm['offset'], itm['dbnumber'], itm['datanumber']]


    def __build_payload(self, items):
        payload = [i for itm in items for i in self.__message_to_list(itm)]
        hdr = (self.__DT_CLS_DB, self.__DT_REQ_DTL_CNCT, len(payload)+2, len(payload)/4)
        payload = list(struct.unpack('BBBBBB', struct.pack('>BBHH', *hdr))) + payload
        return payload


    def __build_packet(self, payload):
        packet = [self.__CODE_STX, self.sequence_number, (1 << 8) - 1 - self.sequence_number, 2]
        packet += list(struct.unpack('BB', struct.pack('>H', len(payload)))) + payload + [self.__CODE_ETX]
        packet += [self.__build_checksum(packet)]
        return packet


    def __build_checksum(self, packet):
        csum = packet[1] & 0xff
        for v in packet[2:]:
            csum ^= (v & 0xff)
        return csum


    def __decode(self, data):
        blocksize = struct.unpack('>H', data[:2])[0]
        ret = []
        pos = 2
        for _ in range(blocksize):
            params = struct.unpack('>4BH', data[pos:pos + 6])
            pos += 6
            val = struct.unpack(['>b','>h','','>l'][params[4]-1], data[pos:pos + params[4]])[0]
            pos += params[4]
            ret.append({'offset':params[1], 'dbnumber':params[2], 'datanumber':params[3], 'value':val})
        return ret


    def __recieve(self):
        rxd = self.serial.read(6)
        if len(rxd) == 0:
            raise SCP220DebugError('The chamber did not respond in time.')
        rxcount = struct.unpack('>H', rxd[-2:])[0]
        rxd += self.serial.read(rxcount + 2)
        if ord(rxd[-1]) != self.__build_checksum(struct.unpack('%dB' % (len(rxd) - 1), rxd[:-1])):
            raise SCP220DebugError('Recieved checksum does not match calculated')
        return rxd[10:-2]


    def __interact(self, packet):
        self.serial.write(struct.pack('%dB' % len(packet), *packet))
        rsp = self.__recieve()
        ret = self.__decode(rsp)
        self.sequence_number += 1
        return ret


    def __test_packet(self):
        packet = self.__build_packet([self.__DT_CLS_VER1, self.__DT_REQ_DTL_CNCT, 0, 2, 0, 0])
        return self.__interact(packet)


    def close(self):
        '''
        Close the connection the the chamber
        '''
        self.serial.close()


    def read_item(self, **kwargs):
        '''
            Read paramter from the controller.
            
            kwargs:
                datatype: string see DATA_TYPES for posible values
                offset: int
                dbnumber: int
                datanumber: int
            returns:
                dict: ex: {'datatype':'long2', 'offset':0, 'dbnumber':13, 'datanumber':8, 'value':}
        '''
        return self.read_items([kwargs])[0]


    def read_items(self, items):
        '''
            Read parameters from the controller using a list of arguments for each parameter

            params:
                list: ex: [{'datatype':'long2', 'offset':0, 'dbnumber':13, 'datanumber':8}]
            returns:
                list: ex: [{'datatype':'long2', 'offset':0, 'dbnumber':13, 'datanumber':8, 'value':}]
        '''
        packet = self.__build_packet(self.__build_payload(items))
        ret = self.__interact(packet)
        for itm, rsp in zip(items, ret):
            if 'scalar' in itm:
                rsp['value'] =  float(rsp['value']) / itm['scalar']
            rsp.update(itm)
        return ret

if __name__ == '__main__':
    pkt = [
        {'datatype':'long2', 'offset':0, 'dbnumber':13, 'datanumber':8, 'scalar':256},
        {'datatype':'long2', 'offset':0, 'dbnumber':13, 'datanumber':9, 'scalar':256}
    ]
    tst = SCP220Debug(port='/dev/ttyUSB1')
    tmp = tst.read_items(pkt)
    for i in tmp:
        print i
