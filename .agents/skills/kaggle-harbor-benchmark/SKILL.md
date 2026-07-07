---
name: kaggle-harbor-benchmark
description: Use when creating, updating, validating, or documenting a Kaggle benchmark repository that uses Harbor task specs, Kaggle model proxy credentials, custom Harbor agents, or committed sample job outputs.
---

# Kaggle Harbor Benchmark

Build Kaggle benchmark repos as small, runnable Harbor projects with committed
evidence. Prefer working examples over prose.

## Repository Shape

Use this layout unless the repo already has a stronger convention:

```text
dataset.toml
tasks/<task-name>/task.toml
tasks/<task-name>/instruction.md
tasks/<task-name>/environment/Dockerfile
tasks/<task-name>/tests/
agents/
jobs/<named-run>/
runner/
```

Keep the first task deterministic. A good smoke task asks the agent to create
one exact file and verifies it with shell or pytest checks.

## Model Proxy

Tell users to install and authenticate the Kaggle CLI with uv:

```bash
uv tool install kaggle
kaggle auth login
kaggle benchmarks auth -y --env-file .env
```

Document that `.env` contains `MODEL_PROXY_URL`, `MODEL_PROXY_API_KEY`, and
`MODEL_PROXY_EXPIRY_TIME`. Use curl smoke tests for both:

```text
${MODEL_PROXY_URL%/}/openapi
${MODEL_PROXY_URL%/}/anthropic
```

For OpenAI-compatible tool-calling agents, prefer
`/openapi/chat/completions` unless the agent specifically requires the
Responses API.

## Agent Patterns

Pick one of these patterns:

| Pattern | Use when | Example |
| --- | --- | --- |
| Built-in Harbor agent | Standard smoke test is enough. | `harbor run -a mini-swe-agent` |
| Binary CLI agent | The agent is installed and run as a command. | `agents/opencode_binary_agent.py` |
| SDK custom agent | The agent has a Python SDK or custom runtime. | `agents/antigravity_agent.py` plus `agents/antigravity_runner.py` |

For binary agents, use `BaseInstalledAgent`: install packages, run the binary,
save raw logs under `/logs/agent`, convert logs to ATIF, and populate
`AgentContext` metrics.

For SDK agents, keep the Harbor adapter small. Upload a uv script into the task
container, declare SDK dependencies in PEP 723 metadata, pass model credentials
through env vars, and write an ATIF trajectory.

For OpenCode with the Kaggle model proxy, avoid the built-in `openai` provider
for tool calls. It uses `/responses`. Register a custom OpenCode provider with
`@ai-sdk/openai-compatible` and run that provider internally so OpenCode uses
`/chat/completions`.

## Validation

Always validate locally before documenting success:

```bash
harbor run -p tasks/hello-world -a mini-swe-agent -m openai/gemini-3.5-flash
```

For model proxy runs, pass the proxy key and base URL:

```bash
source .env
MODEL_PROXY_HOST="$(python3 -c 'from urllib.parse import urlparse; import os; print(urlparse(os.environ["MODEL_PROXY_URL"]).hostname)')"

harbor run \
  -p tasks/hello-world \
  -a mini-swe-agent \
  -m openai/google/gemini-3.5-flash \
  --ae OPENAI_API_KEY="${MODEL_PROXY_API_KEY}" \
  --ae OPENAI_BASE_URL="${MODEL_PROXY_URL%/}/openapi" \
  --allow-agent-host "${MODEL_PROXY_HOST}"
```

For packaged runner smoke tests on macOS Docker Desktop, pass
`DOCKERD_STORAGE_DRIVER=vfs` because Docker-in-Docker can fail with nested
overlay storage.

## Committed Evidence

Commit named sample runs for the main paths:

```text
jobs/mini-swe-agent
jobs/opencode-binary
jobs/antigravity
```

Each run should include aggregate and per-trial `result.json`, verifier output,
artifacts, agent logs, and ATIF trajectory when available. Scan committed job
outputs for raw API keys, bearer tokens, and unredacted proxy credentials.

## References

- Vercel skills CLI: skills need a directory with `SKILL.md` and YAML
  frontmatter containing `name` and `description`.
- Phil Schmid's testing guidance: define measurable success criteria, use
  deterministic checks where possible, test negative cases, isolate runs, and
  run multiple trials.
- Phil Schmid's writing guidance: keep skills lean, make the description
  specific, and use directives instead of long explanations.
