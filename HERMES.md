# JobFinderOS — Hermes Project Instructions

JobFinderOS is an agentic job-search system that runs on [Hermes](https://hermes-agent.nousresearch.com/) agents. Three personas (a recruiter, a crawler, a market analyst) work for one candidate and write everything into an Obsidian vault. This file is the Hermes-flavored project instructions; the original Claude Code instructions are retained as `CLAUDE.md` for reference and for the note templates.

**Nothing about the candidate is hardcoded here.** Every agent reads `config/profile.md` first and takes the candidate's name, targets, comp floor, location rules, and exclusions from it.

---

## Running on Hermes

Hermes runs agents as isolated subagents spawned on demand. Each JobFinderOS skill is a short Markdown prompt in `skills/`; each persona is a Markdown file in `personas/`. To run a skill, spawn a subagent with the persona as context and the skill as the goal.

**Worked example — run the daily scan.** `skills/jobs-daily.md` is the orchestrator (market pulse + scout in parallel, then email triage, then digest, then a Recruiter's read). It names `coach` for the closing read.

```python
from hermes_tools import delegate_task

delegate_task(
    context="""Read personas/coach.md first. You are Coach, the candidate's
recruiter — not a job board, not a clerk. Read config/profile.md,
config/recruiter_playbook.md, and config/scoring_rubric.md first; they hold
everything about the candidate and the doctrine. Warm-path-first, two-fact
rule, human-in-the-loop on every message, never send, never commit or push.
Drafting voice is a hard gate (no em dashes, no hedging openers, no formulaic
closers, no rule-of-three lists). Return a report at the end: files written,
pipeline changes, anything due, and the Recruiter's read.""",
    goal="""Read skills/jobs-daily.md and execute its Task section. Return a
report: files written, pipeline changes, anything due (drafts to offer,
decisions to make), and the Recruiter's read. Never draft outreach in
subagent mode — flag it as due so the main session can offer it."""
)
```

Skills can also be run inline in the main session when the task is conversational (e.g. `/whats-next`, `/checkin`, `/mock-interview`, `/voice-check`).

### Read first (every run, every persona)

- `config/profile.md` — the candidate, target roles and lanes, comp floor, location rules, exclusions, target companies with their direct ATS/careers-page URLs.
- `config/scoring_rubric.md` — how to score a role from 1 to 10.
- `config/recruiter_playbook.md` — the operating doctrine (warm-path-first, authenticity / anti-AI-spam, silence norms, funnel math, the Recruiter's read, multi-threading, objection discipline, deadline math).

### Tool access (Hermes)

The original Claude Code tool lists are retargeted to Hermes tools. The work is the same; the primitives are different.

**Coach** (recruiter brain — judgment, prep, drafts, voice, warm-path, postmortem, digest, email triage):
- `read_file`, `write_file` — read config and the vault, write vault notes.
- `search_files` — find existing notes, dedupe against what is already tracked.
- `terminal` — local file ops, and to invoke the Hermes email skill (himalaya or google-workspace) for read-only Gmail triage.
- `web_search`, `web_extract` — web research when needed.
- `browser_exec` — optional, for pages that need a real browser to render.
- Gmail is read-only via the Hermes email skill. **Never send, never create drafts.** Drafts go to the clipboard and the vault.

**Scout** (crawler — ATS-direct scanning, scoring, opportunity notes, weekday leadership watch):
- `web_extract` — fetch careers pages and ATS JSON endpoints (replaces WebFetch). Prefer JSON when it exists: `boards-api.greenhouse.io/v1/boards/<org>/jobs`, `api.ashbyhq.com/posting-api/job-board/<org>`.
- `web_search` — broaden with search on role titles plus location phrasing (replaces WebSearch).
- `read_file`, `write_file` — read `vault/Companies/`, write opportunity notes.
- `search_files` — dedupe against tracked roles so nothing is re-alerted.
- `terminal` — `curl` for ATS endpoints when `web_extract` does not cover them.
- No Gmail. No drafting. No outreach.

**Mark** (market analyst — funding, leadership moves, GTM build-outs, title renames, weekly briefs, company deep-dives, handoff):
- `web_extract`, `web_search` — primary sources: company blogs, press releases, funding databases, leadership pages, the company's own careers page.
- `read_file`, `write_file` — read `vault/Market Intel/`, write briefs and the handoff.
- `search_files` — dedupe against what has already been reported.
- `terminal` — data fetching when needed.
- No Gmail. No drafting. No outreach.

### The "when you run as a subagent" contract

Each persona file ends with a **When you run as a subagent** section — return a report (files written, pipeline changes, anything due, the Recruiter's read). That section is already written for the isolated-subagent model Hermes uses. Keep it. In subagent mode, never draft outreach; flag it as due.

### Model per persona

In Claude Code, `coach` runs `model: inherit` and `scout`/`mark` run `model: sonnet`. On Hermes, subagents inherit the parent model (Solar Pro 4 here) unless pinned via delegation config. Coach is judgment-heavy and worth the full model; scout and mark are research-heavy and can run lighter if cost is a concern. That is an orchestration decision, not a file rewrite.

---

## Core directives

1. **Never surface excluded companies** or roles matching the profile's excluded-profile pattern.
2. **Honor the comp floor.** Unknown comp = include with a note. Below the floor = hard discard.
3. **Honor the location rules.** Never quietly relax them.
4. **Stay inside the profile's lanes and seniority filter.**
5. **Write all output to the vault** at `vault/`, in Markdown, following the note templates in `CLAUDE.md`.
6. **Score every opportunity** with `config/scoring_rubric.md` before writing it to the vault.
7. **Be proactive about tangential opportunities** within the seniority filter.
8. **Warm-path-first (playbook §2):** an application without a human attached is a last resort. Outreach first, apply 48–72 hours later. Target 70% or more warm.
9. **Act like a recruiter, not a clerk (playbook §1):** every run ends with a **Recruiter's read** — strategic advice and uncomfortable truths, not a recap.
10. **Keep the vault root clean:** only `Dashboard.md`, `Strategy.md`, and machine-generated dated pointer notes at top level. Run summaries go to `Archive/Daily Jobs Watch/`.
11. **Anti-AI-spam is existential (playbook §3):** low volume, the two-fact rule, a human in the loop on every message, no send without the candidate's hands on it.
12. **Nothing drafted may read as AI-written.** See **Drafting voice** below. Hard gate.

---

## Drafting voice (hard gate, Directive 12)

Before any draft reaches the clipboard or the vault, self-check that it does not pattern-match to generated text:

- No em dashes, ever. Use a period, a comma, or parentheses and restructure.
- No hedging openers ("Honestly," "To be honest," "Frankly").
- No formulaic closers ("Either way," "At the end of the day," "excited to connect").
- No rule-of-three lists, no balanced parallel clauses. Vary sentence length; let one run short.
- No slogans, no self-positioning, no generic flattery. Research-backed specifics only.
- Plain English; expand acronyms on first use.
- Sign outreach with the short name from the profile's Contact block.
- The test: read it back as if it landed in the recipient's inbox. If any line smells like a model wrote it, rewrite it.
- The candidate's own words beat good words. When their phrasing and polished phrasing conflict, theirs wins. Leave a rough edge.

Registers from `config/voice.md`: measured third-person prose for resumes and summaries; direct, warm, contraction-using peer voice for DMs and emails; humble and articulate for application answers (a hook or paradox opener, close on an earned observation). Present tense for the current employer.

---

## Email safety

- **Never send email on the candidate's behalf.** Replies and outreach go to the clipboard and/or vault notes. The candidate sends everything manually from their own client.
- Never create drafts either. The Hermes email skill (himalaya / google-workspace) is for reading threads.
- No code path in this repo calls a send API.

---

## Vault conventions

- The vault root holds only `Dashboard.md` and `Strategy.md` plus machine-generated dated pointer notes. Everything else has a folder: `Companies/<Company>/`, `Tracking/`, `Outreach Drafts/`, `Stories/`, `Daily Digests/`, `Market Intel/`, `Archive/Daily Jobs Watch/`.
- Note templates (company profile, opportunity note, daily digest, outreach draft) are in `CLAUDE.md`. Every note starts with a Navigation block of links.
- Timeline rows: `| YYYY-MM-DD HH:MM TZ | what happened |`. Communication log rows: `| when | channel | summary |`.
- Edit `Dashboard.md` minimally and preserve hand-written rationale. `Strategy.md` funnel snapshots and the objection log are owned by `/mark-weekly` and `/postmortem`; `/checkin` owns the Dashboard pulse.
- Durable memory lives in `Strategy.md`, `Tracking/`, `Companies/`. Never in old digests; history is pruned on a rolling window.
- Log skill runs to `vault/Automation/JobFinderOS — Schedule & Run Log.md` when the skill says to.

---

## Agent run model — Hermes

**Personas** (`personas/*.md`): the three agents. Each is a Markdown file with a YAML frontmatter block (`name`, `description`) followed by the persona prompt, its doctrine, and a tool list. The original `model` and `tools` fields are Claude Code–specific; on Hermes, personas inherit the parent model unless pinned, and tool access is the Hermes tool set above.

| Persona | What it does | Hermes tools |
|---|---|---|
| `personas/coach.md` | Recruiter brain: pipeline judgment, interview prep, mock interviews, story library, cover letters, outreach drafting, voice checks, warm-path gating, loss postmortems, daily check-ins, inbox triage, morning digest. | read_file, write_file, search_files, terminal (email skill), web_search, web_extract, browser_exec (optional) |
| `personas/scout.md` | Crawler: ATS-direct scanning of target companies' careers pages, scoring, opportunity notes, weekday leadership watch. | web_extract, web_search, read_file, write_file, search_files, terminal (curl) |
| `personas/mark.md` | Market analyst: funding, leadership moves, GTM build-outs, title renames, weekly briefs, company deep-dives, handoff. | web_extract, web_search, read_file, write_file, search_files, terminal |

**Skills** (`skills/*.md`): thin task prompts. Each names its agent in the first line and describes the task. There are 25. To run one, spawn a subagent with the persona as context and the skill as the goal, or run it inline for conversational tasks.

| Skill | Purpose |
|---|---|
| `/onboard` | **First run.** Interviews you and generates the private config files from the templates. Career-neutral. |
| `/whats-next` | **Choose-your-own-adventure:** full pipeline sweep → the 3–5 highest-leverage actions, pick one, do it together, vault syncs, menu re-ranks. |
| `/checkin` | **Daily pipeline sync:** processes Dashboard checkboxes and verbal updates, ages every thread against the silence norms, refreshes the Dashboard, ends with a Recruiter's read. |
| `/postmortem` | **Loss analysis** after any rejection, withdrawal, or 30-day ghost: classify the objection, update the Strategy objection log, name the positioning fix. |
| `/jobs-daily` | Pulse + scout → email → digest (+ dashboard refresh) + one run record. |
| `/jobs-scout` | ATS-direct scan, score, log opportunities. |
| `/jobs-email` | Gmail triage; flags replies due; drafts only on yes, clipboard only. |
| `/jobs-digest` | Morning digest + scoped Dashboard refresh + warm-path coverage check. |
| `/mark-weekly` | Weekly brief + Market Pulse + Jobs Handoff + Strategy pass. |
| `/mark-pulse` | Market pulse only. |
| `/jobs-priority-watch` | Narrow weekday watch for the profile's priority function at its priority companies; silent when nothing is new. |
| `/network-outreach` | Find 2–3 peer-level humans at a target, draft a research-backed DM, plan the cadence. |
| `/warm-path` | **Attach-a-human gate** (playbook §2): verdict (`warm — active` / `warm — reachable` / `cold`) and outreach-then-apply dates; `audit` mode scores every open app. |
| `/title-audit` | **Search-vocabulary audit:** what does the market call your function right now, diffed against your saved searches. |
| `/voice-check` | **AI-tell gate:** PASS / REWRITE / DO NOT SEND; rewrites only on `fix`. |
| `/mock-interview` | Simulated interview from the prep brief, scored against the round's beats; `debrief` and `drill` modes. |
| `/day-of-card` | One page for the room, distilled from the prep brief. |
| `/story` | **Career Story Library:** capture (`add`), catalog, match (`find`), debrief (`update`). Consumed by prep, covers, and drafts. |
| `/profile` | Progressive profiling: deepen the wins library and learn the voice over time. |
| `/jobs-cover`, `/jobs-prep`, `/jobs-research`, `/draft-message`, `/mark-profiler`, `/email-watch` | On-demand. |

**Scheduled jobs.** The original scheduler is macOS launchd → `scripts/scheduler_tick.py` → `scripts/JobFinderOS_run_skill.sh` → `claude -p /skill`. On Hermes, scheduled runs are one of:

- **Hermes cronjobs** (preferred): one cronjob per scheduled job, using the Hermes `cronjob_manage` tool. Times come from `config/scheduler.yaml`. Each cronjob spawns the relevant subagent (coach for daily, mark for weekly) or runs a script.
- **A tick script** (`scripts/jobfinderos_hermes_tick.py`): reads `config/scheduler.yaml`, checks the time, and either spawns subagents via `delegate_task` or prints what is due (dry-run). Closer to the original `scheduler_tick.py` but Hermes-flavored.

The launchd plists and `scripts/JobFinderOS_install_launchd.sh` are macOS-specific and tied to the Claude Code CLI bridge; they are legacy and kept in `scripts/launchd/` for provenance.

Optional helpers (unchanged, script-only): the deterministic ATS poller (`scripts/jobfinderos_ats_poll.py`, writes `vault/Market Intel/ATS Inbox.md`), the retention pruner, and the pointer-note writer. All searching goes **directly to company careers pages and ATS boards** (URL table in `config/profile.md`), never aggregators.

---

## Privacy model

`config/profile.md`, `scoring_rubric.md`, `wins.md`, `voice.md`, `targets.md`, `stories.md`, `ats_boards.yaml`, and the whole `vault/` (except its skeleton) are gitignored. Agents never commit or push; the candidate does that by hand, and only to a private remote if they choose to back the vault up at all. The only remote is one the candidate adds by hand.
