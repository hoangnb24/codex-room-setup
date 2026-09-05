# Profiles and overlays

The word “profile” appears at three different levels:

1. **Paseo custom provider:** `codex-supervisor`, `codex-lead`, or `codex-peer` extends the built-in Codex adapter.
2. **Codex Room overlay:** a focused TOML fragment merged into a generated `CODEX_HOME`.
3. **Native Codex profile:** selected through `codex --profile`; this room does not use that mechanism.

Changing a Paseo provider model affects the model picker and Paseo default. Changing an overlay affects the Codex process default after the next sync. Keep both aligned deliberately.

The Peer overlay owns one bounded implementation, investigation, architecture,
or read-only candidate review outcome. Peer has no Paseo MCP injection and its
role instructions forbid coordinating other seats.

The sync allowlist is intentionally small. New top-level role-specific keys must be added to `OVERRIDE_KEYS` in `codex-room-sync` and covered by tests.

Retired role entrypoints are backed up and removed during install. Existing
runtime directories and private operator files remain untouched.
