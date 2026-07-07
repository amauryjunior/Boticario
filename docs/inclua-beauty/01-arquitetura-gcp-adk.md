# 01 — Arquitetura de Referência: GCP + Vertex AI + Google ADK

Este documento descreve a arquitetura técnica da **Inclua Beauty AI** como
engenheiro de IA/GCP, detalhando a malha de agentes no **Google Agent
Development Kit (ADK)**, o desenho de infraestrutura serverless, segurança
multi-tenant, observabilidade e FinOps de inferência.

---

## 1. Princípios de arquitetura

1. **Serverless-first**: Cloud Run + Vertex AI eliminam gestão de cluster e
   escalam a zero, ideal para cargas irregulares de análise (rajadas).
2. **Managed AI**: o raciocínio multimodal (imagem + texto) usa **Gemini via
   Vertex AI**, sem hospedar modelos próprios no MVP.
3. **Agentes como unidade de composição**: cada competência de acessibilidade é
   um agente ADK independente, testável e observável.
4. **Rastreabilidade obrigatória** (RNF-005/006): toda saída de IA carrega
   `agent_name`, `input`, `output`, tokens, custo e latência (`AgentTrace`).
5. **Separação evidência × opinião × validação humana**: contratos de dados
   forçam o campo de "status da norma" e "necessita validação".
6. **Multi-tenant seguro** (RNF-008): isolamento lógico por `organization_id`,
   criptografia em repouso/trânsito (CMEK opcional), least-privilege IAM.

---

## 2. Diagrama lógico (alto nível)

```text
                         ┌──────────────────────────────────────────┐
   Usuário (browser)     │                 GCP                       │
   React + WCAG 2.2 AA   │                                          │
        │                │  ┌────────────┐     ┌──────────────────┐  │
        │  HTTPS         │  │  Cloud     │     │  Cloud Run:       │  │
        ├───────────────▶│  │  Load Bal. │────▶│  api (FastAPI)    │  │
        │                │  │  + Armor   │     │  - auth/z         │  │
        │                │  └────────────┘     │  - CRUD projetos  │  │
        │                │        │            │  - dispatch jobs  │  │
        │                │        │            └───────┬──────────┘  │
        │                │        │                    │             │
        │                │        │        Pub/Sub     ▼             │
        │                │        │   ┌────────────────────────────┐ │
        │                │        │   │ Cloud Run: agents (ADK)    │ │
        │                │        │   │  Orquestrador → subagentes │ │
        │                │        │   └───┬───────────────┬────────┘ │
        │                │        │       │ Vertex AI     │          │
        │                │        │       ▼ (Gemini)      ▼          │
        │                │  ┌───────────┐  ┌────────────┐ ┌────────┐ │
        │                │  │ Cloud SQL │  │ Cloud      │ │ Vertex │ │
        │                │  │ PG +      │  │ Storage    │ │ Vector/│ │
        │                │  │ pgvector  │  │ (imagens,  │ │ pgvec  │ │
        │                │  │ (dados +  │  │  relatóri.)│ │ (RAG   │ │
        │                │  │  traces)  │  │            │ │ normas)│ │
        │                │  └───────────┘  └────────────┘ └────────┘ │
        │                │                                          │
        │                │  Observabilidade: Cloud Trace / Logging / │
        │                │  Monitoring · Secret Manager · Artifact   │
        │                │  Registry · Cloud Build (CI/CD)           │
        │                └──────────────────────────────────────────┘
```

---

## 3. Componentes GCP e mapeamento de responsabilidade

| Camada | Serviço GCP | Responsabilidade | Requisito atendido |
|---|---|---|---|
| Borda | Cloud Load Balancing + Cloud Armor | TLS, WAF, rate limit, DDoS | RNF-007 |
| API | Cloud Run (`api`) | FastAPI, authN/Z, orquestração de jobs | RNF-003 |
| Agentes | Cloud Run (`agents`) | Runtime ADK dos agentes | RF-... análise |
| Modelo | Vertex AI (Gemini 2.5 Flash/Pro) | Raciocínio multimodal | Análise IA |
| Fila | Pub/Sub | Desacoplar análise assíncrona | RNF-009 |
| Dados | Cloud SQL PostgreSQL + pgvector | OLTP + embeddings + traces | RNF-011 |
| Objetos | Cloud Storage | Imagens, relatórios, anexos | RF-005/027 |
| RAG | pgvector (MVP) → Vertex AI Vector Search (escala) | Base normativa versionada | RF-015/016 |
| Segredos | Secret Manager | Chaves, credenciais, JWT | RNF-007 |
| Identidade | Identity Platform (ou Firebase Auth) | Login, OAuth, MFA | RF-003 |
| CI/CD | Cloud Build + Artifact Registry | Build, testes, deploy | RNF-013 |
| Observab. | Cloud Trace / Logging / Monitoring | Traces de agente, SLO, alertas | RNF-004/012 |
| IaC | Terraform | Provisionamento reprodutível | — |

> **Regra de escolha pgvector vs. Vertex AI Vector Search:** comece com
> `pgvector` no Cloud SQL (simplicidade, custo ~zero adicional, joins com dados
> relacionais). Migre a base normativa para **Vertex AI Vector Search** quando o
> corpus passar de ~1M de chunks ou a latência de recuperação p95 exceder o SLO.

---

## 4. Malha de agentes no Google ADK

O **ADK** (Agent Development Kit) permite compor agentes em Python com
ferramentas (tools), sub-agentes, workflows determinísticos (`SequentialAgent`,
`ParallelAgent`, `LoopAgent`) e um `LlmAgent` para raciocínio. A Inclua Beauty
usa um **orquestrador** que roteia para agentes especialistas, muitos rodando em
**paralelo** para caber no SLO de < 60s (RNF-009).

### 4.1 Topologia

```text
InclusaBeautyOrchestrator (LlmAgent, root)
│
├─ IngestionAgent            (multimodal: extrai atributos da imagem+texto)
├─ CategoryAgent             (classifica categoria cosmética)
├─ ComponentDecompAgent      (decompõe frasco/tampa/rótulo/válvula/…)
│
├─ AnalysisFanOut (ParallelAgent)   ← executa em paralelo:
│   ├─ ErgonomicsAgent       (abertura, força, pega, textura)
│   ├─ LabelingAgent         (contraste, fonte, braille, QR, pictograma)
│   ├─ AssistiveTechAgent    (NaviLens, áudio, mapa tátil, feedback)
│   ├─ SustainabilityAgent   (refil, reciclabilidade, materiais)
│   └─ ComplianceAgent       (normas + status confirmada/hipótese) [+ RAG tool]
│
├─ ScoringAgent              (índice 0–100 por dimensão + gates)
├─ RecommendationAgent       (mín/interm/premium por barreira)
├─ ReportAgent               (monta relatório estruturado)
└─ HumanReviewGate           (LongRunningTool / callback → fila de revisão)
```

### 4.2 Padrões ADK aplicados

- **`ParallelAgent`** para o fan-out de análise: reduz latência agregada (5
  agentes concorrentes em vez de sequenciais).
- **`SequentialAgent`** para o pipeline global (ingestão → categoria →
  componentes → análise → score → recomendação → relatório).
- **Function tools** para acesso a dados: `get_standards(jurisdiction)`,
  `vector_search_norms(query)`, `save_trace(...)`, `create_report(...)`.
- **`before_model_callback` / `after_model_callback`** para gravar `AgentTrace`
  (tokens, custo, latência) e aplicar guardrails (PII, linguagem não capacitista).
- **Human-in-the-loop** (RNF-010): agentes marcam itens `A validar`; um
  `LongRunningFunctionTool` publica no Pub/Sub e pausa a emissão do relatório
  "final" até parecer do especialista.
- **Structured output** via `output_schema` (Pydantic) para forçar contratos
  auditáveis (checklist, score, recomendações) em vez de texto livre.

### 4.3 Esqueleto de código (ADK, Python)

```python
# backend/app/agents/orchestrator.py
from google.adk.agents import LlmAgent, SequentialAgent, ParallelAgent
from .tools import vector_search_norms, get_standards, save_trace
from .schemas import ChecklistOutput, ScoreOutput, RecommendationsOutput

MODEL_FAST = "gemini-2.5-flash"     # roteamento/decomposição/checklist
MODEL_PRO  = "gemini-2.5-pro"       # raciocínio normativo e recomendações

ergonomics = LlmAgent(
    name="ErgonomicsAgent", model=MODEL_FAST,
    instruction=("Avalie abertura, força, pega, textura e manuseio do "
                 "componente. Classifique barreiras por perfil de deficiência. "
                 "Nunca afirme conformidade legal; marque 'A validar' quando "
                 "faltar evidência."),
)

labeling = LlmAgent(name="LabelingAgent", model=MODEL_FAST, instruction="...")
assistive = LlmAgent(name="AssistiveTechAgent", model=MODEL_FAST, instruction="...")
sustainability = LlmAgent(name="SustainabilityAgent", model=MODEL_FAST, instruction="...")

compliance = LlmAgent(
    name="ComplianceAgent", model=MODEL_PRO,
    tools=[vector_search_norms, get_standards],
    instruction=("Relacione recomendações a normas (ISO, NBR, LBI, ANVISA, "
                 "WCAG, ADA, EAA). Para cada norma defina status: confirmada | "
                 "aplicável com ressalva | referência de design | hipótese | "
                 "pendente de validação. Cite a fonte recuperada."),
)

analysis_fanout = ParallelAgent(
    name="AnalysisFanOut",
    sub_agents=[ergonomics, labeling, assistive, sustainability, compliance],
)

scoring = LlmAgent(name="ScoringAgent", model=MODEL_FAST, output_schema=ScoreOutput)
recommend = LlmAgent(name="RecommendationAgent", model=MODEL_PRO,
                     output_schema=RecommendationsOutput)
report = LlmAgent(name="ReportAgent", model=MODEL_FAST)

pipeline = SequentialAgent(
    name="InclusaBeautyPipeline",
    sub_agents=[
        # ingestion, category, component agents ...
        analysis_fanout, scoring, recommend, report,
    ],
)

root_agent = LlmAgent(
    name="InclusaBeautyOrchestrator", model=MODEL_PRO,
    sub_agents=[pipeline],
    instruction="Coordene a análise de acessibilidade de embalagens de beleza.",
    after_model_callback=save_trace,   # grava AgentTrace por chamada
)
```

```python
# backend/app/agents/tools.py  (RAG normativo com pgvector)
from google.adk.tools import ToolContext

def vector_search_norms(query: str, jurisdiction: str, tool_context: ToolContext):
    """Recupera trechos de normas/guidelines mais relevantes (pgvector)."""
    emb = embed(query)                       # text-embedding-004 via Vertex AI
    rows = db.fetch(
        """SELECT title, source, status, chunk,
                  1 - (embedding <=> %s) AS score
           FROM standard_chunks
           WHERE jurisdiction = %s
           ORDER BY embedding <=> %s LIMIT 6""",
        (emb, jurisdiction, emb),
    )
    return {"matches": rows}
```

### 4.4 Modelo de roteamento de modelos (custo × qualidade)

| Tarefa | Modelo | Justificativa |
|---|---|---|
| Decomposição de componentes, checklist, score | **Gemini 2.5 Flash** | rápido/barato, tarefa estruturada |
| Raciocínio normativo, recomendações premium | **Gemini 2.5 Pro** | precisão em raciocínio jurídico/design |
| Visão (extrair atributos da embalagem) | **Gemini 2.5 Flash (multimodal)** | imagem + texto num só passo |
| Embeddings (RAG normativo) | **text-embedding-004** | recuperação semântica |

---

## 5. Fluxo de execução de uma análise (assíncrono)

```text
1. POST /analysis-runs  → api valida payload, cria AnalysisRun(status=queued)
2. api publica msg no Pub/Sub topic "analysis.requested"
3. Cloud Run (agents) recebe push, carrega imagens do Cloud Storage (Signed URL)
4. ADK executa pipeline; cada LlmAgent chama Vertex AI (Gemini)
5. after_model_callback grava AgentTrace (tokens/custo/latência) no Cloud SQL
6. ComplianceAgent consulta pgvector (RAG normativo)
7. ScoringAgent grava ChecklistItem + score; itens incertos → status "A validar"
8. Se houver itens críticos → HumanReviewGate publica "review.requested" (pausa)
9. ReportAgent monta relatório; arquivo salvo no Cloud Storage
10. api atualiza AnalysisRun(status=done) e notifica o frontend (SSE/websocket)
```

- **SLO (RNF-009):** análise simples p95 < 60s. O fan-out paralelo e o uso de
  Flash nas etapas estruturadas são os principais alavancadores.
- **Idempotência:** `analysis_run_id` como chave; reprocessamento seguro.

---

## 6. Segurança e conformidade (LGPD-ready)

- **Identidade**: Identity Platform (e-mail/senha, OAuth Google/Microsoft, MFA
  para planos corporativos — RF-003).
- **Autorização**: RBAC por papel (RF-002) aplicado na API; claims no JWT.
- **Isolamento multi-tenant**: `organization_id` em todas as tabelas +
  Row-Level Security no PostgreSQL; buckets com prefixo por tenant.
- **Criptografia**: TLS em trânsito; criptografia em repouso padrão (opção
  **CMEK** via Cloud KMS para clientes enterprise).
- **Segredos**: Secret Manager; nada de credencial em imagem/código.
- **Rede**: Cloud Run com **VPC connector** + **Private IP** para Cloud SQL;
  egress restrito; Cloud Armor na borda.
- **LGPD**: imagens de produto podem conter IP confidencial → contrato de
  confidencialidade, retenção configurável, direito de exclusão, DPA.
- **Guardrails de IA**: `after_model_callback` valida linguagem não capacitista
  e bloqueia afirmações de conformidade legal definitiva (RNF-015).

---

## 7. Observabilidade e FinOps de inferência

- **Cloud Trace**: o ADK exporta spans por agente/tool; correlaciona latência
  ponta a ponta (RNF-004).
- **Cloud Logging**: log estruturado por `analysis_run_id` e `agent_name`.
- **Cloud Monitoring**: dashboards de SLO (latência, taxa de erro), alertas.
- **Custo por análise (RNF-012)**: `AgentTrace.cost` agrega tokens × preço do
  modelo → métrica `cost_per_analysis` exportada ao Monitoring e faturamento.
- **Billing export → BigQuery**: análise de custo por tenant/feature para
  precificação baseada em consumo (ver doc 04).

---

## 8. CI/CD e ambientes

- **Ambientes**: `dev`, `staging`, `prod` (projetos GCP separados;
  recomendação: pasta na organização + billing account única).
- **Pipeline (Cloud Build)**: lint → testes (backend, agentes, a11y) → build de
  imagem → push Artifact Registry → deploy Cloud Run (canary/traffic split).
- **Avaliação de agentes**: suíte de *evals* do ADK em CI (casos de aceite do
  doc de requisitos, ex.: perfume, baixa visão, destreza) — impede regressão de
  qualidade dos agentes (RNF-013).
- **IaC**: Terraform versiona toda a infra (doc 02).

---

## 9. Decisões de arquitetura resumidas (ADR curto)

| Decisão | Escolha | Alternativa descartada | Motivo |
|---|---|---|---|
| Compute | Cloud Run | GKE | menor ops, escala a zero, custo variável |
| Orquestração de agentes | Google ADK | LangGraph | alinhamento nativo Vertex/Gemini, evals, deploy |
| Vetores (MVP) | pgvector | Vector Search | simplicidade, custo, joins relacionais |
| Modelo | Gemini 2.5 Flash/Pro | modelo self-hosted | sem MLOps de modelo no MVP |
| Fila | Pub/Sub | Celery/Redis | serverless, retry/ DLQ gerenciados |
| Auth | Identity Platform | build próprio | MFA/OAuth/compliance prontos |

> **Portabilidade:** o núcleo (FastAPI + ADK + Pydantic) é agnóstico; caso o
> cliente exija outro provedor, os `LlmAgent` podem apontar para modelos via
> LiteLLM sem reescrever a orquestração.
