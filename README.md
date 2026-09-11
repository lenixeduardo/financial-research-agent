# Financial Research Agent

Case de **AI Engineering aplicado a finanças**: pesquisa documental com evidências, dados de mercado via tool calling, cálculos determinísticos, model routing, verificação independente, observabilidade, evals e unit economics.

> Projeto educacional. Não constitui recomendação de investimento.

## O que este case demonstra

- **Tool calling real** via `FinancialDataProvider`, com adapter BRAPI e mock determinístico para testes.
- **RAG com citations** para PDF, CSV, TXT, Markdown e XLSX.
- **Hybrid retrieval**: BM25-style lexical score + dense feature hashing determinístico + MMR-like reranking.
- **Provenance** em fontes, documentos, localização e score de recuperação.
- **Agent workflow**: `research_agent -> financial_analysis_agent -> verifier`.
- **Model routing** por tipo/complexidade de tarefa, com política separada para verificação.
- **Structured output** com Pydantic.
- **Deterministic financial math**: o modelo não calcula os índices financeiros.
- **Verifier** para fontes, métricas, confiança e evidências de risco.
- **Observability** com `run_id`, tool calls, agent steps, latency, model policy e custo estimado.
- **Unit economics**: custo total e custo médio por execução respondida.
- **Guardrails**: limite de upload e bloqueio determinístico de padrões óbvios de prompt injection.
- **Versioned evals** + testes + cobertura + lint executados como gate no GitHub Actions.
- **Architecture Decision Records** documentando decisões técnicas.

## Arquitetura

```text
                       Financial Research Agent

Client
  |
  v
FastAPI + Pydantic
  |
  +------------------------+-------------------------+
  |                        |                         |
  v                        v                         v
Documents              Analyses                 Observability
  |                        |                         |
Parsing                  Research Agent           Traces
  |                        |                         |
Chunking                  Tool Call                Costs
  |                        |                         |
Hybrid Retrieval       BRAPI / Mock              Latency
BM25 + dense + MMR         |
  |                    Deterministic Metrics
Citations                   |
                           Model Router
                              |
                    Financial Analysis Agent
                              |
                         Independent Verifier
                              |
                       Structured Output
```

Detalhes: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Rodar localmente

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --reload
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e '.[dev]'
uvicorn app.main:app --reload
```

Swagger: `http://localhost:8000/docs`

## Dados reais com BRAPI

O mock permanece como padrão para desenvolvimento reproduzível. Para usar BRAPI:

```bash
cp env.example .env
```

```env
FRA_FINANCIAL_PROVIDER=brapi
FRA_BRAPI_TOKEN=seu_token_quando_necessario
```

A interface do domínio não muda ao trocar o provider.

## Endpoints principais

```text
GET  /health
GET  /system/capabilities
POST /analyses
POST /documents
GET  /documents
POST /research
GET  /observability/runs
GET  /observability/summary
```

Exemplo:

```bash
curl -X POST http://localhost:8000/analyses \
  -H 'Content-Type: application/json' \
  -d '{"ticker":"PETR4"}'
```

Cada análise devolve `X-Run-ID`, permitindo localizar todo o trace da execução.

## Document Intelligence / RAG

```bash
curl -X POST http://localhost:8000/documents \
  -F 'ticker=PETR4' \
  -F 'file=@relatorio.pdf'

curl -X POST http://localhost:8000/research \
  -H 'Content-Type: application/json' \
  -d '{"ticker":"PETR4","question":"Qual é a receita líquida informada?"}'
```

Uma resposta de research inclui `citations`, `location`, `excerpt`, `score` e `retrieval_method`. Quando não existe evidência suficiente, o sistema retorna `422 insufficient_evidence` em vez de fabricar uma resposta.

## Testes, evals e CI

```bash
ruff check app tests scripts
pytest -q --cov=app --cov-report=term-missing
python scripts/run_evals.py
```

O workflow `.github/workflows/ci.yml` executa lint, testes com threshold de cobertura e a suíte versionada de evals em pull requests.

A avaliação produz métricas agregadas de pass rate e verifica, além do contrato HTTP, provenance, verification, traces e model routing.

## Observabilidade e unit economics

```bash
curl http://localhost:8000/observability/runs
curl http://localhost:8000/observability/summary
```

O trace registra:

```text
run_id
status
latency_ms
tool_calls[]
agent_steps[]
model_usage[]
sources[]
citations_count
estimated_cost_usd
```

Os preços por milhão de tokens são configuráveis por ambiente, permitindo trocar implementações determinísticas por modelos reais sem alterar o contrato de observabilidade.

## Decisões de engenharia

- [`ADR 001 — Hybrid retrieval`](docs/adr/001-hybrid-retrieval.md)
- [`ADR 002 — Deterministic math + verification`](docs/adr/002-deterministic-math-and-verification.md)

## Limites atuais — declarados de propósito

Este repositório **não finge infraestrutura que não existe**. Atualmente documentos e traces ficam em memória; os identificadores de modelo representam a política de routing, mas o pipeline financeiro segue determinístico e não reporta tokens fictícios.

Próximas extensões de produção: PostgreSQL + pgvector, trace backend OpenTelemetry/Langfuse-compatible, workers assíncronos, OIDC/RBAC e adapters para modelos hosted/local. Essas extensões já possuem pontos de substituição claros na arquitetura.

## Por que isto é um case de AI Engineering

O objetivo não é demonstrar apenas uma chamada para LLM. O case mostra como construir um sistema onde **dados, tools, retrieval, evidência, routing, verificação, qualidade, segurança, observabilidade e custo** são componentes testáveis e substituíveis. O modelo é uma peça do sistema — não o sistema inteiro.
