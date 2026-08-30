# Profiles and overlays

The word “profile” appears at three different levels:

1. **Paseo custom provider:** `codex-supervisor`, `codex-lead`, `codex-peer`, `codex-review`, or `codex-harness` extends the built-in Codex adapter.
2. **Codex Room overlay:** a focused TOML fragment merged into a generated `CODEX_HOME`.
3. **Native Codex profile:** selected through `codex --profile`; this room does not use that mechanism.

Changing a Paseo provider model affects the model picker and Paseo default. Changing an overlay affects the Codex process default after the next sync. Keep both aligned deliberately.

The Peer overlay owns independent premise, architecture, solution-shape, and
macro review. It has no OCR responsibility.

The Review overlay is the dedicated OCR-assisted profile for a frozen, bounded
candidate when file or rule selection is materially uncertain. A `DEEP`
`EXPLORATORY` Review uses Luna Max and must run `command -v ocr`, then
`ocr delegate preview`, then `ocr delegate rule`. Review verifies the selected
files, selected rules, and findings. Any command failure, empty or malformed
result, invalid selection, or result that cannot be reconciled with the
candidate and contract causes `DEPENDENCY_REQUEST`. There is no manual fallback.

Lead may explicitly create a `FAST` close-out seat with
`codex-review/gpt-5.6-sol` and medium reasoning. When accepted finding IDs, the
correction base, and the delta are clear, close-out does not use OCR by default.
Sol Medium is selectable but not the provider default. Luna Max remains the
default. Both choices stay inside the same Review role and provider.

The sync allowlist is intentionally small. New top-level role-specific keys must be added to `OVERRIDE_KEYS` in `codex-room-sync` and covered by tests.

The Harness overlay is a read-only Better Harness coordinator. It binds one
explicit `~/.codex-runtime/<role>` as evidence with `--codex-home`, then maps
Session Evidence, Project Harness Evidence, and Agent Customize Evidence to
exactly three fresh `codex-peer` Paseo seats. It neither uses Review/OCR nor
changes the selected workspace. Its private plugin lifecycle is documented in
[better-harness-role.md](better-harness-role.md).
