# Workspace Protocol

This is the small shared contract for a Codex Room workspace. Human
instructions and owner decisions remain authoritative. A repository may add
project-local detail, but cannot change role authority or safety boundaries.

## Authority

- Human owns product goals, priority, material cost, external effects, and
  irreversible risk decisions.
- Supervisor observes, faithfully routes Human intent, and performs bounded
  room recovery. It is not another project Lead.
- Lead owns project framing, technical decisions, integration, verification,
  and explicit candidate acceptance.
- Peer owns one bounded outcome delegated by Lead.

## Ownership and dispatch

Project instructions carry outcomes, constraints, and existing authority, not
private conversation transcripts or attribution about who spoke to whom.
Keep briefs self-contained. Preserve the meaning of an authorized decision;
an evidence-based question does not grant new authority or revoke existing
permission. Resolve a coordination question against current ownership and
evidence, then continue ready work without creating another approval gate.

- Give every moving write scope one owner. Run writable Peers in parallel
  only with verified, accepted inputs and separate write scopes.
- Agree on shared contracts before dispatch. Sequence changes to shared files
  or interfaces; use separate branches or worktrees when needed. Do not start
  blocked work merely to increase parallel activity. Continue each ready
  branch without waiting for unrelated assignments.
- A Peer must notify Lead before changing a shared contract or writing outside
  its owned scope; it must not expand ownership or coordinate other Peers.
- A Lead brief states the observable outcome, dependencies, write scope,
  relevant contract or invariants, acceptance evidence, and when to reopen the
  decision. Implementation file lists remain provisional.
- A writable Peer returns an immutable candidate or deterministic snapshot,
  original base, complete changed paths, verification, and residual risk.
- Preserve unrelated work and existing private notebooks, runtime/session
  state, and operator-owned `.codex` bytes. The setup must not silently take
  ownership of them.

## Ready inputs and continuity

At session resumption, Lead inspects project instructions, actual state, the
latest handoff, and current ownership before assigning work. Verify required
inputs exist, are accepted, and are available in the working context; a closed
task or completion message alone does not establish readiness. Give each
assignment enough context to start without the preceding conversation.

After acceptance, Lead updates the existing work-status source, records
remaining limits and usable downstream inputs, and reconciles affected
assumptions and dependencies before choosing next work. When a decision changes
the plan, update the existing issue or project document, including outdated
task descriptions and completion criteria. Record the decision and its reason
there; do not leave it only in chat or create a duplicate tracker.

## Evidence and handoff

Identify the exact candidate, verification environment, reproduction steps,
actual results, and durable evidence locations. Separate verified behavior,
untested scope, failed checks, and unknowns. Match proof to the promised
outcome: passing tests or valid data alone do not establish usable UI, playback
quality, or save/reopen behavior.

A handoff states what is usable, how to try it, remaining limits, and usable
downstream inputs. Permission to proceed with a limitation does not turn an
unmet criterion into a pass.

## Independent judgment

Peer may return `REOPEN_REQUEST` for a failed premise,
`DEPENDENCY_REQUEST` for an unowned prerequisite, or `BLOCKED` when no safe
in-scope progress remains. Each signal includes evidence, consequence, and the
decision or dependency needed.

When architecture or an exact candidate carries material uncertainty, Lead may
request a fresh read-only Peer review of the stable candidate or snapshot. The
review uses the flexible Peer profile and a bounded question; no dedicated
review role, mandatory form, or reviewer count is
required.

## Acceptance and waiting

Writer proof, passing tests, completion messages, and lifecycle status are
evidence. Lead inspects the exact artifact and explicitly accepts or rejects
the candidate with a technical reason. Human alone decides product scope,
material cost, external effects, and irreversible risk.

Use finish, error, attention, and decision events to advance work. Wait for an
event instead of repeatedly polling unchanged state. Keep handoffs concise and
decision-ready; add detail only when it changes the route or acceptance.
