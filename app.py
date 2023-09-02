from wsgiref.simple_server import make_server
from request_handler import WSGIRequestHandler
from server import Server

class PseudoFlask:
    def __init__(self):
        self.__route = {}

    def __call__(self, environ, start_response):
        self.environ = environ
        self.start_response = start_response
        return self
    
    def __iter__(self):
        endpoint, query = self.__url_parser()
        controller = self.__controller(endpoint=endpoint)
        status_code, response_headers, response = self.__get_response(controller)
        self.start_response(status_code, response_headers)
        yield response.encode("utf-8")
    
    def __url_parser(self):
        path = self.environ["PATH_INFO"]
        endpoint = path
        query = self.environ["QUERY_STRING"]
        if query:
            query = {key: value for key, value in [u.split("=") for u in query.split("&")]}
        return endpoint, query
    
    def __controller(self, endpoint):
        return self.__route[endpoint]
    
    def __get_response(self, controller, *args):
        response_body = controller(*args)
        return "200 OK", [("Content-Type", "text/plain")], response_body
    
    def route(self, endpoint):
        def controller(func):
            self.__route[endpoint] = func
        return controller
    
pseudo_flask = PseudoFlask()


@pseudo_flask.route("/")
def home():
    return "hello world"

@pseudo_flask.route("/ping")
def ping():
    return "pong"

httpd = Server(("127.0.0.1", 9000), pseudo_flask)
httpd.forever()
