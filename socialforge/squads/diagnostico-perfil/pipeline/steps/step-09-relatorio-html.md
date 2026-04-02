---
id: step-09
name: "Geração do Relatório HTML"
type: agent
agent: analista
---

# Step 09 — Relatório HTML Interativo

## Agente: Nina Números

### Antes de gerar
Perguntar: "Tem paleta de cores da marca? (cor primária e secundária em hex). Se não, uso um visual escuro profissional padrão."

### Ações
1. Consultar pipeline/data/estrutura-relatorio-html.md pra design system
2. Gerar HTML completo com Chart.js (NUNCA barras CSS)
3. Incluir: KPIs, gráficos comparativos, doughnut de interações, bloco comportamental, gargalo, insights em accordion, plano de ação
4. KPIs com counter animado (requestAnimationFrame)
5. Responsivo (mobile-first)
6. Salvar em output/relatorio-perfil.html

### Output
Arquivo HTML interativo. Salvar em `output/relatorio-perfil.html`
