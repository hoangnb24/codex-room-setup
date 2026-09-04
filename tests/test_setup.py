from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import re


ROOT = Path(__file__).resolve().parents[1]
HOME_MIRROR = ROOT / "home"
ROOM = HOME_MIRROR / ".config" / "codex-room"
PASEO_TEMPLATE = HOME_MIRROR / ".paseo" / "config.json.template"
SYNC = HOME_MIRROR / ".local" / "bin" / "codex-room-sync"
LAUNCHER = HOME_MIRROR / ".local" / "bin" / "codex-room"
SYNC_ALL = ROOT / "scripts" / "sync-all"
SESSION_USAGE = ROOT / "scripts" / "session-usage"
WORKFLOW_PILOT_REPORT = ROOT / "scripts" / "workflow-pilot-report"


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
            self.assertIn("FRONTIER_BRIEF v1", protocol.read_text())
            notebook = fake_home / ".config" / "codex-room" / "workflow" / "SUPERVISOR_NOTEBOOK.md"
            notebook.write_text("# Runtime learning\n")
            second_install = subprocess.run(
                [str(ROOT / "scripts" / "install"), "--apply"],
                check=True,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(notebook.read_text(), "# Runtime learning\n")
            self.assertIn("PRESERVED  ~/.config/codex-room/workflow/SUPERVISOR_NOTEBOOK.md", second_install.stdout)
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

    def test_bootstrap_core_path_does_not_require_ocr_or_harness(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bin_dir = root / "bin"
            log = root / "actions.log"
            component = self.executable(
                bin_dir / "component",
                "#!/bin/sh\nprintf '%s\\n' \"$*\" >> \"$ACTION_LOG\"\n",
            )
            for command_name in ("codex", "git", "jq", "node", "npm", "python3"):
                self.executable(bin_dir / command_name, "#!/bin/sh\nexit 0\n")
            env = {
                **os.environ,
                "HOME": str(root / "home"),
                "PATH": str(bin_dir) + ":/usr/bin:/bin",
                "ACTION_LOG": str(log),
                "PASEO_INSTALL_BIN": str(component),
                "CODEX_ROOM_INSTALL_BIN": str(component),
                "CODEX_ROOM_SYNC_ALL_BIN": str(component),
                "CODEX_ROOM_VERIFY_BIN": str(component),
            }
            completed = subprocess.run(
                [str(ROOT / "scripts/bootstrap"), "--apply"],
                env=env, capture_output=True, text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(log.read_text().splitlines(), ["--preflight", "--apply", "", "", ""])
            self.assertNotIn("ocr", completed.stdout + completed.stderr)
            self.assertNotIn("harness", completed.stdout.lower() + completed.stderr.lower())

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
        harness_source = (ROOT / "better-harness" / "source.toml").read_text()
        harness_guide = (ROOT / "docs" / "better-harness-role.md").read_text()
        updater = (HOME_MIRROR / ".local" / "bin" / "paseo-local-update").read_text()

        self.assertIn('fork = "git@github.com:hoangnb24/paseo.git"', paseo_source)
        self.assertIn(
            'verified_commit = "8511089eaeb06cddd049b629562926822020de5c"',
            paseo_source,
        )
        self.assertIn(
            'fork = "https://github.com/hoangnb24/better-harness.git"',
            harness_source,
        )
        self.assertIn(
            'verified_commit = "ef5253ca2e201d46a7071c3fc9c1de7237d3f86c"',
            harness_source,
        )
        self.assertIn("github.com/hoangnb24/better-harness.git", harness_guide)
        self.assertNotIn("github.com/QoderAI/better-harness.git \\", harness_guide)
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

    def legacy_bootstrap_preflights_before_mutation_and_rolls_back_harness(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); bin_dir = root / "bin"; log = root / "actions.log"
            runtime = root / "runtime"; harness = runtime / "harness"; harness.mkdir(parents=True)
            (harness / "state").write_text("prior\n")
            component = self.executable(
                bin_dir / "component",
                "#!/bin/sh\nprintf 'component %s\\n' \"$*\" >> \"$ACTION_LOG\"\n"
            )
            verify = self.executable(bin_dir / "verify", "#!/bin/sh\necho verify >> \"$ACTION_LOG\"\n")
            sync = self.executable(
                bin_dir / "sync",
                "#!/bin/sh\nprintf 'sync %s\\n' \"$*\" >> \"$ACTION_LOG\"\n"
                "mkdir -p \"$LIVE_HOME\"\nprintf 'mutated\\n' > \"$LIVE_HOME/state\"\n"
            )
            self.executable(bin_dir / "ocr", "#!/bin/sh\necho 'open-code-review v0.0.0'\n")
            npm = self.executable(bin_dir / "npm", "#!/bin/sh\nprintf 'npm %s\\n' \"$*\" >> \"$ACTION_LOG\"\n")
            self.executable(bin_dir / "node", "#!/bin/sh\nexit 0\n")
            self.executable(
                bin_dir / "codex",
                "#!/usr/bin/env python3\n"
                "import json, os, pathlib, sys\n"
                "home=pathlib.Path(os.environ['CODEX_HOME']); root=home/'market-root'\n"
                "args=sys.argv[1:]\n"
                "if args[:3] == ['plugin','marketplace','add']:\n root.mkdir(parents=True,exist_ok=True); print('{}')\n"
                "elif args[:3] == ['plugin','marketplace','list']:\n print(json.dumps({'marketplaces':[{'name':'better-harness','root':str(root),'marketplaceSource':{'sourceType':'git','source':'https://github.com/hoangnb24/better-harness.git'}}]}))\n"
                "elif args[:2] == ['plugin','add']:\n"
                " print('{}') if str(home) != os.environ['LIVE_HOME'] else sys.exit(23)\n"
                "elif args[:2] == ['plugin','list']:\n print(json.dumps({'installed':[{'pluginId':'better-harness@better-harness','installed':True,'enabled':True}], 'available':[]}))\n"
                "else: print('{}')\n"
            )
            self.executable(
                bin_dir / "git",
                "#!/bin/sh\ncase \"$2\" in */market-root) echo ef5253ca2e201d46a7071c3fc9c1de7237d3f86c ;; *) exec /usr/bin/git \"$@\" ;; esac\n"
            )
            env = os.environ.copy()
            env.update({
                "HOME": str(root / "home"), "PATH": str(bin_dir) + os.pathsep + env["PATH"],
                "ACTION_LOG": str(log), "LIVE_HOME": str(harness), "CODEX_ROOM_RUNTIME_ROOT": str(runtime),
                "PASEO_INSTALL_BIN": str(component), "CODEX_ROOM_INSTALL_BIN": str(component),
                "CODEX_ROOM_SYNC_ALL_BIN": str(sync), "CODEX_ROOM_VERIFY_BIN": str(verify),
                "CODEX_ROOM_NPM_BIN": str(npm),
            })
            failed = subprocess.run([str(ROOT / "scripts/bootstrap"), "--apply"], env=env, capture_output=True, text=True)
            self.assertNotEqual(failed.returncode, 0)
            self.assertEqual((harness / "state").read_text(), "prior\n")
            actions = log.read_text().splitlines()
            self.assertEqual(actions[0], "component --preflight")
            self.assertIn("npm install --global @alibaba-group/open-code-review@1.11.0", actions)
            self.assertLess(actions.index("component --preflight"), actions.index("npm install --global @alibaba-group/open-code-review@1.11.0"))
            self.assertNotIn("verify", actions)

            rejecting = self.executable(
                bin_dir / "rejecting-paseo",
                "#!/bin/sh\nprintf 'rejecting %s\\n' \"$*\" >> \"$ACTION_LOG\"\n"
                "[ \"${1:-}\" != --preflight ] || exit 41\n"
            )
            log.unlink()
            env["PASEO_INSTALL_BIN"] = str(rejecting)
            failed_preflight = subprocess.run([str(ROOT / "scripts/bootstrap"), "--apply"], env=env, capture_output=True, text=True)
            self.assertNotEqual(failed_preflight.returncode, 0)
            self.assertEqual(log.read_text().splitlines(), ["rejecting --preflight"])
            self.assertEqual((harness / "state").read_text(), "prior\n")

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
                "PATH": str(bin_dir) + os.pathsep + env["PATH"],
            })
            completed = subprocess.run([str(ROOT / "scripts/verify")], env=env, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertIn("OK    Paseo CLI links to local fork", completed.stdout)
            self.assertFalse((root / "ocr.log").exists())
            self.assertEqual((runtime / "review/private").read_text(), "must remain ignored\n")
            self.assertEqual((runtime / "harness/private").read_text(), "must remain ignored\n")

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

    def test_launcher_resolves_only_a_direct_role_home_without_sync(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            runtime_root = Path(temporary) / "runtime"
            lead_home = runtime_root / "lead"
            lead_home.mkdir(parents=True)
            env = os.environ.copy()
            env.update(
                {
                    "CODEX_ROOM_RUNTIME_ROOT": str(runtime_root),
                    "CODEX_ROOM_SYNC_BIN": str(Path(temporary) / "must-not-run"),
                }
            )

            completed = subprocess.run(
                [str(LAUNCHER), "--resolve-evidence-home", "lead"],
                check=True,
                env=env,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.stdout.strip(), str(lead_home.resolve()))

    def test_launcher_rejects_redirected_evidence_role_home(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime_root = root / "runtime"
            runtime_root.mkdir()
            redirected = root / "redirected-lead"
            redirected.mkdir()
            (runtime_root / "lead").symlink_to(redirected, target_is_directory=True)
            env = os.environ.copy()
            env["CODEX_ROOM_RUNTIME_ROOT"] = str(runtime_root)

            completed = subprocess.run(
                [str(LAUNCHER), "--resolve-evidence-home", "lead"],
                check=False,
                env=env,
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("must not be a symlink", completed.stderr)

    def test_launcher_rejects_legacy_roles_on_both_routes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            env = {**os.environ, "CODEX_ROOM_RUNTIME_ROOT": str(Path(temporary) / "runtime")}
            for arguments in (("review",), ("harness",), ("--resolve-evidence-home", "review"), ("--resolve-evidence-home", "harness")):
                with self.subTest(arguments=arguments):
                    completed = subprocess.run(
                        [str(LAUNCHER), *arguments], env=env, capture_output=True, text=True
                    )
                    self.assertEqual(completed.returncode, 2)
                    self.assertIn("unknown", completed.stderr)

    def test_session_usage_reports_requests_tools_tokens_and_cost(self) -> None:
        fixture = ROOT / "tests" / "fixtures" / "session-usage.jsonl"
        completed = subprocess.run(
            [
                str(SESSION_USAGE),
                "--format",
                "json",
                "--input-rate",
                "5",
                "--cached-input-rate",
                "0.5",
                "--output-rate",
                "30",
                str(fixture),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        summary = json.loads(completed.stdout)

        self.assertEqual(summary["session_id"], "fixture-session")
        self.assertEqual(summary["timing"]["duration_ms"], 5000)
        self.assertEqual(summary["model_requests"], 2)
        self.assertEqual(summary["tools"]["invocations"], 2)
        self.assertEqual(summary["usage"]["cumulative"]["total_tokens"], 2800)
        self.assertEqual(
            summary["usage"]["final_request"]["context_window_used_tokens"],
            1700,
        )
        self.assertAlmostEqual(summary["estimated_api_cost_usd"], 0.017)

    def test_workflow_pilot_report_counts_only_assistant_markers(self) -> None:
        fixture = ROOT / "tests" / "fixtures" / "workflow-pilot.jsonl"
        completed = subprocess.run(
            [str(WORKFLOW_PILOT_REPORT), "--format", "json", str(fixture)],
            check=True,
            capture_output=True,
            text=True,
        )
        summary = json.loads(completed.stdout)

        self.assertEqual(summary["assistant_messages_scanned"], 4)
        self.assertEqual(summary["markers"]["FRONTIER_BRIEF v1"], 1)
        self.assertEqual(summary["markers"]["PLAN_RECONCILIATION v1"], 1)
        self.assertEqual(summary["peer_dispositions"]["REOPEN_REQUEST"], 1)
        self.assertEqual(summary["lead_rulings"]["REVISE_PLAN"], 1)
        self.assertEqual(summary["foundation_statuses"]["FOUNDATION_REQUIRED"], 1)
        self.assertEqual(summary["parallel_decisions"]["SERIAL"], 1)
        self.assertEqual(summary["reconciliation_plan_updates"]["yes"], 1)
        self.assertEqual(summary["warnings"], [])

    def test_workflow_pilot_contracts_are_present_in_protocol_and_roles(self) -> None:
        protocol = (ROOM / "workflow" / "WORKSPACE_PROTOCOL.md").read_text()
        for marker in (
            "FRONTIER_BRIEF v1",
            "FOUNDATION_CHECK v1",
            "PEER_DISPOSITION v1",
            "LEAD_RULING v1",
            "PLAN_RECONCILIATION v1",
            "PARALLEL_CHECK v1",
        ):
            self.assertIn(marker, protocol)

        lead = (ROOM / "overlays" / "lead.config.toml").read_text()
        peer = (ROOM / "overlays" / "peer.config.toml").read_text()
        supervisor = (ROOM / "overlays" / "supervisor.config.toml").read_text()
        self.assertIn("FOUNDATION_CHECK v1", lead)
        self.assertIn("PLAN_RECONCILIATION v1", lead)
        self.assertIn("NO_REVIEW", lead)
        self.assertIn("FAST", lead)
        self.assertIn("review_mode: EXPLORATORY | CLOSEOUT", lead)
        self.assertIn("read-only Peer", lead)
        self.assertNotIn("codex-review", lead)

        lead = (ROOM / "overlays" / "lead.config.toml").read_text()
        self.assertIn("Every\n`CLOSEOUT` brief uses `review_class: FAST`", lead)
        self.assertIn("`review_model_actual`", lead)
        self.assertIn("do not emit updates that only say no event has arrived", lead)

        self.assertIn("Review classes and close-out", protocol)
        self.assertIn("one correction batch", protocol)
        self.assertIn("PEER_DISPOSITION v1", peer)
        self.assertIn("workflow pilot", supervisor)

    def legacy_review_routing_and_ocr_boundaries(self) -> None:
        config = json.loads(PASEO_TEMPLATE.read_text().replace("@@HOME@@", "/tmp/operator"))
        providers = config["agents"]["providers"]
        self.assertIn("codex-review", providers)
        self.assertNotIn("codex-ocr", providers)
        self.assertNotIn("codex-review", config["daemon"]["mcp"]["injectIntoProviders"])

        lead = (ROOM / "overlays" / "lead.config.toml").read_text()
        lead_words = " ".join(lead.split())
        self.assertIn("Use `NO_REVIEW` for tiny or low-risk work", lead_words)
        self.assertIn("Use a read-only ordinary Peer", lead_words)
        self.assertIn("Lead never runs OCR", lead_words)
        self.assertIn("Use `codex-review` only for an OCR-assisted review", lead_words)
        self.assertIn("Review returns `DEPENDENCY_REQUEST` and stops if any command fails", lead_words)
        self.assertIn("any result is empty or malformed", lead_words)
        self.assertIn("a file or rule selection is invalid", lead_words)
        self.assertIn(
            "result cannot be independently reconciled with the candidate and contract",
            lead_words,
        )
        self.assertIn("Do not substitute a manual or non-OCR", lead_words)
        self.assertIn(
            "one exploratory batch, one correction batch, and one bounded close-out",
            lead_words,
        )
        self.assertIn("does not use OCR by default", lead_words)

        peer = (ROOM / "overlays" / "peer.config.toml").read_text()
        self.assertIn("system-level macro judgment", " ".join(peer.split()))
        self.assertNotIn("ocr", peer.lower())
        self.assertNotIn("open code review", peer.lower())

        review = (ROOM / "overlays" / "review.config.toml").read_text()
        command_check = review.index("`command -v ocr`")
        preview = review.index("`ocr delegate preview`", command_check)
        rule = review.index("`ocr delegate rule`", preview)
        self.assertLess(command_check, preview)
        self.assertLess(preview, rule)
        review_words = " ".join(review.split())
        self.assertIn("If any command fails, return `DEPENDENCY_REQUEST`", review_words)
        self.assertIn("command result is empty or malformed", review_words)
        self.assertIn("file or rule selection is invalid", review_words)
        self.assertIn(
            "result cannot be independently reconciled with the stable candidate and review contract",
            review_words,
        )
        self.assertIn("Do not replace the required OCR evidence with a manual pass", review_words)
        self.assertIn("selected files, selected rules, and findings", review_words)
        self.assertIn("Do not ask Lead or the user to run them", review_words)
        self.assertIn("Do not invoke OCR by default in `CLOSEOUT` mode", review_words)
        self.assertIn("Behavioral read-only", review_words)
        self.assertIn("Do not start a third loop automatically", review_words)

    def legacy_harness_maps_exactly_three_read_only_better_harness_lanes(self) -> None:
        harness = (ROOM / "overlays" / "harness.config.toml").read_text()
        harness_words = " ".join(harness.split())
        self.assertIn("exactly three fresh `codex-peer` seats", harness_words)
        self.assertIn("Session Evidence", harness)
        self.assertIn("Project Harness Evidence", harness)
        self.assertIn("Agent Customize Evidence", harness)
        self.assertIn("codex-room --resolve-evidence-home <role>", harness)
        self.assertIn("--codex-home <resolved-absolute-home>", harness)
        self.assertIn("$better-harness:better-harness", harness)
        self.assertIn("inline/no-files", harness)
        self.assertIn("Do not pass `--include-memories` or `--include-user-home` by default", harness_words)
        self.assertIn("A Peer must not delegate", harness_words)
        self.assertIn("use OCR", harness_words)
        self.assertIn("edit project files", harness_words)

    def test_lead_review_is_pull_based(self) -> None:
        lead = (ROOM / "overlays" / "lead.config.toml").read_text()
        expected = """
            Review is pull-based. A new diff, commit, frontier, or completed Peer task is
            not itself a review trigger. Dispatch independent review only when its result
            can change the next technical decision and deterministic checks cannot answer
            the concern more cheaply. Review a premise early when a wrong choice would lock
            architecture or lifecycle. Before an irreversible or owner-gated action,
            review only when material residual risk remains after owning checks. Otherwise,
            batch related work at one stable integration or acceptance boundary.
        """
        self.assertIn(" ".join(expected.split()), " ".join(lead.split()))

class RuntimeGenerationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.canonical = self.root / "canonical"
        self.workflow = self.root / "room-workflow"
        self.canonical.mkdir()
        self.workflow.mkdir()

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
        for name in ("WORKSPACE_PROTOCOL.md", "ANTI_PATTERNS.md", "SUPERVISOR_NOTEBOOK.md"):
            (self.workflow / name).write_text(f"# {name}\n")

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
            self.assertEqual(
                (runtime / "ANTI_PATTERNS.md").resolve(),
                (self.workflow / "ANTI_PATTERNS.md").resolve(),
            )
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

    def legacy_review_strips_mcp_servers(self) -> None:
        runtime = self.run_sync("review")
        self.assertNotIn("[mcp_servers.", (runtime / "config.toml").read_text())

    def legacy_harness_strips_inherited_mcp_servers(self) -> None:
        runtime = self.run_sync("harness")
        self.assertNotIn("[mcp_servers.", (runtime / "config.toml").read_text())

    def test_sync_removes_legacy_workspace_protocol_link(self) -> None:
        runtime = self.root / ".runtime" / "lead"
        runtime.mkdir(parents=True)
        (runtime / "WORKSPACE_PROTOCOL.md").symlink_to(
            self.workflow / "WORKSPACE_PROTOCOL.md"
        )

        self.run_sync("lead")

        self.assertFalse((runtime / "WORKSPACE_PROTOCOL.md").exists())

    def test_supervisor_keeps_mcp_servers_and_initializes_notebook(self) -> None:
        runtime = self.run_sync("supervisor")
        self.assertIn("[mcp_servers.example]", (runtime / "config.toml").read_text())
        self.assertTrue((runtime / "SUPERVISOR_NOTEBOOK.md").is_file())

    def legacy_harness_migrates_only_expected_canonical_plugins_symlink(self) -> None:
        runtime = self.root / ".runtime" / "harness"
        runtime.mkdir(parents=True)
        (runtime / "plugins").symlink_to(self.canonical / "plugins", target_is_directory=True)

        self.run_sync("harness")

        self.assertTrue((runtime / "plugins").is_dir())
        self.assertFalse((runtime / "plugins").is_symlink())

    def legacy_harness_generation_failure_preserves_expected_plugins_symlink(self) -> None:
        runtime = self.root / ".runtime" / "harness"
        runtime.mkdir(parents=True)
        plugins = runtime / "plugins"
        plugins.symlink_to(self.canonical / "plugins", target_is_directory=True)
        shutil.rmtree(self.canonical / "skills")

        completed = self.run_sync_process("harness")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("shared target does not exist", completed.stderr)
        self.assertTrue(plugins.is_symlink())
        self.assertEqual(plugins.resolve(), (self.canonical / "plugins").resolve())

    def legacy_harness_config_write_failure_preserves_expected_plugins_symlink(self) -> None:
        runtime = self.root / ".runtime" / "harness"
        runtime.mkdir(parents=True)
        plugins = runtime / "plugins"
        plugins.symlink_to(self.canonical / "plugins", target_is_directory=True)
        (runtime / "config.toml").mkdir()

        completed = self.run_sync_process("harness")

        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue((runtime / "model-catalog.no-native-agents.json").is_file())
        self.assertTrue(plugins.is_symlink())
        self.assertEqual(plugins.resolve(), (self.canonical / "plugins").resolve())

    def legacy_harness_rejects_unexpected_plugin_paths(self) -> None:
        for kind in ("unexpected-symlink", "file"):
            with self.subTest(kind=kind):
                runtime = self.root / ".runtime" / "harness"
                if runtime.exists():
                    shutil.rmtree(runtime)
                runtime.mkdir(parents=True)
                plugins = runtime / "plugins"
                if kind == "unexpected-symlink":
                    unexpected = self.root / "unexpected-plugins"
                    unexpected.mkdir(exist_ok=True)
                    plugins.symlink_to(unexpected, target_is_directory=True)
                    expected_error = "refusing to replace unexpected runtime symlink"
                else:
                    plugins.write_text("not a directory\n")
                    expected_error = "refusing to replace non-directory runtime path"

                completed = self.run_sync_process("harness")

                self.assertNotEqual(completed.returncode, 0)
                self.assertIn(expected_error, completed.stderr)
                if kind == "unexpected-symlink":
                    self.assertTrue(plugins.is_symlink())
                else:
                    self.assertEqual(plugins.read_text(), "not a directory\n")

    def legacy_harness_preserves_private_plugins_across_repeated_sync(self) -> None:
        runtime = self.run_sync("harness")
        marker = runtime / "plugins" / "installed-plugin.marker"
        marker.write_text("preserve me\n")
        (runtime / "plugins").chmod(0o755)

        self.run_sync("harness")

        self.assertEqual(marker.read_text(), "preserve me\n")
        self.assertFalse((runtime / "plugins").is_symlink())
        self.assertEqual((runtime / "plugins").stat().st_mode & 0o777, 0o700)

    def legacy_harness_preserves_only_better_harness_registration(self) -> None:
        runtime = self.run_sync("harness")
        config = runtime / "config.toml"
        config.write_text(
            config.read_text().rstrip()
            + """

[marketplaces.better-harness]
source_type = "git"
source = "https://github.com/QoderAI/better-harness.git"
ref = "audited-commit"

[plugins."better-harness@better-harness"]
enabled = true

[marketplaces.unrelated]
source_type = "git"
source = "https://example.invalid/unrelated.git"

[plugins."unrelated@unrelated"]
enabled = true

[mcp_servers.runtime-only]
url = "https://example.invalid/runtime-mcp"
"""
        )

        self.run_sync("harness")
        first = config.read_text()
        self.run_sync("harness")
        repeated = config.read_text()

        self.assertEqual(repeated, first)
        self.assertEqual(first.count("[marketplaces.better-harness]"), 1)
        self.assertEqual(first.count('[plugins."better-harness@better-harness"]'), 1)
        self.assertIn('ref = "audited-commit"', first)
        self.assertIn("enabled = true", first)
        self.assertNotIn("marketplaces.unrelated", first)
        self.assertNotIn('plugins."unrelated@unrelated"', first)
        self.assertNotIn("mcp_servers.", first)
        self.assertIn("[agents]\nenabled = false", first)
        self.assertIn("multi_agent = false", first)
        self.assertIn("multi_agent_v2 = false", first)
        self.assertEqual((runtime / "plugins").stat().st_mode & 0o777, 0o700)

    def legacy_harness_sync_does_not_synthesize_registration(self) -> None:
        runtime = self.run_sync("harness")
        config = (runtime / "config.toml").read_text()

        self.assertNotIn("[marketplaces.better-harness]", config)
        self.assertNotIn('[plugins."better-harness@better-harness"]', config)

    def legacy_fresh_config_registration_takes_precedence_without_duplication(self) -> None:
        canonical_config = self.canonical / "config.toml"
        canonical_config.write_text(
            canonical_config.read_text().rstrip()
            + """

[marketplaces.better-harness]
source_type = "git"
source = "https://example.invalid/canonical.git"

[plugins."better-harness@better-harness"]
enabled = false
"""
        )
        runtime = self.root / ".runtime" / "harness"
        runtime.mkdir(parents=True)
        (runtime / "config.toml").write_text(
            """[marketplaces.better-harness]
source_type = "git"
source = "https://example.invalid/stale.git"

[plugins."better-harness@better-harness"]
enabled = true
"""
        )

        self.run_sync("harness")

        generated = (runtime / "config.toml").read_text()
        self.assertEqual(generated.count("[marketplaces.better-harness]"), 1)
        self.assertEqual(generated.count('[plugins."better-harness@better-harness"]'), 1)
        self.assertIn('source = "https://example.invalid/canonical.git"', generated)
        self.assertNotIn("stale.git", generated)

    def legacy_other_role_does_not_preserve_better_harness_registration(self) -> None:
        runtime = self.run_sync("lead")
        config = runtime / "config.toml"
        config.write_text(
            config.read_text().rstrip()
            + """

[marketplaces.better-harness]
source_type = "git"
source = "https://github.com/QoderAI/better-harness.git"

[plugins."better-harness@better-harness"]
enabled = true
"""
        )

        self.run_sync("lead")

        regenerated = config.read_text()
        self.assertNotIn("[marketplaces.better-harness]", regenerated)
        self.assertNotIn('[plugins."better-harness@better-harness"]', regenerated)


if __name__ == "__main__":
    unittest.main()
