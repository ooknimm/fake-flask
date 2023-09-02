import email.utils
from http.client import HTTPMessage
from socketserver import BaseRequestHandler
import socket
import io
import selectors
import time
from typing import List, Optional, Tuple
from urllib.parse import urlsplit

class _SocketWriter(io.BufferedIOBase):
    def __init__(self, sock: socket.socket):
        self._socket = sock
    
    def writable(self):
        return True
    
    def write(self, b):
        self._socket.sendall(b)
        with memoryview(b) as view:
            return view.nbytes
        
    def fileno(self):
        return self._socket.fileno()


class StreamRequestHandler(BaseRequestHandler):
    def __init__(self, request: socket.socket, client_address, server) -> None:
        super().__init__(request, client_address, server)
        self.request: socket.socket
        self.rfile: io.BufferedReader
        self.wfile: _SocketWriter

    def setup(self) -> None:
        self.request.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
        self.rfile = self.request.makefile("rb", -1)
        self.wfile = _SocketWriter(self.request)
        print(self.request)

    def finish(self):
        if not self.wfile.closed:
            try:
                self.wfile.flush()
            except socket.error:
                pass
        self.wfile.close()
        self.rfile.close()


class WSGIRequestHandler(StreamRequestHandler):
    def __init__(self, request: socket, client_address, server) -> None:
        super().__init__(request, client_address, server)
        self.status: Optional[str] = None
        self.headers: List[Tuple[str, str]] = []
        self._headers_buffer = []

    def handle_one_request(self):
        self.raw_requestline = self.rfile.readline(65537)
        self.parse_request()
        self.run_wsgi()

    def parse_headers(self):
        header_list = []
        while True:
            line = self.rfile.readline(65537)
            if line in (b"\r\n", b"\n", b""):
                break
            header_list.append(line)
        headers = dict((header.decode("iso-8859-1").rstrip("\r\n").split(": ") for header in header_list))
        return headers
        
    def parse_request(self):
        self.request_line = str(self.raw_requestline, "iso-8859-1").rstrip("\r\n")
        words = self.request_line.split()
        self.command, self.path = words[:2]
        if self.path.startswith("//"):
            self.path = "/" + self.path.lstrip("/")
        self.header = self.parse_headers()

    def handle(self) -> None:
        self.handle_one_request()

    def make_environ(self): 
        request_url = urlsplit(self.path)
        path_info = request_url.path
        return {
            "PATH_INFO": path_info,
            "QUERY_STRING": request_url.query,
            "REQUEST_METHOD": self.command
        }

    def write(self, data):
        code, msg = self.status.split(None, 1)
        _headers_buffer = []
        _headers_buffer.append((f"HTTP/1.0 {code} {msg}\r\n").encode("latin-1"))
        _headers = ["{}: {}\r\n".format(h[0], h[1]).encode("latin-1") for h in self.headers]
        _headers_buffer.extend(_headers)
        self.wfile.write(b"".join(_headers_buffer))
        self.wfile.write(b"\r\n")
        self.wfile.write(data)
        self.wfile.flush()

    def start_response(self, status, headers):
        self.status = status
        self.headers = headers

    def run_wsgi(self):
        environ = self.make_environ()
        application_iter = self.server.application(environ, self.start_response)
        for data in application_iter:
            self.write(data)