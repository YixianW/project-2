import os
from flask import Flask
from flask_cors import CORS

from .routes import api


def create_app() -> Flask:
    # 计算项目根目录，确保无论从哪里运行都能找到static和templates文件夹
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(__name__, 
                static_folder=os.path.join(base_dir, "static"), 
                template_folder=os.path.join(base_dir, "templates"))
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
    
    # 启用 CORS，支持前后端分离部署
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    app.register_blueprint(api)
    return app


# create a module‐level application object for WSGI servers that
# expect to import ``app`` from the package (e.g. using ``gunicorn
# app:app``).  This keeps the factory pattern available while
# providing a convenient default for deployments.
app: Flask = create_app()
