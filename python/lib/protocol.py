class Protocol:

    # Name of the service (used for multicast announcements)
    SERVICE_NAME = 'RECH_'

    # OP -1
    # Forcefully closed by server (error)
    @staticmethod
    def close(message: str) -> bytes:
        return ('{"op": -1, "message": "' + message + '"}').encode()

    # OP 0
    # Exit chat connection
    @staticmethod
    def exit() -> bytes:
        return '{"op": 0}'.encode()

    # OP 1
    # Define Nickname
    @staticmethod
    def nickname(name: str) -> bytes:
        return ('{"op": 1, "name": "' + name + '"}').encode()

    # OP 2
    # Broadcast chat Message
    @staticmethod
    def message(message: str, name: str = None) -> bytes:
        if name is None:
            return ('{"op": 2, "message": "' + message + '"}').encode()
        else:
            return ('{"op": 2, "message": "' + message + '", "name": "' + name + '"}').encode()
