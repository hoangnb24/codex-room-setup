# Desktop build

`paseo-local-update` performs the local macOS flow:

1. Validate the exact owner-fork branch/commit, normalized remotes, tracking,
   clean tracked/index state, lockfile, and lifecycle-hook policy.
2. Fetch the immutable commit directly and allow only an exact-pin no-op or a
   clean fast-forward to it. No pull, merge, rebase, or reset is used.
3. Run `npm ci` and prove `package-lock.json` is unchanged.
4. Build the architecture-specific Desktop directory bundle.
5. Apply an ad-hoc code signature and verify it.
6. Stop the current Desktop and daemon.
7. Backup and replace `/Applications/Paseo.app`.
8. Relink the local CLI, start the daemon and open Desktop.

The operation mutates `/Applications` and should be run interactively by the operator.
