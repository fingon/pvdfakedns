#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# $Id: pvdfakedns.py $
#
# Author: Markus Stenberg <markus stenberg@iki.fi>
#
# Copyright (c) 2015 cisco Systems, Inc.
#
# Created:       Sat Oct 31 17:20:42 2015 mstenber
# Last modified: Sat Oct 31 18:15:57 2015 mstenber
# Edit time:     50 min
#
"""

Fake DNS server. Configuration is at the end. The basic idea is to
respond to pairs of:

_pvd.*.X.ip6.arpa with a PTR to Y
Y with a TXT that contains arbitrary binary data.

Requirement:
- dnspython

"""

import ipaddress
import dns.message
import dns.rdata
import dns.rdatatype
import socket
from fnmatch import fnmatch

def ipv6_to_nonzero_arpa(ipv6addr):
    l = []
    for c in ipaddress.ip_address(unicode(ipv6addr)).packed:
        l.append(hex(ord(c)/16)[-1])
        l.append(hex(ord(c)%16)[-1])
    l.reverse()
    l.append('ip6')
    l.append('arpa')
    l.append('')
    s = '.'.join(l)
    while s.startswith('0.'):
        s = s[2:]
    return s

def add_ipv6_pvd(mappings, ipv6addr, fqdn, txtdata):
    rdclass = dns.rdataclass.IN
    k = ('_pvd.*.%s' % ipv6_to_nonzero_arpa(ipv6addr), dns.rdatatype.PTR)
    print k
    #mappings[k] = dns.rdata.from_text(rdclass, dns.rdatatype.PTR, fqdn)
    mappings[k] = dns.rrset.from_text(k[0], 123, rdclass, dns.rdatatype.PTR, fqdn)
    k = (fqdn, dns.rdatatype.TXT)
    print k
    #mappings[k] = dns.rdata.from_text(rdclass, dns.rdatatype.TXT, txtdata)
    mappings[k] = dns.rrset.from_text(k[0], 123, rdclass, dns.rdatatype.TXT, txtdata)

def serve(mappings, addr='', port=53535):
    s = socket.socket(family=socket.AF_INET6, type=socket.SOCK_DGRAM)
    s.bind((addr, port))
    while True:
        data, src = s.recvfrom(2**16)
        q = dns.message.from_wire(data)
        r = dns.message.make_response(q)
        if q.question:
            qd = q.question[0]
            qdn = qd.name.to_text()
            for (mq, mt), rd in mappings.items():
                if qd.rdtype in [dns.rdatatype.ANY, mt]:
                    if fnmatch(qdn, mq):
                        rd.name = qd.name
                        r.answer.append(rd)
                    else:
                        #print('x', qdn, mq)
                        pass
                else:
                    #print('y', qd.rdtype, mt)
                    pass
        s.sendto(r.to_wire(), src)

if __name__ == '__main__':
    mappings = {}
    add_ipv6_pvd(mappings, '2001:0470:ff61::', 'second.global.home.', 'n=wifi id=42')
    add_ipv6_pvd(mappings, 'fd00::', 'local.home.', 'n=cable id=43')
    add_ipv6_pvd(mappings, '2001:0470:ff87::', 'first.global.home.', 'n=cellular id=31')
    serve(mappings)
