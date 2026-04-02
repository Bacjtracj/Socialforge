"""Squad Loader — reads and validates YAML squad definitions from disk."""

from pathlib import Path

import yaml

from app.models.squads import (
    AgentDefinition,
    PipelineStep,
    SquadPipeline,
    Squad,
)

__all__ = ["SquadLoader"]


class SquadLoader:
    """Loads squad definitions from a directory of YAML files."""

    def __init__(self, squads_dir: str | Path) -> None:
        self._squads_dir = Path(squads_dir)
        self._cache: dict[str, Squad] | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_all(self) -> dict[str, Squad]:
        """Load every squad directory and return a dict keyed by squad code.

        Skips directories whose name starts with ``_``.
        Result is cached; call again to get the same object.
        """
        if self._cache is not None:
            return self._cache

        squads: dict[str, Squad] = {}
        for squad_dir in sorted(self._squads_dir.iterdir()):
            if not squad_dir.is_dir():
                continue
            if squad_dir.name.startswith("_"):
                continue
            squad = self._load_squad(squad_dir)
            squads[squad.code] = squad

        self._cache = squads
        return self._cache

    def get(self, code: str) -> Squad | None:
        """Return a single squad by code, loading all squads if needed."""
        return self.load_all().get(code)

    def list_squads(self) -> list[dict]:
        """Return a summary list with essential fields for each squad."""
        squads = self.load_all()
        return [
            {
                "code": squad.code,
                "name": squad.name,
                "description": squad.description,
                "icon": squad.icon,
                "agent_count": len(squad.agents),
                "step_count": len(squad.pipeline.steps),
            }
            for squad in squads.values()
        ]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_squad(self, squad_dir: Path) -> Squad:
        """Load a single squad from *squad_dir*."""
        squad_yaml_path = squad_dir / "squad.yaml"
        with squad_yaml_path.open(encoding="utf-8") as fh:
            raw: dict = yaml.safe_load(fh)

        # Agents
        agents: list[AgentDefinition] = [
            AgentDefinition(
                id=a["id"],
                name=a["name"],
                icon=a["icon"],
            )
            for a in raw.get("agents", [])
        ]

        # Data files (squad.yaml key is "data" — a list of file paths)
        data_files: list[str] = raw.get("data", [])

        # Pipeline — resolve the entry path relative to squad_dir
        pipeline_entry: str = raw["pipeline"]["entry"]
        pipeline_path = squad_dir / pipeline_entry
        pipeline = self._load_pipeline(pipeline_path)

        return Squad(
            name=raw["name"],
            code=raw["code"],
            description=raw["description"].strip(),
            icon=raw["icon"],
            version=raw["version"],
            agents=agents,
            pipeline=pipeline,
            data_files=data_files,
            squad_dir=str(squad_dir),
        )

    def _load_pipeline(self, pipeline_path: Path) -> SquadPipeline:
        """Load a pipeline definition from *pipeline_path*."""
        with pipeline_path.open(encoding="utf-8") as fh:
            raw: dict = yaml.safe_load(fh)

        steps: list[PipelineStep] = [
            PipelineStep(
                id=s["id"],
                name=s["name"],
                type=s["type"],
                file=s["file"],
                agent=s.get("agent"),
                tasks=s.get("tasks", []),
                depends_on=s.get("depends_on"),
            )
            for s in raw.get("steps", [])
        ]

        checkpoints: list[str] = raw.get("checkpoints", [])

        return SquadPipeline(
            name=raw["name"],
            steps=steps,
            checkpoints=checkpoints,
        )
