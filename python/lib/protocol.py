class Protocol:

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
    def message(message: str) -> bytes:
        return ('{"op": 2, "message": "' + message + '"}').encode()
