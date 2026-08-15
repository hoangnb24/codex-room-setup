# Runtime generation

`codex-room-sync` treats each role directory as an isolated Codex home while sharing stable personal resources by symlink.

```text
shared:   auth.json, AGENTS.md, hooks.json, skills, plugins
isolated: config.toml, sessions, logs, state, memories, queues
room:     model instructions and workflow documents
```

The model catalog is queried from the installed Codex CLI. Every model has `multi_agent_version` set to `null`, and the generated config disables native agents. Paseo therefore owns the supervisor/lead/peer/review topology.

Runtime snapshots in this repository are optional sanitized audit output. They are ignored by default and are not installation inputs.

