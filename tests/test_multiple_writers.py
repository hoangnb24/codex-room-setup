from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class MultipleWriterGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.readme = (ROOT / "README.md").read_text().casefold()
        cls.pilot = (ROOT / "docs" / "workflow-pilot.md").read_text().casefold()
        cls.operations = (ROOT / "docs" / "operations.md").read_text().casefold()
        protocol = (
            ROOT / "home" / ".config" / "codex-room" / "workflow" / "WORKSPACE_PROTOCOL.md"
        ).read_text()
        lead_config = (
            ROOT / "home" / ".config" / "codex-room" / "overlays" / "lead.config.toml"
        ).read_text()
        cls.protocol = " ".join(protocol.casefold().split())
        cls.lead_config = " ".join(lead_config.casefold().split())

    def assert_signals(self, document: str, signals: tuple[str, ...]) -> None:
        for signal in signals:
            with self.subTest(signal=signal):
                self.assertIn(signal.casefold(), document)

    def test_readme_exposes_the_capability_and_runbook(self) -> None:
        self.assert_signals(
            self.readme,
            (
                "guarded multiple-writer operation",
                "at most two writers",
                "docs/workflow-pilot.md#guarded-multiple-writer-pilot",
                "docs/operations.md#run-the-guarded-multiple-writer-pilot",
            ),
        )

    def test_pilot_preserves_admission_and_evidence_contract(self) -> None:
        self.assert_signals(
            self.pilot,
            (
                "positive gate",
                "default is `serial`",
                "maximum is two concurrent writers per repository",
                "unknown or unverified condition resolves to `serial`",
                "same exact base commit",
                "separate git worktree",
                "physical write scopes",
                "logical responsibilities",
                "frozen contract",
                "shared integration surface",
                "immutable commit",
                "current accepted tip",
                "focused proof",
                "composed proof",
                "velocity gain",
                "without more correction",
            ),
        )

    def test_pilot_states_isolation_and_enforcement_limits(self) -> None:
        self.assert_signals(
            self.pilot,
            (
                "worktree isolation prevents two processes from writing the same checkout",
                "does not prove logical independence",
                "prompt-level policy",
                "does not atomically reserve scopes",
                "at least two comparable misses",
            ),
        )

    def test_operations_contains_a_concrete_serial_integration_runbook(self) -> None:
        self.assert_signals(
            self.operations,
            (
                "git rev-parse head",
                "shasum -a 256",
                "create_workspace",
                'isolation: "worktree"',
                "returned `workspaceid` and `cwd`",
                "exact `base` commit",
                "diff-tree --no-commit-id --name-only",
                'git cherry-pick "$candidate_a"',
                'git cherry-pick "$candidate_b"',
                "focused and composed",
                "two comparable misses",
            ),
        )
        self.assertNotIn("git worktree add", self.operations)

    def test_authoritative_sources_preserve_multiple_writer_guards(self) -> None:
        sources = {
            "workspace protocol": (
                self.protocol,
                (
                    "positive opportunity gate",
                    "unknown or incomplete evidence means `serial`",
                    "no repository may have more than two concurrent writers",
                    "same exact base commit",
                    "one isolated worktree per writer",
                    "`candidate_identity` is an immutable commit",
                    "current accepted integration tip",
                    "one at a time",
                ),
            ),
            "lead config": (
                self.lead_config,
                (
                    "positive opportunity gate",
                    "unknown or incomplete evidence means `serial`",
                    "never run more than two writers concurrently in one repository",
                    "same exact base commit",
                    "separate isolated worktree",
                    "immutable candidate commit",
                    "current accepted integration tip",
                    "one at a time",
                ),
            ),
        }
        for source, (document, signals) in sources.items():
            with self.subTest(source=source):
                self.assert_signals(document, signals)


if __name__ == "__main__":
    unittest.main()
