# Notes: converging with upstream's jfgraph architecture

Working notes, not a decision. Written 2026-10-31 after the upstream creator's
issue-thread message offering to link both runtime forks and proposing a
pluggable LLM-client interface. Keep this out of the issue thread — it's a
bigger design conversation than that thread wants.

## Where upstream went

Four commits after our fork point (`77853cd`):

- `3094fa5` — `scripts/jfgraph/` package: graph runtime, ATS transports, LLM
  client, state-dir guard. The old `jobfinderos_ats_poll.py` logic becomes a
  graph.
- `0067669` — sim: simulation protocol, acceptance gates, a published
  benchmark. `sim/` + `tests/` — the project's first real test suite.
- `1f11448` — discovery wired into the daily routine.

The model is only called at three seams: **scoring**, **classifying near-miss
titles by description**, and **a web sweep**. Everything else (fetching boards,
finding boards for new companies, seniority/location/comp gates, the seen-set)
is deterministic Python.

## The clean seam we found

`scripts/jfgraph/llm.py`:

- `LLMCall` / `LLMResult` dataclasses are already runtime-neutral: prompt,
  schema, model name, budget, timeout, token counts. Nothing Claude-specific
  in the data model.
- Only `ClaudeCLI.argv()` (builds `claude -p --output-format json ...`) and
  `ClaudeCLI.call()` (subprocess + record/replay cache) know about Claude.
- `RunContext.llm` is typed `Any` with the comment `# jfgraph.llm.ClaudeCLI` —
  the graph already treats the client as an implicit interface. It just isn't
  named yet.

So the PR shape proposed in the thread: add a small `LLMClient` Protocol/ABC,
move subprocess bits into `ClaudeCLI(LLMClient)`, retype the context field.
Keep the record/replay cache, `LiveBudgetExceeded`, and metrics untouched —
those are the valuable parts both forks inherit for free, along with
`tests/fake_claude.py` and the golden fixtures.

A Hermes client would map `call()` to a `delegate_task` subagent (prompt as
goal, persona as context) and parse the report back into `LLMResult.structured`.

## The bigger question (not raised in the thread)

jfgraph is a **different architecture** from our skills-as-subagents port, not
a replacement for it:

- **Ours:** the daily routine is `jobs-daily` orchestrating coach/scout/mark
  subagents, each reading skills/*.md. The model does everything, including
  fetching and gating.
- **Upstream's:** the daily routine runs a deterministic graph for fetch +
  gates + seen-set; the model is called only at score/classify/sweep seams.

Converging would mean our scheduled daily/digest flow adopts the graph for the
deterministic 80% and calls the model only at those seams. Gains: cheaper
runs, the sim harness, the test suite, upstream bugfixes flowing in cleanly.
Costs: re-thinks what our 25 skills *are* — some (jobs-scout, jobs-priority-
watch, parts of jobs-daily) would shrink to prompt configs over graph nodes.

## Open questions for when this conversation happens

1. Do we adopt jfgraph wholesale (fork tracks upstream minus runtime), or only
   take the LLM-client interface and keep our skill orchestration?
2. What happens to `skills/jobs-daily.md` as orchestrator if the graph owns
   the daily routine? Does it become a thin "run the graph, then coach reads
   the output" skill?
3. Where do personas live in a graph world? Coach's judgment (Recruiter's
   read, warm-path, drafts) still needs a conversational agent — the graph
   doesn't replace that half.
4. The sim/benchmark harness (`sim/gates.yaml`, acceptance gates) — can our
   subagent-based runs even be expressed in it, or is it graph-only?
5. Windows support landed upstream too (`f75c598`) — free if we track closely.

## Thread state

- We replied: yes to README link, interested in the LLM-client PR, deferred
  runner interface design to the Codex author.
- Watch the upstream issue thread for @Souheil-Yazji's response before
  drafting anything.
