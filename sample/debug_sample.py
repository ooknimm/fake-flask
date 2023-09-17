import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from app import FakeFlask
app = FakeFlask()


@app.route("/")
def home():
    time.sleep(3)
    return "hello world"

@app.route("/ping")
def ping():
    return "pong"

app.run(debug=True)

