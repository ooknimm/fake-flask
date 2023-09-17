import socket
import selectors
from typing import Callable, Optional
from request_handler import RequestHandler

class Server:
    def __init__(self, server_address: str, application: Callable, fd: Optional[int]) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = server_address
        self.application = application
        self.fd = fd
        self.finish = False
        self.bind()
        self.activate()

    def fileno(self) -> int:
        return self.socket.fileno()
    
    def bind(self) -> None:
        if self.fd:
            self.socket = socket.fromfd(self.fd, socket.AF_INET, socket.SOCK_STREAM)
            self.server_address = self.socket.getsockname()
        else:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(self.server_address)

    def activate(self) -> None:
        self.socket.listen()

    def close(self) -> None:
        self.socket.close()
    
    def accept(self) -> None:
        return self.socket.accept()
    
    def forever(self) -> None:
        try:
            with selectors.SelectSelector() as selector:
                selector.register(self, selectors.EVENT_READ)
                while self.finish:
                    ready = selector.select(0.5)
                    if ready:
                        self.handle_request()
        finally:
            self.finish = True
            self.close()

    def handle_request(self) -> None:
        request, _ = self.accept()
        RequestHandler(request, self.application)
        request.close()