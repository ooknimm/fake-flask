from contextvars import ContextVar
from functools import partial
import json
from typing import Any, Callable, Dict, Optional, cast, IO, TYPE_CHECKING
from operator import attrgetter
import io
import functools
if TYPE_CHECKING:
    from app import FakeFlask



class AppContext:
    def __init__(self, app: "FakeFlask") -> None:
        self.app = app
        self.g = AppCtxGlobals()
    def push(self) -> None:
        self.token = _cv_app.set(self)
        print(self.token)
    
    def pop(self) -> None:
        print("pop app ctx")
        _cv_app.reset(self.token)

class RequestContext:
    def __init__(self, app: "FakeFlask", environ: Dict[str, Any], path: str, query: Dict[str, str]) -> None:
        self.app = app
        self.request = Request(environ=environ, path=path, query=query)

    def push(self) -> None:
        self.token = _cv_request.set(self)
        print(self.token)
    def pop(self) -> None:
        print("pop req ctx")
        _cv_request.reset(self.token)

class ProxyLookup:
    def __init__(self, f: Callable) -> None:
        if f:
            def bind_f(_, obj):
                return partial(f, obj)
        else:
            bind_f = None
        self.bind_f: Optional[Callable] = bind_f
    def __set_name__(self, _, name: str) -> None:
        self.name = name
    def __get__(self, instance: "LocalProxy", _):
        obj = instance.get_current_obj()
        if self.bind_f:
            return self.bind_f(instance, obj)
        return getattr(obj, self.name)


class LocalProxy:
    def __init__(self, ctx: ContextVar, name: str) -> None:
        def get_current_obj() -> Any:
            get_name = attrgetter(name)
            obj = ctx.get()
            return get_name(obj)
        object.__setattr__(self, "get_current_obj", get_current_obj)

    __doc__ = ProxyLookup(__doc__)
    __repr__ = ProxyLookup(repr)
    __str__ = ProxyLookup(str)
    __getattr__ = ProxyLookup(getattr)
    __setattr__ = ProxyLookup(setattr)
    __delattr__ = ProxyLookup(delattr)
    __dir__ = ProxyLookup(dir)


class Request:
    def __init__(self, environ: Dict[str, Any], path: str, query: Dict[str, str]) -> None:
        self.method = environ.get("REQUEST_METHOD", "GET")
        self.path = path
        self.query = query
        self.environ = environ
        self.stream = cast(io.BufferedReader, self.environ["wsgi.input"])
    
    def read_stream(self):
        content_length = self.environ.get("CONTENT_LENGTH")
        if content_length is not None:
            return self.stream.read(int(content_length))
        return self.stream.read1()
        
    def get_json(self) -> Any:
        print(f"request data stream: {self.stream}")
        return json.loads(self.read_stream())
    
    
class AppCtxGlobals: 
    def __getattr__(self, name: str) -> Any:
        try:
            self.__dict__[name]
        except KeyError:
            print(f"KeyError {name}")
    def __setattr__(self, name: str, value: Any):
        self.__dict__[name] = value

    def get(self, name: str, default: Any) -> Any:
        return self.__dict__.get(name, default)
    
    def pop(self, name: str, default = None) -> Any:
        if not default:
            return self.__dict__.pop(name)
        else:
            return self.__dict__(name, default)


# 앱 컨텍스트
_cv_app: ContextVar[AppContext] = ContextVar("flask.app_ctx")

# 요청 컨텍스트
_cv_request: ContextVar[RequestContext] = ContextVar("flask.request_ctx")

request: Request = LocalProxy(_cv_request, "request")
g: AppCtxGlobals = LocalProxy(_cv_app, "g")
current_app = LocalProxy(_cv_app, "app")