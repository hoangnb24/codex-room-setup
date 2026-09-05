# Provider profiles

The live template defines exactly three derived Codex providers: Supervisor,
Lead, and Peer. Their `command` launches `codex-room`, which selects an isolated
runtime through `CODEX_HOME`.

`models` is a replacement catalog for each custom profile. `additionalModels` would be additive; this setup does not currently use it.
