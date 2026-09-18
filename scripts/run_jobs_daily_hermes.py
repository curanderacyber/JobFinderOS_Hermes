#!/usr/bin/env python3
"""
JobFinderOS — Hermes driver for the daily scan (jobs-daily).

Bounded end-to-end run of the jobs-daily skill against a FICTIONAL candidate
profile, as the proof-of-concept that the port actually runs a skill as a
Hermes subagent. Not a real candidate's data; not scheduled; does not touch
the real vault.

Reads:
  - personas/coach.md, personas/scout.md, personas/mark.md (personas)
  - skills/jobs-daily.md (the orchestrator skill)
  - config/examples/fictional_profile.md (fictional candidate config)

What it runs (matches the HERMES.md worked example, coach + jobs-daily goal):
  1. Market Pulse  -> subagent: mark, context: personas/mark.md, goal: read
     skills/mark-pulse.md and execute its Task section.
  2. Scout         -> subagent: scout, context: personas/scout.md, goal: read
     skills/jobs-scout.md and execute its Task section.
  3. Digest+close  -> subagent: coach, context: personas/coach.md, goal: read
     skills/jobs-daily.md and execute its Task section (this is the orchestrator;
     it covers pulse + scout + email + digest in the real flow, but for the
     fictional run we only run pulse and scout as separate subagents, then a
     final coach pass that closes out without email since there is no real inbox).

Email is skipped for the fictional run: there is no real Gmail inbox and the
fictional candidate has no real threads. The coach pass is told to treat email
as a no-op and to produce the consolidated Recruiter's read + a written daily
digest to the vault output dir.

Output (gitignored, under vault/examples/jobfinderos-hermes-run/):
  - README.md  (what ran, when, why fictional)
  - run_report.md (the consolidated report: files written, pipeline changes,
    anything due, Recruiter's read)
  - daily_digest.md (the morning briefing the coach would write)
  - market_pulse_report.md (what mark returned)
  - scout_report.md (what scout returned)

Safety
  - This script does NOT commit or push anything.
  - It does NOT send email.
  - It writes only under vault/examples/jobfinderos-hermes-run/, which is a
    dedicated, explicitly-gitignored demo output dir.
  - It does NOT read or write any real candidate's config or vault.

How to run
  python3 scripts/run_jobs_daily_hermes.py

How to read the result
  open vault/examples/jobfinderos-hermes-run/run_report.md

Connection to the port story
  This is the "does not yet run a skill end to end as a Hermes subagent" gap
  from commit 1/2, closed with a bounded, fictional, demonstrable run. It is
  the smallest real end-to-end artifact: a driver that spawns Hermes subagents
  using delegate_task with the HERMES.md worked example as the template, passes
  persona + skill as context/goal, and writes real vault-style Markdown output.
  The fictional profile keeps it career-neutral and safe to commit.

Co-Authored-By: Hermes Agent <noreply@nousresearch.com>
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from datetime import datetime
from pathlib import Path

try:
    from hermes_tools import delegate_task, shell_quote
except Exception as e:
    print(f"This driver is written for the Hermes runtime (hermes_tools). "
          f"Running it outside Hermes will fail: {e}", file=sys.stderr)
    sys.exit(2)


ROOT = Path(__file__).resolve().parent.parent
PERSONAS = ROOT / "personas"
SKILLS = ROOT / "skills"
EXAMPLE_CONFIG = ROOT / "config" / "examples" / "fictional_profile.json"
VAULT_OUT = ROOT / "vault" / "examples" / "jobfinderos-hermes-run"


PULSE_GOAL = textwrap.dedent("""\
    Read skills/mark-pulse.md and execute its Task section. You are running
    against the FICTIONAL candidate defined in config/examples/fictional_profile.json.
    Treat this as a demonstration run: use the profile's target tiers and watch
    list as your market, do real web research against the named companies, and
    write the Market Pulse + Daily Marketing Brief to the output directory
    vault/examples/jobfinderos-hermes-run/ instead of the real vault/Market Intel/.
    Return a report: top signals with sources, files written, and the
    Recruiter's read. No email. No outreach.
    """).strip()

SCOUT_GOAL = textwrap.dedent("""\
    Read skills/jobs-scout.md and execute its Task section. You are running
    against the FICTIONAL candidate defined in config/examples/fictional_profile.json.
    Treat this as a demonstration run: scan the profile's target companies and
    watch list directly (careers pages / ATS), score each role against the rubric
    in config/examples/fictional_profile.json, log the strong ones as opportunity
    notes under vault/examples/jobfinderos-hermes-run/Companies/ instead of the
    real vault/Companies/, and surface actionable finds into the Dashboard-ish
    file under vault/examples/jobfinderos-hermes-run/. Return a report: roles
    found (table), files written, anything that changes priorities, and the
    Recruiter's read. No email. No outreach. No git.
    """).strip()

DAILY_GOAL = textwrap.dedent("""\
    Read skills/jobs-daily.md and execute its Task section, but as a bounded,
    FICTIONAL demonstration run against config/examples/fictional_profile.json.
    You already have the Market Pulse and scout results in the output directory
    vault/examples/jobfinderos-hermes-run/. Perform the Email pass as a no-op
    (there is no real inbox and the fictional candidate has no real threads —
    note that explicitly in the report). Perform the Digest pass: compile the
    morning briefing into vault/examples/jobfinderos-hermes-run/daily_digest.md
    using the Daily Digest template from CLAUDE.md, with the scoped Dashboard
    refresh and a warm-path coverage check against the opportunity notes you
    just wrote. Then produce one consolidated Recruiter's read covering market,
    pipeline, and the single most important move for the fictional candidate.
    If anything is due (drafts to offer, decisions to make), list it and stop —
    do not draft. Write nothing until a human says yes. Never draft outreach in
    subagent mode.
    """).strip()

COACH_CONTEXT = textwrap.dedent("""\
    Read personas/coach.md first. You are Coach, the candidate's recruiter —
    not a job board, not a clerk. Read config/examples/fictional_profile.json
    and the doctrine file config/recruiter_playbook.md first; they hold
    everything about the (fictional) candidate and the doctrine. Warm-path-first,
    two-fact rule, human-in-the-loop on every message, never send, never commit
    or push. Drafting voice is a hard gate (no em dashes, no hedging openers,
    no formulaic closers, no rule-of-three lists). Return a report at the end:
    files written, pipeline changes, anything due, and the Recruiter's read.
    This is a FICTIONAL demonstration run — the profile in
    config/examples/fictional_profile.json is not a real person.
    """).strip()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def ensure_out_dir() -> Path:
    d = VAULT_OUT
    d.mkdir(parents=True, exist_ok=True)
    (d / "Market Intel").mkdir(parents=True, exist_ok=True)
    (d / "Companies").mkdir(parents=True, exist_ok=True)
    (d / "Daily Digests").mkdir(parents=True, exist_ok=True)
    (d / "Archive" / "Daily Jobs Watch").mkdir(parents=True, exist_ok=True)
    (d / "Outreach Drafts").mkdir(parents=True, exist_ok=True)
    return d


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def run_mark() -> str:
    print("==> spawning mark subagent (market pulse)")
    report = delegate_task(
        context=COACH_CONTEXT.replace("Coach, the candidate's recruiter",
                                      "Mark, the candidate's market intelligence analyst").replace(
            "Read personas/coach.md first.",
            "Read personas/mark.md first."),
        goal=PULSE_GOAL,
    )
    return report


def run_scout() -> str:
    print("==> spawning scout subagent (jobs-scout)")
    report = delegate_task(
        context=COACH_CONTEXT.replace("Coach, the candidate's recruiter",
                                      "Scout, the candidate's opportunity crawler").replace(
            "Read personas/coach.md first.",
            "Read personas/scout.md first."),
        goal=SCOUT_GOAL,
    )
    return report


def run_coach(mark_report: str, scout_report: str) -> str:
    print("==> spawning coach subagent (jobs-daily orchestrator, email=no-op)")
    combined_goal = DAILY_GOAL + "\n\n---- pulse (mark) ----\n" + mark_report + "\n\n---- scout ----\n" + scout_report
    report = delegate_task(
        context=COACH_CONTEXT,
        goal=combined_goal,
    )
    return report


def write_run_report(mark_report: str, scout_report: str, coach_report: str) -> Path:
    now = datetime.now().astimezone()
    ts = now.strftime("%Y-%m-%d %H:%M %Z")
    lines = [
        f"# JobFinderOS Hermes run — {now.date().isoformat()}",
        "",
        f"> **JobFinderOS:** Hermes demo · {ts}",
        "",
        "## What ran",
        "",
        "Bounded end-to-end demonstration of the `jobs-daily` skill running as a "
        "Hermes subagent against a fictional candidate profile. This is the proof-of-concept "
        "for the port from Claude Code to Hermes: a driver (`scripts/run_jobs_daily_hermes.py`) "
        "that spawns `mark`, `scout`, and `coach` subagents via `delegate_task`, passing each "
        "persona from `personas/` as context and the corresponding skill from `skills/` as the "
        "goal — exactly the shape described in `HERMES.md`.",
        "",
        "## Inputs",
        "",
        "- Personas: `personas/coach.md`, `personas/scout.md`, `personas/mark.md`",
        "- Skills: `skills/jobs-daily.md`, `skills/mark-pulse.md`, `skills/jobs-scout.md`",
        "- Fictional candidate profile: `config/examples/fictional_profile.json`",
        "- Doctrine: `config/recruiter_playbook.md` (the recruiter's read, warm-path-first, two-fact rule, etc.)",
        "",
        "## What was run (Hermes subagents)",
        "",
        "1. **Market Pulse** → mark subagent: read `skills/mark-pulse.md`, execute its Task section.",
        "2. **Scout** → scout subagent: read `skills/jobs-scout.md`, execute its Task section.",
        "3. **Daily (coach orchestrator, email=no-op)** → coach subagent: read `skills/jobs-daily.md`, "
        "execute its Task section with the pulse and scout results in context; email pass treated as no-op.",
        "",
        "## Mark report",
        "",
        "```",
        mark_report.strip(),
        "```",
        "",
        "## Scout report",
        "",
        "```",
        scout_report.strip(),
        "```",
        "",
        "## Coach (jobs-daily) report",
        "",
        "```",
        coach_report.strip(),
        "```",
        "",
        "## Safety notes",
        "",
        "- This run used a **fictional** candidate profile. No real person's data was read or written.",
        "- No email was sent and no drafts were created for a real inbox.",
        "- No git commit or push was made by this script.",
        "- Output is under `vault/examples/jobfinderos-hermes-run/`, which is gitignored.",
        "",
        "## How to run it yourself",
        "",
        "```bash",
        "python3 scripts/run_jobs_daily_hermes.py",
        "```",
        "",
        "Then read `vault/examples/jobfinderos-hermes-run/run_report.md`.",
        "",
        "To wire the real schedule, see `HERMES.md` ('Running on Hermes' -> 'Scheduled jobs') and "
        "the Hermes cronjob tool. The real `jobs-daily` skill still needs a real candidate profile "
        "at `config/profile.md` and, for the email pass, a connected Hermes email skill.",
        "",
        f"> **JobFinderOS:** Hermes demo · {ts}",
    ]
    return write(VAULT_OUT / "run_report.md", "\n".join(lines))


def write_demo_readme() -> Path:
    now = datetime.now().astimezone()
    ts = now.strftime("%Y-%m-%d %H:%M %Z")
    text = f"""# JobFinderOS Hermes demo run

> **JobFinderOS:** Hermes demo · {ts}

This directory holds the output of a **bounded, fictional, end-to-end demonstration**
of the `jobs-daily` skill running as a Hermes subagent.

## Why this exists

This is the proof-of-concept for the port from Claude Code to Hermes. Commit 1 renamed
the folders and added `HERMES.md`; commit 2 retargeted the README; this commit adds a
driver (`scripts/run_jobs_daily_hermes.py`) that actually runs a skill end to end as a
Hermes subagent, using `delegate_task` with the worked example in `HERMES.md` as the template.

## What ran

1. **Market Pulse** → mark subagent (persona: `personas/mark.md`, skill: `skills/mark-pulse.md`)
2. **Scout** → scout subagent (persona: `personas/scout.md`, skill: `skills/jobs-scout.md`)
3. **Daily (coach orchestrator)** → coach subagent (persona: `personas/coach.md`, skill: `skills/jobs-daily.md`);

   the email pass was a no-op because this is a fictional candidate with no real inbox.

## Inputs (all career-neutral / fictional)

- `personas/coach.md`, `personas/scout.md`, `personas/mark.md`
- `skills/jobs-daily.md`, `skills/mark-pulse.md`, `skills/jobs-scout.md`
- `config/examples/fictional_profile.json` (fictional candidate)
- `config/recruiter_playbook.md` (the doctrine)

## Output (gitignored)

- `run_report.md` — the consolidated report: what ran, inputs, the three subagent reports,
  the Recruiter's read, and safety notes.
- `daily_digest.md` — the morning briefing the coach wrote.
- `market_pulse_report.md` — what mark returned.
- `scout_report.md` — what scout returned.
- `Companies/` — any opportunity notes the scout wrote (fictional companies/roles).

## Safety

- No real candidate data was read or written.
- No email was sent and no drafts were created for a real inbox.
- No git commit or push was made by the driver.
- Output is under a gitignored demo directory.

## How to run it yourself

```bash
python3 scripts/run_jobs_daily_hermes.py
```

Then read `run_report.md`. To run the real `jobs-daily` skill, you need a real candidate
profile at `config/profile.md` and, for the email pass, a connected Hermes email skill.
See `HERMES.md` for how a skill runs on Hermes and how the schedule is wired.
"""
    return write(VAULT_OUT / "README.md", text)


def main() -> int:
    ensure_out_dir()
    write_demo_readme()

    profile = read_json(EXAMPLE_CONFIG)
    print(f"==> fictional candidate: {profile.get('name')} / {profile.get('goes_by')}")
    print(f"==> target tiers: {profile.get('target_companies', {}).get('tier_one', [])}")

    mark_report = run_mark()
    write(VAULT_OUT / "market_pulse_report.md", mark_report)

    scout_report = run_scout()
    write(VAULT_OUT / "scout_report.md", scout_report)

    coach_report = run_coach(mark_report, scout_report)
    write(VAULT_OUT / "run_report.md", "")
    write_run_report(mark_report, scout_report, coach_report)
    # rewrite run_report with the coach report included
    write_run_report(mark_report, scout_report, coach_report)

    print("==> done. read vault/examples/jobfinderos-hermes-run/run_report.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
