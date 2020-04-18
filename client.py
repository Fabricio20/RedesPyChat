import socket
import struct
import threading
import time

HOST = '::1'  # The server's hostname or IP address
PORT = 62642  # The port used by the server
CONNECTED = False


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


def find_server():
    group = 'ff15::1'  # IPv6 Multicast (Site-Local)

    # Look up multicast group address in name server and find out IP version
    addrinfo = socket.getaddrinfo(group, None)[0]

    # Create a socket
    s = socket.socket(addrinfo[0], socket.SOCK_DGRAM)

    # Allow multiple copies of this program on one machine
    # (not strictly needed)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind it to the port
    s.bind(('', 1900))

    group_bin = socket.inet_pton(addrinfo[0], addrinfo[4][0])
    # Join group
    mreq = group_bin + struct.pack('@I', 0)
    s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq)

    # Loop, printing any data we receive
    while True:
        data, sender = s.recvfrom(1500)
        while data[-1:] == '\0': data = data[:-1]  # Strip trailing \0's
        print(str(sender) + '  ' + repr(data))


try:
    find_server()
    server = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    server.connect((HOST, PORT))
    print('> Connected to {}\n'.format((HOST, PORT)))
    threading.Thread(target=handle_message, args=(server, (HOST, PORT))).start()
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
