# Kaggle Harbor Benchmark

Use this skill when building or updating a Kaggle benchmark repository that
uses Harbor-compatible task specs, model proxy credentials, or custom Harbor
agent integrations.

## Goal

Produce a benchmark template that someone can fork, run locally with Harbor,
verify through the Kaggle runner image, and inspect through committed sample
job outputs.

## Repository Shape

Prefer this layout:

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

Keep the first task tiny and deterministic. A good smoke task asks the agent to
write one exact file and verifies that file with shell or pytest checks.

## Model Proxy Setup

Tell users to install the Kaggle CLI with uv:

```bash
uv tool install kaggle
kaggle auth login
kaggle benchmarks auth -y --env-file .env
```

The `.env` file should provide:

```text
MODEL_PROXY_URL
MODEL_PROXY_API_KEY
MODEL_PROXY_EXPIRY_TIME
```

Document both proxy endpoint families:

```text
${MODEL_PROXY_URL%/}/openapi
${MODEL_PROXY_URL%/}/anthropic
```

Use simple curl smoke tests before running a benchmark. For OpenAI-compatible
calls, prefer `/openapi/chat/completions` unless the benchmark specifically
needs the OpenAI Responses API.

## Agent Patterns

Support three patterns when useful:

| Pattern | Use when | Example |
| --- | --- | --- |
| Built-in Harbor agent | The task only needs a standard coding-agent smoke test. | `harbor run -a mini-swe-agent` |
| Binary CLI agent | The agent is installed and invoked as a command. | `agents/opencode_binary_agent.py` |
| SDK-backed custom agent | The agent has a Python SDK or richer runtime setup. | `agents/antigravity_agent.py` plus `agents/antigravity_runner.py` |

The custom examples can borrow Harbor's interfaces directly:

- Use `BaseInstalledAgent` when the adapter installs a binary in the task
  environment, runs it, and converts its logs to ATIF.
- Use `BaseAgent` when the adapter uploads a script or runner into the task
  environment and controls execution itself.
- Set `SUPPORTS_ATIF = True` when the implementation writes
  `/logs/agent/trajectory.json`.
- Populate `AgentContext` from trajectory metrics after the run when available.

## Binary Agent Notes

For a binary coding agent:

1. Install system packages with `exec_as_root`.
2. Install user-level tools with `exec_as_agent`.
3. Run the binary against the rendered Harbor instruction.
4. Save raw logs under `/logs/agent`.
5. Convert tool calls, observations, text, reasoning, and token metrics into
   ATIF.

For OpenCode with the Kaggle model proxy, avoid the built-in `openai` provider
when using tool calls. The built-in provider uses `/responses`; the proxy's
`/openapi/chat/completions` path handles tool-result turns correctly. Register
a custom OpenCode provider with `@ai-sdk/openai-compatible` and run that
provider internally, while still accepting Harbor model names such as
`openai/google/gemini-3.5-flash`.

## SDK Agent Notes

For SDK-backed agents:

1. Keep the Harbor adapter small.
2. Upload a uv script into the task container.
3. Let the uv script declare SDK dependencies in PEP 723 metadata.
4. Pass credentials and model names through environment variables.
5. Write the SDK transcript as ATIF.

This keeps task containers simple and makes it easy for users to inspect or
replace the SDK runner.

## Local Validation

Start with a direct local Harbor run. This uses the host Docker daemon and does
not require Docker-in-Docker:

```bash
harbor run \
  -p tasks/hello-world \
  -a mini-swe-agent \
  -m openai/gemini-3.5-flash \
  --ae OPENAI_API_KEY="${GEMINI_API_KEY}" \
  --ae OPENAI_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai/" \
  --allow-agent-host generativelanguage.googleapis.com
```

For model-proxy validation:

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

## Runner Image Validation

After local Harbor validation passes, smoke test the packaged runner image.
That flow clones the repo, checks out a ref, and runs Harbor against a task
path. On Docker Desktop for macOS, Docker-in-Docker can fail with nested overlay
storage, so pass:

```bash
-e DOCKERD_STORAGE_DRIVER=vfs
```

Use a commit SHA for `KAGGLE_TASK_REPO_REF`. For private repos, pass
`KAGGLE_GIT_TOKEN`; users already authenticated with GitHub CLI can generate it
with:

```bash
gh auth token
```

## Committed Evidence

Commit named job outputs for the main examples:

```text
jobs/mini-swe-agent
jobs/opencode-binary
jobs/antigravity
```

Each named run should include:

- aggregate `result.json`
- per-trial `result.json`
- verifier output
- produced artifacts
- agent logs
- ATIF trajectory when available

Before committing job outputs, scan for raw secrets. Harbor normally redacts
environment values in config files, but check for API keys, bearer tokens, and
unredacted proxy credentials anyway.

## Useful Failure Mode

If an OpenCode run against the proxy succeeds at the tool call but exits
nonzero after sending the tool result, check whether it is using
`/openapi/responses`. A minimal OpenAI client repro can compare:

- `client.responses.create(...)`, which may expose Responses API translation
  bugs.
- `client.chat.completions.create(...)`, which is the safer path for OpenCode
  through `@ai-sdk/openai-compatible`.
