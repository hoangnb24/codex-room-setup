# Paths and ownership

## Tracked canonical files

```text
~/.config/codex-room/model-instructions.md
~/.config/codex-room/overlays/*.config.toml
~/.config/codex-room/workflow/*.md
~/.local/bin/codex-room
~/.local/bin/codex-room-sync
~/.local/bin/paseo-local-update
~/.paseo/config.json
```

The repository stores HOME-dependent JSON as `*.template`; installation renders it to the path without `.template`.

## Generated files

```text
~/.codex-runtime/<role>/config.toml
~/.codex-runtime/<role>/model-catalog.no-native-agents.json
~/.codex-runtime/<role>/*.sqlite*
~/.codex-runtime/<role>/sessions/
```

Never edit generated `config.toml` as the durable source. Change the base Codex config or role overlay, then run `scripts/sync-all`.

## Private state

Never commit:

- `~/.codex/auth.json` or other Codex auth stores.
- Paseo daemon keypairs, push tokens, IDs, agent state, worktrees, uploads, logs or PID files.
- Runtime sessions, logs, memories, queues or SQLite databases.
- Backup directories.

