import json
import socket
import struct
import threading
import time

from lib.client import Client
from lib.protocol import Protocol

SVC_NAME = 'RECH_'  # Name of the service for broadcasting
USERS = []
PROTOCOL = Protocol()


# noinspection PyShadowingNames
def accept(socket):
    conn, addr = socket.accept()
    print("> Accepted connection from {}".format(addr))
    client = Client(conn)
    USERS.append(client)
    threading.Thread(target=handle_messages, args=([client])).start()


def handle_messages(client: Client):
    while True:
        try:
            msg = client.socket.recv(1024)
        except socket.error:
            print('> Prematurely Ended connection from {}'.format(client))
            USERS.remove(client)
            client.close()
            return
        # Payload decoding
        message = json.loads(msg.decode())
        op = message['op']
        if op == 0:  # Exit
            print("> Closing connection to {}".format(client))
            USERS.remove(client)
            client.close()
            return
        elif op == 1:  # Set nickname
            name = message['name']
            # Prevent name hijacking
            for user in USERS:
                if user.name == name:
                    client.send(PROTOCOL.close('Duplicate nickname'))
                    USERS.remove(client)
                    client.close()
                    return
            client.name = message['name']
        elif op == 2:  # Broadcast message
            for user in USERS:
                user.send(PROTOCOL.message(message['message'], client.name))
        else:  # Unknown
            print("> Received unknown OP from {}".format(client))


def start_announcing(port: int):
    skt = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    # Set TTL to 1-Hop to avoid leaking to org-local network
    ttl_bin = struct.pack('@i', 1)
    skt.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, ttl_bin)
    print("Announcing service on FF15::1 at port 1900\n")
    # Broadcast data
    data = (SVC_NAME + str(port) + '\0').encode()
    # Announce
    while True:
        # Interface-Local all devices Multicast group
        skt.sendto(data, ('ff15::1', 1900))
        time.sleep(5)


try:
    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    sock.bind(('::', 0))
    sock.listen()
    print("Listening on {} at port {}".format(sock.getsockname()[0], sock.getsockname()[1]))

    # Announce
    threading.Thread(target=start_announcing, args=([sock.getsockname()[1]])).start()

    while True:
        accept(sock)
except KeyboardInterrupt:
    print("Exiting..")
