from fastapi import FastAPI

from app.api.routes.telemetry import router as telemetry_router

app = FastAPI(title="F1 Real-Time Telemetry Streaming Platform")

app.include_router(telemetry_router)


@app.get("/")
def root():
    return {"message": "F1 Telemetry Platform is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}