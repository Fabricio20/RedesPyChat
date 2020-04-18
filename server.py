import json
import selectors
import socket
import struct
import time
import types

eventHandler = selectors.DefaultSelector()

HOST = '::1'
PORT = 0
clients = []


# noinspection PyShadowingNames
def accept(socket):
    conn, addr = socket.accept()
    conn.setblocking(False)
    print("> Accepted connection ", addr)
    data = types.SimpleNamespace(addr=addr, inb=b'', outb=b'')
    eventHandler.register(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, data=data)
    clients.append(conn)


# noinspection PyShadowingNames
def handle_message(client, addr, event):
    message = b''
    if event & selectors.EVENT_READ:
        try:
            recv_data = client.recv(1024)
        except socket.error:
            print('> Prematurely Ended connection from {}'.format(addr))
            eventHandler.unregister(client)
            clients.remove(client)
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
                clients.remove(client)
                client.close()
            else:
                print("> Echoing '{}' to {}".format(message, addr))
                broadcast(message['message'])


def broadcast(message):
    for client in clients:
        client.sendall(message.encode())


def start_announcing():
    addr = socket.getaddrinfo('ff15::1', None)[0]
    s = socket.socket(addr[0], socket.SOCK_DGRAM)
    # Set TTL to 1-Hop to avoid leaking to org-local network
    ttl_bin = struct.pack('@i', 1)
    s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, ttl_bin)
    while True:
        data = repr(time.time())
        s.sendto((data + '\0').encode(), (addr[4][0], 50000))
        time.sleep(1)


try:
    find_client()
    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    sock.bind((HOST, PORT))
    sock.listen()

    print("Listening on {} at port {}\n".format(sock.getsockname()[0], sock.getsockname()[1]))

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
