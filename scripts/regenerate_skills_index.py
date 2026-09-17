# JobFinderOS — Skills index (Hermes)

Skills are short Markdown prompts in `skills/`. Each names its agent in the first line and describes the task. To run one, spawn a Hermes subagent with the persona from `personas/` as context and the skill as the goal (see the worked example in `HERMES.md`), or run it inline in the main session for conversational skills.

**Target state (25 skills):** each file in this directory should have one line `description: ...` in YAML frontmatter and one line `**Agent:** <coach|scout|mark|orchestrator|none> ...`. No file should still reference `.claude/commands/` or `.claude/agents/`.

Below is the commit-time copy. Regenerate from the tree when skills are added or renamed.

| Skill | Agent | Description (from YAML frontmatter) |
|-------|-------|--------------------------------------|
| `skills/checkin.md` | coach | Daily pipeline sync. Processes Dashboard checkboxes and verbal updates, ages every thread against the silence norms, refreshes the Dashboard and vault notes, and ends with a candid Recruiter's read. |
| `skills/day-of-card.md` | coach | The one page to have open during an interview round. Distills the full prep brief into logistics, the one thing the round is about, the beats, a per-interviewer block (who they are, opener, lead story and landing line, questions, traps), spent-story callbacks, and a before-you-walk-in checklist. /day-of-card <Company> [Round | interviewer] [date]. |
| `skills/draft-message.md` | coach | Draft a follow-up, thank you, cold outreach, recruiter reply, or offer acknowledgment in the candidate's voice. Copies to clipboard and logs to the vault. Never sends, never creates Gmail drafts. |
| `skills/email-watch.md` | coach | Scan Gmail like a recruiter with eyes on the inbox. Surfaces inbound opportunities, pipeline updates, stale threads, and anything that needs action today, as a briefing. Read-only except for clear pipeline updates. |
| `skills/jobs-cover.md` | coach | Write a tailored cover letter for a specific role, researched and in the candidate's voice. Saves to the vault. Claude Code, no API keys. |
| `skills/jobs-daily.md` | orchestrator | Full daily routine. Runs the market pulse and the scout in parallel, then email triage, then the digest, and writes one consolidated run record and Recruiter's read. The everyday driver. Claude Code, no API keys. |
| `skills/jobs-digest.md` | coach | Compile the morning briefing (new opportunities, recruiter emails to review, pipeline updates, action items) into Daily Digests/, with a scoped Dashboard refresh and a warm-path coverage check. Claude Code, no API keys. |
| `skills/jobs-email.md` | coach | Triage recruiter and inbound email, run the rejection sweep, auto-prep for any interview detected, age silent threads per the silence norms, and keep the Email Follow-ups Queue current. Flags replies that are due; drafts only on the candidate's yes, clipboard or vault only. Claude Code, no API keys. |
| `skills/jobs-prep.md` | coach | Build a complete interview prep guide for a specific company, role, and stage, grounded in the story library. Saves to the vault. Claude Code, no API keys. |
| `skills/jobs-priority-watch.md` | scout | Priority-function watch. Narrow, fast ATS-direct scan of the profile's priority companies for the function the profile marks as priority, honoring its seniority filter. Vault-only, silent when nothing is new. Weekday scheduled watch. No email. |
| `skills/jobs-research.md` | mark | Company research brief. Business model, funding, leadership, product, GTM motion, culture, open reqs in the candidate's lanes, interview signals, and a recommended angle. Saves to the vault. Claude Code, no API keys. |
| `skills/jobs-scout.md` | scout | Scan for new roles that fit the profile, direct from company careers pages and ATS boards plus web search, score them, and log the strong ones to the vault. Works for any career. Claude Code, no API keys. |
| `skills/mark-profiler.md` | mark | Deep company evaluation for a career decision. Scored dimensions, the real day-to-day role, 12 to 24 month trajectory, honest verdict. Saves to the vault. Claude Code, no API keys. |
| `skills/mark-pulse.md` | mark | Market pulse. Scan the target cohort for funding, leadership moves, GTM build-outs, and renames relevant to the search. Writes the Market Pulse, the Daily Marketing Brief, and the Jobs Handoff. Claude Code, no API keys. |
| `skills/mark-weekly.md` | mark | Weekly brief. Market pulse, the weekly brief, the Jobs Handoff, and the weekly Strategy pass (funnel snapshot, objection-log patterns, proof assets, pre-posting plays, deadline math). Local vault only. Claude Code, no API keys. |
| `skills/mock-interview.md` | coach | Simulated interview for a specific company, role, and round. Plays the interviewer in character from the prep brief, probes like a real one, then scores every answer against the round's beats and the locked story scripts. Saves a debrief and drill list. /mock-interview <Company> [Role] [Stage | interviewer] [debrief | drill <question>]. |
| `skills/network-outreach.md` | coach | Identify 2 to 3 strategic humans at a target company, draft a research-backed peer-to-peer outreach message, and plan a follow-up cadence. Saves to Outreach Drafts/ and Contacts.md. Never sends. |
| `skills/onboard.md` | none | First-run setup. Interviews you about your career, goals, and a few real wins, then generates your private JobFinderOS profile so the agents can find and win jobs tailored to you. Runs on Claude Code, no API keys. |
| `skills/postmortem.md` | coach | Loss-pattern analysis after any rejection, withdrawal, or 30-day ghost. Classifies the objection (stated vs inferred), updates the Strategy objection log, and names the positioning fix. /postmortem <Company> [Role], or let /checkin trigger it. |
| `skills/profile.md` | coach | Progressive profiling. Deepen the Wins Library and learn the candidate's voice over time, so applications get more tailored the more JobFinderOS is used. Runs on Claude Code, no API keys. |
| `skills/story.md` | coach | Career Story Library manager. Interview the candidate to capture a story's highlights, catalog it for reuse, and match stories to interviews, cover letters, resumes, and application answers. /story [list | add <hint> | find <need> | update <id>]. |
| `skills/title-audit.md` | mark | Audit the search vocabulary against what the market calls the job right now. Reads real postings at target companies, extracts the live title vocabulary, diffs it against saved searches and profile terms, and hands back the exact terms to paste into LinkedIn preferences. /title-audit [function description | quick]. Claude Code, no API keys. |
| `skills/voice-check.md` | coach | The AI-tell gate. Run any draft (DM, email, cover letter, application answer, LinkedIn post, resume line) through the authenticity doctrine before it leaves the candidate's hands. Reports every tell with a fix, verifies the two-fact rule, rewrites only on request. /voice-check [register] [fix] with the draft pasted, a file path, or "clipboard". |
| `skills/warm-path.md` | coach | The attach-a-human gate. Before any application goes in, walk the warm-path ladder, return a verdict, set the outreach-then-apply dates, and log the human path on the opportunity note. /warm-path <Company> [Role], or /warm-path audit to score every open application against the 70% target. Never drafts, never sends. |
| `skills/whats-next.md` | coach | "Choose-your-own-adventure session. Full pipeline sweep, then the 3 to 5 highest-leverage actions toward landing the next role. Pick one, do it together, the vault syncs, the menu re-ranks. Triggers on 'what should we do next?'" |

Regenerate this table with:

```bash
python3 - <<'PY'
from pathlib import Path
import yaml, re, textwrap

rows = []
for p in sorted(Path("skills").glob("*.md")):
    text = p.read_text(encoding="utf-8")
    m = re.search(r"^---\n(.*?)\n---", text, re.S)
    body = yaml.safe_load(m.group(1)) if m else {}
    desc = (body.get("description") or "").strip().replace("\n", " ").strip()
    agent = ""
    for line in text.splitlines():
        if line.strip().startswith("**Agent:**"):
            agent = line.split("**Agent:**", 1)[1].strip()
            break
    rows.append((p.name, agent, desc))

out = ["# JobFinderOS — Skills index (Hermes)", "",
       "Skills are short Markdown prompts in `skills/`. Each names its agent in the first line and describes the task. To run one, spawn a Hermes subagent with the persona from `personas/` as context and the skill as the goal (see the worked example in `HERMES.md`), or run it inline in the main session for conversational skills.",
       "",
       "**Target state (25 skills):** each file in this directory should have one line `description: ...` in YAML frontmatter and one line `**Agent:** <coach|scout|mark|orchestrator|none> ...`. No file should still reference `.claude/commands/` or `.claude/agents/`.",
       "",
       "Below is the commit-time copy. Regenerate from the tree when skills are added or renamed.",
       ""]
out.append("| Skill | Agent | Description (from YAML frontmatter) |")
out.append("|-------|-------|--------------------------------------|")
for name, agent, desc in rows:
    out.append(f"| `{name}` | {agent} | {desc} |")
out.append("")
out.append("Regenerate this table with:")
out.append("")
out.append("```bash")
out.append(textwrap.dedent("""\
    python3 - <<'PY'
    from pathlib import Path
    import yaml, re, textwrap
    ...
    PY
    ```"))
out.append("")

Path("SKILLS_INDEX.md").write_text("\n".join(out), encoding="utf-8")
print("wrote SKILLS_INDEX.md with", len(rows), "skills")
PY
```
