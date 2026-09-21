"""Automated monitoring: polls all simulated sources on a fixed interval (Requirement 2)."""
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from sqlmodel import Session

from app.config import settings
from app.database import engine
from app.services.case_runner import run_monitoring_sweep

logger = logging.getLogger("scheduler")
scheduler = BackgroundScheduler()


def scheduled_sweep() -> None:
    with Session(engine) as session:
        try:
            cases = run_monitoring_sweep(session)
            if cases:
                logger.info("Monitoring sweep produced/updated %d case(s)", len(cases))
        except Exception:
            logger.exception("Monitoring sweep failed")


def start_scheduler() -> None:
    if not scheduler.running:
        scheduler.add_job(scheduled_sweep, "interval", seconds=settings.monitor_interval_seconds, id="monitoring_sweep")
        scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
