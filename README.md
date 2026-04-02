# SocialForge

**Seu time de IA para social media.** Agentes especializados em conteudo, diagnostico e gestao de clientes, tudo visual num escritorio pixel art.

<!-- TODO: adicionar GIF animado do office com agentes trabalhando -->

## O que e o SocialForge?

SocialForge e um time de agentes de IA que trabalham pra voce. Voce descreve o que precisa, os agentes aparecem no escritorio e comecam a trabalhar. Voce acompanha tudo em tempo real e aprova cada etapa.

### 3 Times Prontos

| Time | O que faz | Agentes |
|------|-----------|---------|
| Fabrica de Conteudo | Calendario editorial, copy, roteiros de stories | Sol, Luna, Davi, Bia, Leo |
| Diagnostico de Perfil | Analise de metricas, concorrentes, plano de acao | Sherlock, Nina, Max |
| Maquina de Clientes | Precificacao, contratos, onboarding | Rafa, Clara, Dani |

## Instalacao

Voce precisa de:
- Python 3.13+
- Node.js 20+
- Uma chave da API do Claude ([pegar aqui](https://console.anthropic.com/))

```bash
git clone https://github.com/SEU-USUARIO/socialforge.git
cd socialforge
make install
```

## Como usar

1. Configure sua chave:
```bash
export ANTHROPIC_API_KEY="sua-chave-aqui"
```

2. Inicie o SocialForge:
```bash
make dev
```

3. Abra no navegador: **http://localhost:3333**

4. Escolha um time ou descreva o que precisa no chat!

## Como funciona

1. Voce escreve o que precisa (ex: "planejar conteudo do mes pro meu cliente dentista")
2. O SocialForge identifica o time certo e inicia
3. Os agentes aparecem no escritorio e comecam a trabalhar
4. Em cada etapa importante, o sistema pausa e pede sua aprovacao
5. Voce aprova, ajusta, e o time continua ate entregar tudo pronto

## Deploy na VPS

Com Docker (um comando):
```bash
docker compose up -d
```

Sem Docker:
```bash
export ANTHROPIC_API_KEY="sua-chave"
make install
make dev
```

Acesse: `http://IP-DA-SUA-VPS:3333`

## Variaveis de ambiente

| Variavel | Obrigatoria | Descricao |
|----------|-------------|-----------|
| `ANTHROPIC_API_KEY` | Sim | Chave da API do Claude |
| `SOCIALFORGE_PORT` | Nao | Porta do frontend (padrao: 3333) |

## Estrutura

```
socialforge/
├── backend/           # API (FastAPI + Python)
├── frontend/          # Interface (Next.js + PixiJS)
├── socialforge/       # Definicoes dos squads e agentes
│   └── squads/
│       ├── fabrica-de-conteudo/
│       ├── diagnostico-perfil/
│       └── maquina-clientes/
├── hooks/             # Integracao com Claude Code
└── docker-compose.yml # Deploy com um comando
```

## Creditos

- Interface baseada no [Claude Office Visualizer](https://github.com/paulrobello/claude-office) por Paul Robello
- Framework de squads baseado no [OpenSquad](https://github.com/renatoasse/opensquad) por Renato Asse
- Squads e agentes por Joao Victor Mendes

## Licenca

MIT
