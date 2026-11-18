import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.get("/")
def home():
    return jsonify(
        application=os.getenv("APP_NAME", "platform-demo"),
        message="Hello from a Kubernetes-managed application!",
        version=os.getenv("APP_VERSION", "1.0.0"),
    )

@app.get("/health")
def health():
    return jsonify(status="healthy"), 200

@app.get("/ready")
def ready():
    return jsonify(status="ready"), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
