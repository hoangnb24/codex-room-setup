# Fork dependencies

This setup relies on Paseo behavior for:

- Derived providers using `extends`.
- Per-provider command replacement.
- Replacement model lists and `isDefault` selection.
- Provider-specific MCP injection allowlists.
- Codex app-server model and thinking controls.
- Local Desktop and daemon operation from the source checkout.

When rebasing onto upstream, verify these behaviors with this repository's tests and `scripts/verify --live`.

