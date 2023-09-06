    
from app import FakeFlask


pseudo_flask = FakeFlask()


@pseudo_flask.route("/")
def home():
    return "hello world"

@pseudo_flask.route("/ping")
def ping():
    return "pong"

pseudo_flask.run()
