# Financial Research Agent

Primeiro milestone de um sistema de pesquisa financeira rastreável, construído com Python, FastAPI e Pydantic.

> Projeto educacional. Não fornece recomendação de investimento.

## O que já funciona

- `POST /analyses` recebe e normaliza um ticker.
- Provedor mockado reproduzível para PETR4 e VALE3.
- Cinco indicadores calculados em Python, sem delegar matemática a um LLM.
- Resultado estruturado e validado com Pydantic.
- Fontes, timestamp, confiança, dados ausentes e disclaimer.
- Erros tipados para ativo inexistente, validação e timeout.
- Testes de unidade e integração.
- Execução local ou via Docker.

## Arquitetura

```text
Request
  ↓
FastAPI + Pydantic
  ↓
FinancialAnalysisService
  ├── FinancialDataProvider
  └── Deterministic Metrics
  ↓
AnalysisResult
```

O LLM será adicionado na próxima etapa somente para interpretar dados já calculados. Ele não será responsável por realizar a matemática financeira.

## Executar localmente

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --reload
```

A documentação interativa estará em `http://localhost:8000/docs`.

## Exemplo

```bash
curl -X POST http://localhost:8000/analyses \
  -H 'Content-Type: application/json' \
  -d '{"ticker":"PETR4"}'
```

## Testes

```bash
pytest -q
```

## Docker

```bash
docker compose up --build
```

## Próximos milestones

1. Conectar um provedor real atrás da mesma interface.
2. Persistir análises em PostgreSQL.
3. Adicionar Redis e execução assíncrona.
4. Integrar LLM com structured output para interpretação.
5. Criar dataset de evals e testes contra números sem evidência.
6. Ingerir relatórios financeiros com RAG e citações.
7. Adicionar tracing, custo e latência ao DataPulse/Arena.

