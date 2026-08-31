# Better Harness role

Harness is a fifth Codex Room role for coordinating one read-only Better
Harness report. It uses the common `codex-room harness` launcher and
`codex-room-sync` generator. Native Codex agents remain disabled; Paseo injects
its MCP tools so Harness can dispatch exactly three fresh `codex-peer` evidence
seats.

## Private plugin lifecycle

`~/.codex-runtime/harness/plugins` is a private directory. Sync creates it when
absent and preserves all contents on repeated runs. During migration, sync may
unlink only a symlink resolving to `~/.codex/plugins`; an unexpected symlink,
file, or other non-directory path stops sync without replacing that path.

After Codex CLI installs Better Harness, sync also preserves only its exact
`marketplaces.better-harness` and
`plugins."better-harness@better-harness"` registration tables from the private
Harness config. It does not retain other runtime config edits and does not
synthesize either registration before installation.

Sync is deliberately offline and never installs Better Harness. The normal
fresh-machine path is `scripts/bootstrap --apply`, which performs the following
audited plugin installation after creating the Harness profile. For targeted
maintenance, the equivalent commands are:

```bash
BETTER_HARNESS_REF=ef5253ca2e201d46a7071c3fc9c1de7237d3f86c
CODEX_HOME="$HOME/.codex-runtime/harness" \
  codex plugin marketplace add https://github.com/hoangnb24/better-harness.git \
  --ref "$BETTER_HARNESS_REF"
CODEX_HOME="$HOME/.codex-runtime/harness" \
  codex plugin add better-harness@better-harness
CODEX_HOME="$HOME/.codex-runtime/harness" \
  codex plugin list --marketplace better-harness --json
CODEX_HOME="$HOME/.codex-runtime/harness" \
  codex plugin marketplace list --json
```

This ref contains the fork's provider-home provenance and trusted lifecycle
attribution changes on top of upstream v0.6.5. The machine-readable source of
truth is [`../better-harness/source.toml`](../better-harness/source.toml).
Replace `BETTER_HARNESS_REF` only with a newly audited immutable commit from the
fork. These commands are operator actions; `scripts/install`,
`scripts/sync-all`, and `codex-room-sync` never run them, infer registration
from the plugin cache, or write to canonical `~/.codex`.

`scripts/bootstrap --apply` first repeats the add/install in a disposable
`CODEX_HOME`, obtains the marketplace checkout root from
`codex plugin marketplace list --json`, and requires that root's Git `HEAD` to
equal the audited commit. This happens before OCR, tracked config, runtime, live
Paseo, or plugin state changes. Before live Better Harness replacement,
bootstrap snapshots the Harness runtime; any failed remove, add, install, root
verification, sync, or final verification restores the prior registration and
private plugin/marketplace state. Errors are not suppressed.

## Evidence boundary

Start Harness through the `codex-harness` Paseo provider and invoke
`$better-harness:better-harness` with:

- one absolute target workspace;
- one explicit evidence role resolved with
  `codex-room --resolve-evidence-home <role>`;
- `--platform codex` and `--codex-home` forwarded to every evidence command;
- inline/no-files output by default;
- no Memories or user-home scope unless separately authorized.

One report covers one role home. Do not combine Supervisor, Lead, Peer, Review,
or Harness sessions into a common population: their mandates and evidence are
not interchangeable. Raw rollouts remain private in the selected role home and
must not be copied, committed, or passed to evidence Peers.

The resolver accepts only the five known roles, requires a real direct child of
the canonical runtime root, and rejects role-directory symlinks. It performs no
sync. Pass its returned absolute path unchanged as `--codex-home`; do not build
that path from `$HOME` inside Harness instructions.

Harness maps the Better Harness lanes one-to-one to fresh read-only Peers:

1. Session Evidence;
2. Project Harness Evidence;
3. Agent Customize Evidence.

The Peers receive only their contract-authorized envelopes and exact reference
paths from the plugin installed in the Harness home. They do not use OCR,
delegate, inspect raw sessions, or edit the target. Harness performs the final
reconciliation and reporting itself.
