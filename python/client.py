import json
import os
import socket
import struct
import sys
import threading
import time

from lib.protocol import Protocol

SVC_NAME = 'RECH_'  # Name of the service for broadcasting
PROTOCOL = Protocol()


def print_err(message: str):
    print(message, file=sys.stderr)


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
        if op == 'DISCONNECT':
            print("Error during communication: {}".format(message['message']))
            server.close()
            os._exit(1)
            return
        elif op == 'ERROR':
            print_err(message['message'])
        elif op == 'MESSAGE':
            if message['target'].startswith('#'):
                print('[' + message['target'] + '] ' + message['name'] + ': ' + message['message'])
            elif message['target'] == '*' or message['target'] == '&':
                print('>> ' + message['name'] + ': ' + message['message'])
            else:
                print(message['name'] + ': ' + message['message'])
        elif op == 'JOIN':
            print('> ' + message['user'] + ' has joined ' + message['channel'])
        elif op == 'PART':
            print('> ' + message['user'] + ' left ' + message['channel'] + '. (Left)')
        elif op == 'ADMIN':
            print('> ' + message['user'] + ' is now an admin at ' + message['channel'])
        elif op == 'KICK':
            if 'message' in message:
                print('> ' + message['user'] + ' left ' + message['channel'] + '. (' + message['message'] + ')')
            else:
                print('> ' + message['user'] + ' left ' + message['channel'] + '. (Kicked)')
        elif op == 'CHANNELS':
            print('>> CHANNELS: ' + ', '.join(message['channels']))
        elif op == 'USERS':
            if 'channel' in message:
                print('>> USERS [' + message['channel'] + ']: ' + ', '.join(message['users']))
            else:
                print('>> USERS: ' + ', '.join(message['users']))
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


def handle_commands(message: str, server: socket) -> bool:
    if not message.startswith('/'):
        # nothing
        return False
    args = message.split(' ')[1:]
    command = message.split(' ')[0][1:].lower()
    if command == 'help':
        print_err('Help: /join, /part, /admin, /kick, /channels, /users')
    elif command == 'join':
        if len(args) == 0:
            print_err('Usage: /join <#channel> (password)')
            return True
        if not args[0].startswith('#'):
            print_err('Invalid channel name, must start with #.')
            return True
        if len(args) == 1:
            # Join channel
            server.sendall(PROTOCOL.join(args[0]))
        else:
            # Join channel (password)
            server.sendall(PROTOCOL.join(args[0], None, args[1]))
        return True
    elif command == 'part':
        if len(args) == 0:
            print_err('Usage: /part <#channel>')
            return True
        if not args[0].startswith('#'):
            print_err('Invalid channel name, must start with #.')
            return True
        server.sendall(PROTOCOL.part(args[0]))
    elif command == 'admin':
        if len(args) < 2:
            print_err('Usage: /admin <user> <#channel>')
            return True
        if not args[1].startswith('#'):
            print_err('Invalid channel name, must start with #.')
            return True
        server.sendall(PROTOCOL.admin(args[1], args[0]))
    elif command == 'kick':
        if len(args) < 2:
            print_err('Usage: /kick <user> <#channel> (message)')
            return True
        if not args[1].startswith('#'):
            print_err('Invalid channel name, must start with #.')
            return True
        if len(args) == 2:
            server.sendall(PROTOCOL.kick(args[1], args[0]))
        else:
            server.sendall(PROTOCOL.kick(args[1], args[0], args[2]))
    elif command == 'channels':
        server.sendall(PROTOCOL.channels())
    elif command == 'users':
        if len(args) == 1 and not args[0].startswith('#'):
            print_err('Invalid channel name, must start with #.')
            return True
        if len(args) == 0:
            server.sendall(PROTOCOL.users(''))
        else:
            server.sendall(PROTOCOL.users('', args[0]))
    else:
        print_err('Unknown command')
    return True


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
    server.sendall(PROTOCOL.login(nickname))

    while True:
        msg = input()
        if msg == 'exit':
            server.sendall(PROTOCOL.disconnect())
            break
        else:
            if handle_commands(msg, server):
                continue
            if ':' in msg:
                args = msg.split(':')
                target = args[0]
                message = ' '.join(args[1:])
                server.sendall(PROTOCOL.message(target, message))
            else:
                print_err('>> Usage [Channel]: #channel: Message')
                print_err('>> Usage [DMs]: username: Message')
                print_err('>> Usage [Global]: *: Message')
                print_err('>> Usage [Local]: &: Message')
        time.sleep(0.3)
except KeyboardInterrupt:
    print("Exiting..")
