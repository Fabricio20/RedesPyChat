import json
import os
import socket
import struct
import threading
import time

from lib.protocol import Protocol

SVC_NAME = 'RECH_'  # Name of the service for broadcasting
PROTOCOL = Protocol()


# noinspection PyShadowingNames
def handle_message(server: socket):
    while True:
        try:
            msg = server.recv(1024)
        except socket.error:
            print('> Error during transmission.')
            os._exit(1)
            return
        # Payload decoding
        message = json.loads(msg.decode())
        op = message['op']
        if op == -1:  # Exit
            print("Error during communication: {}".format(message['message']))
            server.close()
            os._exit(1)
            return
        elif op == 2:  # Broadcast message
            print(message['name'] + ": " + message['message'])
        else:  # Unknown
            print("> Received unknown OP {}".format(message))


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
    # Ask for nickname
    nickname = str(input('Nickname: '))

    # Server connection
    host, port = find_server()
    server = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    server.connect((host, port))
    print('> Connected to server at {}\n'.format((host, port)))
    threading.Thread(target=handle_message, args=([server])).start()

    # Set nickname
    server.sendall(PROTOCOL.nickname(nickname))

    while True:
        msg = input()
        if msg == 'exit':
            server.sendall(PROTOCOL.exit())
            break
        else:
            server.sendall(PROTOCOL.message(msg))
        time.sleep(0.3)
except KeyboardInterrupt:
    print("Exiting..")
