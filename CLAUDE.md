# CLAUDE.md

## Idioma
- SEMPRE responda em português brasileiro em TODAS as interações.
- Nunca use inglês a menos que o usuário peça explicitamente.

## Overview

SocialForge é um time de agentes de IA para social media. Funciona 100% local com Claude Code Desktop, sem API key externa. Os agentes rodam como subagents (via Task tool) e aparecem no escritório pixel art em tempo real.

## Como funciona (modo local)

1. O usuário pede algo no Claude Code Desktop (ex: "planejar conteúdo do mês pro dentista")
2. A skill do squad é ativada automaticamente
3. Cada agente roda como um subagent via Task tool
4. Os hooks capturam os eventos e mandam pro backend
5. O frontend mostra os agentes trabalhando no escritório pixel art

**Não precisa de ANTHROPIC_API_KEY.** O Claude Code Desktop é o cérebro.

## Skills dos Squads

As skills estão em `.claude/skills/`. São ativadas automaticamente:

- **fabrica-de-conteudo**: Calendário editorial, copies, roteiros de stories (5 agentes: Sol, Luna, Davi, Bia, Léo)
- **diagnostico-perfil**: Análise de perfil, métricas, plano de ação (3 agentes: Sherlock, Nina, Max)
- **maquina-clientes**: Precificação, contratos, onboarding (3 agentes: Rafa, Clara, Dani)

## Comandos

```bash
# Instalar tudo
make install

# Rodar (recomendado - usa tmux)
make dev-tmux

# Rodar sem tmux
# Terminal 1: cd backend && make dev
# Terminal 2: cd frontend && npm run dev

# Instalar hooks
cd hooks && ./install.sh

# Parar
make dev-tmux-kill
```

## Comportamento

- Fale de forma natural, como no WhatsApp com um colega de profissão
- Seja direto e prático, sem enrolação
- Quando entregar um trabalho (calendário, diagnóstico, proposta), entregue COMPLETO
- Não peça confirmação pra cada micro-etapa, só nos checkpoints definidos na skill
- Use os nomes dos agentes (Sol, Luna, Davi...) pra criar subagents — isso faz eles aparecerem no escritório

## Economia de Tokens

- Respostas diretas, sem repetir o que o usuário disse
- Sem saudações desnecessárias
- Entregas sem narração prévia ("Vou criar..." — não, só crie)
- Use o mínimo de tool calls possível

## Debugging

- Logs dos hooks: `~/.claude/claude-office-hooks.log` (ativar com `CLAUDE_OFFICE_DEBUG=1`)
- Backend: `http://localhost:8000/health`
- Frontend: `http://localhost:3333`
