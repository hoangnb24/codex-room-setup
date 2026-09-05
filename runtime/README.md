# Runtime

The runtime is generated at `~/.codex-runtime`, not installed from Git.

Expected top-level roles:

```text
~/.codex-runtime/supervisor
~/.codex-runtime/lead
~/.codex-runtime/peer
```

Use `scripts/export-runtime-snapshots` for sanitized local summaries. Snapshot directories are ignored by default.

Additional role directories or private files may remain from an older
installation. The three-role generator does not inspect, mutate, delete,
export, or launch them.
