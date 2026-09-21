#!/usr/bin/env python3
"""
JobFinderOS — Hermes-flavored scheduler tick.
Reads config/scheduler.yaml, checks whether any scheduled job is due for the
current time, and prints the decision. Replaces the Claude Code launchd bridge
as the scheduling layer; on Hermes, scheduled runs are one of:

- A Hermes cronjob per scheduled job (preferred), driven by this file's
  computed due windows.
- This tick printed as a dry-run source of truth for whichever cronjob
  implementation is chosen.

Does NOT yet spawn subagents. Commit 4a adds the skill/persona/profile loading
helpers (testable with bare `python3 --dry-run`); Commit 4b wires the actual
delegate_task calls.
"""

from __future__ import annotations

import argparse
import json
import re
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


# ---- skill / persona / profile loading (Commit 4a) ----

_SKILL_LINE_RE = re.compile(r"^\*\*Agent:\*\*\s*`?(\w+)`?", re.MULTILINE)
_ORCHESTRATOR_PERSONA_RE = re.compile(r"runs in this session as `(\w+)`")


def load_skill_text(root: Path, skill_name: str) -> str:
    """Read a skill file from skills/{skill_name}.md."""
    path = root / "skills" / f"{skill_name}.md"
    if not path.exists():
        raise FileNotFoundError(f"skill not found: {path}")
    return path.read_text(encoding="utf-8")


def agent_name_for_skill(skill_text: str) -> str:
    """Extract the Hermes subagent persona a skill should run under.

    Skills name the agent right after the frontmatter. Most skills name a
    persona directly (``**Agent:** scout``); the orchestrator skill names an
    orchestrator role and then says which persona it runs as in-session::

        **Agent:** orchestrator · runs in this session as `coach` ...

    We return the in-session persona for orchestrator skills, and the direct
    name for everyone else, so the tick can load the right persona file.
    """
    m = _SKILL_LINE_RE.search(skill_text)
    if not m:
        raise ValueError("skill has no parsable **Agent:** line")
    name = m.group(1)
    if name == "orchestrator":
        pm = _ORCHESTRATOR_PERSONA_RE.search(skill_text)
        if not pm:
            raise ValueError("orchestrator skill has no 'runs in this session as `<persona>`' clause")
        return pm.group(1)
    return name


def load_persona_text(root: Path, agent_name: str) -> str:
    """Read a persona file from personas/{agent_name}.md."""
    path = root / "personas" / f"{agent_name}.md"
    if not path.exists():
        raise FileNotFoundError(f"persona not found: {path}")
    return path.read_text(encoding="utf-8")


def profile_note(root: Path) -> str:
    """One-line note about which profile the tick should pass to subagents.

    Uses the real profile at config/profile.md when it exists; otherwise falls
    back to the fictional demo at config/examples/fictional_profile.json.
    """
    real = root / "config" / "profile.md"
    if real.exists():
        return "Real candidate profile at config/profile.md — read it for the candidate's specifics."
    demo = root / "config" / "examples" / "fictional_profile.json"
    if demo.exists():
        return "FICTIONAL demo profile at config/examples/fictional_profile.json — not a real person; demonstration only."
    return "No profile found; subagents will run without candidate specifics."


def load_profile_text(root: Path) -> str:
    """Return the profile file content subagents should read."""
    real = root / "config" / "profile.md"
    if real.exists():
        return real.read_text(encoding="utf-8")
    demo = root / "config" / "examples" / "fictional_profile.json"
    if demo.exists():
        return demo.read_text(encoding="utf-8")
    return ""


# ---- end loading helpers ----


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
    # config uses launchd convention: 0=Sunday, 1=Monday, ..., 6=Saturday
    # convert to Python weekday (0=Monday ... 6=Sunday)
    py_wd = (weekday + 6) % 7
    monday = monday_of_week(now.date())
    t = datetime(now.year, now.month, now.day, hour, minute)
    return datetime.combine(monday + __import__("datetime").timedelta(days=py_wd),
                            t.timetz().replace(tzinfo=now.tzinfo))


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

    # Commit 4b: replace this placeholder with actual delegate_task calls.
    # today's mapping (from scheduler.yaml + skills/* agent lines):
    #   weekly_due -> skills/mark-weekly.md  -> persona mark
    #   daily_due  -> skills/jobs-daily.md  -> persona coach (orchestrator runs as coach)
    #   watch_due  -> skills/jobs-priority-watch.md -> persona scout
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
