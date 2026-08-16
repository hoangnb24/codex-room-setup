# Measure Codex Session Usage and Cost

Codex rollout JSONL files contain enough local telemetry to compare repository-onboarding benchmark runs without asking the agent to estimate its own usage.

Use one fresh Codex session for one benchmark prompt. This keeps elapsed time, cumulative tokens, model requests, tool calls, and findings attributable to one run.

## Quick start

Given a JSONL file:

```bash
./scripts/session-usage \
  --format json \
  /path/to/rollout-SESSION_ID.jsonl
```

Or locate it by isolated Codex Room role and session ID:

```bash
./scripts/session-usage \
  --role peer \
  --session-id 01a004a9-9790-77c2-925f-b4d18837afd6
```

Role sessions normally live under:

```text
~/.codex-runtime/<role>/sessions/YYYY/MM/DD/rollout-*.jsonl
```

`CODEX_ROOM_RUNTIME_ROOT` or `--runtime-root` can override the runtime root.

## What the script measures

| Metric | JSONL source | Meaning |
| --- | --- | --- |
| Duration | final `task_complete.duration_ms` | Wall-clock time for the completed task |
| Time to first token | final `task_complete.time_to_first_token_ms` | Delay before the first model token |
| Model requests | number of `token_count` events with usage | Completed model invocations observed in the rollout |
| Cumulative usage | final `token_count.info.total_token_usage` | Tokens processed across the task |
| Final context | final `token_count.info.last_token_usage.total_tokens` | Input plus output for the final model invocation |
| Tool invocations | `response_item` records whose type ends in `_call` | Agent-level tool calls, not UI activity lines |
| Tool outputs | `response_item` records whose type ends in `_call_output` | Recorded tool results |

The two token values answer different questions:

```text
final context     = size of the final model invocation
cumulative usage  = sum of model usage across the task
```

For example, seven model requests may use `14K`, `15K`, `20K`, `31K`, `41K`, `42K`, and `49K` tokens. Final context is `49K`; cumulative usage is about `212K`.

Cached input is a subset of input tokens. Reasoning output is a subset of output tokens. Do not add either subset to the total a second time.

## Estimate API-equivalent cost

Look up the current rates for the exact model, then pass USD rates per one million tokens:

```bash
./scripts/session-usage \
  --role peer \
  --session-id SESSION_ID \
  --input-rate 5 \
  --cached-input-rate 0.5 \
  --output-rate 30
```

The script applies:

```text
uncached input = input tokens - cached input tokens

cost =
  uncached input / 1M * uncached input rate
  + cached input / 1M * cached input rate
  + output / 1M * output rate
  + cache writes / 1M * cache-write rate
```

If the JSONL contains cache-write tokens, also supply `--cache-write-rate`. The script leaves cost unset instead of silently undercounting when that rate is missing.

Rates are deliberately not hard-coded. Pricing changes, different models have different rates, and a Codex subscription may not bill the operator at API token rates. Treat this as an API-equivalent comparison unless the run is actually API-billed.

## Benchmark protocol

For each condition:

1. Start a fresh session against the same repository commit.
2. Use the same model, reasoning effort, prompt, instructions, network policy, and time limit.
3. Run exactly one benchmark prompt.
4. Save the agent's final findings separately for blinded quality scoring.
5. Run `session-usage --format json` and store the summary beside the findings.
6. Compare median duration, cumulative tokens, estimated cost, model requests, and tool invocations across repeated runs.

A useful result record is:

```json
{
  "repository": "example-api",
  "commit": "abc123",
  "condition": "baseline",
  "prompt_id": 1,
  "repeat": 1,
  "session_usage": {}
}
```

Place the complete JSON output from `session-usage` in `session_usage`.

## Guardrails and caveats

- Rollout JSONL files contain prompts, model responses, tool arguments, and tool outputs. Do not commit or share raw sessions without reviewing them for secrets and private data.
- The summary script emits aggregate metadata and file paths; it does not emit prompts, responses, tool arguments, or tool outputs.
- Use exactly one completed task per session. The script reports a warning when it sees a different topology.
- `context_window_max_tokens` is the runtime-reported limit for the observed model invocation. It is not cumulative usage.
- UI activity can expand one agent tool invocation into several visible shell entries. Use `tools.invocations` for the stable agent-level count.
- Provider billing is authoritative. The local calculation is an estimate based on supplied rates.
