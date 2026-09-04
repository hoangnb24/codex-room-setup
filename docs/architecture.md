# Architecture

## Control flow

```text
~/.paseo/config.json
  custom provider command
      |
      v
~/.local/bin/codex-room <role>
      |
      +-- codex-room-sync <role>
      |     +-- reads ~/.codex/config.toml
      |     +-- reads ~/.config/codex-room/overlays/<role>.config.toml
      |     +-- reads codex debug models
      |     `-- writes ~/.codex-runtime/<role>/
      |
      `-- CODEX_HOME=~/.codex-runtime/<role> codex ...
```

## Ownership

| Layer | Owner | Mutable state |
| --- | --- | --- |
| `~/.codex` | Operator/Codex | Auth, global config, skills, plugins, sessions |
| `~/.config/codex-room` | This repository | Role overlays and retained workflow references |
| `~/.codex-runtime` | `codex-room-sync` | Generated configs plus role-local sessions and databases |
| `~/.paseo` | Paseo | Provider config, agents, projects, worktrees, logs and identity |
| Paseo fork checkout | Git | Source code for CLI, daemon and Desktop |

## Runtime merge

For a role, the sync script:

1. Reads the operator's Codex user config as the base.
2. Replaces an allowlisted set of top-level scalar values from the role overlay.
3. Adds role-specific `developer_instructions`.
4. Generates a model catalog with native multi-agent metadata removed.
5. Forces `[agents].enabled = false` and all native multi-agent feature flags off.
6. Symlinks shared Codex resources and the anti-pattern catalog.

Supervisor, Lead, and Peer retain a canonical
`plugins -> ~/.codex/plugins` symlink. Review and Harness directories from older
installations are not generated, inspected, migrated, or removed.
The launcher resolves evidence homes read-only with
`codex-room --resolve-evidence-home <role>` and does not sync on that route.

The retained `WORKSPACE_PROTOCOL.md` is not linked into role runtimes. Each
workspace can provide its own `docs/WORKSPACE_PROTOCOL.md`.

CLI flags and trusted project `.codex/config.toml` files can still override generated user-level values according to normal Codex precedence.
