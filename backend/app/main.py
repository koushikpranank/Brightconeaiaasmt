import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes_analytics, routes_dashboard, routes_disruptions, routes_reports, routes_supply, routes_workflow
from app.database import init_db
from app.scheduler import start_scheduler, stop_scheduler
from app.seed_data import seed

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="Agentic AI Supply Chain Disruption Monitoring System",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_supply.router, prefix="/api")
app.include_router(routes_disruptions.router, prefix="/api")
app.include_router(routes_workflow.router, prefix="/api")
app.include_router(routes_reports.router, prefix="/api")
app.include_router(routes_dashboard.router, prefix="/api")
app.include_router(routes_analytics.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}
