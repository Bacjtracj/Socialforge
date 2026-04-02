"""Fixed visual identities for all SocialForge agents."""

from app.models.squads import AgentIdentity

# All 11 agents with fixed visual identity
_IDENTITIES: dict[str, dict[str, AgentIdentity]] = {
    "fabrica-de-conteudo": {
        "estrategista": AgentIdentity(
            squad_agent_id="estrategista",
            display_name="Sol Estratégia",
            color="#FFD700",
            sprite_key="sol-estrategia",
            icon="🧠",
        ),
        "pesquisador": AgentIdentity(
            squad_agent_id="pesquisador",
            display_name="Luna Pesquisa",
            color="#87CEEB",
            sprite_key="luna-pesquisa",
            icon="🔍",
        ),
        "copywriter": AgentIdentity(
            squad_agent_id="copywriter",
            display_name="Davi Copy",
            color="#4CAF50",
            sprite_key="davi-copy",
            icon="✍️",
        ),
        "roteirista-stories": AgentIdentity(
            squad_agent_id="roteirista-stories",
            display_name="Bia Stories",
            color="#FF69B4",
            sprite_key="bia-stories",
            icon="📱",
        ),
        "revisor": AgentIdentity(
            squad_agent_id="revisor",
            display_name="Léo Revisão",
            color="#FF8C00",
            sprite_key="leo-revisao",
            icon="✅",
        ),
    },
    "diagnostico-perfil": {
        "investigador": AgentIdentity(
            squad_agent_id="investigador",
            display_name="Sherlock Social",
            color="#8B4513",
            sprite_key="sherlock-social",
            icon="🕵️",
        ),
        "analista": AgentIdentity(
            squad_agent_id="analista",
            display_name="Nina Números",
            color="#9C27B0",
            sprite_key="nina-numeros",
            icon="📊",
        ),
        "estrategista-perfil": AgentIdentity(
            squad_agent_id="estrategista-perfil",
            display_name="Max Plano",
            color="#1A237E",
            sprite_key="max-plano",
            icon="🎯",
        ),
    },
    "maquina-clientes": {
        "consultor": AgentIdentity(
            squad_agent_id="consultor",
            display_name="Rafa Preço",
            color="#2E7D32",
            sprite_key="rafa-preco",
            icon="💰",
        ),
        "juridico": AgentIdentity(
            squad_agent_id="juridico",
            display_name="Clara Contrato",
            color="#880E4F",
            sprite_key="clara-contrato",
            icon="📋",
        ),
        "onboarding": AgentIdentity(
            squad_agent_id="onboarding",
            display_name="Dani Welcome",
            color="#00BCD4",
            sprite_key="dani-welcome",
            icon="🤝",
        ),
    },
}


class AgentRegistry:
    """Provides fixed visual identities for SocialForge agents."""

    def get_identity(self, squad_code: str, agent_id: str) -> AgentIdentity | None:
        """Get the fixed identity for a squad agent."""
        squad_agents = _IDENTITIES.get(squad_code)
        if not squad_agents:
            return None
        return squad_agents.get(agent_id)

    def total_agents(self) -> int:
        """Total number of registered agent identities."""
        return sum(len(agents) for agents in _IDENTITIES.values())
