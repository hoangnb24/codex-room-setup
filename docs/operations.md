# Operations

The public lifecycle is `./install`, `./install --apply`, then an explicit
Paseo daemon start followed by `./install --verify`. The other scripts in this
repository are focused maintenance interfaces used after that installation;
they are not alternate fresh-install workflows.

## Change a role

1. Edit `home/.config/codex-room/overlays/<role>.config.toml`.
2. Run `make test` and `./scripts/verify --source`.
3. Run `./install` to inspect the complete read-only plan.
4. Run `./install --apply` to publish the changed source transactionally.
5. Start Paseo when no agent turn is active, then run `./install --verify`.

The three roles have distinct authority. Human keeps product, cost, external
effect, and irreversible-risk decisions. Supervisor observes and routes Human
intent. Lead owns the project's technical decision and acceptance. Lead may
have one writable Peer at a time; a Peer owns one bounded outcome and returns
an immutable candidate or a concrete premise, dependency, or block signal.

## Run a bounded project handoff

Lead first records the observable outcome, dependencies, write scope, relevant
invariants, acceptance evidence, and the condition that would reopen the
decision. The writer then reports the exact candidate, original base, changed
paths, commands run, and residual risk. Lead inspects that candidate and
explicitly accepts or rejects it. Tests and lifecycle state support the
decision but do not replace it.

When independent architecture or candidate judgment can change the decision,
Lead requests a fresh read-only Peer against an exact candidate or deterministic
snapshot. The reviewer returns only evidence relevant to the bounded question;
there is no extra standing role or dependency to install.

After dispatch, wait for finish, error, attention, or decision events. Do not
repeatedly query a seat while its state is unchanged. Preserve existing private
notebooks, runtime/session state, and operator-owned `.codex` bytes.

## Change the Paseo provider catalog

1. Edit `home/.paseo/config.json.template`.
2. Run `make test` and `./scripts/verify --source`.
3. Inspect `./install` and apply with `./install --apply`.
4. Restart Paseo explicitly.
5. Run `./install --verify`.

The installer does not restart the daemon because an active restart can
interrupt running agents. The source contract keeps exactly three room
providers and injects Paseo MCP into Supervisor and Lead only. A live provider
inventory still needs an operator check with a running daemon.

## Update the local fork

Run `paseo-local-update` only when no important agent turn or Desktop operation
is active. It verifies the audited owner-fork branch ref, requires normalized
remotes/tracking plus a clean tracked/index state, and permits only an exact-pin
no-op or clean fast-forward to that immutable commit. It refuses detached,
dirty, ahead/divergent, custom-topology, custom-hook, and lock-integrity
states; then it runs `npm ci`, builds, replaces the app, and restarts the
daemon. It never pulls, rebases, resets, or merges automatically.
