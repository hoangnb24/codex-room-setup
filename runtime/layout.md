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
├── model-instructions.md -> ~/.config/codex-room/model-instructions.md
└── ANTI_PATTERNS.md -> ~/.config/codex-room/workflow/ANTI_PATTERNS.md
```

`WORKSPACE_PROTOCOL.md` remains installed under `~/.config/codex-room/workflow/`
as a reference file. Role runtimes do not link to it. A workspace can define its
own protocol at `docs/WORKSPACE_PROTOCOL.md`.

Supervisor additionally owns a durable `SUPERVISOR_NOTEBOOK.md` initialized from the workflow template.
