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

The Review runtime is the read-only, OCR-assisted stable-candidate profile. It
does not inherit MCP servers. OCR operational metadata is the only allowed
write from Review behavior.

Supervisor additionally owns a durable `SUPERVISOR_NOTEBOOK.md` initialized from the workflow template.
