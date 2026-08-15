# Workspace Protocol

## Status

- owner: Human
- version: 1
- applies_to: this lab repository only
- readers: Lead; Supervisor when assigned to audit or update
- required companion for complex/repeated failures: `ANTI_PATTERNS.md`

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

## Routing and escalation

- Peer returns `REOPEN_REQUEST` when evidence invalidates a technical premise.
- Peer returns `DEPENDENCY_REQUEST` for unowned prerequisites.
- Peer returns `BLOCKED` when no safe in-scope progress remains.
- Lead decides technical route and candidate verdict.
- Supervisor challenges workflow with evidence, not direct Peer correction.
- Human decides scope, cost, external action, and portfolio trade-offs.

Suspected anti-patterns use the finding packet, reaction states, reconciliation
states, and convergence guard in `ANTI_PATTERNS.md`. A finding is never a hidden
correction order.

## Verification

Engineer proves the write, Reviewer attempts to falsify the exact candidate, Lead
inspects the artifact and evidence, and Human accepts only owner-level trade-offs.

## Protocol evolution

Supervisor records comparable episodes first. Prefer the smallest reversible
instruction or protocol experiment. Propose a Paseo product mechanism only after
at least two comparable episodes show the same missing mechanism.
