# Помощник кредитного аналитика на базе RAG

Локальный помощник кредитного аналитика, который объединяет:

- RAG для качественных вопросов по содержанию годовых отчетов;
- структурированное хранилище финансовых фактов для точных числовых значений;
- детерминированные расчеты финансовых показателей;
- LLM для понимания естественного языка, классификации запроса и формирования ответа;
- Streamlit-интерфейс для работы с системой через браузер.

Проект сделан как практическая RAG/LLM-система с акцентом на надежность, прослеживаемость источника данных,
воспроизводимость расчетов, оценку retrieval-качества и четкое разделение
ответственности между LLM и обычным кодом.

---

## 1. Задача проекта

Обычный RAG хорошо подходит для вопросов вида:

> Какие риски ЛУКОЙЛ описывает в годовом отчете за 2025 год?

Но плохо подходит для вопросов:

> Какая выручка Роснефти за 2025 год?

или:

> Какой Net Debt / EBITDA у ЛУКОЙЛа за 2025 год?

Векторный поиск ищет семантически похожий текст, но не
гарантирует извлечение именно нужного числа, периода, единицы измерения или
версии показателя.

Поэтому в проекте используются разные сценарии обработки для разных типов задач.

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

LLM не выполняет расчеты.

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

Отсутствующие параметры не подставляются автоматически.
Модуль восстановления параметров заполняет их только в тех случаях, 
когда это можно однозначно определить по доступным данным.

---

## 4. Данные

Проект работает с отчетностью трех компаний:

- ЛУКОЙЛ
- Роснефть
- Татнефть

Периоды:

- 2024
- 2025

### 4.1. Текстовый корпус

Используются годовые отчеты компаний.

Текущий корпус:

```text
848 страниц
3927 чанков
```

### 4.2. Источник точных финансовых значений

Для числовой ветки используется отчетность по МСФО.

Финансовые значения хранятся в типовом виде:

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

Чанки сохраняют: company, year, doc_id, page, chunk_id.

---

## 6. Embeddings и retrieval

Embedding model:

```text
intfloat/multilingual-e5-small
```

Размер embedding — 384. Для E5 используются префиксы
`query:` - поисковый запрос и `passage:` - кандидат на ответ.

Векторы нормализуются для сравнения по направлению, чтобы найти чанки наиболее похожие по смыслу.

Также применяется фильтр по `company` и `year`, чтобы поиск сразу шел в подходящем документе.

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

Для локального инференса используется Ollama.

Текущая модель:

```text
qwen3:4b-instruct
```

LLM используется для:

- обработка естественного языка;
- определения намерения;
- извлечения аргументов запроса;
- генерация на основе найденного контекста.

LLM не используется для:

- поиска точных финансовых значений;
- нормализации единиц измерения;
- Net Debt / EBITDA;
- Free Cash Flow;
- расчёта темпов роста;
- арифметических сравнений.

---

## 9. Structured Financial Layer

Базовые метрики:

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

Рассчитанные метрики:

```text
net_debt_to_ebitda
free_cash_flow_calculated
```

## 10. Streamlit Demo Application

Для работы с системой через браузер используется Streamlit.

Интерфейс позволяет:

- задавать вопросы на естественном языке;
- получать точные финансовые значения;
- получать результаты расчетов;
- сравнивать компании;
- задавать вопросы по годовым отчетам.

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

## 11. Evaluation

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

Проверяет структуру и соответствие источников.

---

## 12. Unit tests и code quality

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

## 13. Структура репозитория

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

## 14. Установка

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

## 15. Подготовка данных

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

## 16. Запуск приложения

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

## 17. Текущие ограничения

Проект является сфокусированным прототипом, а не production-сервисом.

Основные ограничения:

- поддерживаются только три компании;
- используются только периоды 2024–2025;
- извлечение финансовых показателей частично опирается на структуру конкретных документов;
- отсутствующие в отчетности данные не восстанавливаются автоматически;
- не реализована декомпозиция сложных запросов;
- Streamlit-интерфейс предназначен для локального запуска и не развернут как публичный web-сервис;
- отсутствует промышленный API для интеграции с другими системами;
- пока не реализованы полноценное наблюдение за работой системы и мониторинг ее качества в эксплуатации;
- качество генерации ответов ограничено возможностями выбранной локальной языковой модели.

---

## 18. Возможные следующие шаги

- декомпозиция широких качественных запросов на несколько более узких подзапросов;
- поиск по нескольким вариантам одного и того же запроса;
- повышение разнообразия найденных фрагментов, чтобы ответы охватывали больше аспектов документа;
- расширение вручную размеченного набора эталонных вопросов и источников для оценки качества;
- автоматическая проверка корректности извлечения финансовых показателей;
- отложенная загрузка тяжелых RAG-компонентов только тогда, когда они действительно нужны;
- загрузка пользователями собственных PDF-документов;
- поддержка новых компаний;
- добавление средств наблюдения за работой системы;
- контейнеризация приложения;
- мониторинг качества поиска и генерации ответов в эксплуатации.

---

## 19. Ключевая идея проекта

Проект намеренно не использует LLM для каждой операции.

Основной принцип:

```text
Использовать LLM там, где нужно понимать язык.

Использовать retrieval там, где нужны доказательства из документов.

Использовать структурированные данные там, где нужны точные факты.

Использовать код там, где нужны расчеты.
```

Такое разделение делает систему более надежной, объяснимой, тестируемой и
подходящей для задач финансового анализа.
