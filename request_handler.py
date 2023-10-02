import socket
import io
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlsplit


class RequestHandler:
    def __init__(self, request: socket.socket, application: Callable[[Dict[str, str], Callable[[str, str], None]], Iterable[bytes]]) -> None:
        self.application = application
        self.rfile: io.BufferedReader = request.makefile("rb", -1)
        self.wfile: io.BufferedWriter = request.makefile("wb", -1)
        self.status: Optional[str] = None
        self.headers: List[Tuple[str, str]] = []
        try:
            self.handle()
        finally:
            self.finish()
        

    def handle(self) -> None:
        raw_requestline = self.rfile.readline(65537)
        command, path, headers = self.parse_request(raw_requestline)
        self.run_wsgi(command, path, headers)

    def finish(self) -> None:
        self.wfile.close()
        self.rfile.close()

    def parse_headers(self) -> None:
        header_list: List[bytes] = []
        while True:
            line = self.rfile.readline(65537)
            if line in (b"\r\n", b"\n", b""):
                break
            header_list.append(line)
        headers = dict((header.decode("latin-1").rstrip("\r\n").split(": ") for header in header_list))
        return headers
        
    def parse_request(self, raw_requestline: bytes) -> Tuple[str, str, Dict[str, str]]:
        request_line = str(raw_requestline, "latin-1").rstrip("\r\n")
        words = request_line.split()
        command, path = words[:2]
        headers = self.parse_headers()
        return command, path, headers
    
    def make_environ(self, command: str, path: str, headers: Dict[str, str]) -> Dict[str, str]: 
        request_url = urlsplit(path)
        path_info = request_url.path
        environ = {
            "PATH_INFO": path_info,
            "QUERY_STRING": request_url.query,
            "REQUEST_METHOD": command,
            "wsgi.input": self.rfile
        }
        for key, value in headers.items():
            key = key.upper().replace("-", "_")
            environ[key] = value
        return environ

    def make_headers(self) -> List[bytes]:
        code, msg = self.status.split(None, 1)
        headers = [(f"HTTP/1.0 {code} {msg}\r\n").encode("latin-1")]
        for h in self.headers:
            headers.append("{}: {}\r\n".format(h[0], h[1]).encode("latin-1")) 
        return headers

    def write(self, data: bytes) -> None:
        headers = self.make_headers()
        self.wfile.write(b"".join(headers))
        self.wfile.write(b"\r\n")
        self.wfile.write(data)
        self.wfile.flush()

    def start_response(self, status: str, headers: Dict[str, str]) -> None:
        self.status = status
        self.headers = headers

    def run_wsgi(self, command: str, path: str, headers: Dict[str, str]) -> None:
        environ = self.make_environ(command, path, headers)
        application_iter = self.application(environ, self.start_response)
        for data in application_iter:
            self.write(data)