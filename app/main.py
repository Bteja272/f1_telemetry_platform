from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.telemetry import router as telemetry_router
from app.api.routes.websocket_routes import router as websocket_router
from app.api.routes.metrics import router as metrics_router

app = FastAPI(title="F1 Real-Time Telemetry Streaming Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:4173",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:4173",
        "https://f1-telemetry-platform.vercel.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(telemetry_router)
app.include_router(websocket_router)
app.include_router(metrics_router)


@app.get("/")
def root():
    return {"message": "F1 Telemetry Platform is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}