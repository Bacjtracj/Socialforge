---
id: step-01
name: "O que Você Precisa Hoje?"
type: checkpoint
---

# Step 01 — Entrada

O usuário pode precisar de uma coisa ou de todas. Perguntar:

```
O que você precisa hoje?

1. Precificar um serviço (quanto cobrar por X)
2. Analisar se uma proposta vale a pena (me ofereceram Y)
3. Revisar um contrato antes de enviar pro cliente
4. Gerar o manual de onboarding de um cliente novo
5. Pacote completo (precificar + contrato + onboarding)
```

Dependendo da escolha, pular steps que não se aplicam:
- Opção 1 ou 2: executa step-02 e step-03, depois pula pra step-09
- Opção 3: pula pra step-04
- Opção 4: pula pra step-07
- Opção 5: executa tudo em sequência
