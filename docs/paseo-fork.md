# Paseo fork

The source of truth for fork provenance is [`paseo/source.toml`](../paseo/source.toml). The expected checkout is:

```text
~/projects/supervisors/paseo
```

`scripts/install-paseo-fork` clones or verifies the remotes. It does not pull or build an existing checkout. `scripts/update-paseo-fork` delegates to the installed `paseo-local-update`, whose macOS build and replacement behavior is documented in [`paseo/notes/desktop-build.md`](../paseo/notes/desktop-build.md).

Access to the fork remote is an operator prerequisite. The installer does not manage SSH keys or GitHub authentication.

