    
from app import FakeFlask


fake_flask = FakeFlask()


@fake_flask.route("/")
def home():
    return "hello world"

@fake_flask.route("/ping")
def ping():
    return "pong"

fake_flask.run()
