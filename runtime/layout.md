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
├── WORKSPACE_PROTOCOL.md -> ~/.config/codex-room/workflow/WORKSPACE_PROTOCOL.md
└── ANTI_PATTERNS.md -> ~/.config/codex-room/workflow/ANTI_PATTERNS.md
```

Supervisor additionally owns a durable `SUPERVISOR_NOTEBOOK.md` initialized from the workflow template.

