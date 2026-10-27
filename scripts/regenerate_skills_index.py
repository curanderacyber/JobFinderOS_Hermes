#!/usr/bin/env python3
"""Regenerate SKILLS_INDEX.md from the current skills/ tree.

Reads each skills/*.md file, pulls the one-line `description:` from its YAML
frontmatter and the `**Agent:**` line from the body, and rewrites the index
table. Dependency-free (no PyYAML): frontmatter descriptions are single-line.

Run from the repo root:
    python3 scripts/regenerate_skills_index.py
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
OUT = ROOT / "SKILLS_INDEX.md"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.S)
DESC_RE = re.compile(r"^description:\s*(.+?)\s*$", re.M)
AGENT_RE = re.compile(r"^\s*\*\*Agent:\*\*\s*(.+?)\s*$", re.M)

HEADER = [
    "# JobFinderOS — Skills index (Hermes)",
    "",
    "Skills are short Markdown prompts in `skills/`. Each names its agent in the first line and describes the task. To run one, spawn a Hermes subagent with the persona from `personas/` as context and the skill as the goal (see the worked example in `HERMES.md`), or run it inline in the main session for conversational skills.",
    "",
    "**Target state (25 skills):** each file in this directory should have one line `description: ...` in YAML frontmatter and one line `**Agent:** <coach|scout|mark|orchestrator|none> ...`. No file should still reference `.claude/commands/` or `.claude/agents/`.",
    "",
    "Below is the commit-time copy. Regenerate from the tree when skills are added or renamed.",
    "",
]

FOOTER = [
    "",
    "Regenerate this table with the script at `scripts/regenerate_skills_index.py`:",
    "",
    "```bash",
    "python3 scripts/regenerate_skills_index.py",
    "```",
    "",
]


def skill_row(path: Path) -> tuple[str, str, str]:
    text = path.read_text(encoding="utf-8")
    desc = ""
    fm = FRONTMATTER_RE.search(text)
    if fm:
        dm = DESC_RE.search(fm.group(1))
        if dm:
            desc = " ".join(dm.group(1).split())
    agent = ""
    am = AGENT_RE.search(text)
    if am:
        raw = " ".join(am.group(1).split())
        # First token is the persona name (often backticked); the rest is a
        # run-mode note that would make the table unreadably wide.
        agent = raw.split()[0].strip("`")
    return path.name, agent, desc


def main() -> int:
    rows = [skill_row(p) for p in sorted(SKILLS_DIR.glob("*.md"))]
    out = list(HEADER)
    out.append("| Skill | Agent | Description (from YAML frontmatter) |")
    out.append("|-------|-------|--------------------------------------|")
    for name, agent, desc in rows:
        out.append(f"| `skills/{name}` | {agent} | {desc} |")
    out.extend(FOOTER)
    OUT.write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {OUT.name} with {len(rows)} skills")
    missing = [n for n, a, d in rows if not a or not d]
    if missing:
        print("WARNING: skills missing description or agent line:", ", ".join(missing))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
