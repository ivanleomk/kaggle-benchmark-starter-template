#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "cryptography<47",
#   "fastapi",
#   "google-antigravity>=0.1.1",
# ]
# ///
"""Container-side uv script for the custom Antigravity Harbor agent."""

import argparse
import asyncio
import json
import logging
import os
import sys
from importlib.metadata import version
from pathlib import Path


async def run_agent(args: argparse.Namespace) -> None:
    from google.antigravity import Agent, LocalAgentConfig
    from google.antigravity.hooks import policy
    from google.antigravity.types import StepSource, StepStatus

    logging.getLogger().setLevel(logging.ERROR)

    api_key = os.environ.get("GEMINI_API_KEY")
    model = os.environ.get("MODEL_NAME")

    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)
    if not model:
        print("Error: MODEL_NAME environment variable not set", file=sys.stderr)
        sys.exit(1)

    normalized_model = model.split("/")[-1]
    config = LocalAgentConfig(
        model=normalized_model,
        api_key=api_key,
        policies=[policy.allow_all()],
        workspaces=[os.getcwd()],
    )

    steps = [
        {
            "step_id": 1,
            "source": "user",
            "message": args.instruction,
        }
    ]
    step_id = 2
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_cached_tokens = 0

    print(f"Starting Antigravity SDK agent with model: {normalized_model}")
    async with Agent(config) as agent:
        await agent.conversation.send(args.instruction)

        async for step in agent.conversation.receive_steps():
            if step.status != StepStatus.DONE:
                continue
            if step.source == StepSource.USER:
                continue

            usage = getattr(step, "usage_metadata", None)
            if usage is not None:
                total_prompt_tokens += usage.prompt_token_count or 0
                total_completion_tokens += usage.candidates_token_count or 0
                total_cached_tokens += usage.cached_content_token_count or 0

            step_dict = {
                "step_id": step_id,
                "source": "agent" if step.source == StepSource.MODEL else "system",
                "message": step.content or "",
                "model_name": normalized_model,
            }
            if getattr(step, "thinking", None):
                step_dict["reasoning_content"] = step.thinking
            if usage is not None:
                step_dict["metrics"] = {
                    "prompt_tokens": usage.prompt_token_count,
                    "completion_tokens": usage.candidates_token_count,
                    "cached_tokens": usage.cached_content_token_count,
                }
            steps.append(step_dict)
            step_id += 1

    trajectory = {
        "schema_version": "ATIF-v1.7",
        "session_id": os.environ.get("SESSION_ID", "harbor-session"),
        "agent": {
            "name": "custom-antigravity",
            "version": version("google-antigravity"),
        },
        "steps": steps,
        "final_metrics": {
            "total_prompt_tokens": total_prompt_tokens,
            "total_completion_tokens": total_completion_tokens,
            "total_cached_tokens": total_cached_tokens,
            "total_cost_usd": 0.0,
        },
    }

    trajectory_path = Path(args.trajectory_path)
    trajectory_path.parent.mkdir(parents=True, exist_ok=True)
    trajectory_path.write_text(json.dumps(trajectory, indent=2))

    print(f"Agent completed. Trajectory saved to {trajectory_path}")


def main() -> None:
    if "--version" in sys.argv:
        print(version("google-antigravity"))
        return

    parser = argparse.ArgumentParser(description="Run Google Antigravity SDK agent")
    parser.add_argument("--instruction", required=True)
    parser.add_argument("--logs-dir", required=True)
    parser.add_argument("--trajectory-path", required=True)
    args = parser.parse_args()

    asyncio.run(run_agent(args))


if __name__ == "__main__":
    main()
