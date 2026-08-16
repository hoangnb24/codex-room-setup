# Workflow Pilot Before Paseo Enforcement

This pilot tests whether explicit planning, reopening, foundation, reconciliation,
and ownership rules improve real work before Paseo stores or enforces them.

The shared baseline is
`home/.config/codex-room/workflow/WORKSPACE_PROTOCOL.md`. A project may refine it
in `docs/WORKSPACE_PROTOCOL.md`. The project file should contain only local
constraints and tactics; it is not a copied task tracker.

## What the pilot changes

For consequential multi-frontier work, the room uses six observable message
contracts:

- `FRONTIER_BRIEF v1`: Lead's bounded dispatch contract.
- `FOUNDATION_CHECK v1`: pre-feature owner, lifecycle, invariant, mechanism, and
  dependency check.
- `PEER_DISPOSITION v1`: candidate, reopen, dependency, or blocked handoff.
- `LEAD_RULING v1`: binding response to evidence and consequential acceptance.
- `PLAN_RECONCILIATION v1`: checkpoint after three accepted consequential
  frontiers and no later than before dispatch beyond the fourth.
- `PARALLEL_CHECK v1`: explicit independence check before concurrent writers.

Tiny bounded work may stay concise. The formats exist to expose decisions and
failure modes, not to make every task ceremonial.

## Install and activate

After editing the tracked setup:

```bash
make test
./scripts/install --apply
./scripts/sync-all
./scripts/verify
```

The workflow protocol is symlinked into each role runtime. Role overlays also
point to the installed shared protocol and the optional project refinement.
Installing or syncing does not restart Paseo.

## Run a useful comparison

Choose workstreams that exercise different uncertainty:

1. A bounded feature with stable foundations.
2. A false premise that should cause a reopen.
3. A feature whose required mechanism is missing.
4. Two apparently parallel frontiers with overlapping scope or dependency.
5. A workstream long enough to require reconciliation.

Compare a baseline and pilot condition while holding repository commit, Human
objective, model, reasoning effort, permissions, and acceptance boundary fixed.
Use fresh sessions and repeat comparable runs when practical.

Judge three groups of evidence:

| Group | Evidence |
| --- | --- |
| Outcome quality | Real acceptance evidence, integration behavior, workaround debt, stale candidates |
| Efficiency | Duration, cumulative tokens, model requests, tool calls, seat count, correction rounds |
| Coordination | Useful reopen requests, explicit rulings, avoided collisions, reordered or absorbed work |

Do not score a marker's presence as success. A reopen is useful when inspected
evidence changes or validates the route. A reconciliation is useful when it
removes stale work, changes dependency order, confirms the plan against new
evidence, or prevents an unnecessary parallel frontier.

## Create an aggregate marker report

Run the report over one or more local Codex rollout files:

```bash
./scripts/workflow-pilot-report --format json \
  /path/to/lead-rollout.jsonl \
  /path/to/peer-rollout.jsonl
```

The report reads only assistant response messages and emits counts. It does not
emit source text, prompts, responses, tool arguments, session IDs, or file paths.
Raw rollout JSONL remains sensitive and should not be committed or shared without
separate review.

Use `scripts/session-usage` separately for per-session timing, token, request,
tool, and optional API-equivalent cost summaries. Marker counts and resource use
answer different questions and should not be collapsed into one score.

## Decide what belongs in Paseo

Productize only a repeated missing mechanism:

| Repeated pilot observation | Candidate Paseo mechanism |
| --- | --- |
| Overlapping writers are dispatched despite visible scopes | Atomic ownership lease |
| Reopen requests are useful but disappear in transcript | Structured ruling and attention event |
| Lead repeatedly misses a useful reconciliation | Accepted-frontier counter and dispatch gate |
| Work continues after a contract-changing plan edit | Plan reference and digest staleness check |
| Foundation checks are useful but repeatedly skipped | Foundation dependency gate |
| Formats add cost without changing decisions or outcomes | Remove or narrow the ceremony |

Two comparable episodes are the minimum signal for proposing a runtime
mechanism. Higher-risk enforcement should use more evidence and include a clear
rollback path.
