# Validation

## Local Harbor Loop

Use direct local Harbor runs while authoring a benchmark. This uses the host
Docker daemon and avoids Docker-in-Docker.

Direct Gemini API key:

```bash
export GEMINI_API_KEY=<your-gemini-api-key>

harbor run \
  -p tasks/hello-world \
  -a mini-swe-agent \
  -m openai/gemini-3.5-flash \
  --ae OPENAI_API_KEY="${GEMINI_API_KEY}" \
  --ae OPENAI_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai/" \
  --allow-agent-host generativelanguage.googleapis.com
```

Kaggle model proxy:

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

## Runner Image Smoke Test

Use the packaged runner image after the repo is pushed. The runner image clones
the repo, checks out `KAGGLE_TASK_REPO_REF`, and runs Harbor against
`KAGGLE_TASK_PATH`.

On macOS Docker Desktop, pass this for Docker-in-Docker:

```bash
-e DOCKERD_STORAGE_DRIVER=vfs
```

For private repos, pass a GitHub token:

```bash
-e KAGGLE_GIT_TOKEN="$(gh auth token)"
```

Use a commit SHA for `KAGGLE_TASK_REPO_REF` when the smoke test must be
reproducible.

## Named Job Outputs

Commit named successful runs for the examples:

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

Before committing, scan for raw secrets:

```bash
rg --pcre2 -n "sk-[A-Za-z0-9]|AIza|Authorization: Bearer|Bearer [A-Za-z0-9_\\-.=]{20,}" jobs/<named-run>
```
