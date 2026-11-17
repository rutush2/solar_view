import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from app.db import init_db, insert_live_tick
from app.view import get_live_dashboard_data, run_live_diagnosis


async def _telemetry_loop():
    while True:
        await asyncio.sleep(2)
        insert_live_tick()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    task = asyncio.create_task(_telemetry_loop())
    yield
    task.cancel()


app = FastAPI(title="solar_view", lifespan=lifespan)


@app.get("/live")
def live_metrics():
    return get_live_dashboard_data()


@app.post("/diagnose")
def diagnose():
    try:
        return run_live_diagnosis()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))