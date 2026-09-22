# Помощник кредитного аналитика на базе RAG

Локальный помощник кредитного аналитика, который объединяет:

- RAG для качественных вопросов по содержанию годовых отчетов;
- структурированное хранилище финансовых фактов для точных числовых значений;
- детерминированные расчеты финансовых показателей в Python;
- LLM для понимания естественного языка, классификации запроса и формирования ответа;
- Streamlit-интерфейс для работы с системой через браузер.

Проект сделан как практическая RAG/LLM-система с акцентом на надежность, provenance,
воспроизводимость расчетов, оценку retrieval-качества и четкое разделение
ответственности между LLM и обычным кодом.

---

## 1. Задача проекта

Обычный RAG хорошо подходит для вопросов вида:

> Какие риски ЛУКОЙЛ описывает в годовом отчете за 2025 год?

Но плохо подходит как единственный механизм для вопросов:

> Какая выручка Роснефти за 2025 год?

или:

> Какой Net Debt / EBITDA у ЛУКОЙЛа за 2025 год?

Причина в том, что vector retrieval ищет **семантически похожий текст**, но не
гарантирует извлечение именно нужного числа, периода, единицы измерения или
версии показателя.

Поэтому в проекте используются разные execution path для разных типов задач.

---

## 2. Архитектура

```text
                         ВОПРОС ПОЛЬЗОВАТЕЛЯ
                                  |
                                  v
                       +-------------------+
                       |  Question Parser  |
                       |    Local LLM      |
                       +-------------------+
                                  |
                                  v
                       +-------------------+
                       | Validator /       |
                       | Period Resolver   |
                       +-------------------+
                                  |
                                  v
                       +-------------------+
                       |    Dispatcher     |
                       +-------------------+
                         /       |       \
                        /        |        \
                       v         v         v

               QUALITATIVE     NUMERIC    CALCULATION
                    |             |           |
                    v             v           v
               RAG Pipeline   FinancialFact  Python
                              Store           functions
                    |             |           |
                    +-------------+-----------+
                                  |
                                  v
                        +------------------+
                        | Answer Formatter |
                        +------------------+
                                  |
                                  v
                              Streamlit
```

Главный архитектурный принцип:

```text
ТЕКСТОВЫЕ ФАКТЫ     -> RAG
ФИНАНСОВЫЕ ЧИСЛА    -> FinancialFact Store
РАСЧЕТЫ             -> Python
LLM                 -> понимание языка и генерация текста
```

LLM не используется как источник истины для точных финансовых значений и не
выполняет детерминированную финансовую арифметику.

---

## 3. Поддерживаемые типы запросов

| Intent | Пример | Execution path |
|---|---|---|
| `qualitative` | Какие риски описывает ЛУКОЙЛ? | RAG |
| `fact` | Какая выручка Роснефти за 2025 год? | FinancialFact Store |
| `derived_metric` | Какой Net Debt / EBITDA у ЛУКОЙЛа? | Python calculation |
| `comparison` | Сравни выручку трех компаний | Structured facts + normalization |
| `growth` | Как изменилась выручка с 2024 по 2025? | Structured facts + Python |
| `unknown` | Стоит ли выдавать ЛУКОЙЛу кредит? | Unsupported / guardrail |

Отсутствующие параметры не должны молча придумываться. Resolver восстанавливает
их только там, где это безопасно с точки зрения доступных данных и comparability.

---

## 4. Данные

Проект работает с отчетностью трех компаний:

- ЛУКОЙЛ;
- Роснефть;
- Татнефть.

Периоды:

- 2024;
- 2025.

### 4.1. Текстовый корпус

Для качественного RAG используются годовые отчеты компаний.

Текущий корпус:

```text
848 PageDocument
3927 ChunkDocument
```

### 4.2. Источник точных финансовых значений

Для числовой ветки используется консолидированная отчетность по МСФО.

Финансовые значения хранятся в типизированном виде:

```python
FinancialFact(
    company_id="ROSNEFT",
    period="2025",
    standard="IFRS",
    metric="revenue",
    value=Decimal("8236"),
    unit="RUB_BILLION",
    doc_id="rosneft_ifrs_2025",
    page=6,
    extraction_method="table",
    confidence=0.9,
)
```

Каждый факт сохраняет provenance: компанию, период, стандарт, метрику, значение,
единицу измерения, документ, страницу, метод извлечения и confidence.

---

## 5. Text RAG pipeline

```text
PDF
 |
 v
Parsing
 |
 v
Text cleaning
 |
 v
Sentence-aware chunking
 |
 v
Embeddings
 |
 v
Metadata filtering
 |
 v
Dense retrieval
 |
 v
Reranking
 |
 v
Context construction
 |
 v
Grounded generation
 |
 v
Citation formatting
```

Основной PDF-парсер — `pdfplumber`. Подробности выбора и другие архитектурные
решения находятся в `docs/DECISIONS.md`.

Chunking:

```text
chunk size: 1200 символов
overlap: 200 символов
```

Chunks сохраняют metadata: company, year, doc_id, page, chunk_id.

---

## 6. Embeddings и retrieval

Embedding model:

```text
intfloat/multilingual-e5-small
```

Размер embedding — 384. Для E5 используются префиксы `query:` и `passage:`.
Перед similarity search векторы нормализуются.

Перед retrieval применяется metadata prefilter по `company` и `year`.

---

## 7. Эксперименты с retrieval

В проекте сравнивались:

- Dense retrieval;
- BM25;
- Hybrid Dense + BM25 через Reciprocal Rank Fusion;
- Dense retrieval + multilingual reranker.

Финальная retrieval-архитектура:

```text
Metadata prefilter
        |
        v
Dense Top-5
        |
        v
GTE multilingual reranker
        |
        v
Reranked Top-5
```

Reranker:

```text
Alibaba-NLP/gte-multilingual-reranker-base
```

Финальные результаты на golden dataset из 20 вопросов:

| Pipeline | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---:|---:|---:|---:|
| Dense | 0.717 | 0.958 | 1.000 | 0.900 |
| Dense Top-5 + GTE reranker | 0.792 | 0.958 | 1.000 | 0.950 |

Reranker улучшил ранжирование релевантных результатов, сохранив Recall@5.

---

## 8. Локальная LLM

Для локального inference используется Ollama.

Текущая модель:

```text
qwen3:4b-instruct
```

LLM используется для:

- natural-language parsing;
- определения intent;
- извлечения аргументов запроса;
- grounded generation для qualitative-вопросов.

LLM не используется для:

- поиска точного финансового значения;
- unit normalization;
- Net Debt / EBITDA;
- Free Cash Flow;
- growth calculation;
- deterministic comparison arithmetic.

---

## 9. Structured Financial Layer

Поддерживаются canonical metrics:

```text
revenue
ebitda
adjusted_ebitda
operating_profit
net_income
total_assets
total_equity
total_debt
cash_and_equivalents
net_debt
capex
operating_cash_flow
free_cash_flow
interest_expense
dividends
```

Derived metrics:

```text
net_debt_to_ebitda
free_cash_flow_calculated
```

Для финансовых значений используется `Decimal`.

---

## 10. Нормализация и comparability

Поддерживаются денежные масштабы:

```text
RUB
RUB_THOUSAND
RUB_MILLION
RUB_BILLION
```

Перед расчетами и сравнением значения приводятся к общей единице.

Проект отдельно проверяет semantic и temporal comparability. Для временной
сопоставимости используются статусы:

```text
COMPARABLE
NOT_COMPARABLE
UNKNOWN
```

Если периоды известны как `NOT_COMPARABLE`, growth calculation блокируется.

---

## 11. Orchestration layer

```text
Question
   |
   v
Parser
   |
   v
Validator
   |
   v
Resolver
   |
   v
Dispatcher
   |
   v
Tool
   |
   v
Answer Formatter
```

Dispatcher выбирает нужный механизм:

```text
qualitative   -> retrieve_docs
fact          -> query_facts
derived_metric-> compute_metric
comparison    -> compare_companies
growth        -> calculate_growth
```

---

## 12. Streamlit Demo Application

Для работы с системой через браузер используется Streamlit.

Интерфейс позволяет:

- задавать вопросы на естественном языке;
- получать точные финансовые значения;
- получать результаты расчетов;
- сравнивать компании;
- задавать качественные вопросы по годовым отчетам;
- видеть provenance и ссылки на документы/страницы.

Пользовательский поток:

```text
Streamlit
   |
   v
CreditAnalystAssistant.ask_text()
   |
   v
QuestionParser
   |
   v
Validator / Resolver
   |
   v
Dispatcher
   |
   +--> RAG
   |
   +--> FinancialFact Store
   |
   +--> Python calculations
   |
   v
AnswerFormatter
   |
   v
Ответ в браузере
```

Тяжелые модели и RAG-компоненты кэшируются через `st.cache_resource`.

---

## 13. Evaluation

В проекте есть несколько независимых уровней оценки.

### Retrieval evaluation

Папка `evals/` содержит:

```text
evaluate_retrieval.py
evaluate_bm25.py
evaluate_hybrid.py
evaluate_reranker.py
retrieval_golden.jsonl
```

Основные метрики: Recall@1, Recall@3, Recall@5, MRR.

### End-to-end evaluation

```text
scripts/run_e2e_evaluation.py
```

Последний зафиксированный baseline:

```text
8 / 8 cases passed
Intent accuracy:   100%
Tool accuracy:     100%
Argument accuracy: 100%
Numeric cases:     4 / 4
```

### Stress evaluation

```text
scripts/run_stress_evaluation.py
```

Последний зафиксированный результат:

```text
10 / 10 cases passed
Intent accuracy:   100%
Tool accuracy:     100%
Argument accuracy: 100%
Numeric cases:     5 / 5
```

### Qualitative evaluation

```text
scripts/run_qualitative_evaluation.py
```

Проверяет структуру citation и соответствие источников. Citation integrity не
равна полной semantic quality ответа, поэтому эта оценка интерпретируется
отдельно от retrieval metrics.

---

## 14. Unit tests и code quality

Запуск unit tests:

```bash
uv run pytest tests/unit -q
```

Текущее состояние:

```text
61 passed
```

Static analysis:

```bash
uv run ruff check app.py src tests scripts evals
```

Текущий стек:

```text
Python 3.12
uv
pytest
ruff
Streamlit
Pydantic
pdfplumber
PyMuPDF
pypdf
NumPy
PyTorch
Transformers
Sentence Transformers
rank-bm25
Ollama
```

---

## 15. Структура репозитория

```text
credit-analyst-rag/
|
├── app.py
|
├── data/
│   ├── raw/
│   │   └── MANIFEST.csv
│   ├── interim/
│   └── processed/
|
├── docs/
│   └── DECISIONS.md
|
├── evals/
│   ├── evaluate_bm25.py
│   ├── evaluate_hybrid.py
│   ├── evaluate_reranker.py
│   ├── evaluate_retrieval.py
│   └── retrieval_golden.jsonl
|
├── scripts/
│   ├── ask_rag.py
│   ├── build_chunk_cache.py
│   ├── build_financial_facts.py
│   ├── run_e2e_evaluation.py
│   ├── run_qualitative_evaluation.py
│   └── run_stress_evaluation.py
|
├── src/
│   └── credit_rag/
│       ├── assistant/
│       ├── evaluation/
│       ├── financial/
│       └── rag/
|
├── tests/
│   └── unit/
|
├── pyproject.toml
├── uv.lock
└── README.md
```

---

## 16. Установка

Проект использует Python 3.12.

Установка зависимостей:

```bash
uv sync
```

Ollama устанавливается отдельно.

Локальная LLM:

```bash
ollama pull qwen3:4b-instruct
```

Embedding model и reranker должны быть доступны локально.

---

## 17. Подготовка данных

Raw PDF-файлы намеренно не хранятся в Git.

Ожидаемый набор документов описан в:

```text
data/raw/MANIFEST.csv
```

Построение chunk cache:

```bash
uv run python scripts/build_chunk_cache.py
```

Построение FinancialFact Store:

```bash
uv run python scripts/build_financial_facts.py
```

Generated artifacts исключаются из version control.

---

## 18. Запуск приложения

После подготовки данных запустите Streamlit-интерфейс:

```bash
uv run streamlit run app.py
```

После запуска приложение обычно доступно локально по адресу:

```text
http://localhost:8501
```

Примеры вопросов:

```text
Какая выручка Роснефти за 2025 год?

Как изменилась выручка Роснефти с 2024 по 2025 год?

Какой Net Debt / EBITDA у ЛУКОЙЛа за 2025 год?

Какие климатические риски описывает ЛУКОЙЛ в отчете за 2025 год?
```

Evaluation запускается отдельно:

```bash
uv run python scripts/run_e2e_evaluation.py
uv run python scripts/run_stress_evaluation.py
uv run python scripts/run_qualitative_evaluation.py
```

Retrieval experiments:

```bash
uv run python evals/evaluate_retrieval.py
uv run python evals/evaluate_bm25.py
uv run python evals/evaluate_hybrid.py
uv run python evals/evaluate_reranker.py
```

---

## 19. Текущие ограничения

Проект является сфокусированным прототипом, а не production-сервисом.

Основные ограничения:

- поддерживаются только три компании;
- используются только периоды 2024–2025;
- financial extraction частично опирается на document-specific layout rules;
- отсутствующие disclosures не восстанавливаются автоматически;
- broad qualitative queries могут покрывать не все релевантные аспекты документа;
- пока нет query decomposition и multi-query retrieval;
- Streamlit-интерфейс предназначен для локального запуска и не развернут как публичный web-сервис;
- нет production API;
- нет observability и production monitoring;
- качество local generation ограничено выбранной локальной моделью.

Безопасный no-answer предпочтительнее неподтвержденной генерации.

---

## 20. Возможные следующие шаги

- query decomposition для широких qualitative-вопросов;
- multi-query retrieval;
- retrieval diversity;
- расширение manually labeled golden dataset;
- автоматическая валидация financial extraction;
- lazy loading тяжелых RAG-компонентов;
- REST API;
- публичный web-deployment;
- загрузка пользовательских PDF;
- поддержка новых компаний;
- более универсальный financial extraction pipeline;
- observability;
- containerized deployment;
- мониторинг качества retrieval и generation.

---

## 21. Ключевая идея проекта

Проект намеренно не использует LLM для каждой операции.

Основной принцип:

```text
Использовать LLM там, где нужно понимать язык.

Использовать retrieval там, где нужны доказательства из документов.

Использовать structured data там, где нужны точные факты.

Использовать deterministic code там, где нужны расчеты.
```

Такое разделение делает систему более надежной, объяснимой, тестируемой и
подходящей для задач финансового анализа.
