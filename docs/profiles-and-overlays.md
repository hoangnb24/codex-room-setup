# Profiles and overlays

The word “profile” appears at three different levels:

1. **Paseo custom provider:** `codex-supervisor`, `codex-lead`, `codex-peer`, or `codex-review` extends the built-in Codex adapter.
2. **Codex Room overlay:** a focused TOML fragment merged into a generated `CODEX_HOME`.
3. **Native Codex profile:** selected through `codex --profile`; this room does not use that mechanism.

Changing a Paseo provider model affects the model picker and Paseo default. Changing an overlay affects the Codex process default after the next sync. Keep both aligned deliberately.

The sync allowlist is intentionally small. New top-level role-specific keys must be added to `OVERRIDE_KEYS` in `codex-room-sync` and covered by tests.

