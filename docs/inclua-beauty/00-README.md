# Inclua Beauty AI — Documentação de Engenharia, GCP e Negócio

> Plataforma agêntica em Python para diagnóstico, recomendação e relatório de **acessibilidade de embalagens de beleza**, construída sobre **Google Cloud Platform (GCP)**, **Vertex AI / Gemini** e **Google Agent Development Kit (ADK)**.

Este conjunto de documentos complementa o arquivo de requisitos
(`inclua_beauty_plataforma_agentica_requisitos.md`) com a visão de um engenheiro
especialista em **IA, GCP e agentes Google ADK**, cobrindo arquitetura,
instalação/operação em produção e a análise de mercado e financeira.

## Índice

| Documento | Conteúdo |
|---|---|
| [01 — Arquitetura GCP + ADK](01-arquitetura-gcp-adk.md) | Arquitetura de referência, malha de agentes ADK, fluxo de dados, segurança, observabilidade e FinOps. |
| [02 — Instalação e Utilização no GCP](02-instalacao-gcp.md) | Passo a passo completo: bootstrap de projeto, IAM, Vertex AI, Cloud Run, Cloud SQL, Terraform, deploy do ADK e uso da plataforma. |
| [03 — Análise de Mercado](03-analise-mercado.md) | Contexto, tendências, concorrência, drivers regulatórios, personas, GTM e riscos. |
| [04 — TAM / SAM / SOM e Precificação](04-tam-sam-som-precificacao.md) | Dimensionamento de mercado, modelo de preços, custo de uso (unit economics em GCP), valor percebido e projeção de receita. |

## Resumo executivo (1 parágrafo)

A **Inclua Beauty AI** transforma fotos, descrições e requisitos de produtos de
beleza em **diagnósticos, checklists, scores e relatórios de acessibilidade**
por meio de uma equipe de agentes de IA orquestrados. Tecnicamente, roda em GCP
serverless (Cloud Run) com raciocínio multimodal do **Gemini via Vertex AI**,
orquestração pelo **Google ADK**, memória vetorial normativa no **Cloud SQL
(PostgreSQL + pgvector)** e observabilidade nativa (Cloud Trace/Logging). O
modelo de negócio é **SaaS B2B por assinatura + consumo**, com margem bruta de
software (75–85%) sustentada por custo de inferência de poucos centavos a poucos
reais por análise. O mercado endereçável combina a indústria global de
embalagens de cosméticos com a agenda regulatória de acessibilidade (LBI, ANVISA,
European Accessibility Act, ADA, WCAG), criando uma categoria nova:
**"accessibility intelligence" para packaging de beleza**.
