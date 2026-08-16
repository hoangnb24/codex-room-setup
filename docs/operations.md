# Operations

## Change a role

1. Edit `home/.config/codex-room/overlays/<role>.config.toml`.
2. Run `make test`.
3. Run `scripts/install --apply` to install the changed source.
4. Run `scripts/sync-all <role>`.
5. Run `scripts/verify`.

## Run the workflow pilot

The shared protocol and role overlays implement a setup-only workflow pilot.
Read `docs/workflow-pilot.md`, install and sync changed sources, then collect a
sanitized aggregate report with:

```bash
./scripts/workflow-pilot-report --format json /path/to/rollout.jsonl
```

Do not commit raw rollout JSONL. It can contain prompts, source, and tool data.
The pilot does not enforce ownership or ordering atomically; observed misses are
evidence for deciding whether a Paseo runtime mechanism is warranted.

## Change the Paseo provider catalog

1. Edit `home/.paseo/config.json.template`.
2. Run `make test`.
3. Install with backup using `scripts/install --apply`.
4. Restart Paseo explicitly.
5. Run `scripts/verify --live`.

The installer does not restart the daemon because an active restart can interrupt running agents.

## Historical migration helpers

`codex-room-hard-cut`, `codex-review-apply`, and the two candidate JSON files preserve the current installation's guarded migration procedure. They contain expected SHA-256 values and therefore fail closed after relevant config drift. They are reference/recovery tools, not routine install or update commands.

## Update the local fork

Run `paseo-local-update` only when no important agent turn or Desktop operation is active. It pulls with rebase, builds, replaces the app and restarts the daemon.
