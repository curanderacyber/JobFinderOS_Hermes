#!/usr/bin/env bash
# Legacy: preflight for local Claude Code skill automation (macOS launchd bridge).
# DEPRECATED ON HERMES — retained for provenance. On Hermes, the scheduler is one of
# a cronjob per scheduled job or the tick script at scripts/jobfinderos_hermes_tick.py
# (see HERMES.md "Running on Hermes"). Skills were renamed from .claude/commands/ to skills/.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

fail=0
echo "=== JobFinderOS local runner preflight (legacy Claude Code bridge) ==="
echo "NOTE: this check is deprecated on Hermes; see HERMES.md. Skills are now in skills/."

CLAUDE_BIN="${CLAUDE_BIN:-$(command -v claude || true)}"
if [[ -z "$CLAUDE_BIN" || ! -x "$CLAUDE_BIN" ]]; then
  echo "INFO: claude CLI not in PATH (expected on Hermes — no launchd bridge)"
else
  echo "OK: claude at $CLAUDE_BIN ($("$CLAUDE_BIN" --version 2>/dev/null | head -1))"
fi

if [[ ! -d "$ROOT/vault" ]]; then
  echo "FAIL: vault/ missing under $ROOT"
  fail=1
else
  echo "OK: vault/ present"
fi

for skill in jobs-daily mark-weekly jobs-priority-watch; do
  if [[ -f "$ROOT/skills/${skill}.md" ]]; then
    echo "OK: skill skills/${skill}.md"
  elif [[ -f "$ROOT/.claude/commands/${skill}.md" ]]; then
    echo "WARN: legacy skill .claude/commands/${skill}.md still present (skills/ is the new home)"
  else
    echo "WARN: missing skill ${skill}.md (neither skills/ nor legacy .claude/commands/)"
  fi
done

if [[ -x "$ROOT/scripts/JobFinderOS_run_skill.sh" ]]; then
  echo "OK: JobFinderOS_run_skill.sh executable (deprecated on Hermes)"
else
  echo "WARN: scripts/JobFinderOS_run_skill.sh missing or not executable"
fi

if [[ "$fail" -eq 0 && -n "${CLAUDE_BIN:-}" ]]; then
  echo
  echo "--- claude auth status (legacy) ---"
  if ! "$CLAUDE_BIN" auth status 2>&1; then
    echo "INFO: claude auth status unavailable (expected on Hermes)"
  fi
fi

exit "$fail"
