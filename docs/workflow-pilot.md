# Workflow Pilot Before Paseo Enforcement

This pilot tests whether explicit planning, reopening, foundation, reconciliation,
and ownership rules improve real work before Paseo stores or enforces them.

The role overlays contain the default pilot behavior. A workspace may define
local constraints and tactics in `docs/WORKSPACE_PROTOCOL.md`. The retained
`home/.config/codex-room/workflow/WORKSPACE_PROTOCOL.md` is a reference artifact;
profiles and generated role runtimes do not load it.

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

## Guarded multiple-writer pilot

This operation tests whether two genuinely independent writable frontiers can
reduce time to an accepted result without increasing correction work. It is a
positive gate: whenever at least two writable frontiers are ready, Lead must
evaluate them for concurrent admission and record `PARALLEL_CHECK v1`, even when
the ruling is `SERIAL`.

The default is `SERIAL`, the maximum is two concurrent writers per repository,
and an unknown or unverified condition resolves to `SERIAL`. Concurrency is an
explicit exception after all admission checks pass, not a property inferred
from having multiple available agents.

### Admission contract

Lead may admit two writers only when all of these statements are true:

- Both candidates start from the same exact base commit.
- Each writer has a separate Git worktree and branch.
- Their physical write scopes do not overlap, and their logical responsibilities
  can change independently.
- Lead freezes the shared contract and records one digest of it in both briefs.
- Neither frontier changes a shared integration surface, including a common
  schema, public API, composition root, generated artifact, migration, lockfile,
  or shared test fixture.
- Each writer hands off one immutable commit. A writer does not amend or replace
  a handed-off commit while Lead is evaluating or integrating it.

Worktree isolation prevents two processes from writing the same checkout. It
does not prove logical independence: disjoint files can still encode coupled
changes to one API, lifecycle, invariant, or generated output. The
`PARALLEL_CHECK v1` must therefore name both physical scopes and the logical
contract or responsibility owned by each frontier.

This is prompt-level policy. Paseo does not atomically reserve scopes, enforce
the two-writer limit, freeze a contract digest, or prevent a commit from being
rewritten. Lead observes and enforces the pilot in the room. Product enforcement
is deferred until at least two comparable misses show that the same absent
runtime mechanism caused a coordination failure.

### Dispatch and handoff evidence

The positive gate records the candidate frontier IDs, exact base commit,
physical and logical scopes, frozen contract digest, shared-surface check,
writer count, and `PARALLEL` or `SERIAL` ruling. Each admitted
`FRONTIER_BRIEF v1` repeats that evidence and grants exactly one writable scope.

Each `PEER_DISPOSITION v1` returns the frontier ID, immutable candidate commit,
base commit, changed paths, personally run verification, and residual risk.
Lead rejects a candidate that includes paths outside its scope, has the wrong
base, depends on an unaccepted sibling candidate, or changes the frozen
contract. A required cross-frontier change is evidence that the work was not
independent; it is not repaired by asking both writers to edit the same surface.

### Serial integration and proof

Lead integrates one immutable commit at a time onto the current accepted tip.
After each integration Lead checks the candidate's path scope and runs its
focused proof. After the second integration Lead runs the focused checks for
both frontiers plus the composed proof on the new accepted tip. A conflict,
contract mismatch, or composed failure stops acceptance and is recorded as
correction evidence; concurrent writers never reconcile each other.

### Falsifiable success

Compare a guarded run with a comparable serial run while holding the base,
objective, models, reasoning effort, and acceptance boundary fixed. Record
gate decisions, dispatch-to-handoff time, time to accepted composed proof,
correction batches, conflicts, contract reopens, stale candidates, and escaped
defects.

The pilot succeeds only when the guarded run shows a velocity gain to the same
accepted outcome without more correction, weaker proof, scope collisions, or
contract drift. A concurrency decision, two fast handoffs, or clean individual
tests alone are not success. No measured velocity gain, any increase in
correction, or a composed failure falsifies the benefit for that comparison and
returns the next comparable workstream to `SERIAL` unless a new positive gate
admits it.

## Phase 1 review strategy

Lead selects the smallest sufficient route:

| Route | Use | Default model | Expected rounds |
| --- | --- | --- | --- |
| `NO_REVIEW` | Tiny or low-risk work Lead can inspect directly | none | 0 |
| Read-only Peer | Premise, architecture, solution-shape, macro, or candidate review | Sol Medium | 1 bounded review |
| `FAST` Peer close-out | Accepted findings, correction base, and bounded delta | Sol Medium | 1 close-out |

Review is pull-based. A new diff, commit, frontier, or completed Peer task is
not itself a review trigger. Dispatch independent review only when its result
can change the next technical decision and deterministic checks cannot answer
the concern more cheaply. Review a premise early when a wrong choice would lock
architecture or lifecycle. Before an irreversible or owner-gated action,
review only when material residual risk remains after owning checks. Otherwise,
batch related work at one stable integration or acceptance boundary.

An exploratory review returns one complete batch of material findings. Lead
rules once and freezes the accepted finding set. One writer owns one correction
batch. Close-out checks only that finding set, the correction delta, and direct
regressions. If close-out would require a second correction in the same finding
family, reconciliation is required before another dispatch. The limit is one
exploratory batch, one correction batch, and one bounded close-out. Do not start
a third review loop automatically.

For pilot observability, Lead labels review seats with `review_class`,
`review_mode`, `review_lane`, `review_round`, `candidate`, and
`review_model_actual` when practical. Every close-out uses `review_class: FAST`,
even when it reuses the original Peer reviewer seat. Review class measures the
work boundary; `review_model_actual` measures the runtime choice. These labels
contain coordination metadata only; do not put prompts, source, or private
evidence in labels.

Close-out emits exactly one machine-countable state: `CLOSEOUT_CLEAR` or
`CLOSEOUT_FINDINGS`. Do not normalize synonyms in the report after the fact.

## Install and activate

After editing the tracked setup:

```bash
make test
./scripts/install --apply
./scripts/sync-all
./scripts/verify
```

The workflow protocol is not symlinked into role runtimes. Role overlays read
only the optional workspace-local `docs/WORKSPACE_PROTOCOL.md`. Installing or
syncing does not restart Paseo.

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

For review-strategy comparisons, also record:

- exploratory and close-out seat count;
- review class, lane, and model;
- accepted findings per exploratory review;
- correction batches per finding family;
- duplicate reviewer mandates;
- stale-candidate reviews;
- review wait duration and total session usage;
- close-out result and any reconciliation trigger.

For the Milestone 5 pilot, the target is at most one exploratory review, one
correction batch, and one close-out per finding family. Material defects must
still be reported. A lower round count is not success if outcome evidence gets
weaker or a material defect escapes.

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
