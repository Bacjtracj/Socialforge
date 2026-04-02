"""Tests for AgentRegistry with fixed visual identities."""

import pytest
from app.core.agent_registry import AgentRegistry


@pytest.fixture
def registry() -> AgentRegistry:
    return AgentRegistry()


def test_total_agents(registry: AgentRegistry) -> None:
    assert registry.total_agents() == 11


def test_unknown_agent_returns_none(registry: AgentRegistry) -> None:
    assert registry.get_identity("nonexistent-squad", "ghost") is None


def test_unknown_squad_known_agent_returns_none(registry: AgentRegistry) -> None:
    assert registry.get_identity("nonexistent-squad", "estrategista") is None


# --- Fábrica de Conteúdo ---

def test_fabrica_estrategista(registry: AgentRegistry) -> None:
    identity = registry.get_identity("fabrica-de-conteudo", "estrategista")
    assert identity is not None
    assert identity.display_name == "Sol Estratégia"
    assert identity.color == "#FFD700"
    assert identity.sprite_key == "sol-estrategia"
    assert identity.icon == "🧠"


def test_fabrica_pesquisador(registry: AgentRegistry) -> None:
    identity = registry.get_identity("fabrica-de-conteudo", "pesquisador")
    assert identity is not None
    assert identity.display_name == "Luna Pesquisa"
    assert identity.color == "#87CEEB"
    assert identity.sprite_key == "luna-pesquisa"
    assert identity.icon == "🔍"


def test_fabrica_copywriter(registry: AgentRegistry) -> None:
    identity = registry.get_identity("fabrica-de-conteudo", "copywriter")
    assert identity is not None
    assert identity.display_name == "Davi Copy"
    assert identity.color == "#4CAF50"
    assert identity.sprite_key == "davi-copy"
    assert identity.icon == "✍️"


def test_fabrica_roteirista_stories(registry: AgentRegistry) -> None:
    identity = registry.get_identity("fabrica-de-conteudo", "roteirista-stories")
    assert identity is not None
    assert identity.display_name == "Bia Stories"
    assert identity.color == "#FF69B4"
    assert identity.sprite_key == "bia-stories"
    assert identity.icon == "📱"


def test_fabrica_revisor(registry: AgentRegistry) -> None:
    identity = registry.get_identity("fabrica-de-conteudo", "revisor")
    assert identity is not None
    assert identity.display_name == "Léo Revisão"
    assert identity.color == "#FF8C00"
    assert identity.sprite_key == "leo-revisao"
    assert identity.icon == "✅"


# --- Diagnóstico de Perfil ---

def test_diagnostico_investigador(registry: AgentRegistry) -> None:
    identity = registry.get_identity("diagnostico-perfil", "investigador")
    assert identity is not None
    assert identity.display_name == "Sherlock Social"
    assert identity.color == "#8B4513"
    assert identity.sprite_key == "sherlock-social"
    assert identity.icon == "🕵️"


def test_diagnostico_analista(registry: AgentRegistry) -> None:
    identity = registry.get_identity("diagnostico-perfil", "analista")
    assert identity is not None
    assert identity.display_name == "Nina Números"
    assert identity.color == "#9C27B0"
    assert identity.sprite_key == "nina-numeros"
    assert identity.icon == "📊"


def test_diagnostico_estrategista_perfil(registry: AgentRegistry) -> None:
    identity = registry.get_identity("diagnostico-perfil", "estrategista-perfil")
    assert identity is not None
    assert identity.display_name == "Max Plano"
    assert identity.color == "#1A237E"
    assert identity.sprite_key == "max-plano"
    assert identity.icon == "🎯"


# --- Máquina de Clientes ---

def test_maquina_consultor(registry: AgentRegistry) -> None:
    identity = registry.get_identity("maquina-clientes", "consultor")
    assert identity is not None
    assert identity.display_name == "Rafa Preço"
    assert identity.color == "#2E7D32"
    assert identity.sprite_key == "rafa-preco"
    assert identity.icon == "💰"


def test_maquina_juridico(registry: AgentRegistry) -> None:
    identity = registry.get_identity("maquina-clientes", "juridico")
    assert identity is not None
    assert identity.display_name == "Clara Contrato"
    assert identity.color == "#880E4F"
    assert identity.sprite_key == "clara-contrato"
    assert identity.icon == "📋"


def test_maquina_onboarding(registry: AgentRegistry) -> None:
    identity = registry.get_identity("maquina-clientes", "onboarding")
    assert identity is not None
    assert identity.display_name == "Dani Welcome"
    assert identity.color == "#00BCD4"
    assert identity.sprite_key == "dani-welcome"
    assert identity.icon == "🤝"
