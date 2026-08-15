# Troubleshooting

## A role still uses an old model

Cause: the overlay changed but the generated runtime was not refreshed.

```bash
scripts/sync-all <role>
grep -E '^(model|model_reasoning_effort) =' "$HOME/.codex-runtime/<role>/config.toml"
```

## `codex-room-sync` cannot find a shared resource

The operator's `~/.codex` is incomplete for this setup. Check the exact missing path reported by the script. This repository will not create or overwrite it.

## Paseo does not show custom providers

1. Validate `~/.paseo/config.json` with `jq`.
2. Confirm its custom commands point to `~/.local/bin/codex-room`.
3. Confirm `~/.local/bin` is on the daemon's PATH.
4. Restart Paseo when no agent is running.
5. Run `scripts/verify --live`.

## Daemon PID and listener disagree

Compare the PID file with the actual listener:

```bash
cat "$HOME/.paseo/paseo.pid"
lsof -nP -iTCP:6767 -sTCP:LISTEN
```

A wrapper PID and child Node PID can differ. Diagnose before deleting PID or state files.

