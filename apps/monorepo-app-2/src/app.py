from flask import Flask
app = Flask(__name__)

@app.route("/")
def hello():
    return "Monorepo-app-2 v0.0.1"