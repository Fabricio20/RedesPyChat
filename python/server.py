import json
import selectors
import socket
import struct
import threading
import time
import types

from .lib.client import Client
from .lib.protocol import Protocol

eventHandler = selectors.DefaultSelector()

SVC_NAME = 'RECH_'  # Name of the service for broadcasting
CLIENTS = []
PROTOCOL = Protocol()


# noinspection PyShadowingNames
def accept(socket):
    conn, addr = socket.accept()
    conn.setblocking(False)
    print("> Accepted connection ", addr)
    data = types.SimpleNamespace(addr=addr, inb=b'', outb=b'')
    eventHandler.register(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, data=data)
    CLIENTS.append(Client(conn))


# noinspection PyShadowingNames
def handle_message(client, addr, event):
    message = b''
    if event & selectors.EVENT_READ:
        try:
            recv_data = client.recv(1024)
        except socket.error:
            print('> Prematurely Ended connection from {}'.format(addr))
            eventHandler.unregister(client)
            CLIENTS.remove(client)
            client.close()
            return
        if recv_data:
            message += recv_data
    if event & selectors.EVENT_WRITE:
        if message:
            print("> Received {} from {}".format(message.decode(), addr))
            message = json.loads(message.decode())
            if message['op'] == 0:
                print("> Closing connection to {}".format(addr))
                eventHandler.unregister(client)
                CLIENTS.remove(client)
                client.close()
            elif message['op'] == 1:
                # Set nickname

            elif message['op'] == 2:
                broadcast(message['message'])
            else:
                print("Unknown OP")


def broadcast(message):
    for client in CLIENTS:
        client.sendall(PROTOCOL.message(message))


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
    threading.Thread(target=start_announcing, args=([sock.getsockname()[1]])).start()

    sock.setblocking(False)
    eventHandler.register(sock, selectors.EVENT_READ, data=None)
    while True:
        try:
            events = eventHandler.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    accept(key.fileobj)
                else:
                    handle_message(key.fileobj, key.data.addr, mask)
        except socket.error as exception:
            print('Error during event loop', exception)
except KeyboardInterrupt:
    print("Exiting..")
finally:
    eventHandler.close()
