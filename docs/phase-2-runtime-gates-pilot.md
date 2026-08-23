# Phase 2 runtime-gates pilot

This pilot tests four Paseo runtime gates. It does not replace the Paseo app or
the shared daemon. The shared daemon stays on port `6767` with `~/.paseo`.

## Control

The installed control is `paseo-phase2-candidate`. It accepts only these modes:

```bash
paseo-phase2-candidate off
paseo-phase2-candidate observe
paseo-phase2-candidate enforce
```

The default candidate home is `~/.paseo-phase2-runtime-gates`. The default port
is `6779`. The command rejects the shared port `6767` and shared home
`~/.paseo`. The selected mode applies only to the new foreground process.

Use `--dry-run` to validate and print the command:

```bash
paseo-phase2-candidate --dry-run observe
```

`off` keeps Phase 1.1 behavior. When the raw server reads the Paseo environment
variable directly, a missing or invalid value resolves to `off`. The launcher
rejects an invalid mode. Legacy create and send tools bypass all Phase 2 gates
in all modes.

## Build and start the candidate

Use the Paseo experiment branch. Do not run `paseo-local-update`.

```bash
cd ~/projects/supervisors/paseo
npm install
npm run build --workspace=@getpaseo/protocol
npm run typecheck --workspace=@getpaseo/protocol
npm run typecheck --workspace=@getpaseo/server
npm run build:lib --workspace=@getpaseo/server
```

For Codex Room providers, make an isolated copy of the current provider config.
Do not edit the source config during the pilot.

```bash
mkdir -p ~/.paseo-phase2-runtime-gates
install -m 600 ~/.paseo/config.json \
  ~/.paseo-phase2-runtime-gates/config.json
```

Start with observation:

```bash
paseo-phase2-candidate observe
```

Keep this process in its terminal. Use the candidate at `127.0.0.1:6779` from a
separate client. Exit the process before you change mode. A mode change needs a
new process because Paseo reads the mode at startup.

## Pilot record

Use the same repository commit, task, model, reasoning, permissions, and
acceptance checks for each run. Run the same workstream with `off`, `observe`,
and then `enforce`. Use a new candidate process for each run.

Record these fields for every run:

| Field | Source |
| --- | --- |
| Candidate commit and mode | `git rev-parse HEAD`; launch output |
| Gate decisions and reasons | New tool results |
| Gate counters | `runtime_gate_metrics` before and after |
| Duration, tokens, requests, tools | `scripts/session-usage` |
| Created seats and partial batches | Paseo agent list and batch result |
| Outcome and correction rounds | The same workstream acceptance checks |

Do not compare raw counter totals from two long-lived processes. For each run,
subtract the start snapshot from the end snapshot. A lower tool count is not a
success if the outcome is worse.

## Gate 1: attention read

Positive case:

1. Start one test agent and let it finish.
2. Call `read_agent_attention` with its `agentId`, `limit: 5`, and
   `includeFullStatus: false`.
3. Save the returned `cursor` and `readRevision`.
4. Call it again with that exact cursor and revision.
5. Confirm that current evidence can clear finished or error attention.
6. Call it once more with the returned cursor. Confirm `unchanged: true`, an
   empty `activity`, and `updateCount: 0` when no row was added.

Negative case:

1. Use a stale cursor or stale revision.
2. Confirm that attention is not cleared and the result reports stale evidence.
3. For an agent with pending permission, confirm a typed
   `attention / needs_input` dependency and no clear.

## Gate 2: fan-out capability

Positive case:

1. From the probe agent's MCP session, call `record_runtime_probe` with `{}`.
2. Copy the returned target two times into `preflight_agent_fanout.targets`.
3. Pass the returned `probeId` to `preflight_agent_fanout`.
4. Confirm an equivalent result and save its `admissionId`.
5. Call `create_agent_batch` with that admission and two agents that use the
   same provider, model, mode, reasoning, and MCP server names.
6. Confirm two created agent IDs. Confirm that the admission cannot be reused.

Negative case:

1. Request two targets without a probe, or use a non-equivalent target.
2. In `observe`, confirm a soft decision and record whether dispatch continues.
3. In `enforce`, confirm a block and zero created seats.

## Gate 3: typed handoff

Positive case:

1. Call `handoff_workflow` with `action: inspect`, a real `agentId`, a workflow
   family, role, and candidate ID.
2. Confirm that provider, model, status, elapsed time, reasoning, and MCP facts
   come from the runtime result.
3. Send a non-review handoff with `action: send`, a prompt,
   `dispositionStatus`, `reviewClass`, and `reviewMode`.
4. Confirm `dispatched: true` and the typed values in the result.

Negative case:

1. Omit one required send field, or use a value outside its enum.
2. Confirm schema rejection and no dispatch.
3. Confirm that input cannot set provider, model, status, or elapsed facts.

## Gate 4: review family

Use unique opaque strings for `reviewFamilyId` and `findingSetId` in each pilot
run.

Positive case:

1. Call `review_family_guard` for one `kind: review` dispatch.
2. Confirm a visible first-dispatch decision.
3. Use `handoff_workflow` to send that review with matching review family data.
4. Call the guard, then send the first `kind: correction` with the same
   candidate, review family, finding set, and reviewer.
5. Confirm visible allow decisions and reservation outcomes.

Negative case:

1. Call `review_family_guard` for a second correction with the same identity
   and no reconciliation.
2. Attempt the same dispatch through `handoff_workflow`.
3. Confirm a reconciliation block in `enforce`.
4. Attempt to reuse the reviewer with a different family or finding set.
5. Confirm a visible unrelated-family decision.
6. If a send fails, confirm that retry needs typed reconciliation evidence.

## Cutover checks

Do not cut over the shared daemon until all checks are true:

- `observe` false positives are understood.
- `enforce` blocks each negative case and permits each positive case.
- No required client path uses legacy create or send tools.
- Probe and MCP capability matching works for each pilot provider.
- Partial sequential batch creation has an operator recovery procedure.
- Restart loss, 60-second expiry, and bounded record eviction are acceptable.
- Review retries use reconciliation after a failed send.

Known limits: Phase 2 records and metrics are process-local. Restart clears
them. Probes and admissions expire after 60 seconds. Review history is bounded.
Batch creation is sequential and can create a partial batch. `observe` permits
failed gate decisions. Historical data can be partial or unavailable.

## Disable and rollback

Stop the foreground candidate first. This does not stop or restart the shared
daemon. To test the isolated candidate with gates disabled, start a new
process:

```bash
paseo-phase2-candidate off
```

To remove the installed experiment control, stop it and move only that command
to a recoverable backup:

```bash
phase2_backup="$HOME/.codex-room-backups/phase2-runtime-gates-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$phase2_backup"
mv "$HOME/.local/bin/paseo-phase2-candidate" "$phase2_backup/"
```

Preserve `~/.paseo-phase2-runtime-gates` for evidence. Remove it only after its
agent records and logs are no longer needed. No rollback step changes
`~/.paseo`, port `6767`, or `/Applications/Paseo.app`.

To roll back this setup candidate on
`experiment/phase-2-runtime-gates`, run:

```bash
git revert --no-edit \
  655d27ab353c51105ff8a5dadd333259826fa1bc^..experiment/phase-2-runtime-gates
```

To roll back the Paseo experiment on its
`experiment/phase-2-runtime-gates` branch, run from the Paseo checkout:

```bash
git revert --no-edit \
  1e84c503c4ed6f6aaaacaf2523210cc8b2beb410..experiment/phase-2-runtime-gates
```

Do not stage, edit, or remove `.codex/config.toml` during either rollback.
