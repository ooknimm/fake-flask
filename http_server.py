import socket
import selectors
from typing import Callable, Optional
from request_handler import RequestHandler

class Server:
    def __init__(self, server_address: str, application: Callable, fd: Optional[int]) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = server_address
        self.application = application
        self.finish = False
        self.bind(fd=fd)
        self.activate()

    def fileno(self) -> int:
        return self.socket.fileno()
    
    def bind(self, fd: Optional[int]) -> None:
        if fd is not None:
            self.close()
            self.socket = socket.fromfd(fd, socket.AF_INET, socket.SOCK_STREAM, )
            self.server_address = self.socket.getsockname()
        else:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
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
                while not self.finish:
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