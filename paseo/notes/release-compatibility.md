# Required release behavior

Room setup relies on official Paseo support for derived providers (`extends`),
per-provider commands, replacement model catalogs and default thinking settings,
Codex app-server controls, provider-specific `paseoTools.enabled`, and local
CLI/daemon/Desktop builds. Release v0.8.0 includes these configuration interfaces.

For future upgrades, select a published stable release tag, update the tag and
commit pins together in `source.toml` and `home/.local/bin/paseo-local-update`,
run the release and installer tests, and validate an isolated real build. Do not
select a main-branch development commit or a prerelease tag.
