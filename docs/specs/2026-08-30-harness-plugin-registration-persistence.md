# Preserve Harness plugin registration across runtime sync

## Traceability

- Spec ID: harness-plugin-registration-persistence
- Status: Implemented

## Intent

Keep an operator-installed Better Harness plugin discoverable after
`codex-room-sync harness` and after launching a new `codex-harness` Paseo seat.
The current sync preserves the private plugin cache but regenerates
`config.toml` without the marketplace and plugin registration, so every launch
makes a successful installation unavailable.

## Acceptance Scenarios

- AC-1: Given an existing Harness runtime config containing the
  `better-harness` marketplace and `better-harness@better-harness` plugin
  registration, syncing Harness preserves both exact registrations and keeps
  the plugin enabled.
- AC-2: Syncing another role, or syncing Harness before Better Harness has been
  installed, does not synthesize a marketplace or plugin registration.
- AC-3: Repeated Harness sync continues to preserve the private plugin payload,
  restores directory mode `0700`, disables native agents, and strips inherited
  MCP server tables.
- AC-4: The installed live runtime passes the native Codex discovery check
  before and after `codex-room-sync harness`.

## Non-goals

- Installing, upgrading, or selecting a Better Harness revision during sync.
- Preserving arbitrary generated-runtime configuration edits.
- Sharing the canonical Codex plugin directory with Harness.
- Changing the read-only Harness authority or its three-Peer topology.

## Plan and Tasks

1. Treat the two Better Harness registration tables in the existing Harness
   runtime config as operator-owned private lifecycle state.
2. Before replacing the generated config, retain only those exact tables and
   compose them into the fresh base-plus-overlay config without duplicating a
   table already supplied by the fresh configuration.
3. Add focused tests for preservation, absence-before-install, role isolation,
   and the existing private-cache and security invariants.
4. Update the Harness lifecycle documentation to state that sync preserves
   both payload and registration but never performs installation or upgrades.

The boundary remains inside `codex-room-sync`: the runtime generator owns
composition of generated config with the narrowly authorized role-local state.
Codex CLI remains the owner of creating or changing that state.

## Test and Review Evidence

- AC-1, AC-2: `python3 -m unittest tests.test_setup.RuntimeGenerationTests`
  with positive and negative registration fixtures.
- AC-3: the existing repeated-sync, MCP stripping, and native-agent assertions
  in `RuntimeGenerationTests` remain green.
- AC-4: install or re-enable the pinned Better Harness plugin in
  `~/.codex-runtime/harness`, run `codex plugin list --marketplace
  better-harness --json`, run `codex-room-sync harness`, and repeat the same
  discovery command.
- Risk: retaining all runtime tables would preserve stale or unauthorized
  generated config. The implementation must allowlist only the named Better
  Harness marketplace and plugin tables.

Implementation evidence is recorded by the deterministic repository test
fixtures. A disposable real Codex CLI lifecycle also installed Better Harness
0.6.5 from the pinned marketplace revision and reported `installed: true` and
`enabled: true` both before and after repository `codex-room-sync harness`.
The operator-owned live runtime was not modified.
