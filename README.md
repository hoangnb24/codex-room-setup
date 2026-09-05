# Codex Room Setup

Reproducible configuration for a three-role Codex room running through a local Paseo fork:

```text
Paseo provider
  -> codex-room <supervisor|lead|peer>
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

- macOS or a Unix-like environment with Bash, Python 3.11, Git, Node, npm, and jq.
- Codex installed and authenticated.
- `~/.local/bin` on `PATH`.

```bash
git clone <this-repository-url> codex-room-setup
cd codex-room-setup

./install                         # read-only plan and prerequisite check
./install --apply                 # transactional Paseo/config/runtime install
./install --verify                # installed checks plus live provider inventory
```

The root command preflights the pinned Paseo checkout, renders managed HOME
files, stages all three role runtimes, and publishes the complete transition
with rollback on a dependency, generation, or final verification failure. It
does not install or authenticate Codex, touch `~/.codex`, start a daemon, or
build Paseo Desktop. `./install --verify` is read-only and fails when the live
Paseo provider inventory cannot be reached; use `scripts/verify` for an
installed-only diagnostic. The lower-level scripts remain available for
targeted maintenance and are not the normal fresh-install lifecycle.

## Disposable container acceptance test

With Docker available, one command exercises the public installer twice against
a fresh, fake operator home:

```bash
make test-container
```

The test uses a digest-pinned Node 22 base with Debian's Python 3.11, mounts
this checkout read-only, and supplies `tests/fixtures/model-catalog.json` so it
does not need Codex API authentication. It downloads the pinned Paseo source
and npm dependencies (excluding untested Electron/Playwright GUI binaries),
but never mounts or copies the host's `~/.codex`, auth,
sessions, plugins, or other operator data. A successful run prints the exact
Codex role inventory, Paseo MCP recipients, runtime tree, and
`CONTAINER_ACCEPTANCE_OK`.

This Linux container proves the installer topology, legacy-role rejection,
repeatability, and preservation boundaries. It does not prove Paseo Desktop or
GUI behavior, macOS signing/TCC/application restart, or a live Paseo daemon or
Codex session.

The Paseo source manifest pins an immutable commit. The public installer
preflights Paseo in a disposable location before changing live state. Paseo uses
`npm ci` and refuses custom Git hooks because its audited `prepare` lifecycle
installs lefthook; updates are exact-pin/no-op or fast-forward-only and never
silently pull from public upstream.

The installer backs up every replaced managed file and the Paseo checkout under
`~/.codex-room-backups/core3-<UTC timestamp>-<pid>/` with owner-only
permissions. Customized obsolete files are preserved with a warning; only
recognized, unchanged legacy artifacts are retired after backup.

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
Lead may request a fresh read-only Peer review when independent judgment can
change a technical decision. All role overlays currently request `danger-full-access` with
`approval_policy = "never"`. Read
[docs/architecture.md](docs/architecture.md) before changing these boundaries.

## Common operations

```bash
# Regenerate all role runtimes after changing an overlay
./scripts/sync-all

# Validate source only, without requiring installed runtimes
./scripts/verify --source

# Verify installed state and the live Paseo provider inventory
./install --verify

# Export sanitized runtime summaries for local comparison
./scripts/export-runtime-snapshots

# Summarize one Codex rollout session for benchmarking
./scripts/session-usage --role peer --session-id SESSION_ID

```

See [docs/session-usage-benchmark.md](docs/session-usage-benchmark.md) for token,
request, tool-call, timing, and API-equivalent cost definitions.
See [docs/operations.md](docs/operations.md) for the single-writer handoff,
candidate acceptance, and maintenance runbooks.

Official Codex configuration precedence is documented by OpenAI in the [Codex config basics](https://learn.chatgpt.com/docs/config-file/config-basic.md). `codex-room` uses a separate `CODEX_HOME` per role; this is a local orchestration layer, not a replacement for the operator's Codex installation.
