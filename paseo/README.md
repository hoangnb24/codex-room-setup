# Paseo fork

This setup targets Hoang's fork of Paseo and installs it at the same path used by the current local scripts.

```text
fork remote: git@github.com:hoangnb24/paseo.git
upstream:    git@github.com:getpaseo/paseo.git
checkout:    ~/projects/supervisors/paseo
branch:      main
baseline:    v0.7.0-beta.1-13-g8511089ea
```

The installed checkout uses `origin` for the fork and `upstream` for the public
repository. The local `main` branch tracks `origin/main`; update commands never
pull implicitly from the configured tracking branch.

See `source.toml` for machine-readable provenance and `notes/` for the behavior
this setup relies on.
