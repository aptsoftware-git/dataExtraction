from flask import Flask
from flask_cors import CORS
from app.routes.upload import upload_bp

def create_app():
    app = Flask(__name__)

    # Enable CORS for all routes
    CORS(app)

    app.register_blueprint(upload_bp)

    return app