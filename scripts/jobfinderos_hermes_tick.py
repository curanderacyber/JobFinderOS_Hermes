#!/usr/bin/env python3
"""
JobFinderOS — Hermes-flavored scheduler tick (planned).
Reads config/scheduler.yaml, checks whether any scheduled job is due for the
current time, and prints the decision. Replaces the Claude Code launchd bridge
as the scheduling layer; on Hermes, scheduled runs are one of:

- A Hermes cronjob per scheduled job (preferred), driven by this file's
  computed due windows.
- This tick printed as a dry-run source of truth for whichever cronjob
  implementation is chosen.

Does NOT yet spawn subagents. That is a later commit.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, date
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as e:
    print("jobfinderos_hermes_tick.py requires PyYAML: pip install PyYAML", file=sys.stderr)
    raise SystemExit(1) from e

STATE_FILENAME = "scheduler_state.json"
LOCK_FILENAME = "scheduler.lock"


def project_root() -> Path:
    return (Path(__file__).resolve().parent.parent).resolve()


def state_path(root: Path) -> Path:
    d = root / ".jobfinderos_hermes"
    d.mkdir(parents=True, exist_ok=True)
    return d / STATE_FILENAME


def load_state(root: Path) -> dict[str, Any]:
    p = state_path(root)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_state(root: Path, state: dict[str, Any]) -> None:
    p = state_path(root)
    p.write_text(json.dumps(state, indent=2), encoding="utf-8")


def load_config(root: Path, config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        print(f"config not found: {config_path}", file=sys.stderr)
        return {}
    with open(config_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    return cfg


def localize(now: datetime, tz_name: str | None) -> datetime:
    """Best-effort localize to the profile timezone; fall back to system TZ."""
    if tz_name:
        try:
            import zoneinfo
            tz = zoneinfo.ZoneInfo(tz_name)
            return now.astimezone(tz)
        except Exception:
            pass
    return now.astimezone()


def daily_slot_today_local(now: datetime, hour: int, minute: int) -> datetime:
    t = datetime(now.year, now.month, now.day, hour, minute)
    return datetime.combine(now.date(), t.timetz().replace(tzinfo=now.tzinfo))


def monday_of_week(d: date) -> date:
    return d - __import__("datetime").timedelta(days=d.weekday())


def week_slot_start_local(now: datetime, weekday: int, hour: int, minute: int) -> datetime:
    py_wd = weekday  # 0 = Monday through 6 = Sunday (config convention; see README)
    monday = monday_of_week(now.date())
    slot_date = monday + __import__("datetime").timedelta(days=py_wd)
    t = datetime(now.year, now.month, now.day, hour, minute)
    return datetime.combine(slot_date, t.timetz().replace(tzinfo=now.tzinfo))


def weekly_is_due(state: dict[str, Any], now: datetime, cfg: dict[str, Any]) -> bool:
    w = cfg.get("weekly") or {}
    wd = int(w.get("weekday", 1))
    wh = int(w.get("hour", 8))
    wm = int(w.get("minute", 0))
    slot_start = week_slot_start_local(now, wd, wh, wm)
    if now < slot_start:
        return False
    cur = (now.isocalendar().year, now.isocalendar().week)
    last = (state.get("last_weekly_iso_year"), state.get("last_weekly_iso_week"))
    if last == cur:
        return False
    return True


def daily_is_due(state: dict[str, Any], now: datetime, cfg: dict[str, Any], weekly_due: bool) -> bool:
    if weekly_due:
        return False
    d = cfg.get("daily") or {}
    dh = int(d.get("hour", 7))
    dm = int(d.get("minute", 0))
    slot_today = daily_slot_today_local(now, dh, dm)
    if now < slot_today:
        return False
    if state.get("last_daily_date") == now.date().isoformat():
        return False
    return True


def watch_is_due(now: datetime, cfg: dict[str, Any]) -> bool:
    w = cfg.get("watch") or {}
    wh = int(w.get("hour", 9))
    wm = int(w.get("minute", 0))
    slot = daily_slot_today_local(now, wh, wm)
    return now >= slot


def main() -> int:
    ap = argparse.ArgumentParser(description="JobFinderOS Hermes-flavored scheduler tick")
    ap.add_argument("--dry-run", action="store_true", help="Print decisions only; do not run jobs")
    ap.add_argument("--config", type=Path, help="Override path to scheduler.yaml")
    args = ap.parse_args()

    root = project_root()
    cfg_path = args.config or (root / "config" / "scheduler.yaml")
    cfg = load_config(root, cfg_path)
    state = load_state(root)
    now = localize(datetime.now(), cfg.get("timezone") or None)

    weekly_due = weekly_is_due(state, now, cfg)
    daily_due = daily_is_due(state, now, cfg, weekly_due)
    watch_due = watch_is_due(now, cfg)

    decision: dict[str, Any] = {
        "now": now.isoformat(),
        "timezone": cfg.get("timezone") or "system",
        "weekly_due": weekly_due,
        "daily_due": daily_due,
        "watch_due": watch_due,
        "state": state,
    }

    if args.dry_run:
        print(json.dumps(decision, indent=2))
        return 0

    # Placeholder for actual runs (later commit):
    # weekly_due  -> spawn mark subagent with skills/mark-weekly.md as goal
    # daily_due   -> spawn coach subagent with skills/jobs-daily.md as goal
    # watch_due   -> spawn scout subagent with skills/jobs-priority-watch.md as goal
    if weekly_due:
        state["last_weekly_iso_year"] = now.isocalendar().year
        state["last_weekly_iso_week"] = now.isocalendar().week
        state["last_weekly_run_date"] = now.date().isoformat()
        state["last_daily_date"] = now.date().isoformat()
        save_state(root, state)
    elif daily_due:
        state["last_daily_date"] = now.date().isoformat()
        save_state(root, state)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
