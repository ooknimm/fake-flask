from app import FakeFlask, g

from sample.sample_service import home_service

app = FakeFlask()


@app.route("/")
def home():
    g.foo = "bar"
    home_service()
    return "hello world"

@app.route("/ping")
def ping():
    return "pong"

