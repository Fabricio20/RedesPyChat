import json


class Protocol:
    # Name of the service (used for multicast announcements)
    SERVICE_NAME = 'RECH_'

    @staticmethod
    def disconnect(message: str = None) -> bytes:
        if message is None:
            # client-server
            return json.dumps({"op": "DISCONNECT"}).encode()
        else:
            # server-client
            return json.dumps({"op": "DISCONNECT", "message": message}).encode()

    @staticmethod
    def error(message: str) -> bytes:
        return json.dumps({"op": "ERROR", "message": message}).encode()

    @staticmethod
    def login(username: str, hash: str = None) -> bytes:
        if hash is None:
            # client-server
            return json.dumps({"op": "LOGIN", "name": username}).encode()
        else:
            # server-server
            return json.dumps({"op": "LOGIN", "name": username, "hash": hash}).encode()

    # Sends a message, target can be:
    # - Username
    # - #channel
    # - * (all users)
    # - & (all users in this server)
    @staticmethod
    def message(target: str, message: str, username: str = None, hash: str = None) -> bytes:
        if hash is None and username is None:
            # client-server
            return json.dumps({"op": "MESSAGE", "target": target, "message": message}).encode()
        elif hash is None:
            # server-client
            return json.dumps(
                {"op": "MESSAGE", "name": username, "target": target, "message": message}).encode()
        else:
            # server-server
            return json.dumps(
                {"op": "MESSAGE", "name": username, "hash": hash, "target": target, "message": message}).encode()

    @staticmethod
    def join(channel: str, username: str = None, passwd: str = None) -> bytes:
        if passwd is None and username is None:
            # client-server
            return json.dumps({"op": "JOIN", "channel": channel}).encode()
        elif username is None:
            # client-server
            return json.dumps({"op": "JOIN", "channel": channel, "pass": passwd}).encode()
        elif username is not None and passwd is None:
            # server-server (no password)
            return json.dumps({"op": "JOIN", "channel": channel, "user": username}).encode()
        else:
            # server-server (with password)
            return json.dumps({"op": "JOIN", "channel": channel, "user": username, "pass": passwd}).encode()

    @staticmethod
    def part(channel: str, username: str = None) -> bytes:
        if username is None:
            # client-server
            return json.dumps({"op": "PART", "channel": channel}).encode()
        else:
            # server-server
            return json.dumps({"op": "PART", "channel": channel, "user": username}).encode()

    @staticmethod
    def admin(channel: str, username: str) -> bytes:
        return json.dumps({"op": "ADMIN", "channel": channel, "user": username}).encode()

    @staticmethod
    def kick(channel: str, username: str, message: str = None) -> bytes:
        if message is None:
            return json.dumps({"op": "KICK", "channel": channel, "user": username}).encode()
        else:
            return json.dumps({"op": "KICK", "channel": channel, "user": username, "message": message}).encode()

    @staticmethod
    def ack(hash: str, success: bool) -> bytes:
        return json.dumps({"op": "ACK", "hash": hash, "success": success}).encode()

    @staticmethod
    def channels(channels: list = None) -> bytes:
        if channels is None:
            return json.dumps({"op": "CHANNELS"}).encode()
        else:
            return json.dumps({"op": "CHANNELS", "channels": channels}).encode()

    @staticmethod
    def users(hash: str, channel: str = None, users: list = None) -> bytes:
        if channel is None and users is None:
            return json.dumps({"op": "USERS", "hash": hash}).encode()
        elif users is None:
            return json.dumps({"op": "USERS", "hash": hash, "channel": channel}).encode()
        elif channel is None:
            return json.dumps({"op": "USERS", "hash": hash, "users": users}).encode()
        else:
            return json.dumps({"op": "USERS", "hash": hash, "channel": channel, "users": users}).encode()
