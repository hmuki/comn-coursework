# Hoffmann Muki 1894401 #
from socket import *
import sys
import os
import select
import time
from math import ceil

def make_packet(seq_no, eof, payload):
    eof_str = eof.to_bytes(1, 'big')
    seq_no_str = seq_no.to_bytes(2, 'big')
    return seq_no_str + eof_str + payload

clientSocket = socket(AF_INET, SOCK_DGRAM)

RemoteHost = sys.argv[1].strip()
Port = int(sys.argv[2].strip())
Filename = sys.argv[3].strip()
RetryTimeout = int(sys.argv[4].strip())

timeout = RetryTimeout/1000

ack = bytes(2)
ack_buf = 2
payload_buf = 1024

f = open(Filename, 'rb')
filesize = os.path.getsize('./' + Filename)
total_packets = int(ceil(filesize/payload_buf))

seq_no = 1
total_bytes = 0
first_message = True
retransmission_count = 0

serverAddress = (RemoteHost, Port)

while True:
    bytes_read = f.read(payload_buf)

    if bytes_read:
        total_bytes += len(bytes_read)
        if total_bytes < filesize:
            message = make_packet(seq_no, 0, bytes_read)
        else:
            message = make_packet(seq_no, 1, bytes_read)
        
        # send the first-time message
        clientSocket.sendto(message, serverAddress)
        if first_message:
            start_time = time.time() # record time of first message transmission
            first_message = False
        
        # set a timeout
        ready = select.select([clientSocket], [], [], timeout)
        if ready[0]:
            ack, serverAddress = clientSocket.recvfrom(ack_buf)
            if int.from_bytes(ack, 'big') == total_packets: # ack for last packet
                stop_time = time.time()
        
        while int.from_bytes(ack, 'big') != seq_no:
            # resend the message
            clientSocket.sendto(message, serverAddress)
            # augment number of retransmissions
            retransmission_count += 1
            # set a timeout
            ready = select.select([clientSocket], [], [], timeout)
            if ready[0]:
                ack, serverAddress = clientSocket.recvfrom(ack_buf)
                if int.from_bytes(ack, 'big') ==  total_packets: # ack for last packet
                    stop_time = time.time()
        # move to the next packet
        seq_no += 1
    else:
        if total_bytes == filesize:
            f.close()
            print(round(retransmission_count), round((filesize/1000)/(stop_time - start_time)))
            break

clientSocket.close()
