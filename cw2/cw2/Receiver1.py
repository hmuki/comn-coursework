# Hoffmann Muki 1894401 #
from socket import *
import sys

serverSocket = socket(AF_INET, SOCK_DGRAM)

Port = int(sys.argv[1].strip())
Filename = sys.argv[2].strip()
buf = 1027

serverSocket.bind(("", Port))

print('The server is now ready to receive')

f = open(Filename, 'wb')

prev_no = -1

while True:
    message, clientAddress = serverSocket.recvfrom(buf)
    if not message:
        continue
    else:
        curr_no = int.from_bytes(message[:2], 'big')
        if curr_no == prev_no + 1: # are you the successor to the previous package?
            prev_no += 1
            f.write(message[3:])
            if int.from_bytes(message[2:3], 'big') == 1: # the last packet?
                f.close()
                break

serverSocket.close()
