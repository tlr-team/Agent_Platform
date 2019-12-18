import struct
import socket
import io
#defines unpack_name & unpack_RRS & unpack_IPV4 6 unpack_IPV6
from aux import *

qr_mask =     int('1000000000000000',2)
opcode_mask = int('0111100000000000',2)
aa_mask =     int('0000010000000000',2)
tc_mask =     int('0000001000000000',2)
rd_mask =     int('0000000100000000',2)
ra_mask =     int('0000000010000000',2)
z_mask =      int('0000000001110000',2)
rcode_mask =  int('0000000000001111',2)

OC_STANDARD_QUERY = 0
OC_INVERSE_QUERY = 1
OC_SERVER_STATUS_REQUEST = 2

QT_A = 0x00_01
QT_NS = 0x00_02
QT_CNAME = 0x00_05
QT_MX = 0x00_0F

RR_TYPE = {
    28: 'AAAA',
    1: 'A',
    5: 'CNAME',
    13: 'HINFO',
    15: 'MX',
    2: 'NS',
    12: 'PTR',
    6: 'SOA',
    33: 'SRV',
    16: 'TXT',
}

RR_CLASS = {
    1: 'IN'
    }


QT_MAP = {
    'A': QT_A,
    'NS': QT_NS,
    'CNAME': QT_CNAME,
    'MX': QT_MX
}

QC_INTERNET = 0x00_01

QC_MAP = {
    'IN': QC_INTERNET
}

def unpack(fmt, stream):
    size = struct.calcsize(fmt)
    buf = stream.read(size)
    return struct.unpack(fmt, buf)
        
class DNS_Header:
    def __init__(self, _id, qr, opcode, aa, tc, rd, ra, z, rcode, qdcount, ancount, nscount, arcount):
        self._id = _id
        self.qr = qr
        self.opcode = opcode
        self.aa = aa
        self.tc = tc
        self.rd = rd
        self.ra = ra
        self.z = z
        self.rcode = rcode
        self.qdcount = qdcount
        self.ancount = ancount
        self.nscount = nscount
        self.arcount = arcount
        self.header = 0

class DNS_Query:
    def __init__(self,qname, qtype, qclass):
        self.qname = qname
        self.qtype = qtype
        self.qclass = qclass
        self.query = 0

class RRS:
    def __init__(self, name, rtype, rclass, ttl, rdlenght, rdata):
        self.name = name
        self.rtype = rtype
        self.rclass = rclass
        self.ttl = ttl
        self.rdlenght = rdlenght
        self.rdata = rdata

class DNS_PAKAGE:
    def __init__(self):
        self.header = None
        self.querys = []
        self.response = []
        self.authority = []
        self.additional = []
        self.queries_build = 0
        self.response_build = 0
        self.authority_build = 0
        self.additional_build = 0
    
    def build_Query(self, qname, qtype, qclass):
        if self.queries_build < self.header.qdcount:
            d = DNS_Query(qname,qtype,qclass)
            self.querys.append(d)
            self.queries_build += 1
    
    def build_Header(self, _id, qr, opcode, aa, tc, rd, ra, z, rcode, qdcount, ancount, nscount, arcount):
        self.header = DNS_Header(_id, qr, opcode, aa, tc, rd, ra, z, rcode, qdcount, ancount, nscount, arcount)
    
    def build_response(self, name, rtype, rclass, ttl, rdlenght, rdata):
        if self.response_build < self.header.ancount:
            d = RRS(name,rtype, rclass, ttl, rdlenght, rdata)
            self.response.append(d)
            self.response_build += 1
    
    def build_authority(self, name, rtype, rclass, ttl, rdlenght, rdata):
        if self.authority_build < self.header.nscount:
            d = RRS(name,rtype, rclass, ttl, rdlenght, rdata)
            self.authority.append(d)
            self.authority_build += 1
    
    def build_aditional(self, name, rtype, rclass, ttl, rdlenght, rdata):
        if self.additional_build < self.header.arcount:
            d = RRS(name,rtype, rclass, ttl, rdlenght, rdata)
            self.additional.append(d)
            self.additional_build +=1
    
    def __pack_header__(self):
        m_id = self.header._id
        m_2nd = self.header.qr << 15 | self.header.opcode << 11 | self.header.aa << 10 | self.header.tc << 9 | self.header.rd << 8 | self.header.ra << 7 |                      self.header.z << 4 | self.header.rcode
        m_qdc = self.header.qdcount
        m_anc = self.header.ancount
        m_nsc = self.header.nscount
        m_arc = self.header.arcount
        return struct.pack('! HHHHHH',m_id, m_2nd, m_qdc, m_anc, m_nsc, m_arc)
    
    def __pack_queries__(self):
        res = b''
        for a in self.querys:
            res += b''.join([struct.pack(f'! B {len(l)}s', len(l), l) for l in a.qname.encode().split(b'.')])
            res += struct.pack(f'!BHH',0, a.qtype, a.qclass)
        return res
            
    def __pack_responses__(self):
        return b''.join(struct.pack(f'! {len(a.name)}sHHiH{len(a.rdata)}s', a.name, a.rtype, a.rclass, a.ttl, a.rdlenght, a.rdata) for a in self.response)
    
    def __pack_authorities__(self):
        return b''.join(struct.pack(f'! {len(a.name)}sHHiH{len(a.rdata)}s', a.name, a.rtype, a.rclass, a.ttl, a.rdlenght, a.rdata) for a in self.authority)
    
    def __pack_additionals__(self):
        return b''.join(struct.pack(f'! {len(a.name)}sHHiH{len(a.rdata)}s', a.name, a.rtype, a.rclass, a.ttl, a.rdlenght, a.rdata) for a in self.additional)
    
    def pack(self):
        r = self.__pack_header__() + self.__pack_queries__() + self.__pack_responses__() + self.__pack_authorities__() + self.__pack_additionals__()
        return r
    
    def send_and_get(self,dns, port):
        s = socket.socket(type=socket.SOCK_DGRAM)
        s.sendto(self.pack(), (dns, port))
        return DNS_PAKAGE.unpack(self,s)
    
    @staticmethod
    def unpack(self, socket):
        buff = io.BytesIO()
        dict_ = {}
        tmp = b''
        tmp = socket.recv(512)
        print(tmp)
        buff.write(tmp)
        
        buff.seek(0)
        pack = DNS_PAKAGE()
        
        #header
        header = unpack('! HHHHHH', buff)
        qr = (header[1] >> 15)
        opcode = (header[1] & opcode_mask)  >> 11
        aa = (header[1] & aa_mask) >> 10
        tc = (header[1] & tc_mask) >> 9
        rd = (header[1] & rd_mask) >> 8
        ra = (header[1] & ra_mask) >> 7
        z = (header[1] & z_mask) >> 4
        rcode = header[1] & rcode_mask
        pack.build_Header(hex(header[0]),qr,opcode,aa,tc,rd,ra,z,rcode,header[2],header[3],header[4],header[5]) 
        
        pack.print_Header()
        
        #queries
        queries_count = pack.header.qdcount
        if queries_count > 0:
            for i in range(0,queries_count):
                qname = unpack_name(buff,dict_)[0]
                qtype = unpack('!H', buff)[0]
                qclass = unpack('!H', buff)[0]
                pack.build_Query(qname,qtype,qclass)
        
        #answer
        answer_count = pack.header.ancount
        if answer_count > 0:
            for i in range(0,answer_count):
                name , tp , rdata = unpack_RRS(buff, dict_)
                atype = tp[0]
                aclass = tp[1]
                attl = tp[2]
                ardlen = tp[3]
                afname = rdata
                nm = name[1] if name[0] == '' else name[0]  
                pack.build_response(nm, RR_TYPE[atype], RR_CLASS[aclass], attl, ardlen, afname)
            
        #authority
        auth_count = pack.header.nscount
        if auth_count > 0:
            for i in range(0,auth_count):
                name , tp , rdata = unpack_RRS(buff, dict_)
                atype = tp[0]
                aclass = tp[1]
                attl = tp[2]
                ardlen = tp[3]
                afname = rdata
                nm = name[1] if name[0] == '' else name[0] 
                pack.build_authority(nm, RR_TYPE[atype], RR_CLASS[aclass], attl, ardlen, afname)
            
        #additional
        add_count = pack.header.arcount
        if add_count > 0:
            for i in range(0,add_count):
                name , tp , rdata = unpack_RRS(buff, dict_)
                atype = tp[0]
                aclass = tp[1]
                attl = tp[2]
                ardlen = tp[3]
                afname = rdata
                nm = name[1] if name[0] == '' else name[0] 
                pack.build_aditional(nm, RR_TYPE[atype], RR_CLASS[aclass], attl, ardlen, afname)
        
        return pack
    
    def print_RR(self,rr):
        print('-------------RR---------------')
        print('Nombre:',rr.name)
        print('Rtype:', rr.rtype)
        print('Rclass:',rr.rclass)
        print('TTL:', rr.ttl)
        print('Rdlenght:', rr.rdlenght)
        print('Rdata:', rr.rdata)
        
    def print_Header(self):
        print('-----------Header-------------')
        print('ID:',self.header._id)
        print('QR:',self.header.qr)
        print('Opcode:',self.header.opcode)
        print('aa:',self.header.aa)
        print('tc:',self.header.tc)
        print('rd:',self.header.rd)
        print('ra:',self.header.ra)
        print('z:',self.header.z)
        print('rcode:',self.header.rcode)
        print('qdcount:',self.header.qdcount)
        print('ancount:',self.header.ancount)
        print('nscount:',self.header.nscount)
        print('arcount:',self.header.arcount)
        
    def print_Query(self, qr):
        print('-------------Query------------')
        print('Query Name:',qr.qname)
        print('Qtype:', qr.qtype)
        print('Qclass:', qr.qclass)
        
    def __str__(self):
        r = ""
        for i in self.querys:
            self.print_Query(i)
        
        for i in self.response:
            self.print_RR(i)
            
        for i in self.authority:
            self.print_RR(i)
            
        for i in self.additional:
            self.print_RR(i)
        return r

def generate_id() -> int:
    return 0xCAFE  # Return static for now


def do_query(hostname: str, query_type: str, dns: str, port: int) -> DNS_PAKAGE:
    # Generate a new id
    id_ = generate_id()
    
    
    message = DNS_PAKAGE()
    message.build_Header(id_, False, OC_STANDARD_QUERY, False, False, True, False,0,0,1,0,0,0)
    message.build_Query(hostname, query_type, QC_INTERNET)
    # Create queries
    # Note: You can make more queries

    # Send it
    response = message.send_and_get(dns,port)

    return response


def main(args):
    response = do_query(args.hostname, args.query_type, args.dns, args.port)

    # TODO: Pretty print response
    print(response)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Basic DNS client')
    parser.add_argument('hostname', type=str, help='Hostname to query')
    parser.add_argument('-d', '--dns', type=str, default='localhost', help='DNS IP')
    parser.add_argument('-p', '--port', type=int, default=53, help='alternative dns port')
    parser.add_argument('-q', '--query-type', type=str, default=QT_A, help='query type')

    args = parser.parse_args()

    main(args)
