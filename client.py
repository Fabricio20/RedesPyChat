import socket
import struct
import threading
import time

SVC_NAME = 'RECH_'  # Name of the service for broadcasting


# noinspection PyShadowingNames
def handle_message(server: socket, addr):
    while True:
        message = b''
        try:
            recv_data = server.recv(1024)
        except socket.error:
            print('> Prematurely Ended connection to {}'.format(addr))
            server.close()
            return
        if recv_data:
            message += recv_data
        if message:
            print(">> {}".format(message.decode()))


# Service discovery
def find_server():
    print("Waiting for server announcement...")
    # Create UDP socket server
    skt = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    # Allow port sharing
    skt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Bind
    skt.bind(('', 1900))
    # Join multicast group
    group_bin = socket.inet_pton(socket.AF_INET6, 'FF15::1')
    mc_req = group_bin + struct.pack('@I', 0)
    skt.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mc_req)
    # Wait for server broadcast
    while True:
        data, sender = skt.recvfrom(1400)
        data = data.decode()
        if not data.startswith(SVC_NAME):
            continue
        # Strip trailing 0
        while data[-1:] == '\0':
            data = data[:-1]
        sv_host = sender[0]
        sv_port = int(data[len(SVC_NAME):])
        return sv_host, sv_port


try:
    host, port = find_server()
    server = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    server.connect((host, port))
    print('> Connected to server at {}\n'.format((host, port)))
    threading.Thread(target=handle_message, args=(server, (host, port))).start()
    while True:
        msg = input()
        if msg == 'exit':
            server.sendall('{"op": 0}'.encode())
            break
        else:
            server.sendall(('{"op": 1, "message": "' + msg + '"}').encode())
        time.sleep(0.5)
except KeyboardInterrupt:
    print("Exiting..")
#
# data = s.recv(1024)

# print('Received', repr(data))
