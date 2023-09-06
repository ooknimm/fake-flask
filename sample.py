    
from app import FakeFlask


app = FakeFlask()


@app.route("/")
def home():
    return "hello world"

@app.route("/ping")
def ping():
    return "pong"

app.run()
