# Hoffmann Muki 1894401 #
from socket import *
import sys
import os

clientSocket = socket(AF_INET, SOCK_DGRAM)

RemoteHost = sys.argv[1].strip()
Port = int(sys.argv[2].strip())
Filename = sys.argv[3].strip()
buf = 1024

f = open(Filename, 'rb')
filesize = os.path.getsize('./' + Filename)

seq_no = 0
total_bytes = 0

while True:
    bytes_read = f.read(buf)
    if bytes_read:
        total_bytes += len(bytes_read)
        seq_no_str = seq_no.to_bytes(2, 'big')
        if total_bytes < filesize:
            eof = 0
            eof_str = eof.to_bytes(1, 'big') 
        else:
            eof = 1
            eof_str = eof.to_bytes(1, 'big')
        message = seq_no_str + eof_str + bytes_read
        while not clientSocket.sendto(message, (RemoteHost, Port)):
            pass
        seq_no += 1
    else:
        if total_bytes == filesize:
            f.close()
            print(total_bytes, 'were sent')
        else:
            print('file transfer corrupted')
        break

clientSocket.close()
