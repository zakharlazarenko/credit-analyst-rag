# Помощник кредитного аналитика на базе RAG

Локальный помощник кредитного аналитика, который объединяет:

- RAG для качественных вопросов по содержанию годовых отчетов;
- структурированное хранилище финансовых фактов для точных числовых значений;
- детерминированные расчеты финансовых показателей в Python;
- LLM для понимания естественного языка, классификации запроса и формирования ответа.

Проект сделан как практическая RAG/LLM-система с акцентом на надежность,
provenance, воспроизводимость расчетов, оценку retrieval-качества и четкое
разделение ответственности между LLM и обычным кодом.

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
                            ФИНАЛЬНЫЙ ОТВЕТ
```

Главный архитектурный принцип:

```text
ТЕКСТОВЫЕ ФАКТЫ     -> RAG
ФИНАНСОВЫЕ ЧИСЛА    -> FinancialFact Store
РАСЧЕТЫ             -> Python
LLM                 -> понимание языка и генерация текста
```

LLM не используется как источник истины для точных финансовых значений и
не выполняет детерминированную финансовую арифметику.

---

## 3. Поддерживаемые типы запросов

Ассистент различает шесть intents:

| Intent | Пример | Execution path |
|---|---|---|
| `qualitative` | Какие риски описывает ЛУКОЙЛ? | RAG |
| `fact` | Какая выручка Роснефти за 2025 год? | FinancialFact Store |
| `derived_metric` | Какой Net Debt / EBITDA у ЛУКОЙЛа? | Python calculation |
| `comparison` | Сравни выручку трех компаний | Structured facts + normalization |
| `growth` | Как изменилась выручка с 2024 по 2025? | Structured facts + Python |
| `unknown` | Стоит ли выдавать ЛУКОЙЛу кредит? | Unsupported / guardrail |

Отсутствующие параметры не должны молча придумыватьcя.

Например, если в growth-запросе не указаны периоды, отдельный resolver может
восстановить их только тогда, когда это безопасно с точки зрения доступных
данных и comparability.

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

Каждый факт сохраняет provenance:

```text
company_id
period
standard
metric
value
unit
doc_id
page
extraction_method
confidence
```

Это позволяет всегда связать ответ с конкретным документом и страницей.

---

## 5. Text RAG pipeline

Качественная ветка работает по схеме:

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

### 5.1. Парсинг

Основной PDF-парсер:

```text
pdfplumber
```

Он был выбран после сравнения с:

- `pypdf`;
- `PyMuPDF`.

Подробности выбора находятся в:

```text
docs/DECISIONS.md
```

### 5.2. Chunking

Текущая конфигурация:

```text
chunk size: 1200 символов
overlap: 200 символов
```

Chunks сохраняют metadata:

```text
company
year
doc_id
page
chunk_id
```

---

## 6. Embeddings и retrieval

Embedding model:

```text
intfloat/multilingual-e5-small
```

Размер embedding:

```text
384
```

Для E5 используются обязательные префиксы:

```text
query:
passage:
```

Перед similarity search векторы нормализуются.

Также используется metadata prefilter:

```text
company
year
```

То есть поиск идет только внутри нужной компании и нужного периода.

---

## 7. Эксперименты с retrieval

В проекте сравнивались:

- Dense retrieval;
- BM25;
- Hybrid Dense + BM25 через Reciprocal Rank Fusion;
- Dense retrieval + multilingual reranker.

BM25 и Hybrid сохранены как воспроизводимые эксперименты, но не используются
в основном production-like pipeline.

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

Reranker в первую очередь улучшил позицию релевантного документа на ранних
позициях, сохранив Recall@5.

---

## 8. Context construction

Retrieved chunks не передаются модели напрямую.

Context builder:

- объединяет chunks с одной страницы;
- удаляет точные повторы предложений из overlap;
- сохраняет source metadata;
- строит явные source-блоки.

Пример:

```text
[SOURCE 1]
Company: LUKOIL
Year: 2025
Page: 25

...
```

Generation model получает инструкцию отвечать только на основе переданного
контекста.

---

## 9. Локальная LLM

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
- расчета Net Debt / EBITDA;
- расчета Free Cash Flow;
- growth calculation;
- deterministic comparison arithmetic.

---

## 10. Structured Financial Layer

В проекте поддерживаются canonical metrics:

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

Пример:

```text
Net Debt / EBITDA
=
normalized Net Debt
/
normalized EBITDA
```

Для финансовых значений используется `Decimal`.

---

## 11. Нормализация единиц

В отчетности встречаются разные денежные масштабы:

```text
RUB
RUB_THOUSAND
RUB_MILLION
RUB_BILLION
```

Перед расчетами и сравнением значения приводятся к общей единице.

Например:

```text
600 RUB_BILLION
=
600 000 RUB_MILLION
```

Это позволяет безопасно использовать данные из отчетов с разными форматами
представления чисел.

---

## 12. Comparability guardrails

Проект отдельно проверяет, можно ли сравнивать финансовые показатели.

### 12.1. Semantic comparability

Используется при сравнении разных компаний.

Одинаковое название метрики не гарантирует одинаковый economic scope.

Поэтому comparison tool возвращает:

```text
числовое сравнение
+
comparability status
+
комментарий
```

Например:

```text
COMPARABLE
CAUTION
```

### 12.2. Temporal comparability

Используется при сравнении разных периодов одной компании.

Поддерживаются статусы:

```text
COMPARABLE
NOT_COMPARABLE
UNKNOWN
```

Смысл:

- `COMPARABLE` — расчет допустим;
- `NOT_COMPARABLE` — известно, что сравнение методологически некорректно;
- `UNKNOWN` — сопоставимость не подтверждена.

Если периоды известны как `NOT_COMPARABLE`, growth calculation блокируется.

---

## 13. Orchestration layer

Обработка вопроса разделена на несколько слоев:

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

### Parser

LLM преобразует естественный язык в `ParsedQuestion`.

### Validator

Проверяет:

- поддерживаемую компанию;
- метрику;
- intent;
- обязательные параметры.

### Resolver

Безопасно восстанавливает параметры только там, где это разрешено архитектурой.

### Dispatcher

Выбирает инструмент:

```text
qualitative
-> retrieve_docs

fact
-> query_facts

derived_metric
-> compute_metric

comparison
-> compare_companies

growth
-> calculate_growth
```

### Answer Formatter

Превращает структурированный `DispatchResult` в пользовательский ответ и
форматирует provenance.

---

## 14. Финансовые tools

Основные deterministic tools:

```python
query_financial_facts(...)
compute_financial_metric(...)
compare_financial_companies(...)
calculate_financial_growth(...)
```

Tools возвращают JSON-like структуры, содержащие:

```text
result
units
periods
source_facts
provenance
comparability metadata
```

---

## 15. Evaluation

В проекте есть несколько независимых уровней оценки.

### 15.1. Retrieval evaluation

Папка:

```text
evals/
```

Содержит:

```text
evaluate_retrieval.py
evaluate_bm25.py
evaluate_hybrid.py
evaluate_reranker.py
retrieval_golden.jsonl
```

Основные метрики:

```text
Recall@1
Recall@3
Recall@5
MRR
```

### 15.2. End-to-end evaluation

Скрипт:

```text
scripts/run_e2e_evaluation.py
```

Проверяет:

- intent;
- выбранный tool;
- извлеченные аргументы;
- числовой результат.

Последний зафиксированный baseline:

```text
8 / 8 cases passed
Intent accuracy:   100%
Tool accuracy:     100%
Argument accuracy: 100%
Numeric cases:     4 / 4
```

### 15.3. Stress evaluation

Скрипт:

```text
scripts/run_stress_evaluation.py
```

Проверяет unseen и более неоднозначные формулировки.

Последний зафиксированный результат:

```text
10 / 10 cases passed
Intent accuracy:   100%
Tool accuracy:     100%
Argument accuracy: 100%
Numeric cases:     5 / 5
```

### 15.4. Qualitative evaluation

Скрипт:

```text
scripts/run_qualitative_evaluation.py
```

Проверяет:

- наличие citation;
- структуру citation;
- соответствие компании;
- соответствие года;
- валидность страниц.

Важно: citation integrity не равна полной semantic quality ответа.
Поэтому qualitative evaluation интерпретируется отдельно от retrieval metrics.

---

## 16. Unit tests

Детерминированная часть проекта покрыта быстрыми unit tests.

Запуск:

```bash
uv run pytest tests/unit -q
```

Текущее состояние:

```text
61 passed
```

Unit tests покрывают:

- FinancialFact schema;
- metric resolver;
- unit normalization;
- fact store;
- financial calculations;
- mixed-unit calculations;
- semantic comparability;
- temporal comparability;
- validation;
- period resolution;
- dispatcher;
- financial tools;
- answer formatter;
- qualitative evaluator;
- layout parsing helpers.

Unit suite специально не использует:

- Ollama;
- embedding model;
- reranker inference;
- raw PDFs;
- generated artifacts.

LLM и RAG проверяются отдельными evaluation scripts.

---

## 17. Code quality

Static analysis:

```bash
uv run ruff check src tests scripts evals
```

Unit tests:

```bash
uv run pytest tests/unit -q
```

Текущий стек:

```text
Python 3.12
uv
pytest
ruff
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

## 18. Структура репозитория

```text
credit-analyst-rag/
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
└── README.md
```

---

## 19. Установка

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

## 20. Подготовка данных

Raw PDF-файлы намеренно не хранятся в Git.

Ожидаемый набор документов описан в:

```text
data/raw/MANIFEST.csv
```

### Построение chunk cache

```bash
uv run python scripts/build_chunk_cache.py
```

### Построение FinancialFact Store

```bash
uv run python scripts/build_financial_facts.py
```

Generated artifacts исключаются из version control.

---

## 21. Запуск

Основной пользовательский entry point:

```bash
uv run python scripts/ask_rag.py
```

Evaluation:

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

## 22. Текущие ограничения

Проект является сфокусированным прототипом, а не production-сервисом.

Основные ограничения:

- поддерживаются только три компании;
- используются только периоды 2024–2025;
- financial extraction частично опирается на document-specific layout rules;
- отсутствующие disclosures не восстанавливаются автоматически;
- broad qualitative queries могут покрывать не все релевантные аспекты документа;
- пока нет query decomposition и multi-query retrieval;
- нет web UI;
- нет production API;
- нет observability и production monitoring;
- качество local generation ограничено выбранной локальной моделью.

Безопасный no-answer предпочтительнее неподтвержденной генерации.

---

## 23. Возможные следующие шаги

Потенциальные улучшения:

- query decomposition для широких qualitative-вопросов;
- multi-query retrieval;
- retrieval diversity;
- расширение manually labeled golden dataset;
- автоматическая валидация financial extraction;
- lazy loading тяжелых RAG-компонентов;
- REST API;
- web-интерфейс;
- observability;
- containerized deployment;
- мониторинг качества retrieval и generation.

---

## 24. Ключевая идея проекта

Проект намеренно не использует LLM для каждой операции.

Основной принцип:

```text
Использовать LLM там, где нужно понимать язык.

Использовать retrieval там, где нужны доказательства из документов.

Использовать structured data там, где нужны точные факты.

Использовать deterministic code там, где нужны расчеты.
```

Такое разделение делает систему более надежной, объяснимой,
тестируемой и подходящей для задач финансового анализа.
