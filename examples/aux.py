import io
import struct


RR_TEXT = {
    5: 'CNAME',
    2: 'NS',
    12: 'PTR',
    16: 'TXT',
    }

def unpack_name(buff, dict_):
    response = []
    p_bytes = 0
    first = 0
    start = buff.tell()
    while(True):
        lookahead = struct.unpack('B',buff.read(1))[0]
        high = (lookahead & 0b00111111) << 8
        
        if lookahead == 0x00:
            dict_[(start,buff.tell())] = '.'.join(response)
            break
        
        if (lookahead & 0b11000000) >> 6 == 0b11:
            #si es un puntero
            low = struct.unpack('B', buff.read(1))[0]
            #print(high | low)
            p_bytes = high | low
            for tup,val in dict_.items():
                if(p_bytes >= tup[0] and p_bytes < tup[1]):
                    response.append(val[p_bytes - tup[0]:])
                    dict_[(start,buff.tell())] = '.'.join(response)
                    break
            break
        
        else:
            #si es una cadena ordinaria
            char = struct.unpack(f'! {lookahead}s ', buff.read(lookahead))[0]
            response.append(char.decode())
    
    return ('.'.join(response),p_bytes)

def unpack_RRS(buff, dict_):
    rdata = None
    name = unpack_name(buff, dict_)
    tp = struct.unpack('!HHiH', buff.read(10))
    
    if tp[0] in RR_TEXT.keys():
        rdata = unpack_name(buff, dict_)[0]
        
    else:
        tmp = struct.unpack(f'{tp[3]}s',buff.read(tp[3]))[0]
        if tp[0] == 1:
            rdata = unpack_IPV4(tmp)
        elif tp[0] == 28:
            rdata = unpack_IPV6(tmp)
        else:
            rdata = tmp
            
    return name, tp, rdata

def unpack_IPV4(array):
    return ".".join(str(l) for l in struct.unpack('!BBBB', array))

def unpack_IPV6(array):
    return ":".join(str(l) for l in struct.unpack('!HHHHHHHH', array))

#d = io.BytesIO(b'\x03www\x06google\x03com\xC0\x11\x00\x01\x00\x01\x00\x00\x00\x01\x00\x03www')
#print(unpack_RRS(d))
#c = io.BytesIO(b'\xC0\x11')
#print(unpack_name(c)[1])
#e = io.BytesIO(b'\x03www\x06google\x03com\x00')
#print(unpack_name(e)[0])
