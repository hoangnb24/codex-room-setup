# Runtime generation

`codex-room-sync` treats each role directory as an isolated Codex home while sharing stable personal resources by symlink.

```text
shared:   auth.json, AGENTS.md, skills, plugins; hooks.json when present
isolated: config.toml, sessions, logs, state, memories, queues
room:     model instructions and workspace protocol reference
```

The model catalog is queried from the installed Codex CLI. Every model has
`multi_agent_version` set to `null`, and the generated config disables native
agents. Paseo therefore owns exactly the supervisor/lead/peer topology. The
generator never prunes sibling directories or private files, so existing
operator state remains outside the active lifecycle.

The operator may keep native agents enabled in `~/.codex/config.toml`. Each
Room runtime overrides `agents.enabled` and `features.multi_agent` to `false`.
For v2, a boolean becomes `false`; an existing `[features.multi_agent_v2]`
table keeps its settings but gets `enabled = false`. The verifier accepts both
disabled representations and reports TOML parse errors separately from enabled
policy flags. The operator config is never rewritten.

`WORKSPACE_PROTOCOL.md` is an installed reference under
`~/.config/codex-room/workflow/`; it is not copied into each generated
runtime. The generated role instructions carry the authority boundary, while
the workspace protocol remains available to the operator and workspace.

Runtime snapshots in this repository are optional sanitized audit output. They are ignored by default and are not installation inputs.
