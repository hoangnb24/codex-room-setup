# All known providers need an explicit policy: upstream defaults to enabled.
.daemon.mcp.enabled == true and
.daemon.mcp.injectIntoAgents == true and
(.daemon.mcp | has("injectIntoProviders") | not) and
(.agents.providers as $providers |
  (["claude", "codex", "copilot", "opencode", "pi", "omp", "codex-peer", "codex-lead", "codex-supervisor"] |
    all(.[]; . as $id | $providers | has($id)))
) and
(.agents.providers | to_entries | all(.[];
  .value.paseoTools.enabled == (.key == "codex-supervisor" or .key == "codex-lead")
))
