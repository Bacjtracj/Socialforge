---
id: step-02
name: "Investigação de Concorrentes"
type: agent
agent: investigador
---

# Step 02 — Investigação de Concorrentes

## Agente: Sherlock Social

Se o usuário forneceu URLs de perfis, executar investigação completa.
Se não forneceu URLs (só métricas), pular este step.

### Ações
1. web_fetch em cada URL fornecida
2. web_search pra complementar dados
3. Analisar cada perfil seguindo as 8 seções da análise narrativa
4. Se múltiplos perfis, fazer comparação final

### Output
Análise narrativa completa de cada perfil. Salvar em `output/investigacao-concorrentes.md`
