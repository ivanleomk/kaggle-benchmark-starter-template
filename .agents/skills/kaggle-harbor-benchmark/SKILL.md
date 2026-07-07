---
name: kaggle-harbor-benchmark
description: Use when creating, updating, validating, or documenting a Kaggle benchmark repo that uses Harbor task specs, Kaggle model proxy, custom Harbor agents, or committed sample job outputs.
---

# Kaggle Harbor Benchmark

Build Kaggle benchmark repos as runnable Harbor projects with concrete
evidence. Prefer small deterministic tasks, real validation commands, and named
job outputs over long explanations.

Use the references only when needed:

- `references/model_proxy.md`: Kaggle CLI auth, `.env`, OpenAI/Anthropic proxy
  endpoints, model slugs, and `/chat/completions` vs `/responses`.
- `references/agent_patterns.md`: built-in Harbor agents, binary CLI agents,
  SDK-backed agents, ATIF trajectories, and OpenCode proxy config.
- `references/validation.md`: local Harbor runs, packaged runner image smoke
  tests, Docker-in-Docker notes, and committed job evidence.

Default workflow:

1. Keep or create the standard repo shape: `dataset.toml`, `tasks/<name>/`,
   `agents/`, `runner/`, and `jobs/<named-run>/`.
2. Start with a tiny task that has an exact verifier.
3. Validate locally with `harbor run`.
4. Add custom agents only when the example needs a binary or SDK integration.
5. Commit named successful job outputs such as `jobs/mini-swe-agent`,
   `jobs/opencode-binary`, and `jobs/antigravity`.

Before committing job outputs, scan for raw API keys, bearer tokens, and
unredacted proxy credentials.
