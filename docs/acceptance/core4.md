# Minimum core acceptance record

This record is the release handoff for the composed minimum core. It covers
the public installation lifecycle and the evidence that remains for the one
consolidated Human review of CORE-2, CORE-3, CORE-4, and the Epic.

## Public contract

From a clean clone, an operator prepares an existing authenticated Codex home
and runs:

```bash
./install
./install --apply
paseo daemon start
./install --verify
```

The first command is read-only. Apply stages the pinned Paseo checkout, the
managed HOME files, and the Supervisor, Lead, and Peer runtimes as one
transaction. Verification is read-only and includes the live provider
inventory, so it requires a reachable Paseo daemon. `scripts/verify` and the
other lower-level scripts are maintenance interfaces for an already installed
room.

The room owns exactly three derived providers: `codex-supervisor`,
`codex-lead`, and `codex-peer`. Paseo MCP is injected into Supervisor and Lead;
Peer has no orchestration tools. Human retains product, cost, external-effect,
and irreversible-risk decisions. Supervisor routes intent, Lead owns technical
acceptance, and Peer owns one bounded outcome at a time.

Repeated apply regenerates managed outputs while preserving operator
`~/.codex` bytes, existing role sessions and databases, and private legacy
runtime directories. Only recognized, unchanged obsolete artifacts are retired;
customized or redirecting artifacts are preserved with a warning. Transaction
backups are owner-only. The installer does not authenticate Codex, start the
daemon, manage operator credentials, or install Desktop GUI state.

## Evidence matrix

| Boundary | Evidence | Status at handoff |
| --- | --- | --- |
| CORE-2 operating contract | [CORE-2](https://github.com/hoangnb24/codex-room-setup/issues/4) | Technically accepted; Human check deferred |
| CORE-3 public transaction | [CORE-3 handoff](https://github.com/hoangnb24/codex-room-setup/issues/5#issuecomment-5550376777) | Technically accepted; independent F1–F6 closeout passed |
| Role/provider source contract | `./scripts/verify --source` and unit tests | Passed in the writer workspace, clean clone, and container source check |
| Public installer composition | `make test` and `make test-container` | 49 tests and complete container acceptance passed |
| Live Paseo roles and tool inventory | `./install --verify` plus three smoke sessions | Pending the single Human review |

The final candidate is identified by the immutable branch/PR and issue proof
recorded by Lead. This file intentionally contains no self-referential commit
hash.

## Writer validation

The following checks were run in the candidate workspace with
`CODEX_ROOM_TOML_PYTHON=/opt/homebrew/bin/python3.12` set only in the shell:

```text
49 unit/interface tests: OK
python3 -m py_compile scripts/install-room: OK
all tracked shell entrypoints and container scripts: bash -n OK
./scripts/verify --source: VERIFY_OK
git diff --check: OK
```

The complete unit output is retained at
`/tmp/codex-room-core4-tests.log`; source verification output is at
`/tmp/codex-room-core4-source.log`. Lead's independent proof follows.

## Final clean-clone proof

On 2026-09-05, Lead tested implementation commit
`f9a56017e0622158b6791355af1dc4dc181ee7df` in a separate clean clone.
At the initial handoff, the only subsequent change was this evidence record. Independent CORE-4
review found no functional blocker; CORE-3's six transaction findings had
already passed their independent closeout.

```text
make test: 49 tests passed (114.647 seconds)
./scripts/verify --source: VERIFY_OK
Python compilation, shell syntax, git diff --check: passed
PUBLIC_PLAN_READ_ONLY_OK
PUBLIC_INSTALL_PASS fresh
PUBLIC_INSTALL_PASS repeated
PUBLIC_VERIFY_FIXTURE_OK live_inventory_is_fake
ROLE_INVENTORY ["codex-lead","codex-peer","codex-supervisor"]
MCP_RECIPIENTS ["codex-supervisor","codex-lead"]
CONTAINER_ACCEPTANCE_OK node=v22.16.0 python=3.11.2 paseo=8511089eaeb06cddd049b629562926822020de5c
```

The first `make test-container` attempt passed fresh installation but failed
with npm `ECONNRESET` during repeated-install preflight. An unchanged rerun
completed successfully. Both logs are retained; the failed attempt is not
counted as a full pass. Source verification also passed through a separate
read-only invocation inside the first container.

The composed test checks plan bytes/modes/links, fresh and repeated install,
operator and legacy/active JSONL/SQLite preservation, customized obsolete
files, final backup directory permissions, and installed/provider verification.
Regular managed/CLI backup permissions and intentional rollback failures are
covered by the transaction regressions. A supplementary read-only check during
the successful container's repeated-install phase found all 136,175 completed
regular backup files at mode `0600`; final directory modes are checked after
apply. This supplementary check is separate from the committed container test.

The coordination session retains `unit.log`, `source.log`, `container.log`,
`container-retry.log`, `container-source.log`, the backup-file permission result,
full generated instructions, and changed-path manifests. The final immutable
handoff and review status are recorded on
[CORE-4](https://github.com/hoangnb24/codex-room-setup/issues/6).

## Installation feedback: optional hooks

The operator's first installation attempt exposed an overly strict prerequisite:
`hooks.json` was required even when no hooks were configured. The installer and
runtime generator now skip an absent hooks file, share an existing one, and
reject an explicitly dangling hooks symlink. They do not create operator files.
Other required resources retain their previous checks.

Three focused regressions passed, covering public plan/apply/repeat and direct
generation without hooks, hooks added later, dangling hooks, and required-resource
or catalog failures. The read-only plan also passed against the reporting
operator's existing home without creating `hooks.json`. The full-suite result
and correction commit are recorded on PR #8. The container evidence above
belongs to the original implementation; it was not rerun for this correction.

## Installation feedback: native-agent v2 table

The operator deliberately enabled native agents in the personal Codex home;
the Room contract still requires all three role runtimes to disable them.
The generator previously added a v2 boolean alongside the operator's v2 table,
producing invalid TOML. It now preserves the table and sets its `enabled` field
to `false`, or emits boolean `false` for scalar configurations. Verification
recognizes both disabled forms and exposes parser errors instead of hiding them
behind the generic policy failure.

Focused tests parse all three generated runtimes through repeated public apply,
prove the operator config remains unchanged, and check verification of disabled,
enabled and malformed v2 settings. Generation from the reporting operator's
actual base in a disposable stage also produced three valid disabled configs
without changing the base. Correction hashes and full-suite results are tracked
on PR #8; the original container evidence was not rerun for this correction.

## Consolidated Human runbook

Before merge, select the candidate branch explicitly: README's default clone
still selects `main` until this PR is merged.

```bash
git clone --branch core-minimum https://github.com/hoangnb24/codex-room-setup.git
cd codex-room-setup
git rev-parse HEAD   # compare with the final commit recorded on the PR/CORE-4
```

Use this clean clone at the recorded candidate, a disposable operator home, and an
authenticated Codex/Paseo environment prepared by the operator. Follow only
the README for installation, then record commands and observations on
[CORE-4](https://github.com/hoangnb24/codex-room-setup/issues/6):

1. Run the default plan and confirm the home tree is unchanged. Apply twice,
   start Paseo, and run live verification.
2. Inspect the live provider inventory: exactly Supervisor, Lead, and Peer;
   confirm MCP is present only for Supervisor and Lead. Launch one real smoke
   session per role and confirm identity and instructions.
3. Read all generated role instructions. Observe Lead delegate one bounded
   writable task and explicitly accept or reject the returned candidate. Inspect
   the live Peer tool inventory and observe a fresh read-only Peer review.
4. Repeat the install and upgrade from a five-role fixture. Confirm active
   sessions, SQLite state, operator files, and customized obsolete files remain
   unchanged. Inspect owner-only replacement backups.
5. Trigger a controlled preflight or verification failure and confirm the
   previous managed installation remains byte-for-byte unchanged.
6. Post the observed commands and results on CORE-4, set Project `Human
   verification` to `Verified`, and close the child issue only after the Epic
   review is complete.

Live role identity, actual tool inventory, bounded write acceptance, and the
final Project field remain explicitly pending. The fake provider inventory
exercises the verification parser. A separate real daemon smoke exercises
startup and provider RPC, without proving Codex authentication, MCP calls, or
real sessions.

## Paseo build correction

The operator's successful apply exposed a missing runtime build: the CLI
launcher existed, but `packages/cli/dist/index.js` did not. Dependency
installation alone did not produce the server and CLI bundles. Both preflight
and publication now run the audited fork's `build:server:clean`, require the
CLI bundle and daemon runner, and execute CLI help before reporting readiness.
Installed verification also checks these outputs and CLI execution.

A disposable copy of the operator's audited checkout passed the clean build
and a real daemon/provider RPC smoke test on Node 24.9.0. The operator checkout
and Codex configuration were not modified by that test. Container acceptance
now includes the same real daemon smoke after repeated public installation,
using a temporary home and loopback port with relay and web UI disabled.
This smoke tests executable runtime startup; authenticated role sessions and
actual MCP tool inventory remain part of the Human review.

Validation for this correction: 54 tests passed (138.85 seconds), source
verification passed, and independent code review passed. Full container
acceptance passed with Node 22.16.0/Python 3.11.2, including fresh/repeated apply,
preservation checks, and `PASEO_DAEMON_SMOKE_OK real_cli_and_provider_rpc`.
The initial uncached container run was stopped during a slow Git download;
the passing run mounted the same audited Git objects read-only through
`GIT_ALTERNATE_OBJECT_DIRECTORIES`. Remote pin checks and all npm/build steps
still ran. Its log is `/tmp/paseo-build-container-cached.log`; macOS build and
smoke logs are under `/tmp/paseo-build-acceptance.NGT4UM/`.

## Boundaries and deferred work

This release does not add a collector, evaluator, benchmark CLI, scoring rules,
workflow state, leases, gates, or another compatibility layer. Evaluation is a
separate future Epic with its own schema, collector, scoring, and report
interface. Git history retains removed experimental design material.

The final container proof does not cover Paseo Desktop, GUI behavior, macOS
signing or TCC, application restart behavior, or power-loss durability. Those
observations belong to the operator's macOS runbook and future release work.
