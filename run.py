import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    # 从环境变量读取端口，默认5000（本地开发）
    port = int(os.environ.get("PORT", 5000))
    # 根据环境决定是否开启调试模式
    debug = os.environ.get("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)
