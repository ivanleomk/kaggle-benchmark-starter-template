"""Example Harbor custom agent backed by the Google Antigravity SDK.

This module is imported by Harbor, so it assumes the Python environment running
Harbor already has `harbor` installed. The Antigravity SDK itself is installed
inside the task container by `antigravity_runner.py`, which is uploaded during
agent setup and executed with uv.
"""

import json
import os
import shlex
from pathlib import Path
from typing import Any

from harbor.agents.base import BaseAgent
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext


class AntigravityAgent(BaseAgent):
    """Minimal custom Harbor agent adapter for Google Antigravity SDK."""

    SUPPORTS_ATIF = True

    _RUNNER_FILENAME = "antigravity_runner.py"
    _OUTPUT_FILENAME = "antigravity_agent.txt"
    _TRAJECTORY_FILENAME = "trajectory.json"

    def __init__(
        self,
        *args: Any,
        extra_env: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._extra_env = extra_env or {}

    @staticmethod
    def name() -> str:
        return "custom-antigravity"

    def version(self) -> str:
        return "template"

    @property
    def _container_runner_path(self) -> str:
        return f"/installed-agent/{self._RUNNER_FILENAME}"

    async def setup(self, environment: BaseEnvironment) -> None:
        """Install uv if needed and upload the Antigravity runner script."""
        check_result = await environment.exec(command="command -v uv >/dev/null 2>&1")
        if check_result.return_code != 0:
            await environment.exec(
                command=(
                    "apt-get -o Acquire::Retries=5 update -qq && "
                    "apt-get install -y curl ca-certificates python3 && "
                    "curl -LsSf https://astral.sh/uv/install.sh | "
                    "env UV_INSTALL_DIR=/usr/local/bin sh"
                ),
                env={"DEBIAN_FRONTEND": "noninteractive"},
                user="root",
            )

        runner_path = Path(__file__).with_name(self._RUNNER_FILENAME)
        await environment.exec(command="mkdir -p /installed-agent", user="root")
        await environment.upload_file(
            source_path=runner_path,
            target_path=self._container_runner_path,
        )
        await environment.exec(
            command=f"chmod +x {self._container_runner_path}",
            user="root",
        )

    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        gemini_api_key = self._extra_env.get("GEMINI_API_KEY") or os.environ.get(
            "GEMINI_API_KEY"
        )
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY must be set")

        model_name = self.model_name or self._extra_env.get("MODEL_NAME")
        if not model_name:
            raise ValueError("Pass a model with -m, for example google/gemini-3.5-flash")

        logs_dir = "/logs/agent"
        trajectory_path = f"{logs_dir}/{self._TRAJECTORY_FILENAME}"
        command = (
            f"{self._container_runner_path} "
            f"--instruction={shlex.quote(instruction)} "
            f"--logs-dir={shlex.quote(logs_dir)} "
            f"--trajectory-path={shlex.quote(trajectory_path)} "
            f"> {logs_dir}/{self._OUTPUT_FILENAME} 2>&1"
        )

        await environment.exec(
            command=command,
            env={
                "GEMINI_API_KEY": gemini_api_key,
                "MODEL_NAME": model_name,
            },
        )

    def populate_context_post_run(self, context: AgentContext) -> None:
        trajectory_path = self.logs_dir / self._TRAJECTORY_FILENAME
        if not trajectory_path.exists():
            return

        try:
            trajectory = json.loads(trajectory_path.read_text())
        except json.JSONDecodeError:
            return

        metrics = trajectory.get("final_metrics", {})
        context.n_input_tokens = metrics.get("total_prompt_tokens", 0)
        context.n_output_tokens = metrics.get("total_completion_tokens", 0)
        context.n_cache_tokens = metrics.get("total_cached_tokens", 0)
        context.cost_usd = metrics.get("total_cost_usd", 0.0)
