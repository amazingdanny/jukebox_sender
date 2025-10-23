import socket


class RaspberrySender:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    def send(self, message: str):
        with socket.socket() as s:
            s.connect((self.host, self.port))
            s.sendall(message.encode('utf-8'))