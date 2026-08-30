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
| `~/.codex-runtime` | `codex-room-sync` | Generated configs plus role-local sessions, databases, and Harness plugins |
| `~/.paseo` | Paseo | Provider config, agents, projects, worktrees, logs and identity |
| Paseo fork checkout | Git | Source code for CLI, daemon and Desktop |

## Runtime merge

For a role, the sync script:

1. Reads the operator's Codex user config as the base.
2. Replaces an allowlisted set of top-level scalar values from the role overlay.
3. Adds role-specific `developer_instructions`.
4. Generates a model catalog with native multi-agent metadata removed.
5. Forces `[agents].enabled = false` and all native multi-agent feature flags off.
6. Symlinks shared Codex resources and the anti-pattern catalog; Harness keeps a private `plugins/` directory.
7. Removes inherited MCP server tables for Review.

Supervisor, Lead, Peer, and Review retain a canonical
`plugins -> ~/.codex/plugins` symlink. Harness is the sole exception:
`~/.codex-runtime/harness/plugins` is a private directory preserved across
syncs. Migration removes only a symlink resolving to the canonical plugins
directory; every other symlink or non-directory path fails closed.
Harness also strips inherited `[mcp_servers.*]` tables from its generated Codex
config. Its orchestration capability comes only from Paseo provider injection.
The launcher resolves evidence homes read-only with
`codex-room --resolve-evidence-home <role>` and does not sync on that route.

The retained `WORKSPACE_PROTOCOL.md` is not linked into role runtimes. Each
workspace can provide its own `docs/WORKSPACE_PROTOCOL.md`.

CLI flags and trusted project `.codex/config.toml` files can still override generated user-level values according to normal Codex precedence.
