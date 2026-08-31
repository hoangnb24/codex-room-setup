# Paseo fork

The source of truth for fork provenance is [`paseo/source.toml`](../paseo/source.toml). The expected checkout is:

```text
~/projects/supervisors/paseo
```

`scripts/install-paseo-fork` treats that manifest as authority. A fresh install
fetches the exact commit into a sibling staging directory, confirms that the
owner fork's named branch still resolves to that commit, runs `npm ci`, and
publishes the target only after provenance, lockfile, lifecycle-hook, and CLI
checks pass. A failed validation leaves no target checkout.

An existing checkout must be on the expected branch with a clean tracked/index
state. Untracked operator state is preserved. The installer accepts only an
exact-pin no-op or a clean ancestor-to-pin fast-forward; detached, ahead,
divergent, dirty, and custom-topology checkouts are refused. It never performs
an automatic pull, merge, rebase, or reset. The only automatic remote migration
is the recognized legacy layout (`origin = public`, `hoangnb24 = owner fork`),
which becomes `origin = owner fork`, `upstream = public` after eligibility is
proven. The local branch then tracks `origin`.

Paseo's audited `prepare` lifecycle installs lefthook with force. Before
`npm ci`, setup refuses custom hooks and a custom `core.hooksPath`; after the
install it verifies that the lockfile is byte-for-byte unchanged. A conflicting
CLI link is backed up under `~/.codex-room-backups/` before replacement.

`scripts/update-paseo-fork` delegates to the installed `paseo-local-update`.
That updater fetches the immutable commit directly and uses the same no-op or
fast-forward-only policy before dependency install/build. It never silently
follows a newer upstream or fork branch tip. Its macOS build behavior is
documented in [`paseo/notes/desktop-build.md`](../paseo/notes/desktop-build.md).

Access to the fork remote is an operator prerequisite. The installer does not manage SSH keys or GitHub authentication.
