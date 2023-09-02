import socket
import selectors
from request_handler import WSGIRequestHandler

class Server:
    def __init__(self, server_address, application):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = server_address
        self.application = application
        self.bind()
        self.activate()

    def fileno(self):
        return self.socket.fileno()
    
    def bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)

    def activate(self):
        self.socket.listen()

    def close(self):
        self.socket.close()
    
    def accept(self):
        return self.socket.accept()
    
    def forever(self):
        with selectors.SelectSelector() as selector:
            selector.register(self, selectors.EVENT_READ)
            while True:
                ready = selector.select(0.5)
                if ready:
                    self.handle_request()

    def handle_request(self):
        request, client_address = self.accept()
        WSGIRequestHandler(request, client_address, self)
        request.close()