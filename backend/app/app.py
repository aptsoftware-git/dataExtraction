from flask import Flask
from app.routes.upload import upload_bp

def create_app():
    app = Flask(__name__)
    app.register_blueprint(upload_bp)
    return app
