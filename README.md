# Codex Room Setup

Reproducible configuration for a three-role Codex room running through a local Paseo fork:

```text
Paseo provider
  -> codex-room <supervisor|lead|peer>
  -> codex-room-sync
  -> isolated ~/.codex-runtime/<role>
  -> Codex app-server
```

This repository deliberately does **not** own `~/.codex`. Each operator installs and authenticates Codex independently. The sync script reads the operator's existing `~/.codex/config.toml` as its base and shares their auth, skills, plugins, and global `AGENTS.md` by symlink. Hooks are shared only when `hooks.json` exists.

## What gets installed

The `home/` directory mirrors `$HOME`:

| Repository source | Local destination |
| --- | --- |
| `home/.config/codex-room/` | `~/.config/codex-room/` |
| `home/.local/bin/codex-room*` | `~/.local/bin/` |
| `home/.paseo/config.json.template` | `~/.paseo/config.json` |

The public installer creates this checkout-aware symlink:

```text
~/.local/bin/paseo
  -> ~/projects/supervisors/paseo/packages/cli/bin/paseo
```

`@@HOME@@` placeholders are rendered during installation. Runtime databases, sessions, logs, auth files, keypairs, tokens, worktrees, and backups are never installed from or exported into Git.

## Install

Prerequisites:

- macOS or another Unix-like environment with Bash, Python 3.11 or newer,
  Git, Node 22, npm, and jq.
- Codex CLI installed and authenticated, with an existing `~/.codex/config.toml`,
  `auth.json`, `AGENTS.md`, `skills/`, and `plugins/` available for runtime
  sharing. `hooks.json` is optional: an existing file is shared, while an
  absent file is skipped without creating anything in the operator home.
- `~/.local/bin` on `PATH`.

```bash
git clone https://github.com/hoangnb24/codex-room-setup.git codex-room-setup
cd codex-room-setup

./install                         # read-only plan and prerequisite check
./install --apply                 # transactional Paseo/config/runtime install
./install --verify                # installed checks plus live provider inventory
```

The root command preflights the pinned Paseo checkout, installs dependencies,
builds the Paseo server/CLI bundles, renders managed HOME files, stages all
three role runtimes, and publishes the complete transition with rollback on a
dependency, build, generation, or final verification failure. It does not
install or authenticate Codex, touch `~/.codex`, start a daemon, or build
Paseo Desktop. Start and reach the local provider daemon explicitly before
live verification:

```bash
paseo daemon start
paseo daemon status
./install --verify
```

`./install --verify` is read-only and fails when the live Paseo provider
inventory cannot be reached. Use `scripts/verify` for an installed-only
diagnostic while the daemon is stopped. Repeating `./install --apply` is the
upgrade path: it regenerates the three managed runtimes, preserves operator
Codex files and existing runtime/session data, and retires only recognized,
unchanged legacy artifacts.

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

This Linux container checks installer topology, legacy-role rejection,
repeatability, preservation, and real Paseo daemon startup with a provider RPC.
Authenticated Codex sessions, Paseo Desktop/GUI behavior, and macOS
signing/TCC/application restart remain operator checks.

The Paseo source manifest pins an immutable commit. The public installer
preflights Paseo in a disposable location before changing live state. Paseo uses
`npm ci` and refuses custom Git hooks because its audited `prepare` lifecycle
installs lefthook; updates are exact-pin/no-op or fast-forward-only and never
silently pull from public upstream.

The installer backs up every replaced managed file and the Paseo checkout under
`~/.codex-room-backups/core3-<UTC timestamp>-<pid>-<nanoseconds>/` with
owner-only permissions. The coordinator owns the CLI-link backup as part of
the same transaction; the delegated Paseo helper does not create a second
backup. Customized obsolete files are preserved with a warning; only
recognized, unchanged legacy artifacts are retired after backup.

If `Ctrl-C` or `SIGTERM` arrives during apply, the installer settles its
owned helper process group and rolls back the published state. A power loss or
`SIGKILL` can interrupt before rollback and remains an operating-system
durability limit; inspect the restricted transaction backup before retrying.

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
Human retains product, cost, external-effect, and irreversible-risk decisions.
Supervisor routes Human intent and bounded recovery. Lead owns technical
framing, dependency order, verification, and explicit candidate acceptance.
Peer owns one bounded outcome and returns an immutable candidate or a concrete
block signal. Lead may request a fresh read-only Peer review when independent
judgment can change a technical decision. All role overlays currently request
`danger-full-access` with `approval_policy = "never"`. Read
[docs/architecture.md](docs/architecture.md) before changing these boundaries.

## Common operations

```bash
# Lower-level maintenance: regenerate all role runtimes after changing an overlay
./scripts/sync-all

# Validate source only, without requiring installed runtimes
./scripts/verify --source

# Verify installed state and the live Paseo provider inventory
./install --verify

# Optional sanitized runtime summaries for local comparison
./scripts/export-runtime-snapshots

```

The lower-level scripts are maintenance interfaces used by the public
lifecycle and are not alternate fresh-install commands. See
[docs/operations.md](docs/operations.md) for the single-writer handoff,
candidate acceptance, and maintenance runbooks. The composed evidence and
single final Human runbook are in
[docs/acceptance/core4.md](docs/acceptance/core4.md).

Official Codex configuration precedence is documented by OpenAI in the [Codex config basics](https://learn.chatgpt.com/docs/config-file/config-basic.md). `codex-room` uses a separate `CODEX_HOME` per role; this is a local orchestration layer, not a replacement for the operator's Codex installation.
