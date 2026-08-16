# Workspace Protocol

## Status

- owner: Human
- version: 2-pilot
- applies_to: all projects operated through codex-room
- readers: Supervisor, Lead, Peer, and Review
- required companion for complex/repeated failures: `ANTI_PATTERNS.md`

## Precedence and local refinement

Human instructions remain authoritative. A repository may refine this baseline
in `docs/WORKSPACE_PROTOCOL.md`. The repository protocol wins for project-local
tactics and constraints, but cannot silently change Human intent, room-role
authority, or safety boundaries. When the two materially conflict, surface the
conflict instead of combining them.

This pilot standardizes observable handoffs before Paseo enforces workflow
state. The formats below are coordination messages, not a second repository task
tracker. Durable outcome, contract, dependency, decision, and acceptance state
belongs in the active project plan or an ADR. Seat ownership, candidate state,
and pending rulings remain runtime coordination state.

## Authority

- Supervisor owns portfolio governance, routing, workflow observation, evidence
  reconciliation, and authorized Lead lifecycle operations.
- Lead owns project architecture, decomposition, integration, verification, and
  technical acceptance.
- Human owns product goals, portfolio priority, material cost, external effects,
  and risk trade-offs.
- Peer owns only the bounded outcome delegated by Lead.

## Task classes

### Tiny / bounded

Lead may act directly when no judgment separation is needed, otherwise assign one
Peer Engineer.

### Cross-module or lifecycle-sensitive

Use a read-only Architect before one isolated Peer writer. Freeze the candidate,
then use an independent read-only Reviewer.

### Architecture lock-in or owner trade-off

Lead gathers sealed independent opinions, reconciles decision-changing claims,
and escalates owner-only choices through Supervisor to Human.

## Ownership and workspaces

- One writer owns one moving scope.
- Concurrent writers require isolated worktrees.
- Review only an exact commit or deterministic workspace snapshot.
- Preserve unrelated and pre-existing resources.

During the pilot, Lead declares writable scope as normalized repository-relative
directory prefixes. Equal, ancestor, and descendant prefixes overlap. Worktree
isolation does not make overlapping logical scopes independent. When practical,
title a writable seat `[F:<frontier-id>] [W:<scope>]` so ownership is visible in
current Paseo state.

Before parallel dispatch, Lead records:

```text
PARALLEL_CHECK v1
frontiers:
dependency_independent: yes | no
write_scopes:
scope_overlap: yes | no
shared_contract_frozen: yes | no
integration_order:
decision: SERIAL | PARALLEL
```

Use this check only when opening concurrent writable frontiers. Parallel work
requires independent dependencies, non-overlapping scopes, a stable shared
contract, and a credible integration order.

## Planning contract

The active plan fixes only decision-relevant contracts: observable outcome,
API or boundary behavior, validation, persistence and lifecycle, failure and
retry semantics, invariants, dependencies, and acceptance evidence. Proposed
files, classes, helpers, and implementation sequence remain provisional unless
an inspected constraint makes them contractual.

For consequential delegated work, Lead sends:

```text
FRONTIER_BRIEF v1
frontier_id:
plan_ref:
outcome:
depends_on:
write_scope:
stable_contract_refs:
invariants:
acceptance:
reopen_when:
candidate_required: commit | deterministic-snapshot | none
```

Omit fields that truly do not apply, but do not replace them with speculative
implementation detail. Tiny bounded work may use a concise natural-language
brief when the same boundaries are unambiguous.

## Foundation gate

Before dispatching a consequential feature involving cross-module state,
lifecycle, persistence, retry, or a shared contract, Lead records:

```text
FOUNDATION_CHECK v1
state_owner:
lifecycle:
cross_boundary_invariants:
required_mechanisms:
dependency_direction:
status: STABLE | DISCOVERY_REQUIRED | FOUNDATION_REQUIRED
evidence:
```

- `STABLE`: dispatch may proceed.
- `DISCOVERY_REQUIRED`: route bounded read-only investigation first.
- `FOUNDATION_REQUIRED`: assign one foundation writer and hold dependent feature
  work until Lead accepts a stable candidate.

Do not require this ceremony for trivial work with no credible foundation
uncertainty.

## Routing and escalation

- Peer returns `REOPEN_REQUEST` when evidence invalidates a technical premise.
- Peer returns `DEPENDENCY_REQUEST` for unowned prerequisites.
- Peer returns `BLOCKED` when no safe in-scope progress remains.
- Lead decides technical route and candidate verdict.
- Supervisor challenges workflow with evidence, not direct Peer correction.
- Human decides scope, cost, external action, and portfolio trade-offs.

Peer returns a decision-ready disposition:

```text
PEER_DISPOSITION v1
frontier_id:
status: CANDIDATE | REOPEN_REQUEST | DEPENDENCY_REQUEST | BLOCKED
candidate_identity:
observed_evidence:
premise_invalidated:
consequence:
decision_needed:
verification:
residual_risk:
```

Lead responds to every non-candidate disposition, and to consequential candidate
acceptance, with a concrete ruling:

```text
LEAD_RULING v1
frontier_id:
decision: ACCEPT | CONTINUE | REVISE_PLAN | CREATE_DEPENDENCY | SPLIT | CANCEL
evidence_considered:
reason:
plan_changed: yes | no
new_plan_ref_or_digest:
next_frontier:
```

When the plan changes, Lead re-briefs affected work. Do not let downstream work
silently continue against a contract known to be stale.

Suspected anti-patterns use the finding packet, reaction states, reconciliation
states, and convergence guard in `ANTI_PATTERNS.md`. A finding is never a hidden
correction order.

## Verification

Engineer proves the write, Reviewer attempts to falsify the exact candidate, Lead
inspects the artifact and evidence, and Human accepts only owner-level trade-offs.

## Reconciliation cadence

Lead tracks accepted consequential frontiers since the last reconciliation.
After the third acceptance, reconciliation is due. Before dispatch beyond the
fourth, it is required. Reconcile earlier after a reopen, a newly discovered
dependency, or evidence of wrapper, fallback, compatibility, or duplicate-state
work used to preserve a failed premise.

```text
PLAN_RECONCILIATION v1
plan_ref:
accepted_since_last:
code_changed_assumptions:
absorbed_or_obsolete_frontiers:
dependency_changes:
foundation_changes:
parallel_frontier:
next_frontier:
plan_updated: yes | no
```

Reconciliation is a decision checkpoint, not a meeting quota. If no observed
evidence changes the plan, record that compactly and continue. Only Lead updates
the project plan and resets the count.

## Pilot observation

Supervisor may evaluate tagged pilot work without taking over project authority.
Record aggregate marker counts, candidate churn, correction rounds, scope
collisions, stale reviews, accepted reopen requests, outcome evidence, duration,
and token/tool usage. During an evaluation run, avoid coaching that would change
the condition except for material ownership, safety, or Human-intent risk.

Raw rollout JSONL may contain private source and prompts. Keep it local. Export
only sanitized aggregate reports unless Human explicitly authorizes otherwise.

## Protocol evolution

Supervisor records comparable episodes first. Prefer the smallest reversible
instruction or protocol experiment. Propose a Paseo product mechanism only after
at least two comparable episodes show the same missing mechanism.
