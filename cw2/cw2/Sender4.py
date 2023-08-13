# Hoffmann Muki 1894401 #
from socket import *
import sys
import os
import select
import time
import threading
import math

def make_packet(seq_no, eof, payload):
    eof_str = eof.to_bytes(1, 'big')
    seq_no_str = seq_no.to_bytes(2, 'big')
    return seq_no_str + eof_str + payload

clientSocket = socket(AF_INET, SOCK_DGRAM)

RemoteHost = sys.argv[1].strip()
Port = int(sys.argv[2].strip())
Filename = sys.argv[3].strip()
RetryTimeout = int(sys.argv[4].strip())
WindowSize = int(sys.argv[5].strip())

timeout = RetryTimeout/1000

ack = bytes(2)
ack_buf = 2
payload_buf = 1024

f = open(Filename, 'rb')
filesize = os.path.getsize('./' + Filename)
total_packets = int(math.ceil(filesize/payload_buf))

base = 1
seq_no = 1
next_seq_no = 1
client_buffer = []
N = WindowSize

total_bytes = 0
last_message = False

serverAddress = (RemoteHost, Port)
lock = threading.Lock()
start, stop = 0, 0
timers = [0 for _ in range(total_packets)]
received = [False for _ in range(total_packets)]
unacked_packets = [(i+1) for i in range(total_packets)]

def resend(packet_index):
    global timers
    global clientSocket, client_buffer, serverAddress
    lock.acquire()
    clientSocket.sendto(client_buffer[packet_index-1], serverAddress)
    # print('resent packet', packet_index)
    timers[packet_index-1] = time.time() # restart timer
    lock.release()

def sender():
    global base, next_seq_no, N, timers, start
    global clientSocket, client_buffer, serverAddress
    while next_seq_no <= total_packets:
        if next_seq_no == 1:
            # record time of first message
            start = time.time()
        if next_seq_no < (base + N):
            clientSocket.sendto(client_buffer[next_seq_no-1], serverAddress)
            # print('sent packet', next_seq_no)
            lock.acquire()
            timers[next_seq_no-1] = time.time() # begin timer for the packet
            next_seq_no += 1
            lock.release()

def receiver():
    global base, next_seq_no, ack, ack_buf, timer, last_message, stop
    global clientSocket
    while int.from_bytes(ack, 'big') <= total_packets:
        ack, serverAddress = clientSocket.recvfrom(ack_buf)
        packet_no = int.from_bytes(ack, 'big')
        # print('received packet', packet_no)
        if packet_no >= base and packet_no <= base+N-1: # packet is within window
            lock.acquire()
            if not received[packet_no-1]:
                unacked_packets.remove(packet_no)
                received[packet_no-1] = True # mark as received
                if unacked_packets:
                    base = unacked_packets[0] # update base
                else:
                    base = total_packets+1 # we're done
            lock.release()
            if all(received):
                # record time of receipt of last message
                stop = time.time()
                last_message = True
                break

# read all the file data into a buffer
while True:
    bytes_read = f.read(payload_buf)
    if bytes_read:
        total_bytes += len(bytes_read)
        if total_bytes < filesize:
            message = make_packet(seq_no, 0, bytes_read)
        else:
            message = make_packet(seq_no, 1, bytes_read)
        client_buffer.append(message)
        seq_no += 1
    else:
        break

sender_thread = threading.Thread(target=sender)
receiver_thread = threading.Thread(target=receiver)

sender_thread.start()
receiver_thread.start()

while True:
    if last_message:
        sender_thread.join()
        receiver_thread.join()
        break
    for packet_index in range(base, next_seq_no): # for sent packets in window
        if time.time() < (timers[packet_index-1] + timeout):
            continue
        else:
            resend_thread = threading.Thread(target=resend, args=(packet_index,))
            resend_thread.start()
            resend_thread.join()

print(round((filesize/1000)/(stop - start)))

clientSocket.close()
