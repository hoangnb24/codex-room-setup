# Desktop build

`paseo-local-update` performs the local macOS flow:

1. Pull the fork with rebase.
2. Install npm dependencies.
3. Build the architecture-specific Desktop directory bundle.
4. Apply an ad-hoc code signature and verify it.
5. Stop the current Desktop and daemon.
6. Backup and replace `/Applications/Paseo.app`.
7. Relink the local CLI, start the daemon and open Desktop.

The operation mutates `/Applications` and should be run interactively by the operator.

