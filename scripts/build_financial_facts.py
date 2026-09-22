from pathlib import Path

from credit_rag.financial.configs import (
    lukoil_2024,
    lukoil_2025,
    rosneft_2024,
    rosneft_2025,
    tatneft_2024,
    tatneft_2025,
)
from credit_rag.financial.fact_store import save_facts
from credit_rag.financial.layout_extraction import (
    extract_financial_facts,
)
from credit_rag.financial.schemas import FinancialFact

PROJECT_DIR = Path(__file__).resolve().parents[1]

FINANCIAL_DIR = (
    PROJECT_DIR
    / "data"
    / "raw"
    / "financial"
)

OUTPUT_PATH = (
    PROJECT_DIR
    / "data"
    / "processed"
    / "financial_facts.jsonl"
)


DOCUMENTS = (
    (
        lukoil_2024,
        "lukoil_ifrs_2024.pdf",
    ),
    (
        lukoil_2025,
        "lukoil_ifrs_2025.pdf",
    ),
    (
        rosneft_2024,
        "rosneft_ifrs_2024.pdf",
    ),
    (
        rosneft_2025,
        "rosneft_ifrs_2025.pdf",
    ),
    (
        tatneft_2024,
        "tatneft_ifrs_2024.pdf",
    ),
    (
        tatneft_2025,
        "tatneft_ifrs_2025.pdf",
    ),
)


def extract_document_facts(
    config,
    pdf_filename: str,
) -> list[FinancialFact]:
    """
    Извлекает финансовые факты одного документа
    согласно его конфигурации.
    """
    pdf_path = FINANCIAL_DIR / pdf_filename

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"Файл не найден: {pdf_path}"
        )

    return extract_financial_facts(
        pdf_path=pdf_path,
        rules=config.METRIC_RULES,
        company_id=config.COMPANY_ID,
        period=config.PERIOD,
        doc_id=config.DOC_ID,
        standard=config.STANDARD,
        unit=config.UNIT,
    )


def validate_unique_facts(
    facts: list[FinancialFact],
) -> None:
    """
    Проверяет, что в итоговом хранилище нет
    дубликатов одного и того же финансового факта.

    Уникальный ключ:
    company_id + period + standard + metric.
    """
    seen_keys = set()

    for fact in facts:
        key = (
            fact.company_id,
            fact.period,
            fact.standard,
            fact.metric,
        )

        if key in seen_keys:
            raise ValueError(
                "Обнаружен дубликат финансового факта: "
                f"{fact.company_id} | "
                f"{fact.period} | "
                f"{fact.standard.value} | "
                f"{fact.metric.value}"
            )

        seen_keys.add(key)


def main() -> None:
    all_facts: list[FinancialFact] = []

    for config, pdf_filename in DOCUMENTS:
        document_facts = extract_document_facts(
            config=config,
            pdf_filename=pdf_filename,
        )

        all_facts.extend(
            document_facts
        )

    validate_unique_facts(
        all_facts
    )

    save_facts(
        facts=all_facts,
        path=OUTPUT_PATH,
    )

    print("=" * 100)
    print("FINANCIAL FACT STORE — 2024–2025")
    print("=" * 100)

    for company_id in (
        "LUKOIL",
        "ROSNEFT",
        "TATNEFT",
    ):
        for period in (
            "2024",
            "2025",
        ):
            company_period_facts = [
                fact
                for fact in all_facts
                if (
                    fact.company_id == company_id
                    and fact.period == period
                )
            ]

            print(
                f"{company_id:<10} "
                f"{period} "
                f"{len(company_period_facts):>2} фактов"
            )

            for fact in company_period_facts:
                print(
                    f"  {fact.metric.value:<25} "
                    f"{fact.value:>15} "
                    f"{fact.unit}"
                )

            print()

    print("-" * 100)
    print(
        f"Всего фактов: {len(all_facts)}"
    )
    print(
        f"Сохранено: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()