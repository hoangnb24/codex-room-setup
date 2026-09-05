from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
import re


ROOT = Path(__file__).resolve().parents[1]
HOME_MIRROR = ROOT / "home"
ROOM = HOME_MIRROR / ".config" / "codex-room"
PASEO_TEMPLATE = HOME_MIRROR / ".paseo" / "config.json.template"
SYNC = HOME_MIRROR / ".local" / "bin" / "codex-room-sync"
LAUNCHER = HOME_MIRROR / ".local" / "bin" / "codex-room"
SYNC_ALL = ROOT / "scripts" / "sync-all"


class SetupShapeTests(unittest.TestCase):
    def make_paseo_remote(self, root: Path) -> tuple[Path, str, str]:
        work = root / "paseo-work"
        remote = root / "paseo.git"
        subprocess.run(["git", "init", "-q", "-b", "main", str(work)], check=True)
        (work / "packages" / "cli" / "bin").mkdir(parents=True)
        (work / "packages" / "cli" / "bin" / "paseo").write_text("#!/usr/bin/env node\n")
        (work / "package.json").write_text('{"scripts":{"prepare":"true"}}\n')
        (work / "package-lock.json").write_text('{"lockfileVersion":3}\n')
        subprocess.run(["git", "-C", str(work), "add", "."], check=True)
        subprocess.run(["git", "-C", str(work), "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "one"], check=True)
        first = subprocess.run(["git", "-C", str(work), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
        (work / "version.txt").write_text("two\n")
        subprocess.run(["git", "-C", str(work), "add", "."], check=True)
        subprocess.run(["git", "-C", str(work), "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "two"], check=True)
        second = subprocess.run(["git", "-C", str(work), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
        subprocess.run(["git", "clone", "-q", "--bare", str(work), str(remote)], check=True)
        return remote, first, second

    def fake_npm(self, root: Path, *, change_lock: bool = False) -> Path:
        root.mkdir(parents=True, exist_ok=True)
        npm = root / "npm"
        npm.write_text(
            "#!/bin/sh\n"
            "printf '%s\\n' \"$*\" >> \"${NPM_LOG:?}\"\n"
            + ("printf changed >> package-lock.json\n" if change_lock else "")
            + "mkdir -p .git/hooks\nprintf '# lefthook managed\\n' > .git/hooks/pre-commit\n"
        )
        npm.chmod(0o755)
        return npm

    def paseo_env(self, home: Path, remote: Path, target: Path, commit: str, npm: Path) -> dict[str, str]:
        env = os.environ.copy()
        env.update({
            "HOME": str(home), "PASEO_REPO_DIR": str(target),
            "PASEO_FORK_URL": str(remote), "PASEO_UPSTREAM_URL": str(remote) + "-upstream",
            "PASEO_BRANCH": "main", "PASEO_VERIFIED_COMMIT": commit,
            "PASEO_NPM_BIN": str(npm), "NPM_LOG": str(home.parent / "npm.log"),
        })
        return env

    def executable(self, path: Path, text: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        path.chmod(0o755)
        return path

    def test_repository_does_not_own_codex_home(self) -> None:
        self.assertFalse((HOME_MIRROR / ".codex").exists())

    def test_paseo_template_is_valid_and_has_expected_roles(self) -> None:
        config = json.loads(PASEO_TEMPLATE.read_text().replace("@@HOME@@", "/tmp/operator"))
        providers = config["agents"]["providers"]
        room_roles = sorted(name for name in providers if name.startswith("codex-"))
        self.assertEqual(
            room_roles,
            ["codex-lead", "codex-peer", "codex-supervisor"],
        )
        self.assertEqual(
            config["daemon"]["mcp"]["injectIntoProviders"],
            ["codex-supervisor", "codex-lead"],
        )
        self.assertNotIn("codex-peer", config["daemon"]["mcp"]["injectIntoProviders"])
        self.assertIn("without Paseo orchestration tools", providers["codex-peer"]["description"])
        self.assertIn(
            "Do not spawn, manage, or coordinate other agents",
            (ROOM / "overlays/peer.config.toml").read_text(),
        )

    def test_role_defaults_are_aligned(self) -> None:
        config = json.loads(PASEO_TEMPLATE.read_text().replace("@@HOME@@", "/tmp/operator"))
        expected = {
            "supervisor": ("gpt-5.6-sol", "medium"),
            "lead": ("gpt-5.6-sol", "medium"),
            "peer": ("gpt-5.6-sol", "medium"),
        }
        for role, (model, effort) in expected.items():
            overlay_text = (ROOM / "overlays" / f"{role}.config.toml").read_text()
            overlay = dict(
                re.findall(
                    r'^(model|model_reasoning_effort)\s*=\s*"([^"]+)"',
                    overlay_text,
                    flags=re.MULTILINE,
                )
            )
            profile_models = config["agents"]["providers"][f"codex-{role}"]["models"]
            default = next(item for item in profile_models if item.get("isDefault"))
            self.assertEqual(overlay["model"], model)
            self.assertEqual(overlay["model_reasoning_effort"], effort)
            self.assertEqual(default["id"], model)
            thinking = next(item for item in default["thinkingOptions"] if item.get("isDefault"))
            self.assertEqual(thinking["id"], effort)

    def test_no_private_state_or_machine_home_is_tracked(self) -> None:
        forbidden_names = {
            "auth.json",
            "daemon-keypair.json",
            "push-tokens.json",
            "server-id",
            "cli-client-id",
        }
        for path in HOME_MIRROR.rglob("*"):
            self.assertNotIn(path.name, forbidden_names)
            if path.is_file():
                self.assertNotIn("/Users/tubakhuym", path.read_text(errors="ignore"))

    def test_installer_renders_home_without_touching_codex_home(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fake_home = Path(temporary)
            env = os.environ.copy()
            env["HOME"] = str(fake_home)
            subprocess.run(
                [str(ROOT / "scripts" / "install"), "--apply"],
                check=True,
                env=env,
                capture_output=True,
                text=True,
            )
            paseo_config = fake_home / ".paseo" / "config.json"
            self.assertTrue(paseo_config.is_file())
            self.assertNotIn("@@HOME@@", paseo_config.read_text())
            self.assertIn(str(fake_home / ".local" / "bin" / "codex-room"), paseo_config.read_text())
            protocol = fake_home / ".config" / "codex-room" / "workflow" / "WORKSPACE_PROTOCOL.md"
            self.assertTrue(protocol.is_file())
            self.assertIn("Lead keeps at most one active", protocol.read_text())
            self.assertFalse((fake_home / ".config/codex-room/workflow/ANTI_PATTERNS.md").exists())
            self.assertFalse((fake_home / ".config/codex-room/workflow/SUPERVISOR_NOTEBOOK.md").exists())
            notebook = fake_home / ".config" / "codex-room" / "workflow" / "SUPERVISOR_NOTEBOOK.md"
            notebook.write_text("# Runtime learning\n")
            anti_patterns = fake_home / ".config" / "codex-room" / "workflow" / "ANTI_PATTERNS.md"
            anti_patterns.write_bytes(b"private workflow notes\x00")
            second_install = subprocess.run(
                [str(ROOT / "scripts" / "install"), "--apply"],
                check=True,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(notebook.read_text(), "# Runtime learning\n")
            self.assertEqual(anti_patterns.read_bytes(), b"private workflow notes\x00")
            self.assertNotIn("SUPERVISOR_NOTEBOOK", second_install.stdout)
            self.assertEqual(
                sorted(path.name for path in (fake_home / ".config/codex-room/overlays").glob("*.config.toml")),
                ["lead.config.toml", "peer.config.toml", "supervisor.config.toml"],
            )
            self.assertFalse((fake_home / ".codex").exists())
            self.assertFalse((fake_home / ".codex-runtime").exists())
            paseo_link = fake_home / ".local" / "bin" / "paseo"
            paseo_link.symlink_to(
                fake_home / "projects" / "supervisors" / "paseo" / "packages" / "cli" / "bin" / "paseo"
            )
            subprocess.run(
                [str(ROOT / "scripts" / "uninstall"), "--apply"],
                check=True,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertFalse((fake_home / ".config/codex-room/overlays/lead.config.toml").exists())

    def test_upgrade_retires_legacy_entrypoints_without_touching_runtime_or_codex_data(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fake_home = Path(temporary)
            codex_home = fake_home / ".codex"
            runtime_root = fake_home / ".codex-runtime"
            codex_home.mkdir()
            (codex_home / "auth.json").write_bytes(b"operator-auth\x00data")
            (codex_home / "private").mkdir()
            (codex_home / "private/state").write_text("operator state\n")
            for role in ("review", "harness"):
                role_home = runtime_root / role
                role_home.mkdir(parents=True)
                (role_home / "config.toml").write_text(f"legacy {role}\n")
                (role_home / "private.sqlite").write_bytes(b"sqlite\x00private")

            obsolete = [
                ".config/codex-room/overlays/review.config.toml",
                ".config/codex-room/overlays/harness.config.toml",
                ".config/codex-room/paseo.phase2-coexist.candidate.json",
                ".config/codex-room/paseo.phase2-hard-cut.candidate.json",
                ".local/bin/codex-room-hard-cut",
                ".local/bin/codex-review-apply",
            ]
            for relative in obsolete:
                path = fake_home / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("legacy managed artifact\n")

            def snapshot(root: Path) -> list[tuple[str, str, bytes | str, int]]:
                result = []
                for path in sorted(root.rglob("*")):
                    relative = str(path.relative_to(root))
                    mode = path.lstat().st_mode & 0o777
                    if path.is_symlink():
                        result.append((relative, "link", os.readlink(path), mode))
                    elif path.is_file():
                        result.append((relative, "file", path.read_bytes(), mode))
                    else:
                        result.append((relative, "dir", b"", mode))
                return result

            codex_before = snapshot(codex_home)
            legacy_before = snapshot(runtime_root)
            env = {**os.environ, "HOME": str(fake_home)}
            for _ in range(2):
                subprocess.run(
                    [str(ROOT / "scripts/install"), "--apply"],
                    check=True, env=env, capture_output=True, text=True,
                )

            self.assertEqual(snapshot(codex_home), codex_before)
            self.assertEqual(snapshot(runtime_root), legacy_before)
            self.assertTrue(all(not (fake_home / relative).exists() for relative in obsolete))

    def test_paseo_fresh_install_is_exact_and_atomic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); home = root / "home"; target = root / "installed"
            remote, first, second = self.make_paseo_remote(root)
            npm = self.fake_npm(root)
            env = self.paseo_env(home, remote, target, second, npm)
            subprocess.run([str(ROOT / "scripts" / "install-paseo-fork")], check=True, env=env, capture_output=True, text=True)
            self.assertEqual(subprocess.run(["git", "-C", str(target), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip(), second)
            link = home / ".local" / "bin" / "paseo"
            self.assertTrue(link.is_symlink())
            self.assertEqual(os.readlink(link), str(target / "packages/cli/bin/paseo"))
            self.assertEqual((root / "npm.log").read_text().splitlines(), ["ci"])

            wrong_target = root / "wrong"
            failed = subprocess.run([str(ROOT / "scripts" / "install-paseo-fork")], env=self.paseo_env(home, remote, wrong_target, first, npm), capture_output=True, text=True)
            self.assertNotEqual(failed.returncode, 0)
            self.assertFalse(wrong_target.exists())

    def test_paseo_preflight_validates_existing_target_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); home = root / "home"
            remote, first, second = self.make_paseo_remote(root)
            npm = self.fake_npm(root)

            def clone(name: str, commit: str = first) -> tuple[Path, dict[str, str]]:
                target = root / name
                subprocess.run(["git", "clone", "-q", str(remote), str(target)], check=True)
                subprocess.run(["git", "-C", str(target), "checkout", "-q", "-B", "main", commit], check=True)
                subprocess.run(["git", "-C", str(target), "remote", "add", "upstream", str(remote) + "-upstream"], check=True)
                subprocess.run(["git", "-C", str(target), "config", "branch.main.remote", "origin"], check=True)
                return target, self.paseo_env(home, remote, target, second, npm)

            def snapshot(target: Path):
                custom_hook = target / ".git/hooks/pre-push"
                return (
                    subprocess.run(["git", "-C", str(target), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout,
                    subprocess.run(["git", "-C", str(target), "branch", "--show-current"], check=True, capture_output=True, text=True).stdout,
                    subprocess.run(["git", "-C", str(target), "remote", "-v"], check=True, capture_output=True, text=True).stdout,
                    (target / ".git/config").read_bytes(),
                    (target / "package.json").read_bytes(),
                    subprocess.run(["git", "-C", str(target), "status", "--porcelain"], check=True, capture_output=True, text=True).stdout,
                    custom_hook.read_bytes() if custom_hook.exists() else b"",
                )

            fresh = root / "not-created"
            subprocess.run(
                [str(ROOT / "scripts/install-paseo-fork"), "--preflight"],
                check=True, env=self.paseo_env(home, remote, fresh, second, npm),
                capture_output=True, text=True,
            )
            self.assertFalse(fresh.exists())

            ancestor, ancestor_env = clone("ancestor")
            ancestor_before = snapshot(ancestor)
            subprocess.run([str(ROOT / "scripts/install-paseo-fork"), "--preflight"], check=True, env=ancestor_env, capture_output=True, text=True)
            self.assertEqual(snapshot(ancestor), ancestor_before)

            cases = [
                ("dirty", lambda target: (target / "package.json").write_text("dirty\n")),
                ("unknown-remotes", lambda target: subprocess.run(["git", "-C", str(target), "remote", "set-url", "origin", str(root / "custom.git")], check=True)),
                ("unknown-tracking", lambda target: subprocess.run(["git", "-C", str(target), "config", "branch.main.remote", "upstream"], check=True)),
                ("detached", lambda target: subprocess.run(["git", "-C", str(target), "checkout", "-q", "--detach", first], check=True)),
                ("custom-hook", lambda target: (target / ".git/hooks/pre-push").write_text("#!/bin/sh\necho custom\n")),
                ("core-hooks", lambda target: subprocess.run(["git", "-C", str(target), "config", "core.hooksPath", ".custom-hooks"], check=True)),
            ]
            for name, mutate in cases:
                with self.subTest(name=name):
                    target, env = clone(name)
                    mutate(target)
                    before = snapshot(target)
                    completed = subprocess.run([str(ROOT / "scripts/install-paseo-fork"), "--preflight"], env=env, capture_output=True, text=True)
                    self.assertNotEqual(completed.returncode, 0)
                    self.assertEqual(snapshot(target), before)

            for name, base in (("divergent", first), ("ahead", second)):
                with self.subTest(name=name):
                    target, env = clone(name, base)
                    (target / "local.txt").write_text(name + "\n")
                    subprocess.run(["git", "-C", str(target), "add", "."], check=True)
                    subprocess.run(["git", "-C", str(target), "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", name], check=True)
                    before = snapshot(target)
                    completed = subprocess.run([str(ROOT / "scripts/install-paseo-fork"), "--preflight"], env=env, capture_output=True, text=True)
                    self.assertNotEqual(completed.returncode, 0)
                    self.assertEqual(snapshot(target), before)

            invalid = root / "invalid-target"
            invalid.write_text("operator file\n")
            completed = subprocess.run(
                [str(ROOT / "scripts/install-paseo-fork"), "--preflight"],
                env=self.paseo_env(home, remote, invalid, second, npm),
                capture_output=True, text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertEqual(invalid.read_text(), "operator file\n")

            real_target, _ = clone("real-target")
            linked_target = root / "linked-target"
            linked_target.symlink_to(real_target, target_is_directory=True)
            real_before = snapshot(real_target)
            completed = subprocess.run(
                [str(ROOT / "scripts/install-paseo-fork"), "--preflight"],
                env=self.paseo_env(home, remote, linked_target, second, npm),
                capture_output=True, text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertTrue(linked_target.is_symlink())
            self.assertEqual(snapshot(real_target), real_before)

    def test_paseo_cli_backup_preserves_broken_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); home = root / "home"; target = root / "checkout"
            remote, _, second = self.make_paseo_remote(root)
            npm = self.fake_npm(root)
            cli_link = root / "bin/paseo"
            cli_link.parent.mkdir()
            cli_link.symlink_to("missing-operator-target")
            env = self.paseo_env(home, remote, target, second, npm)
            env["PASEO_CLI_LINK"] = str(cli_link)
            subprocess.run([str(ROOT / "scripts/install-paseo-fork")], check=True, env=env, capture_output=True, text=True)
            self.assertTrue(cli_link.is_symlink())
            self.assertEqual(os.readlink(cli_link), str(target / "packages/cli/bin/paseo"))
            backup_dirs = list((home / ".codex-room-backups").glob("paseo-cli-*"))
            self.assertEqual(len(backup_dirs), 1)
            backup = backup_dirs[0] / "paseo"
            self.assertTrue(backup.is_symlink())
            self.assertEqual(os.readlink(backup), "missing-operator-target")

    def test_paseo_existing_transitions_and_refusals_are_fail_safe(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); home = root / "home"
            remote, first, second = self.make_paseo_remote(root)
            npm = self.fake_npm(root)

            def clone(name: str, commit: str = first) -> tuple[Path, dict[str, str]]:
                target = root / name
                subprocess.run(["git", "clone", "-q", str(remote), str(target)], check=True)
                subprocess.run(["git", "-C", str(target), "checkout", "-q", "-B", "main", commit], check=True)
                subprocess.run(["git", "-C", str(target), "remote", "add", "upstream", str(remote) + "-upstream"], check=True)
                subprocess.run(["git", "-C", str(target), "config", "branch.main.remote", "origin"], check=True)
                return target, self.paseo_env(home, remote, target, second, npm)

            target, env = clone("ff")
            (target / ".codex").mkdir()
            subprocess.run([str(ROOT / "scripts" / "install-paseo-fork")], check=True, env=env, capture_output=True, text=True)
            self.assertEqual(subprocess.run(["git", "-C", str(target), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip(), second)
            self.assertTrue((target / ".codex").is_dir())
            before = subprocess.run(["git", "-C", str(target), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
            subprocess.run([str(ROOT / "scripts" / "install-paseo-fork")], check=True, env=env, capture_output=True, text=True)
            self.assertEqual(before, subprocess.run(["git", "-C", str(target), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip())

            dirty, dirty_env = clone("dirty")
            (dirty / "package.json").write_text("dirty\n")
            failed = subprocess.run([str(ROOT / "scripts" / "install-paseo-fork")], env=dirty_env, capture_output=True, text=True)
            self.assertNotEqual(failed.returncode, 0)
            self.assertEqual(subprocess.run(["git", "-C", str(dirty), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip(), first)

            detached, detached_env = clone("detached")
            subprocess.run(["git", "-C", str(detached), "checkout", "-q", "--detach", first], check=True)
            self.assertNotEqual(subprocess.run([str(ROOT / "scripts" / "install-paseo-fork")], env=detached_env).returncode, 0)

            custom, custom_env = clone("custom")
            subprocess.run(["git", "-C", str(custom), "remote", "set-url", "origin", str(root / "custom.git")], check=True)
            self.assertNotEqual(subprocess.run([str(ROOT / "scripts" / "install-paseo-fork")], env=custom_env).returncode, 0)
            self.assertEqual(subprocess.run(["git", "-C", str(custom), "remote", "get-url", "origin"], check=True, capture_output=True, text=True).stdout.strip(), str(root / "custom.git"))

            divergent, divergent_env = clone("divergent")
            (divergent / "local.txt").write_text("ahead\n")
            subprocess.run(["git", "-C", str(divergent), "add", "."], check=True)
            subprocess.run(["git", "-C", str(divergent), "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "local"], check=True)
            divergent_head = subprocess.run(["git", "-C", str(divergent), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
            self.assertNotEqual(subprocess.run([str(ROOT / "scripts" / "install-paseo-fork")], env=divergent_env).returncode, 0)
            self.assertEqual(subprocess.run(["git", "-C", str(divergent), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip(), divergent_head)

    def test_paseo_exact_legacy_migration_and_hook_lock_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); home = root / "home"; remote, _, second = self.make_paseo_remote(root); npm = self.fake_npm(root)
            target = root / "legacy"
            subprocess.run(["git", "clone", "-q", str(remote), str(target)], check=True)
            subprocess.run(["git", "-C", str(target), "remote", "rename", "origin", "hoangnb24"], check=True)
            subprocess.run(["git", "-C", str(target), "remote", "add", "origin", str(remote) + "-upstream"], check=True)
            subprocess.run(["git", "-C", str(target), "config", "branch.main.remote", "origin"], check=True)
            env = self.paseo_env(home, remote, target, second, npm)
            subprocess.run([str(ROOT / "scripts" / "install-paseo-fork")], check=True, env=env, capture_output=True, text=True)
            self.assertEqual(subprocess.run(["git", "-C", str(target), "remote", "get-url", "origin"], check=True, capture_output=True, text=True).stdout.strip(), str(remote))
            self.assertEqual(subprocess.run(["git", "-C", str(target), "remote", "get-url", "upstream"], check=True, capture_output=True, text=True).stdout.strip(), str(remote) + "-upstream")

            (target / ".git/hooks/pre-push").write_text("#!/bin/sh\necho custom\n")
            before_log = (root / "npm.log").read_text()
            self.assertNotEqual(subprocess.run([str(ROOT / "scripts" / "install-paseo-fork")], env=env).returncode, 0)
            self.assertEqual((root / "npm.log").read_text(), before_log)

            (target / ".git/hooks/pre-push").unlink()
            changing_npm = self.fake_npm(root / "changing", change_lock=True)
            changing_env = self.paseo_env(home, remote, target, second, changing_npm)
            self.assertNotEqual(subprocess.run([str(ROOT / "scripts" / "install-paseo-fork")], env=changing_env).returncode, 0)

    def test_fork_provenance_and_update_sources_are_explicit(self) -> None:
        paseo_source = (ROOT / "paseo" / "source.toml").read_text()
        updater = (HOME_MIRROR / ".local" / "bin" / "paseo-local-update").read_text()

        self.assertIn('fork = "git@github.com:hoangnb24/paseo.git"', paseo_source)
        self.assertIn(
            'verified_commit = "8511089eaeb06cddd049b629562926822020de5c"',
            paseo_source,
        )
        for forbidden in ("git pull", "git rebase", "git reset", "npm install"):
            self.assertNotIn(forbidden, updater)
        self.assertIn('git ls-remote "$PASEO_FORK_URL"', updater)
        self.assertIn('"$NPM_BIN" ci', updater)
        self.assertIn("PASEO_VERIFIED_COMMIT", updater)

    def test_updater_rejects_moved_ref_before_dependency_or_build_actions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); home = root / "home"; target = root / "checkout"
            remote, first, second = self.make_paseo_remote(root)
            subprocess.run(["git", "clone", "-q", str(remote), str(target)], check=True)
            subprocess.run(["git", "-C", str(target), "checkout", "-q", "-B", "main", first], check=True)
            subprocess.run(["git", "-C", str(target), "remote", "add", "upstream", str(remote) + "-upstream"], check=True)
            subprocess.run(["git", "-C", str(target), "config", "branch.main.remote", "origin"], check=True)
            npm = self.fake_npm(root)
            env = self.paseo_env(home, remote, target, first, npm)
            failed = subprocess.run([str(HOME_MIRROR / ".local/bin/paseo-local-update")], env=env, capture_output=True, text=True)
            self.assertNotEqual(failed.returncode, 0)
            self.assertFalse((root / "npm.log").exists())
            self.assertEqual(subprocess.run(["git", "-C", str(target), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip(), first)
            self.assertIn(second, subprocess.run(["git", "ls-remote", str(remote), "refs/heads/main"], check=True, capture_output=True, text=True).stdout)

    def test_installed_verify_needs_only_three_roles_and_no_ocr_or_harness(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); home = root / "home"; runtime = home / ".codex-runtime"
            subprocess.run([str(ROOT / "scripts/install"), "--apply"], env={**os.environ, "HOME": str(home)}, check=True, capture_output=True, text=True)
            paseo = root / "custom-paseo"; (paseo / "packages/cli/bin").mkdir(parents=True)
            (paseo / "packages/cli/bin/paseo").write_text("#!/usr/bin/env node\n")
            subprocess.run(["git", "init", "-q", "-b", "main", str(paseo)], check=True)
            subprocess.run(["git", "-C", str(paseo), "add", "."], check=True)
            subprocess.run(["git", "-C", str(paseo), "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "fixture"], check=True)
            subprocess.run(["git", "-C", str(paseo), "remote", "add", "origin", "git@github.com:hoangnb24/paseo.git"], check=True)
            subprocess.run(["git", "-C", str(paseo), "remote", "add", "upstream", "git@github.com:getpaseo/paseo.git"], check=True)
            subprocess.run(["git", "-C", str(paseo), "config", "branch.main.remote", "origin"], check=True)
            subprocess.run(["git", "-C", str(paseo), "config", "branch.main.merge", "refs/heads/main"], check=True)
            link = home / ".local/bin/paseo"
            link.symlink_to(paseo / "packages/cli/bin/paseo")
            canonical_plugins = home / ".codex/plugins"; canonical_plugins.mkdir(parents=True)
            for role in ("supervisor", "lead", "peer"):
                role_home = runtime / role; role_home.mkdir(parents=True)
                (role_home / "config.toml").write_text(
                    "[features]\nmulti_agent = false\nmulti_agent_v2 = false\n\n[agents]\nenabled = false\n"
                )
                (role_home / "model-catalog.no-native-agents.json").write_text(
                    '{"models":[{"multi_agent_version":null}]}\n'
                )
                (role_home / "plugins").symlink_to(canonical_plugins, target_is_directory=True)
            for legacy_role in ("review", "harness"):
                legacy = runtime / legacy_role
                legacy.mkdir()
                (legacy / "private").write_text("must remain ignored\n")
            bin_dir = root / "bin"
            self.executable(bin_dir / "codex", "#!/bin/sh\nexit 0\n")
            self.executable(bin_dir / "ocr", "#!/bin/sh\necho called > \"$OCR_LOG\"\nexit 99\n")
            self.executable(
                bin_dir / "git",
                "#!/bin/sh\n"
                "if [ \"$1\" = -C ] && [ \"$3\" = rev-parse ] && [ \"$4\" = HEAD ]; then\n"
                " case \"$2\" in \"$PASEO_REPO_DIR\") echo 8511089eaeb06cddd049b629562926822020de5c ;; *) exec /usr/bin/git \"$@\" ;; esac\n"
                "else exec /usr/bin/git \"$@\"; fi\n"
            )
            env = os.environ.copy(); env.update({
                "HOME": str(home), "PASEO_REPO_DIR": str(paseo), "OCR_LOG": str(root / "ocr.log"),
                "CODEX_ROOM_TOML_PYTHON": os.environ.get("CODEX_ROOM_TOML_PYTHON", sys.executable),
                "PATH": str(bin_dir) + os.pathsep + env["PATH"],
            })
            completed = subprocess.run([str(ROOT / "scripts/verify")], env=env, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertIn("OK    Paseo CLI links to local fork", completed.stdout)
            self.assertFalse((root / "ocr.log").exists())
            self.assertEqual((runtime / "review/private").read_text(), "must remain ignored\n")
            self.assertEqual((runtime / "harness/private").read_text(), "must remain ignored\n")

            lead_config = runtime / "lead/config.toml"
            valid_config = lead_config.read_text()
            lead_config.write_text(
                "enabled = false\nmulti_agent = false\nmulti_agent_v2 = false\n"
                "[agents]\nenabled = true\n"
                "[features]\nmulti_agent = true\nmulti_agent_v2 = true\n"
            )
            wrong_table = subprocess.run(
                [str(ROOT / "scripts/verify")], env=env, capture_output=True, text=True
            )
            self.assertNotEqual(wrong_table.returncode, 0)
            self.assertIn("FAIL  lead native-agent policy disabled", wrong_table.stdout)
            lead_config.write_text(valid_config)

            lead_catalog = runtime / "lead/model-catalog.no-native-agents.json"
            valid_catalog = lead_catalog.read_text()
            lead_catalog.write_text('{"models":[]}\n')
            empty_catalog = subprocess.run(
                [str(ROOT / "scripts/verify")], env=env, capture_output=True, text=True
            )
            self.assertNotEqual(empty_catalog.returncode, 0)
            self.assertIn("FAIL  lead model agent metadata disabled", empty_catalog.stdout)
            lead_catalog.write_text(valid_catalog)

            obsolete_links = [
                home / ".config/codex-room/overlays/review.config.toml",
                home / ".config/codex-room/overlays/harness.config.toml",
                home / ".config/codex-room/paseo.phase2-coexist.candidate.json",
                home / ".config/codex-room/paseo.phase2-hard-cut.candidate.json",
                home / ".local/bin/codex-room-hard-cut",
                home / ".local/bin/codex-review-apply",
            ]
            for obsolete_link in obsolete_links:
                obsolete_link.symlink_to(root / "missing-obsolete-target")
            dangling_obsolete = subprocess.run(
                [str(ROOT / "scripts/verify")], env=env, capture_output=True, text=True
            )
            self.assertNotEqual(dangling_obsolete.returncode, 0)
            self.assertEqual(
                dangling_obsolete.stdout.count("FAIL  obsolete path is inactive"),
                len(obsolete_links),
            )
            for obsolete_link in obsolete_links:
                obsolete_link.unlink()

            launcher = home / ".local/bin/codex-room"
            launcher.chmod(0o644)
            nonexecutable_launcher = subprocess.run(
                [str(ROOT / "scripts/verify")], env=env, capture_output=True, text=True
            )
            self.assertNotEqual(nonexecutable_launcher.returncode, 0)
            self.assertIn("FAIL  room launcher is executable", nonexecutable_launcher.stdout)

    def test_sync_all_uses_the_common_generator_for_all_three_roles(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fake_sync = root / "fake-sync"
            sync_log = root / "roles.log"
            fake_sync.write_text(
                "#!/usr/bin/env python3\n"
                "import os, sys\n"
                "with open(os.environ['SYNC_LOG'], 'a') as stream:\n"
                "    stream.write(sys.argv[1] + '\\n')\n"
            )
            fake_sync.chmod(0o755)
            env = os.environ.copy()
            env.update(
                {
                    "HOME": str(root / "home"),
                    "CODEX_ROOM_SYNC_BIN": str(fake_sync),
                    "SYNC_LOG": str(sync_log),
                }
            )

            subprocess.run(
                [str(SYNC_ALL)],
                check=True,
                env=env,
                capture_output=True,
                text=True,
            )

            self.assertEqual(
                sync_log.read_text().splitlines(),
                ["supervisor", "lead", "peer"],
            )

            for legacy_role in ("review", "harness"):
                rejected = subprocess.run(
                    [str(SYNC_ALL), legacy_role], env=env, capture_output=True, text=True
                )
                self.assertNotEqual(rejected.returncode, 0)
                self.assertIn(f"unknown role: {legacy_role}", rejected.stderr)

    def test_launcher_rejects_legacy_roles(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            env = {**os.environ, "CODEX_ROOM_RUNTIME_ROOT": str(Path(temporary) / "runtime")}
            for arguments in (("review",), ("harness",)):
                with self.subTest(arguments=arguments):
                    completed = subprocess.run(
                        [str(LAUNCHER), *arguments], env=env, capture_output=True, text=True
                    )
                    self.assertEqual(completed.returncode, 2)
                    self.assertIn("unknown", completed.stderr)

    def test_minimum_role_contracts_have_capabilities_without_pilot_ceremony(self) -> None:
        protocol = (ROOM / "workflow" / "WORKSPACE_PROTOCOL.md").read_text()
        for capability in (
            "Human owns product goals",
            "Supervisor observes",
            "Lead owns project framing",
            "Peer owns one bounded outcome",
            "at most one active",
            "immutable candidate",
            "REOPEN_REQUEST",
            "DEPENDENCY_REQUEST",
            "BLOCKED",
            "fresh read-only Peer",
            "explicitly accepts or rejects",
            "repeatedly polling unchanged state",
        ):
            self.assertIn(capability, protocol)

        lead = (ROOM / "overlays" / "lead.config.toml").read_text()
        peer = (ROOM / "overlays" / "peer.config.toml").read_text()
        supervisor = (ROOM / "overlays" / "supervisor.config.toml").read_text()
        self.assertIn("at most one active writable Peer", lead)
        self.assertIn("fresh read-only Peer", lead)
        self.assertIn("explicitly ACCEPT or REJECT", lead)
        self.assertFalse((ROOM / "overlays" / "review.config.toml").exists())
        self.assertNotIn("codex-review", lead)
        self.assertIn("REOPEN_REQUEST", peer)
        self.assertIn("DEPENDENCY_REQUEST", peer)
        self.assertIn("BLOCKED", peer)
        self.assertIn("Do not spawn, manage, or coordinate other agents", peer)
        self.assertIn("faithfully routes Human intent", protocol)
        self.assertIn("bounded recovery", supervisor)
        for active in (protocol, lead, peer, supervisor):
            for retired in ("PARALLEL_CHECK", "multiple-writer", "workflow pilot", "marker"):
                self.assertNotIn(retired.casefold(), active.casefold())

class PublicInstallTransactionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.home = self.root / "home"
        self.home.mkdir()
        codex = self.home / ".codex"
        codex.mkdir()
        (codex / "config.toml").write_text(
            'model = "operator-model"\n'
            "\n[features]\n"
            "multi_agent = true\n"
            "multi_agent_v2 = true\n"
            "\n[agents]\n"
            "enabled = true\n"
        )
        for name in ("auth.json", "AGENTS.md", "hooks.json"):
            (codex / name).write_text("operator\n")
        for name in ("skills", "plugins"):
            (codex / name).mkdir()
            (codex / name / "operator.marker").write_text("private\n")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def executable(self, path: Path, text: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        path.chmod(0o755)
        return path

    def lifecycle_env(self, paseo: Path, verifier: Path) -> dict[str, str]:
        return {
            **os.environ,
            "HOME": str(self.home),
            "CODEX_ROOM_MODEL_CATALOG": str(ROOT / "tests/fixtures/model-catalog.json"),
            "CODEX_ROOM_TOML_PYTHON": os.environ.get("CODEX_ROOM_TOML_PYTHON", sys.executable),
            "PASEO_INSTALL_BIN": str(paseo),
            "CODEX_ROOM_VERIFY_BIN": str(verifier),
            "VERIFY_LOG": str(self.root / "verify.log"),
        }

    def make_fake_paseo(self) -> Path:
        return self.executable(
            self.root / "fake-paseo",
            "#!/bin/sh\n"
            "set -eu\n"
            "if [ \"${1:-}\" = --preflight ]; then\n"
            "  if [ \"${PREFLIGHT_FAIL:-0}\" = 1 ]; then exit 19; fi\n"
            "  exit 0\n"
            "fi\n"
            "mkdir -p \"$PASEO_REPO_DIR/packages/cli/bin\"\n"
            "if [ ! -d \"$PASEO_REPO_DIR/.git\" ]; then\n"
            "  git init -q -b main \"$PASEO_REPO_DIR\"\n"
            "  git -C \"$PASEO_REPO_DIR\" remote add origin \"$PASEO_FORK_URL\"\n"
            "  git -C \"$PASEO_REPO_DIR\" remote add upstream \"$PASEO_UPSTREAM_URL\"\n"
            "  git -C \"$PASEO_REPO_DIR\" config branch.main.remote origin\n"
            "  git -C \"$PASEO_REPO_DIR\" config branch.main.merge refs/heads/main\n"
            "  git -C \"$PASEO_REPO_DIR\" -c user.name=Test -c user.email=test@example.invalid commit --allow-empty -qm bootstrap\n"
            "fi\n"
            "printf '%s\\n' '#!/bin/sh' > \"$PASEO_REPO_DIR/packages/cli/bin/paseo\"\n"
            "chmod 755 \"$PASEO_REPO_DIR/packages/cli/bin/paseo\"\n"
            "mkdir -p \"$(dirname \"$PASEO_CLI_LINK\")\"\n"
            "ln -sfn \"$PASEO_REPO_DIR/packages/cli/bin/paseo\" \"$PASEO_CLI_LINK\"\n",
        )

    def make_fake_verifier(self) -> Path:
        return self.executable(
            self.root / "fake-verify",
            "#!/bin/sh\n"
            "set -eu\n"
            "printf '%s\\n' \"$*\" >> \"$VERIFY_LOG\"\n"
            "if [ \"${VERIFY_FAIL:-0}\" = 1 ]; then exit 23; fi\n"
            "test -f \"$HOME/.paseo/config.json\"\n"
            "test -f \"$HOME/.codex-runtime/supervisor/config.toml\"\n"
            "test -f \"$HOME/.codex-runtime/lead/config.toml\"\n"
            "test -f \"$HOME/.codex-runtime/peer/config.toml\"\n",
        )

    def run_install(self, arguments: tuple[str, ...], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(ROOT / "install"), *arguments],
            env=env,
            capture_output=True,
            text=True,
        )

    def tree_snapshot(self, root: Path) -> list[tuple[str, str, bytes | str, int]]:
        if not root.exists() and not root.is_symlink():
            return []
        result: list[tuple[str, str, bytes | str, int]] = []
        for path in sorted(root.rglob("*")):
            relative = str(path.relative_to(root))
            mode = path.lstat().st_mode & 0o777
            if path.is_symlink():
                result.append((relative, "link", os.readlink(path), mode))
            elif path.is_file():
                result.append((relative, "file", path.read_bytes(), mode))
            else:
                result.append((relative, "dir", b"", mode))
        return result

    def test_public_apply_stages_three_roles_is_repeatable_and_verify_is_live(self) -> None:
        paseo = self.make_fake_paseo()
        verifier = self.make_fake_verifier()
        env = self.lifecycle_env(paseo, verifier)
        first = self.run_install(("--apply",), env)
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        generated = self.home / ".codex-runtime"
        first_configs = {
            role: (generated / role / "config.toml").read_bytes()
            for role in ("supervisor", "lead", "peer")
        }
        second = self.run_install(("--apply",), env)
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertEqual(
            {role: (generated / role / "config.toml").read_bytes() for role in first_configs},
            first_configs,
        )
        self.assertEqual((self.home / ".codex" / "auth.json").read_text(), "operator\n")
        verify = self.run_install(("--verify",), env)
        self.assertEqual(verify.returncode, 0, verify.stdout + verify.stderr)
        self.assertEqual((self.root / "verify.log").read_text().splitlines()[-1], "--live")

    def test_default_plan_is_complete_and_non_mutating(self) -> None:
        paseo = self.make_fake_paseo()
        verifier = self.make_fake_verifier()
        env = self.lifecycle_env(paseo, verifier)
        before = self.tree_snapshot(self.home)
        planned = self.run_install((), env)
        self.assertEqual(planned.returncode, 0, planned.stdout + planned.stderr)
        self.assertIn("PREFLIGHT", planned.stdout)
        self.assertIn("supervisor, lead, peer", planned.stdout)
        self.assertIn("rollback on failure", planned.stdout)
        self.assertEqual(self.tree_snapshot(self.home), before)

    def test_immutable_manifest_pin_override_is_refused_before_mutation(self) -> None:
        paseo = self.make_fake_paseo()
        verifier = self.make_fake_verifier()
        env = self.lifecycle_env(paseo, verifier)
        before = self.tree_snapshot(self.home)
        failed = self.run_install(("--apply",), {**env, "PASEO_VERIFIED_COMMIT": "0" * 40})
        self.assertNotEqual(failed.returncode, 0)
        self.assertIn("immutable Paseo commit", failed.stderr)
        self.assertEqual(self.tree_snapshot(self.home), before)

    def test_managed_target_obstacle_fails_closed_before_paseo_publish(self) -> None:
        redirected = self.root / "redirected-instructions"
        redirected.write_text("operator-owned bytes\n")
        managed = self.home / ".config/codex-room/model-instructions.md"
        managed.parent.mkdir(parents=True)
        managed.symlink_to(redirected)
        paseo = self.make_fake_paseo()
        verifier = self.make_fake_verifier()
        failed = self.run_install(("--apply",), self.lifecycle_env(paseo, verifier))
        self.assertNotEqual(failed.returncode, 0)
        self.assertTrue(managed.is_symlink())
        self.assertEqual(redirected.read_text(), "operator-owned bytes\n")
        self.assertFalse((self.home / "projects").exists())

    def test_missing_resource_and_bad_catalog_fail_during_staging(self) -> None:
        auth = self.home / ".codex/auth.json"
        auth.unlink()
        paseo = self.make_fake_paseo()
        verifier = self.make_fake_verifier()
        missing = self.run_install(("--apply",), self.lifecycle_env(paseo, verifier))
        self.assertNotEqual(missing.returncode, 0)
        self.assertFalse((self.home / "projects").exists())

        auth.write_text("operator\n")
        bad_catalog = self.root / "bad-catalog.json"
        bad_catalog.write_text('{"models": []}\n')
        failed = self.run_install(
            ("--apply",),
            {**self.lifecycle_env(paseo, verifier), "CODEX_ROOM_MODEL_CATALOG": str(bad_catalog)},
        )
        self.assertNotEqual(failed.returncode, 0)
        self.assertFalse((self.home / "projects").exists())

    def test_optional_hooks_absent_then_added_support_public_install_and_sync(self) -> None:
        hooks = self.home / ".codex/hooks.json"
        hooks.unlink()
        env = self.lifecycle_env(self.make_fake_paseo(), self.make_fake_verifier())
        before = self.tree_snapshot(self.home)
        planned = self.run_install((), env)
        self.assertEqual(planned.returncode, 0, planned.stdout + planned.stderr)
        self.assertEqual(self.tree_snapshot(self.home), before)
        operator_before = self.tree_snapshot(self.home / ".codex")
        for _ in range(2):
            result = self.run_install(("--apply",), env)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for role in ("supervisor", "lead", "peer"):
            runtime_hooks = self.home / ".codex-runtime" / role / "hooks.json"
            result = subprocess.run(
                [str(self.home / ".local/bin/codex-room-sync"), role],
                env=env, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse(runtime_hooks.exists() or runtime_hooks.is_symlink())
        self.assertEqual(self.tree_snapshot(self.home / ".codex"), operator_before)
        hooks.write_text('{"hooks": {}}\n')
        result = self.run_install(("--apply",), env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for role in ("supervisor", "lead", "peer"):
            runtime_hooks = self.home / ".codex-runtime" / role / "hooks.json"
            self.assertTrue(runtime_hooks.is_symlink())
            self.assertEqual(runtime_hooks.resolve(), hooks.resolve())

    def test_optional_hooks_dangling_link_fails_without_mutation(self) -> None:
        hooks = self.home / ".codex/hooks.json"
        hooks.unlink()
        hooks.symlink_to(self.home / "missing-hooks.json")
        env = self.lifecycle_env(self.make_fake_paseo(), self.make_fake_verifier())
        before = self.tree_snapshot(self.home)
        for args in ((), ("--apply",)):
            result = self.run_install(args, env)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("dangling link", result.stderr)
            self.assertEqual(self.tree_snapshot(self.home), before)

    def test_redirected_active_runtime_role_fails_before_publication(self) -> None:
        redirected = self.root / "redirected-lead"
        redirected.mkdir()
        (redirected / "private.sqlite").write_bytes(b"private\x00")
        runtime_root = self.home / ".codex-runtime"
        runtime_root.mkdir()
        (runtime_root / "lead").symlink_to(redirected, target_is_directory=True)
        paseo = self.make_fake_paseo()
        verifier = self.make_fake_verifier()
        failed = self.run_install(("--apply",), self.lifecycle_env(paseo, verifier))
        self.assertNotEqual(failed.returncode, 0)
        self.assertTrue((runtime_root / "lead").is_symlink())
        self.assertEqual((redirected / "private.sqlite").read_bytes(), b"private\x00")
        self.assertFalse((self.home / "projects").exists())

    def test_final_verification_failure_restores_managed_and_paseo_state(self) -> None:
        paseo = self.make_fake_paseo()
        verifier = self.make_fake_verifier()
        env = self.lifecycle_env(paseo, verifier)
        operator_before = self.tree_snapshot(self.home / ".codex")
        failed = self.run_install(("--apply",), {**env, "VERIFY_FAIL": "1"})
        self.assertNotEqual(failed.returncode, 0)
        self.assertEqual(self.tree_snapshot(self.home / ".codex"), operator_before)
        self.assertFalse((self.home / ".paseo").exists())
        self.assertFalse((self.home / ".codex-runtime").exists())
        self.assertFalse((self.home / "projects").exists())
        self.assertFalse((self.home / ".local/bin/paseo").exists())
        self.assertFalse((self.home / ".config/codex-room/model-instructions.md").exists())

    def test_customized_obsolete_path_is_preserved_and_warned(self) -> None:
        obsolete = self.home / ".config/codex-room/overlays/review.config.toml"
        obsolete.parent.mkdir(parents=True)
        obsolete.write_text("operator private review notes\n")
        redirected = self.home / ".local/bin/codex-room-hard-cut"
        redirected.parent.mkdir(parents=True)
        redirected.symlink_to(self.home / "operator-private-tool")
        paseo = self.make_fake_paseo()
        verifier = self.make_fake_verifier()
        completed = self.run_install(("--apply",), self.lifecycle_env(paseo, verifier))
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(obsolete.read_text(), "operator private review notes\n")
        self.assertTrue(redirected.is_symlink())
        self.assertIn("preserving customized/private obsolete path", completed.stderr)

    def test_preflight_failure_preserves_an_existing_installation(self) -> None:
        paseo = self.make_fake_paseo()
        verifier = self.make_fake_verifier()
        env = self.lifecycle_env(paseo, verifier)
        first = self.run_install(("--apply",), env)
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        before = {
            "config": self.tree_snapshot(self.home / ".config"),
            "paseo": self.tree_snapshot(self.home / "projects"),
            "runtime": self.tree_snapshot(self.home / ".codex-runtime"),
            "cli": self.tree_snapshot(self.home / ".local"),
        }
        failed = self.run_install(("--apply",), {**env, "PREFLIGHT_FAIL": "1"})
        self.assertNotEqual(failed.returncode, 0)
        self.assertEqual(self.tree_snapshot(self.home / ".config"), before["config"])
        self.assertEqual(self.tree_snapshot(self.home / "projects"), before["paseo"])
        self.assertEqual(self.tree_snapshot(self.home / ".codex-runtime"), before["runtime"])
        self.assertEqual(self.tree_snapshot(self.home / ".local"), before["cli"])

    def test_generation_failure_happens_before_any_live_publication(self) -> None:
        paseo = self.make_fake_paseo()
        verifier = self.make_fake_verifier()
        env = self.lifecycle_env(paseo, verifier)
        failing_sync = self.executable(
            self.root / "failing-sync",
            "#!/bin/sh\n"
            "set -eu\n"
            "if [ \"$1\" = lead ]; then exit 29; fi\n"
            f"exec \"{SYNC}\" \"$@\"\n",
        )
        failed = self.run_install(("--apply",), {**env, "CODEX_ROOM_SYNC_BIN": str(failing_sync)})
        self.assertNotEqual(failed.returncode, 0)
        self.assertFalse((self.home / ".paseo").exists())
        self.assertFalse((self.home / ".codex-runtime").exists())
        self.assertFalse((self.home / ".config").exists())
        self.assertFalse((self.home / "projects").exists())

    def test_replaced_managed_file_has_owner_only_backup(self) -> None:
        managed = self.home / ".config/codex-room/model-instructions.md"
        managed.parent.mkdir(parents=True)
        managed.write_bytes(b"operator custom instructions\n")
        managed.chmod(0o644)
        paseo = self.make_fake_paseo()
        verifier = self.make_fake_verifier()
        completed = self.run_install(("--apply",), self.lifecycle_env(paseo, verifier))
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        backup = Path(next(line.split("backup=", 1)[1] for line in completed.stdout.splitlines() if "backup=" in line))
        saved = backup / "managed/.config_codex-room_model-instructions.md"
        self.assertEqual(saved.read_bytes(), b"operator custom instructions\n")
        self.assertEqual(saved.stat().st_mode & 0o777, 0o600)
        self.assertEqual(backup.stat().st_mode & 0o777, 0o700)

    def test_existing_paseo_checkout_rollback_restores_private_tree_metadata(self) -> None:
        paseo = self.make_fake_paseo()
        verifier = self.make_fake_verifier()
        env = self.lifecycle_env(paseo, verifier)
        first = self.run_install(("--apply",), env)
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        checkout = self.home / "projects/supervisors/paseo"
        runtime_root = self.home / ".codex-runtime"
        for role in ("supervisor", "lead", "peer"):
            (runtime_root / role).chmod(0o755)
        runtime_root.chmod(0o755)
        private = checkout / "node_modules/operator-private.bin"
        private.parent.mkdir(parents=True)
        private.write_bytes(b"private dependency bytes\x00")
        private.chmod(0o640)
        custom_hook = checkout / ".git/hooks/operator-hook"
        custom_hook.write_text("#!/bin/sh\nexit 4\n")
        custom_hook.chmod(0o700)
        before = self.tree_snapshot(checkout)
        failed = self.run_install(("--apply",), {**env, "VERIFY_FAIL": "1"})
        self.assertNotEqual(failed.returncode, 0)
        self.assertEqual(self.tree_snapshot(checkout), before)
        self.assertEqual(runtime_root.stat().st_mode & 0o777, 0o755)
        for role in ("supervisor", "lead", "peer"):
            self.assertEqual((runtime_root / role).stat().st_mode & 0o777, 0o755)

    def test_incomplete_paseo_checkout_snapshot_never_deletes_original(self) -> None:
        paseo = self.make_fake_paseo()
        verifier = self.make_fake_verifier()
        env = self.lifecycle_env(paseo, verifier)
        first = self.run_install(("--apply",), env)
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        checkout = self.home / "projects/supervisors/paseo"
        marker = checkout / "operator-private.marker"
        marker.write_bytes(b"private\x00")
        os.mkfifo(checkout / "operator-pipe")
        failed = self.run_install(("--apply",), env)
        self.assertNotEqual(failed.returncode, 0)
        self.assertTrue(checkout.is_dir())
        self.assertEqual(marker.read_bytes(), b"private\x00")
        self.assertTrue((checkout / "operator-pipe").is_fifo())
        self.assertTrue((self.home / ".local/bin/paseo").is_symlink())

    def test_incomplete_paseo_cli_snapshot_never_deletes_original_checkout(self) -> None:
        paseo = self.make_fake_paseo()
        verifier = self.make_fake_verifier()
        env = self.lifecycle_env(paseo, verifier)
        first = self.run_install(("--apply",), env)
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        checkout = self.home / "projects/supervisors/paseo"
        marker = checkout / "operator-private.marker"
        marker.write_bytes(b"private\x00")
        cli = self.home / ".local/bin/paseo"
        cli.unlink()
        os.mkfifo(cli)
        failed = self.run_install(("--apply",), env)
        self.assertNotEqual(failed.returncode, 0)
        self.assertTrue(checkout.is_dir())
        self.assertEqual(marker.read_bytes(), b"private\x00")
        self.assertTrue(cli.is_fifo())

    def test_path_overrides_cannot_alias_protected_or_managed_state(self) -> None:
        paseo = self.make_fake_paseo()
        verifier = self.make_fake_verifier()
        base = self.lifecycle_env(paseo, verifier)
        aliases = (
            {"PASEO_CLI_LINK": str(self.home / ".codex/auth.json")},
            {"PASEO_REPO_DIR": str(self.home / ".codex/paseo")},
            {"CODEX_ROOM_RUNTIME_ROOT": str(self.home / ".codex")},
            {"CODEX_ROOM_BACKUP_ROOT": str(self.home / ".codex")},
            {
                "PASEO_REPO_DIR": str(self.home / ".local/bin/shared"),
                "PASEO_CLI_LINK": str(self.home / ".local/bin/shared/paseo"),
            },
        )
        for override in aliases:
            with self.subTest(override=override):
                failed = self.run_install(("--apply",), {**base, **override})
                self.assertNotEqual(failed.returncode, 0, failed.stdout + failed.stderr)
                self.assertEqual((self.home / ".codex/auth.json").read_text(), "operator\n")
                self.assertFalse((self.home / ".paseo").exists())
                self.assertFalse((self.home / "projects").exists())

    def test_overridden_roots_reserve_canonical_roots_and_managed_targets(self) -> None:
        paseo = self.make_fake_paseo()
        verifier = self.make_fake_verifier()
        base = self.lifecycle_env(paseo, verifier)
        before = self.tree_snapshot(self.home)
        custom_runtime = (self.root / "custom-runtime").resolve()
        custom_backup = (self.root / "custom-backups").resolve()
        failures = (
            {
                "CODEX_ROOM_RUNTIME_ROOT": str(custom_runtime),
                "PASEO_REPO_DIR": str(self.home / ".codex-runtime/paseo"),
            },
            {
                "CODEX_ROOM_BACKUP_ROOT": str(custom_backup),
                "PASEO_REPO_DIR": str(self.home / ".codex-room-backups/paseo"),
            },
            {
                "CODEX_ROOM_BACKUP_ROOT": str(self.home / ".config/codex-room/model-instructions.md"),
            },
        )
        for override in failures:
            with self.subTest(override=override):
                failed = self.run_install(("--apply",), {**base, **override})
                self.assertNotEqual(failed.returncode, 0, failed.stdout + failed.stderr)
                self.assertEqual(self.tree_snapshot(self.home), before)
                self.assertFalse(custom_runtime.exists())
                self.assertFalse(custom_backup.exists())

    def test_disjoint_runtime_and_backup_overrides_remain_supported(self) -> None:
        paseo = self.make_fake_paseo()
        verifier = self.executable(
            self.root / "custom-verify",
            "#!/bin/sh\n"
            "set -eu\n"
            "test -f \"$HOME/.paseo/config.json\"\n"
            "for role in supervisor lead peer; do\n"
            "  test -f \"$CODEX_ROOM_RUNTIME_ROOT/$role/config.toml\"\n"
            "done\n",
        )
        runtime = (self.root / "custom-runtime").resolve()
        backup = (self.root / "custom-backups").resolve()
        env = {
            **self.lifecycle_env(paseo, verifier),
            "CODEX_ROOM_RUNTIME_ROOT": str(runtime),
            "CODEX_ROOM_BACKUP_ROOT": str(backup),
        }
        completed = self.run_install(("--apply",), env)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertTrue((runtime / "supervisor/config.toml").is_file())
        self.assertTrue((runtime / "lead/config.toml").is_file())
        self.assertTrue((runtime / "peer/config.toml").is_file())
        self.assertEqual(backup.stat().st_mode & 0o777, 0o700)

    def test_rendered_historical_phase2_files_are_retired(self) -> None:
        for name in ("coexist", "hard-cut"):
            source = ROOT / "paseo/legacy" / f"paseo.phase2-{name}.candidate.json.template"
            destination = self.home / ".config/codex-room" / f"paseo.phase2-{name}.candidate.json"
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.read_bytes().replace(b"@@HOME@@", str(self.home).encode()))
            destination.chmod(0o600)
        paseo = self.make_fake_paseo()
        verifier = self.make_fake_verifier()
        completed = self.run_install(("--apply",), self.lifecycle_env(paseo, verifier))
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertFalse((self.home / ".config/codex-room/paseo.phase2-coexist.candidate.json").exists())
        self.assertFalse((self.home / ".config/codex-room/paseo.phase2-hard-cut.candidate.json").exists())

    def test_external_checkout_metadata_link_fails_before_publish(self) -> None:
        paseo = self.make_fake_paseo()
        verifier = self.make_fake_verifier()
        env = self.lifecycle_env(paseo, verifier)
        first = self.run_install(("--apply",), env)
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        checkout = self.home / "projects/supervisors/paseo"
        outside = self.root / "outside-hooks"
        outside.mkdir()
        (outside / "operator.marker").write_bytes(b"private\x00")
        hooks = checkout / ".git/hooks"
        shutil.rmtree(hooks)
        hooks.symlink_to(outside, target_is_directory=True)
        failed = self.run_install(("--apply",), env)
        self.assertNotEqual(failed.returncode, 0)
        self.assertTrue(hooks.is_symlink())
        self.assertEqual((outside / "operator.marker").read_bytes(), b"private\x00")

        hooks.unlink()
        hooks.mkdir()
        ancestor = self.root / "ancestor-target"
        ancestor.symlink_to(checkout.parent, target_is_directory=True)
        link = checkout / "workspace-ancestor"
        link.symlink_to(ancestor, target_is_directory=True)
        failed = self.run_install(("--apply",), env)
        self.assertNotEqual(failed.returncode, 0)
        self.assertTrue(link.is_symlink())

    def test_sigint_settles_helper_process_group_before_rollback(self) -> None:
        paseo = self.executable(
            self.root / "interrupting-paseo",
            "#!/bin/sh\n"
            "set -eu\n"
            "if [ \"${1:-}\" = --preflight ]; then exit 0; fi\n"
            "mkdir -p \"$PASEO_REPO_DIR/packages/cli/bin\"\n"
            "printf live > \"$PASEO_REPO_DIR/live-marker\"\n"
            "printf '#!/bin/sh\\n' > \"$PASEO_REPO_DIR/packages/cli/bin/paseo\"\n"
            "printf ready > \"$READY_MARKER\"\n"
            "(trap 'exit 0' TERM INT; sleep 1; printf late > \"$LATE_MARKER\") &\n"
            "trap 'exit 0' TERM INT\n"
            "while :; do sleep 0.1; done\n",
        )
        verifier = self.make_fake_verifier()
        ready = self.root / "ready"
        late = self.root / "late"
        env = {
            **self.lifecycle_env(paseo, verifier),
            "READY_MARKER": str(ready),
            "LATE_MARKER": str(late),
        }
        process = subprocess.Popen(
            [str(ROOT / "install"), "--apply"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        deadline = time.monotonic() + 20
        while not ready.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        self.assertTrue(ready.exists(), "helper did not reach live mutation")
        process.send_signal(signal.SIGINT)
        stdout, stderr = process.communicate(timeout=15)
        self.assertNotEqual(process.returncode, 0, stdout + stderr)
        time.sleep(1.5)
        self.assertFalse(late.exists(), "descendant wrote after rollback")
        self.assertFalse((self.home / "projects").exists())
        self.assertFalse((self.home / ".local/bin/paseo").exists())

    def test_coordinator_owns_cli_backup_and_replaces_nonmatching_entry(self) -> None:
        paseo = self.make_fake_paseo()
        verifier = self.make_fake_verifier()
        env = self.lifecycle_env(paseo, verifier)
        first = self.run_install(("--apply",), env)
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        cli = self.home / ".local/bin/paseo"
        cli.unlink()
        cli.write_bytes(b"operator cli\n")
        cli.chmod(0o640)
        second = self.run_install(("--apply",), env)
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        backup = Path(next(line.split("backup=", 1)[1] for line in second.stdout.splitlines() if "backup=" in line))
        saved = backup / "managed/paseo_cli"
        self.assertEqual(saved.read_bytes(), b"operator cli\n")
        self.assertEqual(saved.stat().st_mode & 0o777, 0o600)
        self.assertEqual(backup.stat().st_mode & 0o777, 0o700)
        self.assertFalse(any(path.name.startswith("paseo-cli-") for path in (self.home / ".codex-room-backups").iterdir()))
        self.assertTrue(cli.is_symlink())


class RuntimeGenerationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.canonical = self.root / "canonical"
        self.canonical.mkdir()

        (self.canonical / "config.toml").write_text(
            '\n'.join(
                [
                    'model = "base-model"',
                    'model_reasoning_effort = "low"',
                    'sandbox_mode = "read-only"',
                    'approval_policy = "on-request"',
                    '',
                    '[mcp_servers.example]',
                    'url = "https://example.invalid/mcp"',
                    '',
                    '[features]',
                    'multi_agent = true',
                    'multi_agent_v2 = true',
                    '',
                    '[agents]',
                    'enabled = true',
                    '',
                ]
            )
        )
        for role in ("supervisor", "lead", "peer"):
            shutil.copyfile(
                ROOM / "overlays" / f"{role}.config.toml",
                self.canonical / f"{role}.config.toml",
            )
        for name in ("auth.json", "AGENTS.md", "hooks.json", "model-instructions.md"):
            (self.canonical / name).write_text("{}\n" if name.endswith(".json") else "fixture\n")
        for name in ("skills", "plugins"):
            (self.canonical / name).mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_sync(self, role: str) -> Path:
        completed = self.run_sync_process(role)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return self.root / ".runtime" / role

    def run_sync_process(self, role: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["CODEX_ROOM_LAB_ROOT"] = str(self.root)
        env["CODEX_ROOM_MODEL_CATALOG"] = str(ROOT / "tests" / "fixtures" / "model-catalog.json")
        return subprocess.run(
            ["python3", str(SYNC), role],
            check=False,
            env=env,
            capture_output=True,
            text=True,
        )

    def test_all_roles_generate_isolated_configs(self) -> None:
        expected = {
            "supervisor": ("gpt-5.6-sol", "medium"),
            "lead": ("gpt-5.6-sol", "medium"),
            "peer": ("gpt-5.6-sol", "medium"),
        }
        for role, (model, effort) in expected.items():
            runtime = self.run_sync(role)
            config = (runtime / "config.toml").read_text()
            self.assertIn(f'model = "{model}"', config)
            self.assertIn(f'model_reasoning_effort = "{effort}"', config)
            self.assertIn("multi_agent = false", config)
            self.assertIn("multi_agent_v2 = false", config)
            self.assertIn("[agents]\nenabled = false", config)
            for name in ("auth.json", "AGENTS.md", "hooks.json", "skills", "plugins"):
                self.assertTrue((runtime / name).is_symlink())
                self.assertEqual((runtime / name).resolve(), (self.canonical / name).resolve())
            self.assertEqual(
                (runtime / "model-instructions.md").resolve(),
                (self.canonical / "model-instructions.md").resolve(),
            )
            self.assertFalse((runtime / "ANTI_PATTERNS.md").exists())
            self.assertFalse((runtime / "SUPERVISOR_NOTEBOOK.md").exists())
            self.assertFalse((runtime / "WORKSPACE_PROTOCOL.md").exists())
            catalog = json.loads((runtime / "model-catalog.no-native-agents.json").read_text())
            self.assertTrue(all(model["multi_agent_version"] is None for model in catalog["models"]))
        self.assertEqual(
            sorted(path.name for path in (self.root / ".runtime").iterdir()),
            ["lead", "peer", "supervisor"],
        )

    def test_repeated_generation_preserves_role_isolation_and_legacy_trees(self) -> None:
        legacy = {}
        for role in ("review", "harness"):
            runtime = self.root / ".runtime" / role
            runtime.mkdir(parents=True)
            (runtime / "config.toml").write_text(f"private {role}\n")
            (runtime / "state.sqlite").write_bytes(b"private\x00state")
            legacy[role] = {
                str(path.relative_to(runtime)): path.read_bytes()
                for path in runtime.rglob("*") if path.is_file()
            }

        first_configs = {}
        for role in ("supervisor", "lead", "peer"):
            runtime = self.run_sync(role)
            first_configs[role] = (runtime / "config.toml").read_bytes()
        for role in ("supervisor", "lead", "peer"):
            runtime = self.run_sync(role)
            self.assertEqual((runtime / "config.toml").read_bytes(), first_configs[role])
            self.assertEqual((runtime / "plugins").resolve(), (self.canonical / "plugins").resolve())

        for role, before in legacy.items():
            runtime = self.root / ".runtime" / role
            after = {
                str(path.relative_to(runtime)): path.read_bytes()
                for path in runtime.rglob("*") if path.is_file()
            }
            self.assertEqual(after, before)

    def test_generator_rejects_legacy_roles_without_mutation(self) -> None:
        for role in ("review", "harness"):
            runtime = self.root / ".runtime" / role
            runtime.mkdir(parents=True)
            marker = runtime / "private"
            marker.write_bytes(b"unchanged\x00")
            completed = self.run_sync_process(role)
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("usage:", completed.stderr)
            self.assertEqual(marker.read_bytes(), b"unchanged\x00")

    def test_sync_and_normal_launcher_reject_redirected_active_role(self) -> None:
        redirected = self.root / "redirected-lead"
        redirected.mkdir()
        marker = redirected / "private"
        marker.write_bytes(b"do not touch\x00")
        runtime_root = self.root / ".runtime"
        runtime_root.mkdir()
        (runtime_root / "lead").symlink_to(redirected, target_is_directory=True)

        direct = self.run_sync_process("lead")
        self.assertNotEqual(direct.returncode, 0)
        self.assertIn("runtime role directory must not be a symlink", direct.stderr)
        self.assertEqual(marker.read_bytes(), b"do not touch\x00")

        codex_marker = self.root / "codex-was-launched"
        fake_codex = self.root / "fake-codex"
        fake_codex.write_text(f"#!/bin/sh\ntouch '{codex_marker}'\n")
        fake_codex.chmod(0o755)
        env = {
            **os.environ,
            "CODEX_ROOM_LAB_ROOT": str(self.root),
            "CODEX_ROOM_SYNC_BIN": str(SYNC),
            "CODEX_ROOM_MODEL_CATALOG": str(ROOT / "tests/fixtures/model-catalog.json"),
            "CODEX_BIN": str(fake_codex),
        }
        launched = subprocess.run(
            [str(LAUNCHER), "lead"], env=env, capture_output=True, text=True
        )
        self.assertEqual(launched.returncode, 2)
        self.assertIn("runtime role directory must not be a symlink", launched.stderr)
        self.assertFalse(codex_marker.exists())
        self.assertEqual(marker.read_bytes(), b"do not touch\x00")

        (runtime_root / "lead").unlink()
        (runtime_root / "lead").mkdir()
        swapping_sync = self.root / "swapping-sync"
        swapping_sync.write_text(
            "#!/usr/bin/env python3\n"
            "import os, pathlib\n"
            "role_home = pathlib.Path(os.environ['ROLE_HOME'])\n"
            "role_home.rmdir()\n"
            "role_home.symlink_to(os.environ['REDIRECT_TARGET'], target_is_directory=True)\n"
        )
        swapping_sync.chmod(0o755)
        env.update(
            {
                "CODEX_ROOM_SYNC_BIN": str(swapping_sync),
                "ROLE_HOME": str(runtime_root / "lead"),
                "REDIRECT_TARGET": str(redirected),
            }
        )
        swapped = subprocess.run(
            [str(LAUNCHER), "lead"], env=env, capture_output=True, text=True
        )
        self.assertEqual(swapped.returncode, 2)
        self.assertIn("runtime role directory became a symlink", swapped.stderr)
        self.assertFalse(codex_marker.exists())
        self.assertEqual(marker.read_bytes(), b"do not touch\x00")

    def test_sync_runs_without_workflow_assets_and_preserves_private_files(self) -> None:
        runtime = self.root / ".runtime" / "lead"
        runtime.mkdir(parents=True)
        private_notebook = runtime / "SUPERVISOR_NOTEBOOK.md"
        private_notebook.write_bytes(b"private notebook\x00")
        private_workflow = runtime / "ANTI_PATTERNS.md"
        private_workflow_target = self.root / "private-workflow.md"
        private_workflow_target.write_bytes(b"private workflow\x00")
        private_workflow.symlink_to(private_workflow_target)

        self.run_sync("lead")

        self.assertEqual(private_notebook.read_bytes(), b"private notebook\x00")
        self.assertTrue(private_workflow.is_symlink())
        self.assertEqual(private_workflow.resolve(), private_workflow_target.resolve())
        self.assertEqual(private_workflow.read_bytes(), b"private workflow\x00")

    def test_supervisor_keeps_mcp_servers_without_initializing_notebook(self) -> None:
        runtime = self.run_sync("supervisor")
        self.assertIn("[mcp_servers.example]", (runtime / "config.toml").read_text())
        self.assertFalse((runtime / "SUPERVISOR_NOTEBOOK.md").exists())

if __name__ == "__main__":
    unittest.main()
