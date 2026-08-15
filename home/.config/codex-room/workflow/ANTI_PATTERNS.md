# Anti-pattern Detection and Reaction

Read this file when planning architecture, reviewing a complex candidate, or
observing a repeated failure. A suspected anti-pattern is a hypothesis, never an
order that a lower role must confirm.

## Ownership

- Supervisor watches portfolio-wide and repeated Lead–Peer workflow signals.
- Lead owns project-level technical reconciliation and corrective decisions.
- Peer reports local signals and challenges false framing with evidence.
- Human decides changes to product goals, portfolio priority, material cost,
  external effects, and owner-only risk.

Supervisor does not bypass Lead to correct Peer. Lead does not treat disagreement
as disobedience. Peer does not manufacture disagreement to appear independent.

## Finding packet

```text
finding_id:
pattern:
observation:
evidence:
counterevidence:
risk:
confidence: low | medium | high
open_question:
```

The open question must not contain a hidden verdict. A packet without inspectable
evidence requests investigation; it does not authorize correction.

## Reaction chain

### Supervisor observes Lead–Peer workflow

```text
Supervisor sends finding packet to Lead
  -> Lead: CONFIRM | PARTIAL | CHALLENGE | BLOCK
  -> Supervisor: UPHOLD | NARROW | DISMISS | ESCALATE
  -> Lead chooses the technical action inside project authority
  -> Human decides only when owner authority is required
```

### Lead observes a problem inside Peer work

```text
Lead sends a neutral finding packet to Peer
  -> Peer: CONFIRM | PARTIAL | CHALLENGE | BLOCK
  -> Lead inspects both sides and decides technical disposition
  -> Supervisor is notified when the pattern repeats, workflow is impaired,
     or an owner/topology decision is required
```

Reaction meanings:

- `CONFIRM`: evidence supports the finding and its framing.
- `PARTIAL`: evidence supports only a narrower cause or scope.
- `CHALLENGE`: evidence contradicts the finding or framing.
- `BLOCK`: safe progress requires a missing prerequisite or authority decision.
- `UPHOLD`: act on the finding as stated.
- `NARROW`: act only on the supported portion.
- `DISMISS`: preserve evidence and take no corrective action.
- `ESCALATE`: Human authority or a material topology/scope decision is required.

Majority vote, model count, role seniority, strong wording, and lifecycle status
are not proof.

## Catalog

### 1. Authority-gradient compliance / sheep behavior

- Signal: Peer repeats Lead's premise and every response says “agreed.”
- Cause: the brief already contains the verdict, so compliance is rewarded.
- Reaction: reopen the question, request evidence, and allow all four reactions.

### 2. Performative dissent

- Signal: Peer invents objections or alternatives without decision-changing evidence.
- Cause: independence is confused with disagreement.
- Reaction: judge mechanism and evidence, not whether Peer agrees or objects.

### 3. Pre-solving / perfect-plan trap

- Signal: Lead predetermines every file, API, lifecycle, and solution.
- Cause: untested assumptions become an implementation order.
- Reaction: make the plan provisional and let Peer reopen a failed premise.

### 4. Parachute optimization / missing brakes

- Signal: a third correction still patches the same symptom family.
- Cause: local patches compensate for one missing foundational mechanism.
- Reaction: stop patching and ask which shared mechanism generates all findings.

### 5. Architecture lock-in

- Signal: each change needs another adapter, exception, or compatibility layer.
- Cause: agents keep a weak foundation alive because changing it feels expensive.
- Reaction: commission read-only alternatives, strongest counterargument, and
  reversal conditions before another layer is added.

### 6. Architecture fog

- Signal: many abstractions exist, but state owner and lifecycle cannot be stated
  in one sentence.
- Cause: wrappers postpone an ownership decision.
- Reaction: name owner, transitions, failure semantics, and what behavior
  disappears if each abstraction is deleted.

### 7. Moving-scope collision

- Signal: two writers edit one subsystem or Reviewer reads while Writer changes it.
- Cause: ownership and candidate identity are unstable.
- Reaction: one writer per moving scope, isolated worktrees, explicit handback,
  and an exact stable candidate.

### 8. Self-benchmark / self-acceptance

- Signal: one agent designs the metric, implements it, runs it, and approves itself.
- Cause: proof and implementation share one blind spot.
- Reaction: Lead sets success boundaries and uses an independent Reviewer when
  consequence warrants it.

### 9. Test-shaped proof

- Signal: tests mirror implementation, mocks remove the real failure, or passing
  tests do not prove the user outcome.
- Cause: the proof route is optimized for green output.
- Reaction: apply deletion sensitivity and independent truth; ask what wrong
  mechanism makes this test fail.

### 10. Overengineering an edge case

- Signal: a low-frequency edge case creates disproportionate infrastructure.
- Cause: completeness is valued without comparing maintenance cost and risk.
- Reaction: quantify frequency, impact, simpler fallback, and reversal cost.

### 11. Polling and autonomous-loop debt

- Signal: unchanged status is polled repeatedly or the same failed tool call is retried.
- Cause: repetition is mistaken for progress despite unchanged prerequisites.
- Reaction: use events and bounded waits; after two identical external failures,
  inspect quota, auth, authority, and durable state before retrying.

### 12. Ceremony capture

- Signal: every task receives councils, votes, reports, and multiple agents.
- Cause: process volume creates false confidence and consumes attention.
- Reaction: use the smallest topology that closes an actual evidence gap.

### 13. Debate framing capture

- Signal: all alternatives remain inside Lead's original and possibly false framing.
- Cause: challenger sees the preferred solution before reconstructing the problem.
- Reaction: use a neutral brief and sealed independent report when framing risk is high.

### 14. Forked independence

- Signal: Reviewer inherits Lead's or Writer's session and is called independent.
- Cause: hidden framing and context are shared.
- Reaction: use a fresh session, neutral mandate, and exact candidate identity.

### 15. Lead attention dilution

- Signal: Lead spends its context answering every Human question instead of
  tracking dependencies, ownership, candidates, and decisions.
- Cause: project coordination and broad advisory conversation share one attention budget.
- Reaction: Supervisor handles portfolio Q&A and relays concise owner decisions.

### 16. Skill pollution

- Signal: Peer orchestrates agents, Lead dives into framework micro-detail, or each
  role loads many irrelevant skills.
- Cause: tool availability redirects role attention.
- Reaction: Supervisor gets strategy skills, Lead macro coordination skills, and
  Peer task-specific micro skills through progressive disclosure.

### 17. Status as acceptance

- Signal: `finished` or “tests pass” is reported as completion without exact diff,
  scope, candidate identity, or evidence review.
- Cause: lifecycle state is mistaken for product truth.
- Reaction: status only wakes the owner; Lead accepts the exact artifact after
  proportionate verification.

### 18. Supervisor overreach

- Signal: Supervisor directly edits project code, declares architecture, or
  micromanages Peer.
- Cause: governance becomes a second Lead and creates conflicting authority.
- Reaction: Supervisor asks an evidence-backed question, relays owner decisions,
  or proposes Lead recovery/replacement; implementation requires an explicit mandate.

### 19. Outcome displacement

- Signal: easy local tasks, plans, and status reports grow while the highest-risk
  acceptance gate remains untouched.
- Cause: visible activity substitutes for progress.
- Reaction: restate the single highest-value blocker and choose the next
  evidence-producing action.

### 20. Scout-as-judge / flaky false-red

- Signal: reconnaissance output becomes a verdict, or concurrent proof jobs
  contend for ports, files, or services.
- Cause: weak or environmentally corrupted evidence triggers correction.
- Reaction: Lead or an independent Reviewer reproduces the claim in an isolated,
  stable environment before authorizing change.

## Convergence guard

After two correction rounds in one finding family:

1. Stop another symptom-level patch.
2. Freeze the latest candidate and correction history.
3. Check for one shared missing mechanism or false premise.
4. Lead decides redesign, bounded correction, no-action, or owner escalation.
5. A new candidate requires fresh independent review when the original review
   boundary materially changed.

## Finding handoff

```text
finding_id:
finding_source: supervisor | lead | peer | reviewer
receiver_reaction: CONFIRM | PARTIAL | CHALLENGE | BLOCK
reaction_evidence:
technical_disposition:
supervisor_reconciliation: UPHOLD | NARROW | DISMISS | ESCALATE | not-required
reconciliation_reason:
candidate_identity:
unresolved_risk:
```

Absence of a reaction is not agreement. Preserve challenged and dismissed
findings so future episodes can compare mechanisms without rewriting history.

