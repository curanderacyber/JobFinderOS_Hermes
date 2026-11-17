# AGENTS.md — JobFinderOS

Guidance for coding agents and IDE copilots working on this repository (the humans' instructions for the *job-search* agents are in `HERMES.md`; the retained Claude Code instructions and note templates are in `CLAUDE.md`).

## What this is

An agentic job-search system ported from Claude Code to Hermes: three personas in `personas/` (`coach.md`, `scout.md`, `mark.md`), 25 skills in `skills/`, doctrine in `config/recruiter_playbook.md`, output in an Obsidian vault at `vault/`. Scheduled runs on Hermes go cronjob or tick script → Hermes subagent (coach/scout/mark) via `delegate_task`, or run inline for conversational skills. The original Claude Code execution layer (launchd → `JobFinderOS_run_skill.sh` → `claude -p /skill`) is retained as legacy reference in `scripts/`; see `HERMES.md`.

Live integrations (this machine, their account only): Gmail read-only via the `gws` CLI (`~/.local/bin/gws`, OAuth token scope `gmail.readonly` — sending is technically impossible) against the dedicated job-search inbox `lafostalicia@gmail.com`; never touch any other Google account. Contact verification via the Hermes `apollo` connector. Scheduling via three Hermes cronjobs (see HERMES.md's cronjobs table for IDs and schedules).

## Read first

`README.md`, `CLAUDE.md`, `config/recruiter_playbook.md`. When touching automation: `config/scheduler.yaml`, `scripts/`, `vault/Automation/`.

## Rules

1. Nothing about a specific candidate goes into this repo. Personal data lives only in gitignored paths (`config/profile.md` and friends, `vault/` content). If you need an example, use a fictional one.
2. Skills refer to "the candidate" and read every specific (name, employer, comp floor, targets, location) from `config/profile.md`.
3. Never add a code path that sends email or creates Gmail drafts. Email access is read-only by construction (OAuth scope `gmail.readonly`); keep it that way — do not re-run `gws auth login` without `--readonly`, and do not authorize any account other than the owner's dedicated job-search inbox.
4. Prefer existing entrypoints over new wrappers. One scheduler; no overlapping jobs.
5. Keep skills thin. A skill names its agent in the first line and describes the task; the persona and doctrine live in the agent file.
6. Automation may commit and push **only with the repo owner's explicit authorization for that work item** (granted per session/task, not globally). Never push speculatively; never push `vault/` content, which is gitignored anyway. **Stage by explicit path, never `git add -A` or `git add .`**: the skeleton files the `.gitignore` whitelists (`vault/Dashboard.md`, `vault/Strategy.md`, `vault/Tracking/`, `vault/Automation/`) fill with private pipeline data over time and must stay uncommitted. On 2026-11-17 a force-push scrub was required after `add -A` swept live vault state into a public commit; do not repeat it.
7. Small, verifiable edits. After an automation change, run `.venv/bin/python scripts/jobfinderos_hermes_tick.py --dry-run` and `bash scripts/verify_local_automation.sh`.

## Quick commands

```bash
.venv/bin/python scripts/jobfinderos_hermes_tick.py --dry-run   # what the Hermes scheduler would run now (PyYAML lives in .venv)
.venv/bin/python scripts/run_jobs_daily_hermes.py               # end-to-end demo (needs the Hermes runtime)
python3 scripts/jobfinderos_ats_poll.py --dry-run
gws gmail users messages list --params '{"userId":"me","maxResults":5}'  # inbox smoke check, read-only

# Legacy Claude Code bridge (kept for provenance; not the Hermes path):
bash scripts/JobFinderOS_check_local_runner.sh
python3 scripts/scheduler_tick.py --dry-run
```
