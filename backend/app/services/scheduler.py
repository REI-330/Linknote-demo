from __future__ import annotations

import threading
from datetime import date, datetime, timedelta

from ..config.settings import AppConfig
from .daily_runner import load_runner_state, scheduled_run_daily


class DailyScheduler:
    def __init__(self, config_loader):
        self._config_loader = config_loader
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, name="linknote-daily-scheduler", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5)

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                config = self._config_loader()
                if config.schedule.enabled and _should_run_now(config):
                    scheduled_run_daily(config)
            except Exception:
                pass
            self._stop_event.wait(30)


def _should_run_now(config: AppConfig) -> bool:
    try:
        target_time = datetime.strptime(config.schedule.daily_time, "%H:%M").time()
    except ValueError:
        return False
    now = datetime.now()
    if now.time() < target_time:
        return False
    state = load_runner_state(config)
    last_report_date = str(state.get("last_report_date", ""))
    last_reason = str(state.get("last_reason", ""))
    return not (last_reason == "scheduled" and last_report_date == date.today().isoformat())


def next_run_at(config: AppConfig, *, now: datetime | None = None) -> str | None:
    if not config.schedule.enabled:
        return None
    try:
        target_time = datetime.strptime(config.schedule.daily_time, "%H:%M").time()
    except ValueError:
        return None
    current = now or datetime.now()
    candidate = current.replace(hour=target_time.hour, minute=target_time.minute, second=0, microsecond=0)
    if candidate <= current:
        candidate += timedelta(days=1)
    return candidate.strftime("%Y-%m-%d %H:%M:%S")
