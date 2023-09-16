from app import g, request, current_app
import time

def home_service():
    print(f"request: {request}")
    print(f"g: {g}")
    print(f"current_app: {current_app}")
    print(request.path)
    print(g.foo)
    time.sleep(3)