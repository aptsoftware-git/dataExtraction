import logging
from flask import Flask
from app.routes.upload import upload_bp

# Disable Flask request logs
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# Disable urllib3 connection spam
logging.getLogger("urllib3").setLevel(logging.CRITICAL)


def create_app():
    app = Flask(__name__)
    app.register_blueprint(upload_bp)
    return app