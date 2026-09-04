from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ContainerAcceptanceInterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.makefile = (ROOT / "Makefile").read_text()
        cls.runner = (ROOT / "tests/container/run").read_text()
        cls.accept = (ROOT / "tests/container/accept").read_text()
        cls.dockerfile = (ROOT / "tests/container/Dockerfile").read_text()

    def test_public_command_uses_a_read_only_source_mount(self) -> None:
        self.assertRegex(self.makefile, r"(?m)^test-container:\n\t\./tests/container/run$")
        self.assertIn("dst=/workspace,readonly", self.runner)
        self.assertNotRegex(self.runner, r"(?:\$HOME|~/|/Users/|\.codex)")

    def test_container_base_and_real_bootstrap_are_pinned(self) -> None:
        self.assertRegex(
            self.dockerfile,
            r"(?m)^FROM mcr\.microsoft\.com/devcontainers/javascript-node:1-22-bookworm@sha256:[0-9a-f]{64}$",
        )
        self.assertIn('"$source_root/scripts/bootstrap" --apply', self.accept)
        self.assertIn("for pass in fresh repeated", self.accept)
        self.assertIn("tests/fixtures/model-catalog.json", self.accept)

    def test_acceptance_script_covers_frozen_invariants(self) -> None:
        signals = (
            "lead peer supervisor",
            'codex-lead","codex-peer","codex-supervisor',
            'codex-supervisor","codex-lead',
            "for legacy_role in review harness",
            "operator or legacy marker bytes changed",
            'CODEX_ROOM_VERIFY_BIN="$fake_bin/verify-installed"',
            "CONTAINER_ACCEPTANCE_OK",
            "RUNTIME_TREE",
        )
        for signal in signals:
            with self.subTest(signal=signal):
                self.assertIn(signal, self.accept)


if __name__ == "__main__":
    unittest.main()
