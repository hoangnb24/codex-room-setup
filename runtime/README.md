# Runtime

The runtime is generated at `~/.codex-runtime`, not installed from Git.

Expected top-level roles:

```text
~/.codex-runtime/supervisor
~/.codex-runtime/lead
~/.codex-runtime/peer
~/.codex-runtime/review
~/.codex-runtime/harness
```

Use `scripts/export-runtime-snapshots` for sanitized local summaries. Snapshot directories are ignored by default.

The Review runtime supports OCR-assisted inspection of frozen, bounded
candidates. It remains behaviorally read-only and does not inherit MCP servers.

Harness coordinates Better Harness through Paseo and keeps a private,
sync-preserved `plugins/` directory. The other roles retain canonical plugin
symlinks. Like Review, Harness strips inherited Codex MCP tables; Paseo injects
its orchestration tools at the provider boundary.
