from app import FakeFlask, request
import time

app = FakeFlask()


@app.route("/")
def home():
    time.sleep(3)
    return "hello world"

@app.route("/ping")
def ping():
    return "pong"

app.run()
