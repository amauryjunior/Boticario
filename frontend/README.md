# Inclua Beauty AI — Frontend (React + Vite)

SPA acessível (**WCAG 2.2 AA**) para a plataforma de acessibilidade de embalagens
de beleza. Consome a API do backend (`../backend`).

## Rodar em desenvolvimento

```bash
# 1) suba o backend (porta 8000)
cd ../backend && . .venv/bin/activate && uvicorn app.main:app --reload

# 2) suba o frontend
cd ../frontend
npm install
npm run dev        # http://localhost:5173  (proxy /api -> 127.0.0.1:8000)
```

Login de demonstração já preenchido: `demo@incluabeauty.ai` / `demo1234`.

## Build de produção

```bash
npm run build      # typecheck (tsc) + bundle (vite) -> dist/
npm run preview
```

## Funcionalidades

- **Login/cadastro** (JWT em `localStorage`).
- **Nova análise**: categoria, tipo de tampa, componentes, perfis de necessidade
  e **upload de imagem** (ingestão multimodal quando o backend usa Gemini).
- **Resultados**: score 0–100 por dimensão + gate, recomendações
  mínima/intermediária/premium com norma e **evidência RAG**, e checklist.
- **Dashboard de uso e custo de IA** (tokens, custo/análise, por agente).

## Acessibilidade (WCAG 2.2 AA)

- HTML semântico com landmarks (`header`, `main`, `nav`), `lang="pt-BR"`.
- Skip link "Pular para o conteúdo".
- Rótulos associados a todos os campos; `fieldset`/`legend` em grupos.
- Foco sempre visível (`:focus-visible`); operável por teclado.
- Contraste AA; status por **texto + cor** (não só cor).
- Regiões `aria-live` para status da análise e resultados; `role="alert"` em erros.
- Tema claro/escuro via `prefers-color-scheme`.

## Estrutura

```
src/
├── api.ts                 # cliente da API + tipos
├── profiles.ts            # perfis de necessidade e componentes
├── App.tsx                # fluxo principal (análise + dashboard)
├── styles.css             # design system acessível (light/dark)
└── components/
    ├── Login.tsx
    ├── Results.tsx        # ScoreCard, ChecklistCard, RecommendationsCard
    └── UsagePanel.tsx     # custo/uso de IA
```
