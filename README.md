# SocialForge

**Seu time de IA para social media.** 11 agentes especializados em conteudo, diagnostico e gestao de clientes, tudo visual num escritorio pixel art. Funciona 100% local com Claude Code Desktop, sem API key extra.

## O que e o SocialForge?

SocialForge e um time de agentes de IA que trabalham pra voce. Voce descreve o que precisa no Claude Code Desktop, os agentes aparecem no escritorio pixel art e comecam a trabalhar. Voce acompanha tudo em tempo real e aprova cada etapa.

**Zero configuracao de API.** O Claude Code Desktop que voce ja usa e o cerebro. Sem custo extra.

### 3 Times, 11 Agentes

| Time | O que faz | Agentes |
|------|-----------|---------|
| Fabrica de Conteudo 🔥 | Calendario editorial, copy, roteiros de stories | Sol, Luna, Davi, Bia, Leo |
| Diagnostico de Perfil 🔬 | Analise de metricas, concorrentes, plano de acao | Sherlock, Nina, Max |
| Maquina de Clientes 💼 | Precificacao, contratos, onboarding | Rafa, Clara, Dani |

## Requisitos

- Claude Code Desktop (plano Pro ou Max)
- Python 3.13+
- Node.js 20+
- Git

## Instalacao

### Opcao 1: Auto-instalador (recomendado)

```bash
git clone https://github.com/Bacjtracj/Socialforge.git
cd Socialforge
python setup.py
```

O script verifica tudo, instala dependencias, compila o frontend e configura os hooks. Funciona em Windows, Mac e Linux.

### Opcao 2: Make (Linux/Mac)

```bash
git clone https://github.com/Bacjtracj/Socialforge.git
cd Socialforge
make setup
```

### Iniciar

```bash
# Com tmux (Linux/Mac):
make dev-tmux

# Ou com o auto-instalador:
python setup.py --start

# Ou manualmente (2 terminais):
# Terminal 1: cd backend && uv run -p 3.13 uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# Terminal 2: cd frontend && npm run dev
```

Abra no navegador: **http://localhost:8000** (tudo numa porta so)

Depois abra o Claude Code Desktop na pasta do projeto e comece a pedir!

## Como usar

Abra o Claude Code Desktop e converse normalmente. As skills dos squads sao ativadas automaticamente:

**Fabrica de Conteudo:**
```
Monta um calendario de Instagram pro meu cliente dentista, 5 posts por semana
```

**Diagnostico de Perfil:**
```
Faz um diagnostico completo do perfil @clinicaexemplo no Instagram
```

**Maquina de Clientes:**
```
Quanto cobrar pra gerenciar Instagram + trafego pago de uma clinica de estetica?
```

## Como funciona

```
Voce (Claude Code Desktop)
    |
    v
Skills ativadas automaticamente
    |
    v
Cada agente roda como subagent (Task tool)
    |
    v
Hooks capturam os eventos
    |
    v
Backend recebe via HTTP POST
    |
    v
Frontend mostra no escritorio pixel art via WebSocket
```

1. Voce escreve o que precisa
2. O SocialForge identifica o time certo e inicia
3. Os agentes aparecem no escritorio e comecam a trabalhar
4. Em cada etapa importante, o sistema pausa e pede sua aprovacao
5. Voce aprova, ajusta, e o time continua ate entregar tudo pronto

## Instalacao manual (sem make)

Se o `make install` falhar:

```bash
# Backend
cd backend
pip install -e ".[dev]"
cd ..

# Frontend
cd frontend
npm install
cd ..

# Hooks
cd hooks
chmod +x install.sh
./install.sh
cd ..
```

## Rodar sem tmux

```bash
# Terminal 1 - Backend
cd backend && make dev
# Ou: uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend && npm run dev
```

## Estrutura

```
socialforge/
├── backend/           # API (FastAPI + Python)
├── frontend/          # Escritorio pixel art (Next.js + PixiJS)
├── socialforge/       # Definicoes dos squads e agentes
│   └── squads/
│       ├── fabrica-de-conteudo/   # 5 agentes, 12 passos
│       ├── diagnostico-perfil/    # 3 agentes, 10 passos
│       └── maquina-clientes/      # 3 agentes, 9 passos
├── .claude/skills/    # Skills que o Claude Code executa
│   ├── fabrica-de-conteudo/
│   ├── diagnostico-perfil/
│   └── maquina-clientes/
├── hooks/             # Ponte entre Claude Code e o visualizador
└── Makefile           # Comandos de instalacao e execucao
```

## Variaveis de ambiente (opcional)

Nenhuma variavel e obrigatoria pro modo local! Opcionais:

| Variavel | Descricao |
|----------|-----------|
| `SUMMARY_ENABLED` | `false` (padrao) — desativa resumos por IA |
| `CLAUDE_OFFICE_DEBUG` | `1` para ativar logs dos hooks |

## Creditos

- Interface baseada no [Claude Office Visualizer](https://github.com/paulrobello/claude-office) por Paul Robello
- Framework de squads baseado no [OpenSquad](https://github.com/renatoasse/opensquad) por Renato Asse
- Squads e agentes por Joao Victor Mendes

## Licenca

MIT
