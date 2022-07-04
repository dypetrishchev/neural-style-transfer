"""Run the style transfer model application."""

from flask import Flask

from src.utils.requests import load_users
from src.views import register_views


def create_app():
    app = Flask(__name__)
    users = load_users("users.yaml")
    register_views(app, users)
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, ssl_context="adhoc")
