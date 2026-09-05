# Expected role layout

```text
<role>/
├── config.toml
├── model-catalog.no-native-agents.json
├── auth.json -> ~/.codex/auth.json
├── AGENTS.md -> ~/.codex/AGENTS.md
├── hooks.json -> ~/.codex/hooks.json
├── skills -> ~/.codex/skills
├── plugins -> ~/.codex/plugins
└── model-instructions.md -> ~/.config/codex-room/model-instructions.md
```

`WORKSPACE_PROTOCOL.md` remains installed under `~/.config/codex-room/workflow/`
as a reference file. Role runtimes do not link to it. A workspace can define its
own protocol at `docs/WORKSPACE_PROTOCOL.md`.

The generator does not initialize or prune private workflow files. Existing
runtime/session state remains in place across repeated generation.
