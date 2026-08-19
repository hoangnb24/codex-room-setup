# Codex Room Setup

Reproducible configuration for a four-role Codex room running through a local Paseo fork:

```text
Paseo provider
  -> codex-room <supervisor|lead|peer|review>
  -> codex-room-sync
  -> isolated ~/.codex-runtime/<role>
  -> Codex app-server
```

This repository deliberately does **not** own `~/.codex`. Each operator installs and authenticates Codex independently. The sync script reads the operator's existing `~/.codex/config.toml` as its base and shares their auth, skills, plugins, hooks, and global `AGENTS.md` by symlink.

## What gets installed

The `home/` directory mirrors `$HOME`:

| Repository source | Local destination |
| --- | --- |
| `home/.config/codex-room/` | `~/.config/codex-room/` |
| `home/.local/bin/codex-room*` | `~/.local/bin/` |
| `home/.paseo/config.json.template` | `~/.paseo/config.json` |

`scripts/install-paseo-fork` also creates this checkout-aware symlink:

```text
~/.local/bin/paseo
  -> ~/projects/supervisors/paseo/packages/cli/bin/paseo
```

`@@HOME@@` placeholders are rendered during installation. Runtime databases, sessions, logs, auth files, keypairs, tokens, worktrees, and backups are never installed from or exported into Git.

## Install

Prerequisites:

- macOS or a Unix-like environment with Bash, Python 3, Git, Node, npm, and jq.
- Codex installed and authenticated.
- `~/.local/bin` on `PATH`.

```bash
git clone <this-repository-url> codex-room-setup
cd codex-room-setup

./scripts/doctor
./scripts/install                 # dry-run only
./scripts/install --apply         # backup and install
./scripts/install-paseo-fork      # clone/verify the fork and link its CLI
./scripts/sync-all                # materialize four CODEX_HOME directories
./scripts/verify                  # verify installed files and runtimes
```

The installer backs up every replaced file under:

```text
~/.codex-room-backups/install-<UTC timestamp>/
```

It never writes to `~/.codex`.

## Paseo Desktop

After the fork exists at `~/projects/supervisors/paseo`:

```bash
paseo daemon start
paseo daemon status
paseo-local-update
```

That command updates the checkout, installs dependencies, builds and signs the local Desktop app, backs up the previous `/Applications/Paseo.app`, restarts the daemon, and opens Paseo.

## Roles

| Role | Default model | Reasoning | Paseo MCP injection |
| --- | --- | --- | --- |
| Supervisor | `gpt-5.6-sol` | medium | yes |
| Lead | `gpt-5.6-sol` | medium | yes |
| Peer | `gpt-5.6-sol` | medium | no |
| Review | `gpt-5.6-luna` | max | no |

All role overlays currently request `danger-full-access` with `approval_policy = "never"`. Review additionally strips inherited MCP server tables. Read [docs/architecture.md](docs/architecture.md) before changing these boundaries.

## Common operations

```bash
# Regenerate all role runtimes after changing an overlay
./scripts/sync-all

# Validate source only, without requiring installed runtimes
./scripts/verify --source

# Include live Paseo checks
./scripts/verify --live

# Export sanitized runtime summaries for local comparison
./scripts/export-runtime-snapshots

# Summarize one Codex rollout session for benchmarking
./scripts/session-usage --role peer --session-id SESSION_ID

# Count workflow-pilot markers without exporting rollout content
./scripts/workflow-pilot-report --format json /path/to/rollout.jsonl
```

See [docs/session-usage-benchmark.md](docs/session-usage-benchmark.md) for token,
request, tool-call, timing, and API-equivalent cost definitions.
See [docs/workflow-pilot.md](docs/workflow-pilot.md) for the setup-only workflow
experiment and the evidence threshold for adding Paseo enforcement.

Official Codex configuration precedence is documented by OpenAI in the [Codex config basics](https://learn.chatgpt.com/docs/config-file/config-basic.md). `codex-room` uses a separate `CODEX_HOME` per role; this is a local orchestration layer, not a replacement for the operator's Codex installation.
