from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from forge.services.telemetry import (
    system_snapshot,
    top_processes,
)

app = FastAPI(
    title="FORGE Engineering API",
    description="Local Linux engineering and diagnostics API",
    version="0.1.0",
)

@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "application": "FORGE",
        "version": "0.1.0",
    }


@app.get("/api/system")
def system():
    return system_snapshot()


@app.get("/api/processes")
def processes():
    return {"processes": top_processes()}


WEB_DIR = Path(__file__).resolve().parents[1] / "web"

app.mount(
    "/static",
    StaticFiles(directory=WEB_DIR / "static"),
    name="static",
)


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(WEB_DIR / "index.html")
