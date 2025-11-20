import socket


class RaspberrySender:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    def send(self, message: str):
        try:
            with socket.socket() as s:
                s.settimeout(3)  # optional: avoid long hang
                s.connect((self.host, self.port))
                s.sendall(message.encode('utf-8'))
        except (ConnectionRefusedError, socket.timeout, OSError) as e:
            print(f"⚠️ Could not send message: {e}")