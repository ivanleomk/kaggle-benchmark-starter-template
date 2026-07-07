# Agent Patterns

This template demonstrates three Harbor-compatible approaches.

| Pattern | Use when | Example |
| --- | --- | --- |
| Built-in Harbor agent | A standard coding-agent smoke test is enough. | `harbor run -a mini-swe-agent` |
| Binary CLI agent | The agent is installed and run as a shell command. | `agents/opencode_binary_agent.py` |
| SDK-backed custom agent | The agent has a Python SDK or custom runtime. | `agents/antigravity_agent.py` and `agents/antigravity_runner.py` |

## Built-In Harbor Agent

Use this first to validate the task, Docker environment, verifier, artifacts,
and model access before debugging a custom agent.

```bash
harbor run -p tasks/hello-world -a mini-swe-agent -m openai/gemini-3.5-flash
```

## Binary CLI Agent

Use `BaseInstalledAgent` when the agent is a binary or CLI.

Expected shape:

1. Install system packages with `exec_as_root`.
2. Install user-level binaries with `exec_as_agent`.
3. Run the binary against the rendered Harbor instruction.
4. Save raw logs under `/logs/agent`.
5. Convert logs into ATIF at `/logs/agent/trajectory.json`.
6. Populate `AgentContext` metrics from the trajectory.

For OpenCode with Kaggle model proxy, accept Harbor model names like
`openai/google/gemini-3.5-flash`, but run OpenCode with an internal custom
provider such as `kaggleproxy/google/gemini-3.5-flash`.

The custom provider should use:

```json
{
  "provider": {
    "kaggleproxy": {
      "npm": "@ai-sdk/openai-compatible",
      "options": {
        "baseURL": "${MODEL_PROXY_URL}/openapi",
        "apiKey": "{env:OPENAI_API_KEY}"
      }
    }
  }
}
```

This avoids OpenCode's built-in `openai` provider, which uses `/responses`.

## SDK-Backed Custom Agent

Use `BaseAgent` when the agent has a Python SDK or a custom runtime. Keep the
Harbor adapter small:

1. Install `uv` in the task container if needed.
2. Upload a runner script into the container.
3. Let the runner script declare dependencies with PEP 723 metadata.
4. Pass model name, credentials, skill paths, and MCP config through env vars.
5. Write the SDK transcript as ATIF.

This keeps SDK-specific complexity out of the task definition and makes the
runner easy to inspect or replace.
