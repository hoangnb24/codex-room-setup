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

    def test_container_base_and_pinned_public_install_are_pinned(self) -> None:
        self.assertRegex(
            self.dockerfile,
            r"(?m)^FROM mcr\.microsoft\.com/devcontainers/javascript-node:1-22-bookworm@sha256:[0-9a-f]{64}$",
        )
        self.assertIn('"$source_root/install" --apply', self.accept)
        self.assertIn("PUBLIC_INSTALL_PASS fresh", self.accept)
        self.assertIn("PUBLIC_INSTALL_PASS repeated", self.accept)
        self.assertIn("tests/fixtures/model-catalog.json", self.accept)
        self.assertIn('"$source_root/install" --verify', self.accept)
        self.assertIn("PUBLIC_PLAN_READ_ONLY_OK", self.accept)
        self.assertIn("live_inventory_is_fake", self.accept)

    def test_acceptance_script_covers_frozen_invariants(self) -> None:
        signals = (
            "lead peer supervisor",
            'codex-lead","codex-peer","codex-supervisor',
            'codex-supervisor","codex-lead',
            "for legacy_role in review harness",
            'review/sessions/private.jsonl',
            'harness/state.sqlite',
            'sessions/live.jsonl',
            "operator or session marker bytes changed",
            'CODEX_ROOM_VERIFY_BIN="$fake_bin/verify-installed"',
            "CONTAINER_ACCEPTANCE_OK",
            "RUNTIME_TREE",
        )
        for signal in signals:
            with self.subTest(signal=signal):
                self.assertIn(signal, self.accept)

    def test_installed_launcher_addresses_every_retained_role(self) -> None:
        self.assertRegex(
            self.accept,
            r'for role in supervisor lead peer; do\n  if ! "\$fake_home/\.local/bin/codex-room" "\$role"; then',
        )
        self.assertIn("installed launcher failed for retained role", self.accept)
        self.assertIn('printf \'%s\\n\' "$role_home"', self.accept)
        self.assertIn('mapfile -t launched_homes <"$CODEX_LAUNCH_LOG"', self.accept)
        self.assertIn('"$fake_home/.codex-runtime/supervisor"', self.accept)
        self.assertIn('"$fake_home/.codex-runtime/lead"', self.accept)
        self.assertIn('"$fake_home/.codex-runtime/peer"', self.accept)
        self.assertIn("installed launcher did not address each expected retained CODEX_HOME exactly once", self.accept)

    def test_paseo_commit_comes_from_the_authoritative_manifest(self) -> None:
        self.assertRegex(
            self.accept,
            r"expected_paseo_commit=\$\(awk .* \"\$source_root/paseo/source\.toml\"\)",
        )
        self.assertIn("verified_commit is missing or malformed", self.accept)
        self.assertNotRegex(self.accept, r"\b8511089eaeb06cddd049b629562926822020de5c\b")


if __name__ == "__main__":
    unittest.main()
