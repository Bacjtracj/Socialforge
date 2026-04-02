# Estrutura do Relatório HTML — Método Abelha

## Dependências

```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
```

---

## Design System

### Modo 1 — Marca própria fornecida

Quando a usuária enviar paleta de cores, aplicar integralmente. Exemplo de implementação completa (`@deborapimenta`):

```css
:root {
  --primary: #2C1810;
  --secondary: #5C3D2E;
  --accent: #C4956A;
  --blush: #E8C9B8;
  --blush-light: #F5EDE7;
  --bg: #FAF7F4;
  --surface: #FFFFFF;
  --surface2: #F5EDE7;
  --border: #E8C9B8;
  --text: #2C1810;
  --text2: #5C3D2E;
  --text3: #C4956A;
  --green: #4A7C59;
  --red: #B85C52;
  /* Períodos nos gráficos */
  --anterior: #C4956A;
  --atual: #5C3D2E;
}
```

**Regras desta identidade:**
- Header: gradiente `linear-gradient(135deg, #2C1810 0%, #5C3D2E 60%, #C4956A 100%)`
- Topbar: fundo `var(--primary)`, handle em Playfair Display, cor `var(--blush)`
- KPI cards: fundo `var(--primary)`, valor em `var(--blush-light)`, fonte Playfair Display
- Gargalo card: fundo `var(--primary)`, título Playfair Display em blush
- Post cards: borda esquerda `3px solid var(--accent)`
- Callouts: borda esquerda colorida + fundo `var(--blush-light)`
- Footer: fundo `var(--primary)`, texto `var(--blush)`
- Fontes: Playfair Display (títulos, KPI values, citações) + Inter (corpo)

```html
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
```

### Modo 2 — Default escuro (sem marca fornecida)

```css
:root {
  --anterior: #FFA07A;
  --atual: #45B7D1;
  --bg: #0F1117;
  --surface: #1A1D27;
  --surface2: #242836;
  --border: #2E3345;
  --text: #E5E7EB;
  --text2: #9CA3AF;
  --text3: #6B7280;
  --green: #22C55E;
  --red: #EF4444;
  --yellow: #F59E0B;
  --blue: #3B82F6;
  font-family: 'Inter', sans-serif;
}
```

```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
```

---

## Seções Obrigatórias — Ordem e Conteúdo

### 1. Topbar (sticky)
- Nome do perfil (@handle)
- Plataforma (Instagram / TikTok)
- Período analisado
- "Gerado com Método Abelha"

### 2. Header
- Título: "Análise de Métricas — [Período]"
- Subtítulo: número do relatório se aplicável
- Dois períodos lado a lado com suas datas

### 3. KPIs Principais
Grid de cards, cada card com:
- Nome da métrica
- Valor do período atual (grande, destacado)
- Valor do período anterior (pequeno, cinza)
- Badge de variação % (verde se positivo, vermelho se negativo)

Métricas obrigatórias nos KPIs: Visualizações, Alcance, Interações, Seguidores, Taxa de Engajamento, Posts.

```html
<!-- Exemplo de card KPI -->
<div class="kpi-card">
  <span class="kpi-label">Alcance</span>
  <span class="kpi-value" data-target="186053">0</span>
  <span class="kpi-prev">Anterior: 124.891</span>
  <span class="kpi-badge positive">+49,0%</span>
</div>
```

Counter animado obrigatório — usar `requestAnimationFrame` ou `IntersectionObserver`.

### 4. Comparativo Visual dos Dois Períodos
Gráfico de barras agrupadas (Chart.js `type: 'bar'`) com:
- Eixo X: métricas principais
- Dois datasets: Período Anterior (#FFA07A) e Período Atual (#45B7D1)
- Tooltips com valor exato e variação %

### 5. Distribuição das Interações
Doughnut chart com: Curtidas, Comentários, Compartilhamentos, Salvamentos.
Mostrar valor absoluto e % de cada fatia.

### 6. Eficiência por Post
Barras agrupadas comparando anterior vs atual:
- Visualizações/post
- Alcance/post
- Interações/post

Incluir variação % acima de cada par de barras.

### 7. Evolução de Seguidores
Barra comparativa simples — anterior vs atual.
Destacar a variação absoluta em card separado.

### 8. Bloco Comportamental
Card dedicado com fundo levemente diferenciado. Conteúdo:
- Dias/horários dominantes
- Formato dominante (com dado que justifica)
- Gatilho dominante identificado

Três afirmações em destaque visual:
```
✓ REPETIR: [comportamento]
✗ PARAR: [comportamento]
? TESTAR: [hipótese]
```

### 9. Gargalo Principal
Card destacado — maior que os outros, borda colorida.
Um único gargalo nomeado com explicação de 2–3 linhas.
Cor da borda: vermelho se urgente, amarelo se moderado.

### 10. Insights Estratégicos
Accordion clicável. Cada insight tem:
- Badge de status: `positivo` (verde) / `atenção` (vermelho) / `oportunidade` (amarelo) / `padrão` (azul)
- Título direto (não pergunta, não vago)
- Texto analítico com números específicos em `<strong>`
- Implicação prática ao final

Mínimo 5 insights. Não repetir dados — cruzar dados.

### 11. Plano de Ação
Três cards separados:
1. **7 dias** — ações imediatas
2. **30 dias** — movimento estratégico
3. **Testes** — hipóteses com critério de sucesso

### 12. Footer
- "Análise gerada com Método Abelha"
- Nome da social media responsável (se fornecido)
- Data de geração

---

## Regras Técnicas

- **Nunca** usar barras CSS para simular gráficos — sempre Chart.js
- **Nunca** usar `height` fixo em containers que podem ter conteúdo variável — usar `min-height`
- **Sempre** usar caminhos relativos para assets externos (CDN only)
- Gráficos devem ter tooltips com valores formatados (ex: `1.786.053` não `1786053`)
- Responsivo: funciona em mobile (min-width: 320px)
- Arquivo único `.html` — CSS e JS inline ou no mesmo arquivo

---

## Formatação de Números

```javascript
// Formatador padrão para valores brasileiros
function fmt(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1).replace('.', ',') + 'M';
  if (n >= 1000) return (n / 1000).toFixed(1).replace('.', ',') + 'K';
  return n.toLocaleString('pt-BR');
}

// Badge de variação
function badge(pct) {
  const cls = pct >= 0 ? 'positive' : 'negative';
  const sign = pct >= 0 ? '+' : '';
  return `<span class="badge ${cls}">${sign}${pct.toFixed(1)}%</span>`;
}
```

---

## Checklist HTML

- [ ] Chart.js carregando via CDN?
- [ ] Cores de período respeitadas (#FFA07A e #45B7D1)?
- [ ] KPIs com counter animado?
- [ ] Todos os gráficos são Chart.js (não CSS)?
- [ ] Accordion dos insights funciona (abrir/fechar)?
- [ ] Gargalo tem destaque visual separado dos insights?
- [ ] Bloco comportamental inclui as 3 afirmações (repetir/parar/testar)?
- [ ] Números formatados em pt-BR?
- [ ] Responsivo em mobile?
- [ ] Arquivo salvo em `/mnt/user-data/outputs/`?
