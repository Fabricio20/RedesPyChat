import json
import socket
import struct
import threading
import time
from typing import Dict

from lib.channel import Channel
from lib.client import Client
from lib.protocol import Protocol

PROTOCOL = Protocol()
SVC_NAME = PROTOCOL.SERVICE_NAME  # Name of the service for broadcasting

USERS: Dict[str, Client] = {}
CHANNELS: Dict[str, Channel] = {}


# noinspection PyShadowingNames
def accept(socket):
    conn, addr = socket.accept()
    print("> Accepted connection from {}".format(addr))
    client = Client(conn)
    USERS[client.name] = client
    threading.Thread(target=handle_messages, args=([client])).start()


def handle_message(client: Client, message: str) -> None:
    message = json.loads(message)
    op = message['op']
    if op == 'DISCONNECT':
        print("> {} Closed.".format(client))
        leave_network(client)
        client.close()
        return
    elif op == 'LOGIN':
        name = message['name']
        # TODO: Validate on the entire network
        # Prevent name hijacking
        if name in USERS:
            client.send(PROTOCOL.error('Duplicate nickname'))
            USERS.pop(client.name)
            client.close()
            print('> {} Closed. [Forced]'.format(client))
            return
        USERS.pop(client.name)
        client.name = message['name']
        USERS[client.name] = client
    elif op == 'MESSAGE':
        msg = message['message']
        target = message['target']
        if target.startswith('#'):
            # channel
            target = message[1:]
            if target not in CHANNELS:
                client.send(PROTOCOL.error('Unknown channel'))
                return
            channel = CHANNELS[target]
            for users in channel.users:
                users.send(PROTOCOL.message(channel.name, msg, client.name))
        elif target == '&':
            # server-local
            for name in USERS:
                USERS[name].send(PROTOCOL.message(target, msg, client.name))
        elif target == '*':
            # network-wide
            # TODO: forward message
            for name in USERS:
                USERS[name].send(PROTOCOL.message(target, msg, client.name))
        else:
            # private
            if target not in USERS:
                client.send(PROTOCOL.error('Unknown user'))
                return
            USERS[target].send(PROTOCOL.message(target, msg, client.name))
    elif op == 'JOIN':
        channel = message['channel']
        if channel in CHANNELS:
            channel = CHANNELS[channel]
            # join channel
            if channel.password is not None:
                # Has password
                if 'pass' not in message:
                    client.send(PROTOCOL.error('Invalid password'))
                    return
                if message['pass'] != channel.password:
                    client.send(PROTOCOL.error('Invalid password'))
                    return
            # If already in channel
            if client in channel.users:
                client.send(PROTOCOL.error('Already in channel'))
                return
            else:
                # Join channel
                channel.users.append(client)
                for user in channel.users:
                    user.send(PROTOCOL.join(channel.name, client.name))
                    # TODO Send network channel join
        else:
            # create channel
            if 'pass' in message:
                channel = Channel(channel, message['pass'])
            else:
                channel = Channel(channel)
            channel.users = [client]
            channel.admins = [client]
            # Add to list
            CHANNELS[channel.name] = channel
            # TODO: Send network channel create
            # tell client he joined
            client.send(PROTOCOL.join(channel.name, client.name))
            # tell client he is admin
            client.send(PROTOCOL.admin(channel.name, client.name))
    elif op == 'PART':
        target = message['channel']
        if target not in CHANNELS:
            client.send(PROTOCOL.error('Unknown channel'))
            return
        channel = CHANNELS[target]
        if client not in channel.users:
            client.send(PROTOCOL.error('You are not part of this channel'))
            return
        for user in channel.users:
            user.send(PROTOCOL.part(channel.name, client.name))
        if client in channel.admins:
            channel.admins.remove(client)
        # TODO: send network user left channel
        channel.users.remove(client)
        if len(channel.users) == 0:
            CHANNELS.pop(channel.name)
    elif op == 'ADMIN':
        channel = message['channel']
        if channel not in CHANNELS:
            client.send(PROTOCOL.error('Unknown channel'))
            return
        channel = CHANNELS[channel]
        if client not in channel.admins:
            client.send(PROTOCOL.error('Missing permissions'))
            return
        user = message['user']
        if user not in USERS:
            client.send(PROTOCOL.error('Unknown user'))
            return
        user = USERS[user]
        if user not in channel.users:
            client.send(PROTOCOL.error('Target user is not part of this channel'))
            return
        if user in channel.admins:
            client.send(PROTOCOL.error('Target user is already an admin'))
            return
        channel.admins.append(user)
        for users in channel.users:
            users.send(PROTOCOL.admin(channel.name, user.name))
            # TODO: send network admin (message)
    elif op == 'KICK':
        channel = message['channel']
        if channel not in CHANNELS:
            client.send(PROTOCOL.error('Unknown channel'))
            return
        channel = CHANNELS[channel]
        if client not in channel.admins:
            client.send(PROTOCOL.error('Missing permissions'))
            return
        user = message['user']
        if user not in USERS:
            # TODO: Erro aqui de achar o user
            client.send(PROTOCOL.error('Unknown user'))
            return
        user = USERS[user]
        if user not in channel.users:
            # TODO: Send network kick
            return
        if 'message' in message:
            for users in channel.users:
                users.send(PROTOCOL.kick(channel.name, user.name, message['message']))
        else:
            for users in channel.users:
                users.send(PROTOCOL.kick(channel.name, user.name))
        channel.users.remove(user)
    elif op == 'CHANNELS':
        lst = []
        for name in CHANNELS:
            lst.append(CHANNELS[name].name)
        client.send(PROTOCOL.channels(lst))
    elif op == 'USERS':
        if 'channel' in message:
            channel = message['channel']
            if channel not in CHANNELS:
                client.send(PROTOCOL.error('Unknown channel'))
                return
            channel = CHANNELS[channel]
            lst = []
            for user in channel.users:
                lst.append(user.name)
            client.send(PROTOCOL.users('', channel.name, lst))
        else:
            lst = []
            for name in USERS:
                lst.append(USERS[name].name)
            client.send(PROTOCOL.users('', None, lst))
    else:
        print("> Received unknown OP from {}".format(client))


def leave_network(client: Client):
    to_remove = []
    for name in CHANNELS:
        channel = CHANNELS[name]
        if client not in channel.users:
            continue
        channel.users.remove(client)
        for user in channel.users:
            user.send(PROTOCOL.part(channel.name, client.name))
        if client in channel.admins:
            channel.admins.remove(client)
        # TODO: propagate leave to network
        if len(channel.users) == 0:
            to_remove.append(name)
    for name in to_remove:
        CHANNELS.pop(name)
    # Remove from list of users
    USERS.pop(client.name)


# Server message loop
def handle_messages(client: Client):
    while True:
        try:
            msg = client.socket.recv(1024)
        except socket.error:
            print('> {} Closed. [Error]'.format(client.name))
            leave_network(client)
            client.close()
            return
        handle_message(client, msg.decode())


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
