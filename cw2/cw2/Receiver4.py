# Hoffmann Muki 1894401 #
from socket import *
import sys
import select

serverSocket = socket(AF_INET, SOCK_DGRAM)

Port = int(sys.argv[1].strip())
Filename = sys.argv[2].strip()
WindowSize = int(sys.argv[3].strip())
message = None
buf = 1027

serverSocket.bind(("", Port))

print('The server is now ready to receive')

f = open(Filename, 'wb')

base = 1
buffered_packets = []
received_packets = set()
done = False
delay = 25/1000 # propagation delay
N = WindowSize

def update_buffer():
    global base, buffered_packets, f
    stop = False
    buffer_size = len(buffered_packets)
    if buffer_size == 1:
        f.write(buffered_packets[0][2]) # write to file
        if int.from_bytes(buffered_packets[0][1], 'big') == 1: # last message
            stop = True
        buffered_packets.pop(0) # remove item at head of list
        base += 1 # increment base
        return [], stop
    else:
        buffered_packets.sort(key=lambda x:x[0]) # sort data
        last_index = 0
        for j in range(buffer_size):
            if buffered_packets[j][0] == base+j:
                f.write(buffered_packets[j][2]) # write to file
                last_index += 1
            else:
                break
        if int.from_bytes(buffered_packets[last_index-1][1], 'big') == 1: # last message
            stop = True
        for _ in range(last_index):
            buffered_packets.pop(0) # remove item at head of list
            base += 1 # increment base
        return buffered_packets, stop

while True:
    # in the worst case wait for as long as ten times propagation delay
    ready = select.select([serverSocket], [], [], 10 * delay)
    if ready[0]:
        message, clientAddress = serverSocket.recvfrom(buf)
    else:
        message = None
    if not message:
        if not done:
            continue
        else:
            break
    else:
        curr_no = int.from_bytes(message[:2], 'big')
        print('received packet', curr_no)
        if curr_no >= base and curr_no <= base+N-1: # packet within window arrives
            if curr_no not in received_packets:
                buffered_packets.append((curr_no, message[2:3], message[3:])) # add to buffer
                received_packets.add(curr_no)
            ack = curr_no.to_bytes(2, 'big')
            serverSocket.sendto(ack, clientAddress) # send ack for current packet
            print('1. sent ack for', curr_no)
            if curr_no == base:
                buffered_packets, done = update_buffer() # update buffer and write to file
                if done:
                    f.close()
                    # send ack 3 times to ensure client receives it
                    for _ in range(3):
                        serverSocket.sendto(ack, clientAddress) # send ack for last received packet
        elif curr_no >= base-N and curr_no <= base-1: # packet from previous window
            ack = curr_no.to_bytes(2, 'big')
            serverSocket.sendto(ack, clientAddress) # send ack for previously acked packet
            print('2. sent ack for', curr_no)
        else:
            continue
        
serverSocket.close()
