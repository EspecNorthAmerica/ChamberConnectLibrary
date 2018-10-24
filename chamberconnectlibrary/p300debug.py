'''
Copyright (C) Espec North America, INC. - All Rights Reserved
Written by Myles Metzler mmetzler@espec.com, Dec. 2017

SCP220 debug port handler.
'''
import struct
import serial
from chamberconnectlibrary.scp220debug import SCP220DebugError, SCP220Debug


class P300Debug(SCP220Debug):
    '''
    A class used to communicate with an P300's debug port
    '''
    DATA_TYPES = {'long':0, 'long2':1}

    def __init__(self, **kwargs):
        super(P300Debug, self).__init__(**kwargs)


    def _message_to_list(self, itm):
        ret = [itm['dbnumber'], itm['datanumber'], itm['offset'], self.DATA_TYPES[itm['datatype']]]
        ret += list(struct.unpack('BB', struct.pack('>H', itm['offset2'])))
        return ret


    def _build_payload(self, items):
        payload = [i for itm in items for i in self._message_to_list(itm)]
        hdr = (self._DT_CLS_DB, 0x06, len(payload)+2, len(payload)/5)
        payload = list(struct.unpack('6B', struct.pack('>BBHH', *hdr))) + payload
        return payload


    def _decode(self, data):
        blocksize = struct.unpack('>H', data[:2])[0]
        ret = []
        pos = 2
        for _ in range(blocksize):
            params = struct.unpack('>4BH', data[pos:pos + 6])
            pos += 6
            val = struct.unpack('>l', data[pos:pos + 4])[0]
            pos += 4
            ret.append({'offset':params[1], 'dbnumber':params[2], 'datanumber':params[3], 'value':val})
        return ret


if __name__ == '__main__':
    pkt = [
        {'datatype':'long2', 'offset':0, 'dbnumber':9, 'datanumber':42, 'offset2':0, 'scalar':1000},
        {'datatype':'long2', 'offset':0, 'dbnumber':9, 'datanumber':43, 'offset2':0, 'scalar':1000}
    ]
    tst = P300Debug(port=11, baud=38400)
    tmp = tst.read_items(pkt)
    for i in tmp:
        print i # pylint: disable=E1601
