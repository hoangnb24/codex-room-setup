# Codex Room Setup

Reproducible configuration for a five-role Codex room running through a local Paseo fork:

```text
Paseo provider
  -> codex-room <supervisor|lead|peer|review|harness>
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
./scripts/bootstrap               # dry-run: show every pinned dependency/action
./scripts/bootstrap --apply       # install dependencies, config and five runtimes
```

`scripts/bootstrap` installs the pinned Open Code Review release, normalizes
the Paseo checkout to `origin = hoangnb24 fork` and `upstream = public repo`,
installs Paseo's npm dependencies, and installs Better Harness from its audited
fork commit into the private Harness home. It does not install or authenticate
Codex and does not build Paseo Desktop. The lower-level `install`,
`install-paseo-fork`, `sync-all`, and `verify` commands remain available for
targeted maintenance.

Both source manifests pin immutable commits. Bootstrap preflights Paseo and
Better Harness in disposable locations before changing live state. Paseo uses
`npm ci` and refuses custom Git hooks because its audited `prepare` lifecycle
installs lefthook; updates are exact-pin/no-op or fast-forward-only and never
silently pull from public upstream. Better Harness installation verifies the
actual marketplace checkout commit and restores the previous Harness runtime if
the live transition fails.

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

That command validates provenance and hook/lock safety, advances only to the
audited commit, runs `npm ci`, builds and ad-hoc signs the local Desktop app,
backs up the prior `/Applications/Paseo.app`, installs the new build, and
restarts Paseo.

## Roles

| Role | Default model | Reasoning | Paseo MCP injection |
| --- | --- | --- | --- |
| Supervisor | `gpt-5.6-sol` | medium | yes |
| Lead | `gpt-5.6-sol` | medium | yes |
| Peer | `gpt-5.6-sol` | medium | no |
| Review (OCR-assisted stable candidate) | `gpt-5.6-luna` | max | no |
| Harness (Better Harness coordinator) | `gpt-5.6-sol` | medium | yes |

Lead sends premise, architecture, and macro review to a read-only Peer. Lead
uses Review only for a frozen, bounded candidate that needs OCR-assisted file or
rule selection. Lead does not run OCR. All role overlays currently request
`danger-full-access` with `approval_policy = "never"`. Review additionally
strips inherited MCP server tables. Read
[docs/architecture.md](docs/architecture.md) before changing these boundaries.

Harness coordinates one Better Harness report over one explicitly selected role
home. Its plugins are private to `~/.codex-runtime/harness`; the other four
roles continue to share `~/.codex/plugins`. Harness dispatches exactly three
fresh read-only Peer seats through Paseo while native Codex agents remain off.
See [docs/better-harness-role.md](docs/better-harness-role.md) for the explicit,
profile-local plugin installation and evidence-scope procedure. The audited
fork and immutable commit are recorded in
[`better-harness/source.toml`](better-harness/source.toml).

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

The workflow pilot also supports a guarded multiple-writer operation. Whenever
at least two writable frontiers are ready, Lead runs a positive concurrency
gate; the safe default remains `SERIAL`, and at most two writers may run at once
in a repository. Admission requires separate worktrees at one exact base,
independent physical and logical scopes, a frozen contract, and commit-only
handoffs. Lead integrates the commits serially and verifies the composed result.
See [docs/workflow-pilot.md](docs/workflow-pilot.md#guarded-multiple-writer-pilot)
for the contract and [docs/operations.md](docs/operations.md#run-the-guarded-multiple-writer-pilot)
for the runbook.

Official Codex configuration precedence is documented by OpenAI in the [Codex config basics](https://learn.chatgpt.com/docs/config-file/config-basic.md). `codex-room` uses a separate `CODEX_HOME` per role; this is a local orchestration layer, not a replacement for the operator's Codex installation.
