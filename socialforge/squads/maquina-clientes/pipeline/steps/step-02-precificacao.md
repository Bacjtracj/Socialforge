---
id: step-02
name: "Análise de Precificação"
type: agent
agent: consultor
---

# Step 02 — Precificação

## Agente: Rafa Preço

### Se o pedido é "quanto cobro por X"
1. Entender o escopo completo (o que exatamente vai entregar)
2. Perguntar nível de experiência do profissional
3. Estimar horas reais (+30%)
4. Consultar tabela de preços em pipeline/data/tabela-precos-mercado.md
5. Calcular valor-hora implícito
6. Sugerir 3 faixas (piso, recomendado, premium)
7. Dar recomendação direta

### Se o pedido é "vale a pena essa proposta?"
1. Calcular valor total que vai receber
2. Estimar horas reais
3. Calcular valor-hora
4. Comparar com régua de mercado
5. Analisar intangíveis
6. Dar veredito

### Output
Análise completa de precificação. Salvar em `output/analise-precificacao.md`
Se pedido, montar proposta comercial em `output/proposta-comercial.md`
