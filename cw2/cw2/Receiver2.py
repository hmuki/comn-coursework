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

prev_no = 0
processed_no = 0

while True:
    message, clientAddress = serverSocket.recvfrom(buf)
    if not message:
        continue
    else:
        curr_no = int.from_bytes(message[:2], 'big')
        if curr_no != prev_no + 1: # out-of-order packet arrives
            if processed_no == curr_no: # packet is a duplicate
                ack = curr_no.to_bytes(2, 'big')
                serverSocket.sendto(ack, clientAddress) # send ack for current packet
                continue
            # some other packet arrived
            ack = prev_no.to_bytes(2, 'big')
            serverSocket.sendto(ack, clientAddress) # send ack for previous packet
            continue
        # in-order packet arrives
        ack = curr_no.to_bytes(2, 'big')
        serverSocket.sendto(ack, clientAddress) # send ack for current packet
        f.write(message[3:])
        prev_no += 1
        processed_no = curr_no
        if int.from_bytes(message[2:3], 'big') == 1: # the last packet?
            f.close()
            # send ack 3 times to ensure client receives it
            for _ in range(3):
                ack = curr_no.to_bytes(2, 'big')
                serverSocket.sendto(ack, clientAddress) # send ack for last packet
            break
        
serverSocket.close()
