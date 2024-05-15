from flask import Flask, render_template
import os

app = Flask(__name__)

@app.route("/")
def home():
    pod_name = os.getenv("POD_NAME")
    pod_ip = os.getenv("POD_IP")
    namespace = os.getenv("POD_NAMESPACE")
    node_name = os.getenv("NODE_NAME")

    app_version = os.getenv("APP_VERSION")
    app_title = os.getenv("APP_TITLE")
    description = os.getenv("APP_DESCRIPTION")

    return render_template("index.html", pod_name=pod_name, pod_ip=pod_ip, namespace=namespace, 
                           node_name=node_name, app_version=app_version, app_title=app_title, description=description)

@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
