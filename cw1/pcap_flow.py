from scapy.utils import RawPcapReader
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, TCP
from scapy.layers.inet6 import IPv6
from ipaddress import ip_address, IPv6Address
from socket import IPPROTO_TCP
import sys
import matplotlib.pyplot as plt

class Flow(object):
    def __init__(self, data):
        self.pkts = 0
        self.flows = 0
        self.ft = {}
        for pkt, metadata in RawPcapReader(data):
            self.pkts += 1
            ether = Ether(pkt)
            if ether.type == 0x86dd:
                ip = ether[IPv6]
                if TCP in ip and ip.nh == 6:
                    data_length = ip.plen - (ip[TCP].dataofs * 4)
            elif ether.type == 0x0800:
                ip = ether[IP]
                if TCP in ip and ip.proto == 6:
                    data_length = ip.len - (ip.ihl * 4) - (ip[TCP].dataofs * 4)
            if TCP in ip and data_length != 0:
                tcp = ip[TCP]
                src_port = tcp.sport
                dst_port = tcp.dport
                src_ip = int(ip_address(ip.src))
                dst_ip = int(ip_address(ip.dst))
                if (src_ip, dst_ip, src_port, dst_port) in self.ft or (dst_ip, src_ip, dst_port, src_port) in self.ft:
                    if (src_ip, dst_ip, src_port, dst_port) in self.ft:
                        self.ft[(src_ip, dst_ip, src_port, dst_port)] += data_length
                    else:
                        self.ft[(dst_ip, src_ip, dst_port, src_port)] += data_length
                else:
                    self.ft[(src_ip, dst_ip, src_port, dst_port)] = data_length
    def Plot(self):
        topn = 100
        data = [i/1000 for i in list(self.ft.values())]
        data.sort()
        data = data[-topn:]
        fig = plt.figure()
        ax = fig.add_subplot(1,1,1)
        ax.hist(data, bins=50, log=True)
        ax.set_ylabel('# of flows')
        ax.set_xlabel('Data sent [KB]')
        ax.set_title('Top {} TCP flow size distribution.'.format(topn))
        plt.savefig(sys.argv[1] + '.flow.pdf', bbox_inches='tight')
        plt.close()
    def _Dump(self):
        with open(sys.argv[1] + '.flow.data', 'w') as f:
            f.write('{}'.format(self.ft))

if __name__ == '__main__':
    d = Flow(sys.argv[1])
    d.Plot()
    d._Dump()
