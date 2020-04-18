class Client:
    name = 'Anonymous'
    socket = None

    def __init__(self, socket):
        self.socket = socket
