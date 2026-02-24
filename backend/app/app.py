from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.upload import router as upload_router

def create_app():
    app = FastAPI(
        title="Data Extraction API",
        description="PDF Data Extraction Service",
        version="1.0.0"
    )

    # Enable CORS for all routes
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure this based on your frontend URL
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(upload_router)

    return app