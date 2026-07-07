# 03 — Análise de Mercado

Análise de mercado da **Inclua Beauty AI** — plataforma agêntica de
"accessibility intelligence" para embalagens de beleza. Cobre contexto,
tendências, drivers regulatórios, concorrência, personas, proposta de valor,
go-to-market e riscos. As dimensões quantitativas (TAM/SAM/SOM) e a
precificação estão no documento 04.

---

## 1. Contexto e problema de mercado

A indústria de beleza é gigantesca e altamente competitiva, mas suas embalagens
foram historicamente projetadas por critérios de estética, custo e prateleira —
**não de acessibilidade**. Tampas escorregadias, rótulos de baixo contraste,
fontes minúsculas, ausência de identificação tátil e instruções complexas
excluem uma parcela enorme de consumidores:

- Pessoas com deficiência visual, motora, cognitiva ou auditiva.
- Pessoas idosas (destreza reduzida, baixa visão) — o segmento 60+ é o que mais
  cresce demograficamente.
- Situações temporárias/situacionais (mão ocluída, ambiente com pouca luz).

Estima-se que **pessoas com deficiência representam ~15–16% da população
mundial** (mais de 1 bilhão de pessoas, referência OMS), e o poder de compra
desse grupo e de suas famílias ("purple pound"/"disability market") é
substancial. Somado ao envelhecimento populacional, forma-se uma **demanda
estrutural por design inclusivo** que a indústria ainda atende de forma pontual
e artesanal.

**A dor específica do comprador B2B** (marcas, converters de embalagem,
agências de design, indústria cosmética) é: como avaliar e melhorar
acessibilidade de forma **rápida, padronizada, rastreável e defensável** frente
a normas (LBI, ANVISA, WCAG, ADA, European Accessibility Act) — sem depender
apenas de consultoria manual cara e não escalável?

---

## 2. Tendências que sustentam a categoria

| Tendência | Efeito sobre a demanda |
|---|---|
| **Regulação de acessibilidade endurecendo** (EAA 2019/882 em vigor na UE; LBI no Brasil; ADA nos EUA) | Cria obrigação/risco jurídico → orçamento de compliance. |
| **ESG e agenda de inclusão (S de "Social")** | Acessibilidade vira métrica reportável; pressão de investidores e consumidores. |
| **Envelhecimento populacional** | Mercado 60+ demanda ergonomia e legibilidade. |
| **IA generativa multimodal madura** (Gemini, GPT, Claude) | Torna viável analisar imagem+contexto a custo baixo — antes inviável. |
| **"Inclusive design" como diferencial de marca** | Marcas globais (ex.: iniciativas de acessibilidade em beleza) buscam liderança reputacional. |
| **Consumidor consciente / mídia social** | Falhas de exclusão viralizam; acertos geram valor de marca. |

A convergência **regulação + IA barata + agenda ESG** é o que faz a categoria
existir *agora* e não há 5 anos.

---

## 3. Cadeia de valor e onde a Inclua Beauty se posiciona

```text
Marca de beleza  →  Agência/Design studio  →  Converter de embalagem  →  Varejo
      │                    │                          │
      └──────── todos precisam avaliar/justificar acessibilidade ───────┘
                                   │
                        INCLUA BEAUTY AI (camada de inteligência)
              diagnóstico · score · recomendação · matriz normativa · relatório
```

A Inclua Beauty não compete com fábricas nem com estúdios: ela vira a **camada
de decisão inclusiva** que padroniza e acelera o trabalho de todos eles — um
"Grammarly/SonarQube da acessibilidade de embalagens".

---

## 4. Segmentação de clientes (ICP)

| Segmento | Perfil | Gatilho de compra | Disposição a pagar |
|---|---|---|---|
| **Grandes marcas de beleza** (multinacionais, grupos nacionais) | times de inovação/P&D e ESG | risco regulatório, reputação, EAA/ADA | Alta (contrato enterprise) |
| **Indústria de embalagem / converters** | engenharia de produto | vender embalagem acessível como diferencial | Média-alta |
| **Agências e estúdios de design** | designers de packaging | entregar acessibilidade certificável aos clientes | Média (por seat/projeto) |
| **Consultorias de acessibilidade** | especialistas | escalar diagnósticos, padronizar laudos | Média |
| **Marcas indie / D2C** | founders | selo de inclusão, marketing | Baixa-média (self-service) |
| **Setor público / editais** | compras públicas | exigência legal de acessibilidade | Variável |

**ICP primário para o beachhead**: grandes marcas de beleza no Brasil e
converters de embalagem, onde há orçamento de inovação/compliance e volume de
SKUs recorrente.

---

## 5. Personas (compra e uso)

- **Gestor(a) de Inovação/ESG** (comprador econômico): quer indicador auditável
  de inclusão e reduzir risco regulatório. Métrica: % de portfólio avaliado,
  score médio, evolução.
- **Designer/Engenheiro de Packaging** (usuário): quer recomendações acionáveis
  (tampa, contraste, braille, QR) e prompts de mockup. Métrica: velocidade de
  iteração.
- **Regulatório/Compliance**: quer separação clara entre "recomendação de
  design" e "exigência legal confirmada" e rastreabilidade.
- **Especialista em acessibilidade**: valida casos incertos (human-in-the-loop).
- **Testador(a) PcD**: fornece evidência qualitativa de co-design.

---

## 6. Concorrência e alternativas

Não há, hoje, um líder consolidado de **"software de acessibilidade de embalagens
de beleza com IA"** — o que é oportunidade (categoria nova) e risco (evangelizar
mercado). O campo competitivo se divide em substitutos:

| Categoria de concorrente | Exemplos/típico | Limitação vs. Inclua Beauty |
|---|---|---|
| **Consultoria manual de acessibilidade** | escritórios de design inclusivo, especialistas | não escala, caro, laudo não padronizado, lento |
| **Ferramentas de a11y digital (WCAG)** | axe, WAVE, Siteimprove | focam em **web/app**, não em embalagem física/ergonomia |
| **Softwares de design/PLM/packaging** | Esko, Adobe, CAD/PLM | não avaliam acessibilidade nem geram score/normas |
| **Selos e certificações de inclusão** | programas de certificação | avaliação pontual, sem loop de melhoria contínuo |
| **"Fazer nada" / planilhas internas** | status quo | subjetivo, não rastreável, risco jurídico |

**Fossos defensáveis (moats) da Inclua Beauty:**

1. **Base normativa versionada e curada** (com status confirmada/hipótese) —
   difícil de replicar e cresce com o uso.
2. **Biblioteca de padrões de solução** (tampas, texturas, QR, braille) que
   melhora as recomendações (data network effect).
3. **Score proprietário** (Índice Inclua Beauty) que pode virar *padrão de
   mercado* / benchmark de categoria.
4. **Loop de co-design com PcD** gerando evidência real, não só heurística.
5. **Traços/auditoria de IA** que dão defensabilidade jurídica (diferencial em
   compliance).

---

## 7. Proposta de valor (por stakeholder)

| Stakeholder | Valor entregue |
|---|---|
| Marca | reduz risco regulatório, acelera inovação inclusiva, gera indicador ESG reportável, protege reputação |
| Design/Engenharia | recomendações acionáveis + prompts de mockup, iteração 10x mais rápida |
| Regulatório | matriz normativa rastreável, separação evidência × opinião |
| Consumidor final (PcD/60+) | produtos utilizáveis com autonomia |
| Investidor/board | métrica de inclusão auditável no portfólio |

**Pitch de uma linha:** *"Transformamos qualquer embalagem de beleza em um
diagnóstico de acessibilidade auditável, com score, recomendações e conformidade
normativa — em menos de um minuto, não em semanas de consultoria."*

---

## 8. Go-to-market (GTM)

**Fase 1 — Beachhead (0–12 meses):**
- Foco: 3–5 grandes marcas/converters no Brasil como *design partners*.
- Motion: *land* com um piloto pago em um portfólio (ex.: 50 SKUs), provar ROI
  (risco evitado + velocidade), *expand* para o portfólio inteiro.
- Prova social: publicar o **Índice Inclua Beauty** e casos de melhoria.

**Fase 2 — Expansão (12–30 meses):**
- Agências e converters como canal de distribuição (revenda/white-label).
- Self-service para marcas indie/D2C (PLG, plano por consumo).
- Internacionalização com base normativa EAA/ADA (UE e EUA).

**Fase 3 — Plataforma/rede (30+ meses):**
- API para integrar catálogos/PLM; marketplace de especialistas; benchmark de
  categoria como dado vendável (relatórios de indústria).

**Canais:** venda direta enterprise; parcerias com associações de embalagem e de
acessibilidade; presença em editais/inovação (o próprio projeto nasce de edital
tipo Centelha); conteúdo técnico (thought leadership em inclusive design).

---

## 9. Análise SWOT

| Forças | Fraquezas |
|---|---|
| Categoria nova com timing regulatório favorável | Mercado precisa ser evangelizado (venda consultiva) |
| Custo de inferência baixo → margem de SaaS | Depende de base normativa curada (esforço inicial) |
| Moats de dados (normas + padrões + co-design) | Risco de credibilidade se IA errar norma |
| Alinhamento ESG/inclusão (compra por board) | Ciclo de venda enterprise longo |

| Oportunidades | Ameaças |
|---|---|
| EAA/ADA/LBI forçando compliance | Big Tech/PLM incumbente adicionar feature similar |
| Envelhecimento populacional (60+) | Commoditização de IA multimodal |
| Expansão para outros setores (alimentos, farma, bens de consumo) | Regulação de IA (transparência/responsabilidade) |
| Score virar padrão de mercado | Orçamentos de inovação cortados em recessão |

---

## 10. Riscos de mercado e mitigação

| Risco | Mitigação |
|---|---|
| "Nice to have" cortável em crise | ancorar em **risco regulatório** (obrigação, não luxo) |
| IA citar norma errada → dano reputacional/jurídico | status normativo + human-in-the-loop + linguagem "recomendação/pendente de validação" (RNF-015) |
| Cliente perceber como consultoria, não produto | UX de produto forte, self-service, tempo de resposta < 60s |
| Concorrência de incumbentes | velocidade, foco vertical e moats de dados |
| Baixa adoção por marcas pequenas | plano self-service por consumo (PLG) |

---

## 11. Conclusão de mercado

A Inclua Beauty ataca uma **lacuna real e crescente** na interseção de beleza,
inclusão e regulação, em um momento em que a IA multimodal tornou a análise
economicamente viável. O maior ativo estratégico não é o modelo de IA (que é
comoditizado), mas a **base normativa curada + score proprietário + rede de
dados de co-design** — que, se bem executados, transformam a solução de "mais uma
ferramenta de IA" em **a infraestrutura de decisão inclusiva da indústria de
beleza**, com potencial de expansão para outros setores de bens de consumo.

O dimensionamento (TAM/SAM/SOM) e a estratégia de preços/monetização estão no
documento **04 — TAM/SAM/SOM e Precificação**.
