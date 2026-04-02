"""Tests for SquadLoader."""

from pathlib import Path

import pytest

from app.core.squad_loader import SquadLoader

SQUADS_DIR = Path(__file__).parents[2] / "socialforge" / "squads"


@pytest.fixture
def loader() -> SquadLoader:
    return SquadLoader(SQUADS_DIR)


# ---------------------------------------------------------------------------
# load_all
# ---------------------------------------------------------------------------


def test_load_all_returns_three_squads(loader: SquadLoader) -> None:
    squads = loader.load_all()
    assert len(squads) == 3


def test_load_all_is_cached(loader: SquadLoader) -> None:
    first = loader.load_all()
    second = loader.load_all()
    assert first is second


# ---------------------------------------------------------------------------
# fabrica-de-conteudo
# ---------------------------------------------------------------------------


def test_fabrica_has_five_agents(loader: SquadLoader) -> None:
    squad = loader.get("fabrica-de-conteudo")
    assert squad is not None
    assert len(squad.agents) == 5


def test_fabrica_has_twelve_pipeline_steps(loader: SquadLoader) -> None:
    squad = loader.get("fabrica-de-conteudo")
    assert squad is not None
    assert len(squad.pipeline.steps) == 12


def test_fabrica_basic_fields(loader: SquadLoader) -> None:
    squad = loader.get("fabrica-de-conteudo")
    assert squad is not None
    assert squad.code == "fabrica-de-conteudo"
    assert squad.name == "Fábrica de Conteúdo"
    assert squad.icon == "🔥"
    assert squad.version == "1.0.0"


def test_fabrica_agent_ids(loader: SquadLoader) -> None:
    squad = loader.get("fabrica-de-conteudo")
    assert squad is not None
    agent_ids = {a.id for a in squad.agents}
    assert agent_ids == {"estrategista", "pesquisador", "copywriter", "roteirista-stories", "revisor"}


def test_fabrica_pipeline_name(loader: SquadLoader) -> None:
    squad = loader.get("fabrica-de-conteudo")
    assert squad is not None
    assert "Fábrica de Conteúdo" in squad.pipeline.name


def test_fabrica_pipeline_checkpoints(loader: SquadLoader) -> None:
    squad = loader.get("fabrica-de-conteudo")
    assert squad is not None
    assert len(squad.pipeline.checkpoints) == 6


# ---------------------------------------------------------------------------
# diagnostico-perfil
# ---------------------------------------------------------------------------


def test_diagnostico_has_three_agents(loader: SquadLoader) -> None:
    squad = loader.get("diagnostico-perfil")
    assert squad is not None
    assert len(squad.agents) == 3


def test_diagnostico_basic_fields(loader: SquadLoader) -> None:
    squad = loader.get("diagnostico-perfil")
    assert squad is not None
    assert squad.code == "diagnostico-perfil"
    assert squad.icon == "🔬"


def test_diagnostico_pipeline_steps(loader: SquadLoader) -> None:
    squad = loader.get("diagnostico-perfil")
    assert squad is not None
    assert len(squad.pipeline.steps) == 10


# ---------------------------------------------------------------------------
# maquina-clientes
# ---------------------------------------------------------------------------


def test_maquina_has_three_agents(loader: SquadLoader) -> None:
    squad = loader.get("maquina-clientes")
    assert squad is not None
    assert len(squad.agents) == 3


def test_maquina_basic_fields(loader: SquadLoader) -> None:
    squad = loader.get("maquina-clientes")
    assert squad is not None
    assert squad.code == "maquina-clientes"
    assert squad.icon == "💼"


def test_maquina_pipeline_steps(loader: SquadLoader) -> None:
    squad = loader.get("maquina-clientes")
    assert squad is not None
    assert len(squad.pipeline.steps) == 9


# ---------------------------------------------------------------------------
# get / unknown
# ---------------------------------------------------------------------------


def test_get_by_code_returns_squad(loader: SquadLoader) -> None:
    squad = loader.get("fabrica-de-conteudo")
    assert squad is not None
    assert squad.code == "fabrica-de-conteudo"


def test_get_unknown_returns_none(loader: SquadLoader) -> None:
    assert loader.get("does-not-exist") is None


# ---------------------------------------------------------------------------
# list_squads
# ---------------------------------------------------------------------------


def test_list_squads_returns_three_items(loader: SquadLoader) -> None:
    summaries = loader.list_squads()
    assert len(summaries) == 3


def test_list_squads_summary_keys(loader: SquadLoader) -> None:
    summaries = loader.list_squads()
    for summary in summaries:
        assert set(summary.keys()) == {"code", "name", "description", "icon", "agent_count", "step_count"}


def test_list_squads_fabrica_summary(loader: SquadLoader) -> None:
    summaries = loader.list_squads()
    fabrica = next(s for s in summaries if s["code"] == "fabrica-de-conteudo")
    assert fabrica["agent_count"] == 5
    assert fabrica["step_count"] == 12


def test_list_squads_all_codes_present(loader: SquadLoader) -> None:
    codes = {s["code"] for s in loader.list_squads()}
    assert codes == {"fabrica-de-conteudo", "diagnostico-perfil", "maquina-clientes"}
