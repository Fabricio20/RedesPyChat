class Client:
    name = 'Anonymous'
    socket = None

    def __init__(self, socket):
        self.socket = socket

    def close(self):
        if self.socket is not None:
            self.socket.close()

    def send(self, message):
        if self.socket is not None:
            self.socket.sendall(message)
