import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from app import FakeFlask, request
app = FakeFlask()


@app.route("/")
def home():
    print(request.get_json())
    return "hello world"

@app.route("/ping")
def ping():
    return "pong"

app.run(port=9000, debug=True)

