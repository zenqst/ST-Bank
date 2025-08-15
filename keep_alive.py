from threading import Thread

from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    return {"status": "🤖 Fast"}


def run():
    app.run(host="127.0.0.1", port=8080)


def keep_alive():
    t = Thread(target=run)
    t.start()
