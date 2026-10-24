"""Single-process, configurable daily scheduler for the Pacheco scraper."""

from __future__ import annotations

import asyncio
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.scrapers.pacheco import PachecoScraper


def _state_path() -> Path:
    state_dir = Path(
        os.getenv(
            "PACHECO_STATE_DIR",
            str(Path(__file__).resolve().parents[2] / "data" / "pacheco"),
        )
    )
    return state_dir / "checkpoint.json"


def _checkpoint() -> dict:
    try:
        return json.loads(_state_path().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _next_run(now: datetime, state: dict) -> datetime:
    """Use the durable prior result so container restarts don't reset cadence."""
    completed = state.get("finished_at")
    if completed:
        try:
            finished_at = datetime.fromisoformat(completed)
        except ValueError:
            finished_at = now
        interval = timedelta(hours=float(os.getenv("PACHECO_INTERVAL_HOURS", "24")))
        retry = timedelta(
            minutes=float(os.getenv("PACHECO_FAILURE_RETRY_MINUTES", "60"))
        )
        status = state.get("status")
        return finished_at + (interval if status in {"complete", "partial"} else retry)

    # First run only occurs when explicitly enabled after a controlled run.
    if state:
        retry = timedelta(
            minutes=float(os.getenv("PACHECO_FAILURE_RETRY_MINUTES", "60"))
        )
        started = state.get("started_at")
        try:
            return datetime.fromisoformat(started) + retry if started else now
        except ValueError:
            return now
    return now


async def serve() -> None:
    enabled = os.getenv("PACHECO_SCHEDULER_ENABLED", "false").casefold()
    if enabled not in {"1", "true", "yes", "on"}:
        print("Pacheco scheduler disabled (PACHECO_SCHEDULER_ENABLED=false)")
        while True:
            await asyncio.sleep(3600)

    interval = float(os.getenv("PACHECO_INTERVAL_HOURS", "24"))
    retry_minutes = float(os.getenv("PACHECO_FAILURE_RETRY_MINUTES", "60"))
    if interval <= 0 or retry_minutes <= 0:
        raise ValueError("Pacheco scheduler intervals must be positive")

    while True:
        now = datetime.now(UTC)
        due = _next_run(now, _checkpoint())
        delay = max(0.0, (due - now).total_seconds())
        if delay:
            print(f"Pacheco next run at {due.isoformat()}")
            await asyncio.sleep(delay)

        started = datetime.now(UTC)
        print(f"Pacheco scheduled run started at {started.isoformat()}")
        try:
            await PachecoScraper().run()
        except Exception as error:
            print(f"Pacheco scheduled run failed: {type(error).__name__}: {error}")
        finished = datetime.now(UTC)
        elapsed = (finished - started).total_seconds()
        state = _checkpoint()
        print(
            "Pacheco scheduled run ended: "
            f"status={state.get('status', 'unknown')} "
            f"products={state.get('products_enqueued', 0)} duration_s={elapsed:.1f}"
        )


if __name__ == "__main__":
    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        print("Pacheco scheduler stopped")
