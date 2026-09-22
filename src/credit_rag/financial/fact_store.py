from collections.abc import Sequence
from pathlib import Path

from credit_rag.financial.metrics import MetricCode, resolve_metric
from credit_rag.financial.schemas import FinancialFact, FinancialStandard


def save_facts(
    facts: Sequence[FinancialFact],
    path: Path,
) -> None:
    """
    Сохраняет финансовые факты в JSONL-файл.
    """
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        for fact in facts:
            file.write(fact.model_dump_json())
            file.write("\n")


def load_facts(
    path: Path,
) -> list[FinancialFact]:
    """
    Загружает финансовые факты из JSONL-файла.
    """
    if not path.exists():
        return []

    facts: list[FinancialFact] = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            facts.append(
                FinancialFact.model_validate_json(line)
            )

    return facts


def query_facts(
    facts: Sequence[FinancialFact],
    company_id: str,
    period: str,
    metric: MetricCode | str,
    standard: FinancialStandard | None = None,
) -> list[FinancialFact]:
    """
    Возвращает финансовые факты по компании, периоду и метрике.
    """
    if isinstance(metric, MetricCode):
        resolved_metric = metric
    else:
        resolved_metric = resolve_metric(metric)

        if resolved_metric is None:
            return []

    normalized_company_id = company_id.strip().upper()
    normalized_period = period.strip()

    results = [
        fact
        for fact in facts
        if fact.company_id.upper() == normalized_company_id
        and fact.period == normalized_period
        and fact.metric == resolved_metric
        and (
            standard is None
            or fact.standard == standard
        )
    ]

    return results