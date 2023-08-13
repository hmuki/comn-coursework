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
start, stop, timer = 0, 0, 0

def resend():
    global base, next_seq_no, total_packets, timer
    global clientSocket, client_buffer, serverAddress
    lock.acquire()
    timer = time.time()
    for j in range(next_seq_no-base):
        clientSocket.sendto(client_buffer[base+j-1], serverAddress)
    lock.release()

def sender():
    global base, next_seq_no, N, timer, start
    global clientSocket, client_buffer, serverAddress
    while next_seq_no <= total_packets:
        if next_seq_no == 1:
            # record time of first message
            start = time.time()
        if next_seq_no < (base + N):
            clientSocket.sendto(client_buffer[next_seq_no-1], serverAddress)
            lock.acquire()
            if base == next_seq_no:
                timer = time.time()
            next_seq_no += 1
            lock.release()

def receiver():
    global base, next_seq_no, ack, ack_buf, timer, last_message, stop
    global clientSocket
    while int.from_bytes(ack, 'big') <= total_packets:
        ack, serverAddress = clientSocket.recvfrom(ack_buf)
        lock.acquire()
        base = int.from_bytes(ack, 'big')+1
        if base == next_seq_no:
            timer = math.inf # stop timer
        else:
            timer = time.time() # restart timer
        lock.release()
        if int.from_bytes(ack, 'big') == total_packets:
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
    if time.time() < (timer + timeout):
        continue
    else:
        resend_thread = threading.Thread(target=resend)
        resend_thread.start()
        resend_thread.join()

print(round((filesize/1000)/(stop - start)))

clientSocket.close()
