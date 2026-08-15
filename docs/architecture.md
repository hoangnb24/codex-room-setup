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
| `~/.config/codex-room` | This repository | Role overlays and shared workflow instructions |
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
6. Symlinks shared Codex resources and room workflow files.
7. Removes inherited MCP server tables for Review.

CLI flags and trusted project `.codex/config.toml` files can still override generated user-level values according to normal Codex precedence.

