# 04 — TAM / SAM / SOM, Precificação, Custo de Uso e Valor Percebido

Dimensionamento de mercado e modelo financeiro da **Inclua Beauty AI**.

> **Aviso metodológico:** os números são **estimativas de ordem de grandeza**
> para planejamento, construídas com premissas explícitas e mescla de abordagens
> *top-down* e *bottom-up*. Devem ser validados com dados primários (entrevistas,
> pilotos) e fontes atualizadas (relatórios de indústria, preços GCP vigentes)
> antes de compromissos de investimento. Câmbio de referência: **USD 1 ≈ BRL 5,50**.

---

## 1. Estratégia de dimensionamento

A Inclua Beauty vive na interseção de dois mercados:

1. **Mercado de embalagens de cosméticos** (o "objeto" analisado).
2. **Mercado de software/serviços de acessibilidade e compliance** (o "valor"
   entregue).

Como é uma **categoria nova** (não há um mercado de "software de acessibilidade
de packaging" já medido), o TAM é estimado como a **fração de gasto que empresas
de beleza dedicariam a inteligência/compliance de acessibilidade de embalagem** —
derivada do tamanho da indústria e do número de empresas/SKUs.

---

## 2. TAM — Total Addressable Market

### 2.1 Abordagem A (top-down, por indústria de embalagem cosmética)

- Mercado global de **embalagens de cosméticos**: ordem de **~US$ 30–40 bilhões/ano**
  (estimativa de indústria; validar em relatório atualizado).
- Premissa: se **0,5% a 1,0%** desse gasto migrar para *inteligência/compliance de
  acessibilidade* (software + serviços) conforme a regulação aperta:

| Cenário | % do gasto de packaging | TAM global (SW/serviços a11y) |
|---|---:|---:|
| Conservador | 0,5% | **~US$ 150–200 mi/ano** |
| Base | 0,75% | **~US$ 225–300 mi/ano** |
| Otimista | 1,0% | **~US$ 300–400 mi/ano** |

### 2.2 Abordagem B (bottom-up, por empresas × contrato)

- Universo global de empresas de beleza/cosmético/higiene relevantes
  (marcas + converters + agências): **~50.000** organizações endereçáveis.
- Ticket médio anual plausível (mix self-service + enterprise): **~US$ 5.000/ano**.
- TAM ≈ 50.000 × US$ 5.000 = **~US$ 250 mi/ano**.

**Convergência:** as duas abordagens apontam um **TAM global da ordem de
US$ 250–300 milhões/ano** (≈ **R$ 1,4–1,7 bilhão/ano**) para a categoria de
inteligência de acessibilidade de embalagens de beleza — expansível para outros
setores de bens de consumo (alimentos, farma, HPC), o que multiplicaria o TAM.

---

## 3. SAM — Serviceable Available Market

Recorte do TAM que a Inclua Beauty **pode atender** com o produto atual
(português + normas BR/UE, foco beleza, GCP), nos primeiros anos:

- Foco geográfico inicial: **Brasil + América Latina + entrada UE (EAA)**.
- Foco de segmento: marcas médias/grandes, converters e agências (deixando de
  fora, no curto prazo, micro/indie sem orçamento).

| Recorte | Premissa | Valor |
|---|---|---:|
| Brasil (beleza é um dos maiores mercados do mundo) | ~15–20% do TAM endereçável ativável | **~US$ 40–55 mi/ano** |
| + LatAm + early UE | adicional | **~US$ 60–80 mi/ano total** |

**SAM ≈ US$ 60–80 milhões/ano (≈ R$ 330–440 mi/ano).**

---

## 4. SOM — Serviceable Obtainable Market

Fração do SAM realisticamente capturável em **3–5 anos**, dada capacidade de
execução, GTM e concorrência (evangelização de categoria).

| Ano | Premissa de penetração do SAM | Clientes pagantes (aprox.) | Receita anual (ARR) |
|---|---|---:|---:|
| Ano 1 | pilotos/design partners | 8–15 | **R$ 0,6–1,5 mi** |
| Ano 2 | early adopters | 30–60 | **R$ 3–6 mi** |
| Ano 3 | expansão + canal | 100–180 | **R$ 10–18 mi** |
| Ano 5 | liderança de categoria (~3–5% do SAM) | 300–500 | **R$ 30–55 mi** |

**SOM (Ano 3) ≈ R$ 10–18 milhões de ARR**; **Ano 5 ≈ R$ 30–55 milhões** — o que
representaria **~3–5% do SAM**, patamar realista para um líder de categoria nova.

```text
        TAM  ~R$ 1,4–1,7 bi/ano   (categoria global de a11y de packaging beleza)
        ██████████████████████████████████████████████████████
        SAM  ~R$ 330–440 mi/ano   (BR+LatAm+early UE, segmento alvo)
        ████████████████
        SOM  ~R$ 10–55 mi/ano     (obtenível em 3–5 anos)
        ██
```

---

## 5. Custo de uso (unit economics em GCP)

O custo variável dominante é a **inferência (Vertex AI/Gemini)** por análise. Uma
análise completa aciona ~10–13 agentes (alguns em paralelo). Estimativa por
análise:

### 5.1 Tokens por análise (estimativa)

| Etapa | Modelo | Tokens in | Tokens out |
|---|---|---:|---:|
| Ingestão multimodal (imagem+texto) | Flash | 3.000 | 1.000 |
| Categoria + decomposição | Flash | 4.000 | 1.500 |
| Fan-out análise (5 agentes) | Flash | 20.000 | 6.000 |
| Compliance + recomendação (RAG) | Pro | 12.000 | 4.000 |
| Score + relatório | Flash | 8.000 | 3.000 |
| **Total aprox.** | | **~47k** | **~15,5k** |

### 5.2 Custo de inferência por análise

> Preços Gemini são **por milhão de tokens** e mudam com frequência — **valide os
> valores vigentes no GCP**. Faixas de referência usadas aqui:
> Flash ≈ US$ 0,10–0,30 in / US$ 0,40–1,20 out por 1M; Pro ≈ US$ 1,25–2,50 in /
> US$ 5–10 out por 1M.

| Cenário | Custo IA/análise (USD) | Custo IA/análise (BRL) |
|---|---:|---:|
| Otimista (Flash-heavy, cache) | ~US$ 0,05 | ~R$ 0,28 |
| **Base** | **~US$ 0,15** | **~R$ 0,83** |
| Pesado (mais Pro, imagens grandes) | ~US$ 0,40 | ~R$ 2,20 |

Somando rateio de **infra fixa** (doc 02: ~US$ 275–610/mês) diluída no volume e
armazenamento/relatório, o **custo total por análise fica na casa de
R$ 0,50 – R$ 3,00** em regime. Isso é o pilar da margem: **preço de venda por
análise/assinatura fica 20–100x acima do custo marginal**.

### 5.3 Alavancas de FinOps

- **Context caching** do Gemini para a base normativa (reduz tokens in).
- **Roteamento Flash/Pro** (Pro só onde o raciocínio exige).
- **Batch/async** e escala a zero no Cloud Run.
- **Provisioned Throughput** só em volume alto (previsibilidade).
- **Monitor de custo/análise** (RNF-012) com alerta de teto.

---

## 6. Modelo de precificação

Modelo **híbrido**: assinatura (previsibilidade) + consumo (escala com uso) +
enterprise (valor). Alinhado a como cada segmento compra (doc 03).

### 6.1 Planos SaaS

| Plano | Público | Preço (BRL/mês) | Inclui | Análises/mês | Excedente |
|---|---|---:|---|---:|---:|
| **Free / Trial** | avaliação | R$ 0 | 1 projeto, marca d'água, sem export PDF | 5 | — |
| **Starter** | indie/D2C, agências pequenas | **R$ 490** | 3 usuários, export PDF, score, checklist | 50 | R$ 12/análise |
| **Professional** | marcas médias, estúdios | **R$ 1.900** | 10 usuários, RAG normativo, relatórios exec./regulatório, API básica | 250 | R$ 8/análise |
| **Business** | marcas grandes, converters | **R$ 6.900** | 30 usuários, SSO, base normativa dedicada, human-in-the-loop, benchmark | 1.200 | R$ 5/análise |
| **Enterprise** | multinacionais, setor público | **sob consulta** (a partir de ~R$ 15k/mês) | multi-tenant dedicado, CMEK, DPA, SLA, integrações PLM, white-label | ilimitado (fair use) | negociado |

### 6.2 Add-ons e serviços

| Item | Preço de referência |
|---|---|
| Onboarding + carga de base normativa customizada | R$ 15.000 – R$ 60.000 (one-time) |
| Consultoria de acessibilidade (especialista humano) | R$ 300 – R$ 600 / hora |
| Painel de teste com pessoas com deficiência (co-design) | R$ 5.000 – R$ 20.000 / rodada |
| Relatório de benchmark de categoria (dado de indústria) | R$ 20.000 – R$ 80.000 / edição |
| API/consumo avulso (pay-as-you-go) | R$ 5 – R$ 15 / análise conforme volume |

### 6.3 Racional de preço (value-based, não cost-plus)

O preço é ancorado no **valor/risco evitado**, não no custo (que é centavos):
uma única consultoria manual de acessibilidade de portfólio custa dezenas de
milhares de reais e leva semanas; um recall/reformulação ou exposição
regulatória custa muito mais. A Inclua Beauty entrega o mesmo diagnóstico em
minutos por uma fração do custo — logo, captura valor via assinatura, não via
custo marginal.

---

## 7. Preço de custo × preço de venda (margem)

| Métrica | Valor de referência |
|---|---:|
| Custo marginal por análise (base) | ~R$ 0,50 – R$ 3,00 |
| Preço médio por análise (planos) | ~R$ 5 – R$ 15 |
| **Margem bruta por análise** | **~70% – 95%** |
| Margem bruta de SaaS (com infra fixa diluída) | **~75% – 85%** |
| CAC alvo (enterprise) | R$ 15k – R$ 60k |
| LTV/CAC alvo | ≥ 3 (saudável para SaaS B2B) |
| Payback de CAC alvo | < 12–18 meses |

A estrutura é a de um **SaaS de margem alta**: o custo de IA é baixo e diluído, e
a receita recorrente escala com número de SKUs/portfólios analisados.

---

## 8. Valor percebido (por que o cliente paga muito mais que o custo)

| Fonte de valor | Quantificação percebida pelo cliente |
|---|---|
| **Risco regulatório evitado** (LBI/ANVISA/EAA/ADA) | multas, embargos e litígios evitados → dezenas a centenas de milhares de R$ |
| **Velocidade** (minutos vs. semanas de consultoria) | redução de time-to-market e horas de especialista |
| **Escala/padronização** | avaliar 1.000 SKUs com o mesmo rigor — impossível manualmente |
| **Reputação/ESG** | evita crise de imagem por exclusão; gera métrica de inclusão reportável |
| **Mercado ampliado** | produtos acessíveis alcançam PcD + 60% (público 60+, situacional) |
| **Rastreabilidade/defensabilidade** | laudo auditável com fontes → defesa jurídica |
| **Inovação acionável** | recomendações + prompts de mockup aceleram P&D |

**Regra de ouro do valor percebido:** o cliente compara o preço da assinatura
(milhares de R$/mês) com o custo de **uma** consultoria manual ou de **um**
incidente regulatório/reputacional — e a conta fecha com folga a favor do
software. Isso sustenta uma precificação value-based e margens altas.

---

## 9. Projeção financeira ilustrativa (cenário base)

| Ano | Clientes pagantes | Ticket médio anual | ARR | Margem bruta | Observação |
|---|---:|---:|---:|---:|---|
| 1 | 12 | R$ 60k | **R$ 0,7 mi** | ~70% | design partners, muito serviço |
| 2 | 45 | R$ 90k | **R$ 4,0 mi** | ~78% | produto amadurece |
| 3 | 130 | R$ 100k | **R$ 13 mi** | ~82% | canal + self-service |
| 5 | 350 | R$ 120k | **R$ 42 mi** | ~84% | liderança de categoria |

> Ticket médio sobe com upsell (mais SKUs, add-ons, enterprise) e expansão
> internacional. Números ilustrativos — sensíveis a taxa de conversão,
> churn e ciclo de venda enterprise.

---

## 10. Sensibilidade e principais riscos financeiros

| Variável | Impacto | Mitigação |
|---|---|---|
| Preço de tokens Gemini sobe | comprime margem por análise | roteamento Flash/Pro, caching, batch |
| Ciclo de venda enterprise longo | atrasa ARR | mix com self-service (PLG) para fluxo de caixa |
| Churn de marcas pequenas | reduz LTV | ancorar valor em compliance recorrente, não projeto único |
| Evangelização de categoria custa CAC | LTV/CAC pressionado | canal via agências/converters (CAC alavancado) |
| Câmbio (custos GCP em USD) | volatilidade de custo | repasse em contratos + committed use discounts |

---

## 11. Resumo financeiro (1 tela)

- **TAM:** ~R$ 1,4–1,7 bi/ano (global, categoria de a11y de packaging de beleza).
- **SAM:** ~R$ 330–440 mi/ano (BR + LatAm + early UE, segmento alvo).
- **SOM:** ~R$ 10–18 mi ARR em 3 anos; ~R$ 30–55 mi em 5 anos.
- **Custo de uso:** ~R$ 0,50–3,00 por análise (dominado por inferência).
- **Preço:** híbrido assinatura + consumo; planos R$ 490 → R$ 15k+/mês.
- **Margem bruta:** ~75–85% (perfil de SaaS de IA).
- **Valor percebido:** ancorado em risco regulatório evitado, velocidade e
  escala — 20–100x o custo marginal, sustentando preço value-based.

> Todos os valores são estimativas de planejamento. Recomenda-se validar com
> (a) relatório atualizado do mercado de embalagens cosméticas, (b) preços
> vigentes do Vertex AI/Gemini, e (c) 15–20 entrevistas com o ICP para calibrar
> disposição a pagar e ticket médio antes de fechar o plano de negócios.
