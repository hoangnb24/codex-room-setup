# Operations

## Change a role

1. Edit `home/.config/codex-room/overlays/<role>.config.toml`.
2. Run `make test`.
3. Run `scripts/install --apply` to install the changed source.
4. Run `scripts/sync-all <role>`.
5. Run `scripts/verify`.

## Run the workflow pilot

Role overlays implement the setup-only workflow pilot. A workspace can add
local rules in `docs/WORKSPACE_PROTOCOL.md`. Read `docs/workflow-pilot.md`,
install and sync changed sources, then collect a sanitized aggregate report
with:

```bash
./scripts/workflow-pilot-report --format json /path/to/rollout.jsonl
```

Do not commit raw rollout JSONL. It can contain prompts, source, and tool data.
The pilot does not enforce ownership or ordering atomically; observed misses are
evidence for deciding whether a Paseo runtime mechanism is warranted.

## Run the guarded multiple-writer pilot

Use this runbook only after reading the admission contract in
`docs/workflow-pilot.md`. Commands below use `BASE`, `FRONTIER_A`, and
`FRONTIER_B` as placeholders; keep the resolved commit and paths in the Lead
record rather than relying on mutable branch names.

1. Resolve the current accepted tip and freeze the shared contract text and its
   digest. Identify every ready writable frontier. If at least two are ready,
   record a positive `PARALLEL_CHECK v1`; do not silently choose serial work.

   ```bash
   git rev-parse HEAD
   shasum -a 256 /path/to/frozen-contract
   ```

2. Check both proposed physical path scopes and logical responsibilities. Search
   for shared APIs, schemas, composition roots, generated files, migrations,
   lockfiles, and fixtures. If any admission fact is unknown, scopes overlap, or
   the work shares an integration surface, record `SERIAL`. Never run more than
   two writers concurrently in one repository.

3. As Lead, invoke Paseo's `create_workspace` MCP tool twice so Paseo registers
   and manages both isolated worktrees. For each request use
   `isolation: "worktree"`, `mode: "branch-off"`, the source checkout as
   `path`, the frontier branch as `branchName`, and the exact commit `BASE` as
   `baseBranch`; give each request a distinct `worktreeSlug`. Record the
   returned `workspaceId` and `cwd`, and use that workspace ID when placing its
   writer. Before dispatch, independently confirm both returned worktree paths
   report the exact `BASE` commit.

   ```bash
   git -C /absolute/path/from/frontier-a-workspace rev-parse HEAD
   git -C /absolute/path/from/frontier-b-workspace rev-parse HEAD
   ```

4. Dispatch at most two `FRONTIER_BRIEF v1` messages. Put the exact base,
   physical write scope, logical responsibility, frozen contract digest,
   forbidden shared surfaces, acceptance commands, and immutable commit handoff
   in each brief. Writers must not inspect or depend on the sibling candidate.

5. On each handoff, verify the returned commit without changing it. Confirm its
   parent is `BASE`, inspect its changed paths against the granted scope, and
   run the frontier's focused proof in that worktree.

   ```bash
   git -C /absolute/path/frontier-a rev-parse "${CANDIDATE_A}^"
   git -C /absolute/path/frontier-a diff-tree --no-commit-id --name-only -r "$CANDIDATE_A"
   git -C /absolute/path/frontier-a show --stat --oneline "$CANDIDATE_A"
   ```

6. Integrate serially in the Lead worktree. Cherry-pick the first immutable
   commit onto the current accepted tip, run its focused proof, then repeat for
   the second commit on the new accepted tip. Do not ask a writer to amend a
   handed-off commit to resolve an integration failure.

   ```bash
   git cherry-pick "$CANDIDATE_A"
   # Run frontier A focused proof.
   git cherry-pick "$CANDIDATE_B"
   # Run frontier A and B focused proofs, then the composed proof.
   ```

7. Accept only the resulting integration commits after focused and composed
   proof pass. Record elapsed time to acceptance, correction batches, conflicts,
   reopens, stale candidates, and proof failures. Compare those values with a
   comparable serial run; claim success only for velocity gain without more
   correction or weaker outcome evidence.

8. Keep enforcement in prompts unless at least two comparable misses identify
   the same missing atomic Paseo mechanism. Worktree isolation alone is not
   logical independence, and the current pilot has no atomic ownership lease or
   concurrency gate.

## Change the Paseo provider catalog

1. Edit `home/.paseo/config.json.template`.
2. Run `make test`.
3. Install with backup using `scripts/install --apply`.
4. Restart Paseo explicitly.
5. Run `scripts/verify --live`.

The installer does not restart the daemon because an active restart can interrupt running agents.

## Historical migration helpers

`codex-room-hard-cut`, `codex-review-apply`, and the two candidate JSON files preserve the current installation's guarded migration procedure. They contain expected SHA-256 values and therefore fail closed after relevant config drift. They are reference/recovery tools, not routine install or update commands.

## Update the local fork

Run `paseo-local-update` only when no important agent turn or Desktop operation
is active. It verifies the audited owner-fork branch ref, requires normalized
remotes/tracking plus a clean tracked/index state, and permits only an exact-pin
no-op or clean fast-forward to that immutable commit. It refuses detached,
dirty, ahead/divergent, custom-topology, custom-hook, and lock-integrity states;
then it runs `npm ci`, builds, replaces the app, and restarts the daemon. It
never pulls, rebases, resets, or merges automatically.
