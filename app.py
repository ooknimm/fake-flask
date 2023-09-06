
from typing import Any, Callable, Dict, List, Optional, Tuple, Iterable


class FakeFlask:
    def __init__(self):
        self.__route: Dict[str, Callable] = {}

    def __call__(self, environ: Dict[str, str], start_response: Callable[[str, List[Tuple[str, str]], None]]) -> "FakeFlask":
        self.environ = environ
        self.start_response = start_response
        return self
    
    def __iter__(self) -> Iterable[bytes]:
        endpoint, query = self.__url_parser()
        controller = self.__controller(endpoint=endpoint)
        status_code, response_headers, response = self.__get_response(controller)
        self.start_response(status_code, response_headers)
        yield response.encode("utf-8")

    def __url_parser(self) -> Tuple[str, str]:
        endpoint = self.environ["PATH_INFO"]
        query = self.environ["QUERY_STRING"]
        if query:
            query = {key: value for key, value in [u.split("=") for u in query.split("&")]}
        return endpoint, query
    
    def __controller(self, endpoint: str) -> Optional[Callable]:
        if endpoint in self.__route:
            return self.__route[endpoint]
        return None
    
    def __get_response(self, controller: Callable, *args) -> Tuple[str, List[Tuple[str, str]], str]:
        if not controller:
            return "404 NOT FOUND", [("Content-Type", "text/plain")], "NOT FOUND"
        try:
            response_body = controller(*args)
        except:
            return "500 INTERNAL ERROR", [("Content-Type", "text/plain")], "INTERNAL ERROR"
        return "200 OK", [("Content-Type", "text/plain")], response_body
    
    def route(self, endpoint: str) -> Callable:
        def controller(func):
            self.__route[endpoint] = func
        return controller
    
    def run(self) -> None:
        from server import Server
        httpd = Server(("127.0.0.1", 9000), self)
        httpd.forever()
