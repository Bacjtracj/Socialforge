# Modelo de Briefing — Coleta de Informações do Cliente

## Perguntas Obrigatórias (sem essas, não avança)

### Bloco 1: Sobre o Negócio
1. **Nicho/segmento:** O que o cliente faz? (ex: dentista, loja de roupas, advogado trabalhista)
2. **Público final:** Pra quem ele vende? (ex: mulheres 25-40 classe B, empresários de pequenas empresas)
3. **Diferencial:** O que ele faz de diferente dos concorrentes? (se não souber, tudo bem)
4. **Objetivo do mês:** O que ele mais precisa agora? (crescer seguidores / engajar a base / vender produto ou serviço / construir autoridade)

### Bloco 2: Sobre o Conteúdo
5. **Mês/ano do planejamento:** Qual mês vamos planejar?
6. **Frequência de posts:** Quantos posts por semana? (3, 4, 5, 6 ou diário?)
7. **Redes sociais:** Quais plataformas? (Instagram, TikTok, LinkedIn, YouTube, Facebook)
8. **Pilares de conteúdo:** Quais temas o cliente quer abordar? (se não souber, sugerimos)
9. **Tom de voz:** Como a marca fala? (direto, educativo, íntimo, provocativo, técnico, leve)

### Bloco 3: Sobre Ofertas e Campanhas
10. **Oferta ativa:** Tem algo sendo vendido ou lançado agora? Qual?
11. **Promoções planejadas:** Alguma promoção ou data especial prevista pro mês?
12. **Lançamento:** Vai lançar produto, serviço ou evento no mês?

### Bloco 4: Sobre Stories
13. **Faz stories:** O cliente posta stories? Com que frequência?
14. **Quem aparece:** O dono aparece na câmera ou prefere só texto/arte?
15. **Rotina filmável:** Tem bastidores interessantes pra mostrar? (atendimento, processo, dia a dia)

## Perguntas Opcionais (melhoram a qualidade mas não travam)

16. **Concorrentes:** Quem são os 2-3 principais concorrentes no Instagram?
17. **Conteúdo que deu certo:** Algum post que já performou bem? Qual?
18. **Conteúdo proibido:** Tem algo que NÃO pode postar? (regulamentação, preferência)
19. **Hashtags:** Usa hashtags específicas? Quais?
20. **Ferramentas:** Usa Canva, CapCut, mLabs ou alguma outra ferramenta?

## Como Tratar Respostas Incompletas

- Se faltou nicho, público ou objetivo: PERGUNTAR antes de continuar
- Se faltou pilares: SUGERIR 4-5 pilares com base no nicho
- Se faltou tom de voz: MOSTRAR os 6 tons com exemplo e pedir pra escolher
- Se faltou informação de stories: ASSUMIR que faz stories e criar roteiro adaptável
- Se faltou frequência: SUGERIR 3-4 posts/semana como padrão

## Output

Salvar as respostas em formato YAML estruturado:

```yaml
cliente:
  nicho: ""
  publico_final: ""
  diferencial: ""
  objetivo_mes: ""

conteudo:
  mes_ano: ""
  posts_semana: 0
  redes: []
  pilares: []
  tom_voz: ""

ofertas:
  oferta_ativa: ""
  promocoes: ""
  lancamento: ""

stories:
  faz_stories: true/false
  frequencia: ""
  dono_aparece: true/false
  bastidores: ""

opcional:
  concorrentes: []
  conteudo_bom: ""
  proibicoes: ""
  hashtags: []
  ferramentas: []
```
