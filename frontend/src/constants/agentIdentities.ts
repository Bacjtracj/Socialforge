import type { AgentIdentity } from "@/types/squads";

export const AGENT_IDENTITIES: Record<string, Record<string, AgentIdentity>> = {
  "fabrica-de-conteudo": {
    estrategista: { squadAgentId: "estrategista", displayName: "Sol Estratégia", color: "#FFD700", spriteKey: "sol-estrategia", icon: "🧠" },
    pesquisador: { squadAgentId: "pesquisador", displayName: "Luna Pesquisa", color: "#87CEEB", spriteKey: "luna-pesquisa", icon: "🔍" },
    copywriter: { squadAgentId: "copywriter", displayName: "Davi Copy", color: "#4CAF50", spriteKey: "davi-copy", icon: "✍️" },
    "roteirista-stories": { squadAgentId: "roteirista-stories", displayName: "Bia Stories", color: "#FF69B4", spriteKey: "bia-stories", icon: "📱" },
    revisor: { squadAgentId: "revisor", displayName: "Léo Revisão", color: "#FF8C00", spriteKey: "leo-revisao", icon: "✅" },
  },
  "diagnostico-perfil": {
    investigador: { squadAgentId: "investigador", displayName: "Sherlock Social", color: "#8B4513", spriteKey: "sherlock-social", icon: "🕵️" },
    analista: { squadAgentId: "analista", displayName: "Nina Números", color: "#9C27B0", spriteKey: "nina-numeros", icon: "📊" },
    "estrategista-perfil": { squadAgentId: "estrategista-perfil", displayName: "Max Plano", color: "#1A237E", spriteKey: "max-plano", icon: "🎯" },
  },
  "maquina-clientes": {
    consultor: { squadAgentId: "consultor", displayName: "Rafa Preço", color: "#2E7D32", spriteKey: "rafa-preco", icon: "💰" },
    juridico: { squadAgentId: "juridico", displayName: "Clara Contrato", color: "#880E4F", spriteKey: "clara-contrato", icon: "📋" },
    onboarding: { squadAgentId: "onboarding", displayName: "Dani Welcome", color: "#00BCD4", spriteKey: "dani-welcome", icon: "🤝" },
  },
};
