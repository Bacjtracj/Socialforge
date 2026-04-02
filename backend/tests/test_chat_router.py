"""Tests for ChatRouter keyword matching and routing."""

import pytest

from app.core.chat_router import ChatRouter

SQUADS = [
    {
        "code": "fabrica-de-conteudo",
        "name": "Fábrica de Conteúdo",
        "description": "Criação de conteúdo, posts e calendário editorial.",
    },
    {
        "code": "diagnostico-perfil",
        "name": "Diagnóstico de Perfil",
        "description": "Análise de métricas, diagnóstico e concorrentes.",
    },
    {
        "code": "maquina-clientes",
        "name": "Máquina de Clientes",
        "description": "Precificação, contratos, onboarding e captação de clientes.",
    },
]


@pytest.fixture
def router() -> ChatRouter:
    return ChatRouter(available_squads=SQUADS)


class TestMatchByKeywords:
    """Tests for the keyword-based matching method."""

    # --- fabrica-de-conteudo ---

    def test_conteudo_matches_fabrica(self, router: ChatRouter) -> None:
        assert router.match_by_keywords("Preciso de conteúdo para minha página") == "fabrica-de-conteudo"

    def test_conteudo_without_accent_matches_fabrica(self, router: ChatRouter) -> None:
        assert router.match_by_keywords("preciso de conteudo para o instagram") == "fabrica-de-conteudo"

    def test_calendario_matches_fabrica(self, router: ChatRouter) -> None:
        assert router.match_by_keywords("Me ajuda a montar um calendário editorial") == "fabrica-de-conteudo"

    def test_post_matches_fabrica(self, router: ChatRouter) -> None:
        assert router.match_by_keywords("Quero criar posts para o feed") == "fabrica-de-conteudo"

    def test_reels_matches_fabrica(self, router: ChatRouter) -> None:
        assert router.match_by_keywords("Cria um roteiro de reels para mim") == "fabrica-de-conteudo"

    def test_carrossel_matches_fabrica(self, router: ChatRouter) -> None:
        assert router.match_by_keywords("Como fazer um carrossel bacana?") == "fabrica-de-conteudo"

    def test_legenda_matches_fabrica(self, router: ChatRouter) -> None:
        assert router.match_by_keywords("Preciso de uma legenda criativa") == "fabrica-de-conteudo"

    def test_gancho_matches_fabrica(self, router: ChatRouter) -> None:
        assert router.match_by_keywords("Qual o melhor gancho para atrair seguidores?") == "fabrica-de-conteudo"

    # --- diagnostico-perfil ---

    def test_metrica_matches_diagnostico(self, router: ChatRouter) -> None:
        assert router.match_by_keywords("Quero entender minhas métricas") == "diagnostico-perfil"

    def test_metrica_without_accent_matches_diagnostico(self, router: ChatRouter) -> None:
        assert router.match_by_keywords("quero ver minhas metricas do instagram") == "diagnostico-perfil"

    def test_diagnostico_matches_diagnostico(self, router: ChatRouter) -> None:
        assert router.match_by_keywords("Pode fazer um diagnóstico do meu perfil?") == "diagnostico-perfil"

    def test_engajamento_matches_diagnostico(self, router: ChatRouter) -> None:
        assert router.match_by_keywords("Meu engajamento está muito baixo") == "diagnostico-perfil"

    def test_instagram_matches_diagnostico(self, router: ChatRouter) -> None:
        assert router.match_by_keywords("Como melhorar meu instagram?") == "diagnostico-perfil"

    def test_concorrente_matches_diagnostico(self, router: ChatRouter) -> None:
        assert router.match_by_keywords("Analisa os meus concorrentes") == "diagnostico-perfil"

    def test_analise_matches_diagnostico(self, router: ChatRouter) -> None:
        assert router.match_by_keywords("Preciso de uma análise do meu perfil") == "diagnostico-perfil"

    def test_relatorio_matches_diagnostico(self, router: ChatRouter) -> None:
        assert router.match_by_keywords("Gera um relatório de desempenho") == "diagnostico-perfil"

    # --- maquina-clientes ---

    def test_contrato_matches_maquina(self, router: ChatRouter) -> None:
        assert router.match_by_keywords("Preciso de um contrato para meu cliente") == "maquina-clientes"

    def test_preco_matches_maquina(self, router: ChatRouter) -> None:
        assert router.match_by_keywords("Como precificar meu serviço?") == "maquina-clientes"

    def test_preco_without_accent_matches_maquina(self, router: ChatRouter) -> None:
        assert router.match_by_keywords("como definir o preco do meu servico") == "maquina-clientes"

    def test_proposta_matches_maquina(self, router: ChatRouter) -> None:
        assert router.match_by_keywords("Ajuda a montar uma proposta comercial") == "maquina-clientes"

    def test_onboarding_matches_maquina(self, router: ChatRouter) -> None:
        assert router.match_by_keywords("Quero melhorar meu onboarding") == "maquina-clientes"

    def test_cliente_matches_maquina(self, router: ChatRouter) -> None:
        assert router.match_by_keywords("Como captar mais clientes?") == "maquina-clientes"

    def test_juridico_matches_maquina(self, router: ChatRouter) -> None:
        assert router.match_by_keywords("Tem alguma cláusula jurídica importante?") == "maquina-clientes"

    def test_boas_vindas_matches_maquina(self, router: ChatRouter) -> None:
        assert router.match_by_keywords("Cria um kit de boas vindas") == "maquina-clientes"

    # --- Direct squad code match ---

    def test_direct_squad_code_fabrica(self, router: ChatRouter) -> None:
        assert router.match_by_keywords("Quero falar com fabrica-de-conteudo") == "fabrica-de-conteudo"

    def test_direct_squad_code_diagnostico(self, router: ChatRouter) -> None:
        assert router.match_by_keywords("diagnostico-perfil por favor") == "diagnostico-perfil"

    def test_direct_squad_code_maquina(self, router: ChatRouter) -> None:
        assert router.match_by_keywords("maquina-clientes") == "maquina-clientes"

    # --- No match ---

    def test_no_match_returns_none(self, router: ChatRouter) -> None:
        assert router.match_by_keywords("Olá, tudo bem?") is None

    def test_empty_message_returns_none(self, router: ChatRouter) -> None:
        assert router.match_by_keywords("") is None

    def test_unrelated_message_returns_none(self, router: ChatRouter) -> None:
        assert router.match_by_keywords("Qual é a capital da França?") is None


class TestRoute:
    """Tests for the async route method."""

    @pytest.mark.asyncio
    async def test_route_high_confidence_keyword_match(self, router: ChatRouter) -> None:
        result = await router.route("Quero criar conteúdo novo")
        assert result["squad_code"] == "fabrica-de-conteudo"
        assert result["confidence"] == "high"
        assert result["explanation"]

    @pytest.mark.asyncio
    async def test_route_no_match_without_api_key(self, router: ChatRouter) -> None:
        result = await router.route("Olá, tudo bem?")
        assert result["squad_code"] is None
        assert result["confidence"] == "low"
        assert result["explanation"]

    @pytest.mark.asyncio
    async def test_route_metrica_diagnostico(self, router: ChatRouter) -> None:
        result = await router.route("Quero analisar minhas métricas")
        assert result["squad_code"] == "diagnostico-perfil"
        assert result["confidence"] == "high"

    @pytest.mark.asyncio
    async def test_route_contrato_maquina(self, router: ChatRouter) -> None:
        result = await router.route("Preciso de um contrato profissional")
        assert result["squad_code"] == "maquina-clientes"
        assert result["confidence"] == "high"
