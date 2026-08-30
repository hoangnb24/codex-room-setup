# Runtime generation

`codex-room-sync` treats each role directory as an isolated Codex home while sharing stable personal resources by symlink.

```text
shared:   auth.json, AGENTS.md, hooks.json, skills; plugins for four ordinary roles
isolated: config.toml, sessions, logs, state, memories, queues
Harness:  private plugins directory and exact Better Harness registration preserved
room:     model instructions and workflow documents
```

The model catalog is queried from the installed Codex CLI. Every model has
`multi_agent_version` set to `null`, and the generated config disables native
agents. Paseo therefore owns the supervisor/lead/peer/review/harness topology.
Harness uses Paseo to create exactly three fresh read-only Peer evidence seats;
it does not re-enable native agents. Runtime generation preserves only the
CLI-created `marketplaces.better-harness` and
`plugins."better-harness@better-harness"` tables when they already exist in the
Harness config. It neither derives registration from cached payloads nor
installs or upgrades the plugin.

Runtime snapshots in this repository are optional sanitized audit output. They are ignored by default and are not installation inputs.
