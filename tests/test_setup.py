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
SESSION_USAGE = ROOT / "scripts" / "session-usage"
WORKFLOW_PILOT_REPORT = ROOT / "scripts" / "workflow-pilot-report"


class SetupShapeTests(unittest.TestCase):
    def test_repository_does_not_own_codex_home(self) -> None:
        self.assertFalse((HOME_MIRROR / ".codex").exists())

    def test_paseo_template_is_valid_and_has_expected_roles(self) -> None:
        config = json.loads(PASEO_TEMPLATE.read_text().replace("@@HOME@@", "/tmp/operator"))
        providers = config["agents"]["providers"]
        room_roles = sorted(name for name in providers if name.startswith("codex-"))
        self.assertEqual(
            room_roles,
            ["codex-lead", "codex-peer", "codex-review", "codex-supervisor"],
        )
        self.assertEqual(
            config["daemon"]["mcp"]["injectIntoProviders"],
            ["codex-supervisor", "codex-lead"],
        )
        self.assertEqual(
            providers["codex-review"]["command"],
            ["/tmp/operator/.local/bin/codex-room", "review"],
        )

    def test_role_defaults_are_aligned(self) -> None:
        config = json.loads(PASEO_TEMPLATE.read_text().replace("@@HOME@@", "/tmp/operator"))
        expected = {
            "supervisor": ("gpt-5.6-sol", "medium"),
            "lead": ("gpt-5.6-sol", "medium"),
            "peer": ("gpt-5.6-sol", "medium"),
            "review": ("gpt-5.6-luna", "max"),
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
            self.assertFalse((fake_home / ".codex").exists())
            self.assertFalse((fake_home / ".codex-runtime").exists())

    def test_paseo_fork_installer_links_cli(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fake_home = Path(temporary) / "home"
            checkout = Path(temporary) / "paseo"
            cli = checkout / "packages" / "cli" / "bin" / "paseo"
            cli.parent.mkdir(parents=True)
            cli.write_text("#!/usr/bin/env node\n")
            subprocess.run(["git", "init", "-q", str(checkout)], check=True)
            subprocess.run(["git", "-C", str(checkout), "add", "."], check=True)
            subprocess.run(
                [
                    "git", "-C", str(checkout),
                    "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                    "commit", "-qm", "fixture",
                ],
                check=True,
            )

            env = os.environ.copy()
            env.update(
                {
                    "HOME": str(fake_home),
                    "PASEO_REPO_DIR": str(checkout),
                    "PASEO_FORK_URL": "git@example.invalid:fork/paseo.git",
                    "PASEO_UPSTREAM_URL": "git@example.invalid:upstream/paseo.git",
                }
            )
            subprocess.run(
                [str(ROOT / "scripts" / "install-paseo-fork")],
                check=True,
                env=env,
                capture_output=True,
                text=True,
            )

            link = fake_home / ".local" / "bin" / "paseo"
            self.assertTrue(link.is_symlink())
            self.assertEqual(os.readlink(link), str(cli))

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
        self.assertIn("DEEP", lead)
        self.assertIn("DUAL", lead)
        self.assertIn("review_mode: EXPLORATORY | CLOSEOUT", lead)

        review = (ROOM / "overlays" / "review.config.toml").read_text()
        self.assertIn("review_mode: EXPLORATORY | CLOSEOUT", review)
        self.assertIn("CLOSEOUT_CLEAR", review)
        self.assertIn("CLOSEOUT_FINDINGS", review)
        self.assertIn("Do not report `CLOSEOUT_NO_FINDINGS`", review)

        lead = (ROOM / "overlays" / "lead.config.toml").read_text()
        self.assertIn("Every\n`CLOSEOUT` brief uses `review_class: FAST`", lead)
        self.assertIn("`review_model_actual`", lead)
        self.assertIn("do not emit updates that only say no event has arrived", lead)

        self.assertIn("Review classes and close-out", protocol)
        self.assertIn("one correction batch", protocol)
        self.assertIn("PEER_DISPOSITION v1", peer)
        self.assertIn("workflow pilot", supervisor)


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
        for role in ("supervisor", "lead", "peer", "review"):
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
        env = os.environ.copy()
        env["CODEX_ROOM_LAB_ROOT"] = str(self.root)
        env["CODEX_ROOM_MODEL_CATALOG"] = str(ROOT / "tests" / "fixtures" / "model-catalog.json")
        subprocess.run(["python3", str(SYNC), role], check=True, env=env, capture_output=True, text=True)
        return self.root / ".runtime" / role

    def test_all_roles_generate_isolated_configs(self) -> None:
        expected = {
            "supervisor": ("gpt-5.6-sol", "medium"),
            "lead": ("gpt-5.6-sol", "medium"),
            "peer": ("gpt-5.6-sol", "medium"),
            "review": ("gpt-5.6-luna", "max"),
        }
        for role, (model, effort) in expected.items():
            runtime = self.run_sync(role)
            config = (runtime / "config.toml").read_text()
            self.assertIn(f'model = "{model}"', config)
            self.assertIn(f'model_reasoning_effort = "{effort}"', config)
            self.assertIn("multi_agent = false", config)
            self.assertIn("multi_agent_v2 = false", config)
            self.assertTrue((runtime / "skills").is_symlink())
            self.assertTrue((runtime / "WORKSPACE_PROTOCOL.md").is_symlink())
            catalog = json.loads((runtime / "model-catalog.no-native-agents.json").read_text())
            self.assertTrue(all(model["multi_agent_version"] is None for model in catalog["models"]))

    def test_review_strips_mcp_servers(self) -> None:
        runtime = self.run_sync("review")
        self.assertNotIn("[mcp_servers.", (runtime / "config.toml").read_text())

    def test_supervisor_keeps_mcp_servers_and_initializes_notebook(self) -> None:
        runtime = self.run_sync("supervisor")
        self.assertIn("[mcp_servers.example]", (runtime / "config.toml").read_text())
        self.assertTrue((runtime / "SUPERVISOR_NOTEBOOK.md").is_file())


if __name__ == "__main__":
    unittest.main()
