---
name: kaggle-harbor-benchmark
description: Build and validate Kaggle benchmarks using Harbor.
---

# Kaggle Harbor Benchmark

Build Kaggle benchmarks with [Harbor](https://github.com/harbor-framework/harbor). For task specs and verifiers, see [Harbor docs](https://github.com/harbor-framework/harbor).

Workflow:
1. Test locally with `harbor run`.
2. Route model requests via Kaggle Model Proxy.
3. Test runner image (`harbor-git-v1`).
4. Commit job evidence (`jobs/`).

Gotchas:
- **Base URL**: Set `OPENAI_BASE_URL` / `MODEL_PROXY_BASE_URL` to `${MODEL_PROXY_URL%/}/openapi/v1`.
- **Model Slug**: Use `openai/` prefix for `mini-swe-agent` (e.g. `openai/google/gemini-3.5-flash`).
- **Runner Mounts**: Mount `-v harbor-dind-data:/var/lib/docker` and `-v "$PWD/kaggle/working:/kaggle/working"`.
