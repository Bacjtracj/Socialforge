"""Squad Engine — core pipeline orchestrator for squad execution."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Callable

from app.core.agent_registry import AgentRegistry
from app.core.queue_manager import QueueManager
from app.core.squad_loader import SquadLoader
from app.models.events import Event, EventData, EventType
from app.models.squads import (
    CheckpointState,
    PipelineState,
    PipelineStep,
    PipelineStepStatus,
    PipelineStepType,
    SquadStatus,
)

__all__ = ["SquadEngine"]

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAYS = [2, 5, 10]


class SquadEngine:
    """Orchestrates the execution of a squad pipeline.

    Manages step-by-step execution, checkpoint pausing, agent calls via the
    Claude API, and event emission.
    """

    def __init__(
        self,
        loader: SquadLoader,
        registry: AgentRegistry,
        queue: QueueManager,
        emit_event: Callable,
        broadcast_state: Callable,
        api_key: str | None = None,
    ) -> None:
        self._loader = loader
        self._registry = registry
        self._queue = queue
        self._emit_event = emit_event
        self._broadcast_state = broadcast_state
        self._api_key = api_key
        self._pipeline_state: PipelineState | None = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def pipeline_state(self) -> PipelineState | None:
        """Return the current pipeline state, or None if no squad is active."""
        return self._pipeline_state

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_squad(self, squad_code: str, session_id: str) -> PipelineState | None:
        """Load squad, create PipelineState, set status RUNNING.

        Returns None if the squad code is unknown.
        """
        squad = self._loader.get(squad_code)
        if squad is None:
            logger.warning("Unknown squad code: %s", squad_code)
            return None

        total_steps = len(squad.pipeline.steps)
        self._pipeline_state = PipelineState(
            squad_code=squad_code,
            session_id=session_id,
            total_steps=total_steps,
            current_step_index=0,
            status=SquadStatus.RUNNING,
            started_at=datetime.now().isoformat(),
        )
        return self._pipeline_state

    def current_step(self) -> PipelineStep | None:
        """Return the current pipeline step by index."""
        if self._pipeline_state is None:
            return None
        squad = self._loader.get(self._pipeline_state.squad_code)
        if squad is None:
            return None
        steps = squad.pipeline.steps
        idx = self._pipeline_state.current_step_index
        if idx >= len(steps):
            return None
        return steps[idx]

    async def approve_checkpoint(
        self, user_input: str = "", approved: bool = True
    ) -> None:
        """Handle checkpoint approval.

        If approved, advances to the next step.
        If rejected, stores feedback in the checkpoint state.
        """
        if self._pipeline_state is None:
            return

        checkpoint = self._pipeline_state.checkpoint
        if checkpoint is None:
            return

        if approved:
            # Mark checkpoint approved and advance
            self._pipeline_state = self._pipeline_state.model_copy(
                update={
                    "checkpoint": checkpoint.model_copy(
                        update={"approved": True, "awaiting_approval": False}
                    ),
                }
            )
            self._advance_step()
        else:
            # Store feedback, keep paused
            self._pipeline_state = self._pipeline_state.model_copy(
                update={
                    "checkpoint": checkpoint.model_copy(
                        update={
                            "approved": False,
                            "feedback": user_input,
                            "awaiting_approval": False,
                        }
                    ),
                    "status": SquadStatus.PAUSED,
                }
            )

    async def execute_current_step(self) -> str | None:
        """Execute the current pipeline step.

        For checkpoints: sets status to PAUSED + WAITING_APPROVAL, creates
        CheckpointState and returns None.

        For agent steps: emits subagent_start, calls the Claude API, emits
        subagent_stop, stores output and returns the output string.
        """
        if self._pipeline_state is None:
            return None

        step = self.current_step()
        if step is None:
            return None

        # Update step state to active
        step_states = dict(self._pipeline_state.step_states)
        step_states[step.id] = PipelineStepStatus.ACTIVE
        self._pipeline_state = self._pipeline_state.model_copy(
            update={"step_states": step_states}
        )

        if step.type == PipelineStepType.CHECKPOINT:
            content = self._get_checkpoint_content(step)
            checkpoint = CheckpointState(
                step_id=step.id,
                step_name=step.name,
                content=content,
                awaiting_approval=True,
            )
            step_states[step.id] = PipelineStepStatus.WAITING_APPROVAL
            self._pipeline_state = self._pipeline_state.model_copy(
                update={
                    "status": SquadStatus.PAUSED,
                    "checkpoint": checkpoint,
                    "step_states": step_states,
                }
            )
            return None

        # Agent step
        result = await self._execute_agent_step(step)

        # Store output
        outputs = dict(self._pipeline_state.outputs)
        outputs[step.id] = result or ""
        step_states[step.id] = (
            PipelineStepStatus.COMPLETED if result is not None else PipelineStepStatus.ERROR
        )
        self._pipeline_state = self._pipeline_state.model_copy(
            update={"outputs": outputs, "step_states": step_states}
        )
        return result

    async def _execute_agent_step(self, step: PipelineStep) -> str | None:
        """Execute an agent step with retry logic (max 3 retries).

        Emits subagent_start / subagent_stop events with squad metadata.
        """
        if self._pipeline_state is None:
            return None

        squad_code = self._pipeline_state.squad_code
        session_id = self._pipeline_state.session_id
        agent_id = step.agent or ""

        # Look up visual identity from registry
        identity = self._registry.get_identity(squad_code, agent_id)

        # Build event data kwargs with squad metadata
        event_kwargs: dict = {
            "agent_id": agent_id,
            "squad_id": squad_code,
            "squad_agent_id": agent_id,
            "pipeline_step": step.id,
            "pipeline_step_name": step.name,
        }
        if identity:
            event_kwargs["display_name"] = identity.display_name
            event_kwargs["sprite_key"] = identity.sprite_key
            event_kwargs["agent_color"] = identity.color
            event_kwargs["agent_name"] = identity.display_name

        # Emit subagent_start
        await self._emit_event(
            Event(
                event_type=EventType.SUBAGENT_START,
                session_id=session_id,
                data=EventData(**event_kwargs),
            )
        )

        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                prompt = self._build_agent_prompt()
                result = await self._call_claude_api(prompt)

                # Emit subagent_stop with success
                stop_kwargs = dict(event_kwargs)
                stop_kwargs["result_summary"] = result[:200] if result else ""
                await self._emit_event(
                    Event(
                        event_type=EventType.SUBAGENT_STOP,
                        session_id=session_id,
                        data=EventData(**stop_kwargs),
                    )
                )
                return result

            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Agent step %s attempt %d/%d failed: %s",
                    step.id,
                    attempt + 1,
                    MAX_RETRIES,
                    exc,
                )
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAYS[attempt] if attempt < len(RETRY_DELAYS) else RETRY_DELAYS[-1]
                    await asyncio.sleep(delay)

                    # Update step state to retry
                    if self._pipeline_state:
                        step_states = dict(self._pipeline_state.step_states)
                        step_states[step.id] = PipelineStepStatus.RETRY
                        self._pipeline_state = self._pipeline_state.model_copy(
                            update={"step_states": step_states}
                        )

        # All retries exhausted — emit subagent_stop with error
        error_kwargs = dict(event_kwargs)
        error_kwargs["message"] = str(last_error)
        await self._emit_event(
            Event(
                event_type=EventType.SUBAGENT_STOP,
                session_id=session_id,
                data=EventData(**error_kwargs),
            )
        )
        return None

    def _build_agent_prompt(self) -> str:
        """Assemble the prompt from persona, task files, step file, and data files."""
        if self._pipeline_state is None:
            return ""

        squad_code = self._pipeline_state.squad_code
        squad = self._loader.get(squad_code)
        if squad is None:
            return ""

        step = self.current_step()
        if step is None:
            return ""

        squad_dir = Path(squad.squad_dir)
        parts: list[str] = []

        # 1. Agent persona (agent.md file)
        if step.agent:
            agent_md_path = squad_dir / "agents" / f"{step.agent}.agent.md"
            if agent_md_path.exists():
                parts.append(agent_md_path.read_text(encoding="utf-8"))

        # 2. Task files for the step
        for task_name in step.tasks:
            task_path = squad_dir / "agents" / step.agent / "tasks" / f"{task_name}.md" if step.agent else None
            if task_path and task_path.exists():
                parts.append(task_path.read_text(encoding="utf-8"))

        # 3. Step file
        step_file_path = squad_dir / "pipeline" / step.file
        if step_file_path.exists():
            parts.append(step_file_path.read_text(encoding="utf-8"))

        # 4. Data files
        for data_file in squad.data_files:
            data_path = squad_dir / data_file
            if data_path.exists():
                parts.append(data_path.read_text(encoding="utf-8"))

        # 5. Previous outputs
        if self._pipeline_state.outputs:
            prev_outputs_section = ["## Previous Step Outputs\n"]
            for step_id, output in self._pipeline_state.outputs.items():
                prev_outputs_section.append(f"### {step_id}\n{output}\n")
            parts.append("\n".join(prev_outputs_section))

        return "\n\n---\n\n".join(parts)

    async def _call_claude_api(self, prompt: str) -> str:
        """Execute prompt via Claude Code CLI (uses existing subscription).

        Falls back to Anthropic API if CLI is not available.
        """
        # Try Claude Code CLI first (uses your subscription, no extra cost)
        try:
            return await self._call_claude_cli(prompt)
        except FileNotFoundError:
            logger.info("Claude CLI not found, falling back to API")
        except Exception as exc:
            logger.warning("Claude CLI failed: %s, falling back to API", exc)

        # Fallback to API if CLI unavailable and key is set
        if self._api_key:
            return await self._call_anthropic_api(prompt)

        raise RuntimeError("Neither Claude CLI nor API key available")

    async def _call_claude_cli(self, prompt: str) -> str:
        """Call Claude Code CLI via subprocess."""
        import shutil
        import tempfile

        claude_path = shutil.which("claude")
        if not claude_path:
            raise FileNotFoundError("claude CLI not found in PATH")

        # Write prompt to temp file to avoid shell escaping issues
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(prompt)
            prompt_file = f.name

        try:
            proc = await asyncio.create_subprocess_exec(
                claude_path, "-p", "--output-format", "text",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Send prompt via stdin
            with open(prompt_file, "rb") as f:
                prompt_bytes = f.read()

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=prompt_bytes),
                timeout=300,  # 5 min timeout per agent step
            )

            if proc.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="replace").strip()
                raise RuntimeError(f"Claude CLI exited with code {proc.returncode}: {error_msg}")

            return stdout.decode("utf-8", errors="replace").strip()
        finally:
            Path(prompt_file).unlink(missing_ok=True)

    async def _call_anthropic_api(self, prompt: str) -> str:
        """Fallback: call Anthropic API directly (requires ANTHROPIC_API_KEY)."""
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=self._api_key)
        message = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        )
        content = message.content
        if content and hasattr(content[0], "text"):
            return content[0].text
        return ""

    def _get_checkpoint_content(self, step: PipelineStep) -> str:
        """Read the step file for checkpoint display content."""
        if self._pipeline_state is None:
            return ""

        squad = self._loader.get(self._pipeline_state.squad_code)
        if squad is None:
            return ""

        squad_dir = Path(squad.squad_dir)
        step_file_path = squad_dir / "pipeline" / step.file
        if step_file_path.exists():
            return step_file_path.read_text(encoding="utf-8")
        return ""

    def _advance_step(self) -> None:
        """Increment current_step_index; set COMPLETED if past last step."""
        if self._pipeline_state is None:
            return

        new_index = self._pipeline_state.current_step_index + 1
        if new_index >= self._pipeline_state.total_steps:
            self._pipeline_state = self._pipeline_state.model_copy(
                update={
                    "current_step_index": new_index,
                    "status": SquadStatus.COMPLETED,
                    "completed_at": datetime.now().isoformat(),
                }
            )
        else:
            self._pipeline_state = self._pipeline_state.model_copy(
                update={
                    "current_step_index": new_index,
                    "status": SquadStatus.RUNNING,
                }
            )

    async def run_pipeline(self) -> None:
        """Run pipeline steps until a checkpoint pause or completion."""
        if self._pipeline_state is None:
            return

        while True:
            state = self._pipeline_state
            if state is None:
                break

            # Stop if completed or errored
            if state.status in (SquadStatus.COMPLETED, SquadStatus.ERROR):
                break

            # Stop if paused (e.g. waiting for checkpoint approval)
            if state.status == SquadStatus.PAUSED:
                break

            step = self.current_step()
            if step is None:
                break

            await self.execute_current_step()

            # Re-read state after execution
            state = self._pipeline_state
            if state is None:
                break

            # If a checkpoint paused us, stop
            if state.status == SquadStatus.PAUSED:
                break

            # Advance to next step for non-checkpoint types
            if step.type == PipelineStepType.AGENT:
                self._advance_step()

            await self._broadcast_state(self._pipeline_state)
