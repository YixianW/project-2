from flask import Flask

from .routes import api


def create_app() -> Flask:
    app = Flask(__name__, static_folder="../static", template_folder="../templates")
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
    app.register_blueprint(api)
    return app
