---
id: step-11
name: "Revisão de Qualidade"
type: agent
agent: revisor
---

# Step 11 — Revisão Final

## Agente: Léo Revisão

### Ações
1. Aplicar os 3 filtros obrigatórios (foco, antivalidação, especificidade) em cada peça
2. Verificar expressões proibidas
3. Validar ganchos e CTAs
4. Pontuar qualidade geral (0-10)
5. Listar itens que precisam correção
6. Se score abaixo de 6, devolver pro agente responsável

### Output
Relatório de revisão com score, aprovados e reprovados. Salvar em `output/revisao-final.md`
