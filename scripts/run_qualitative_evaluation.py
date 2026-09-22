from pathlib import Path

from credit_rag.assistant.assistant import (
    CreditAnalystAssistant,
)
from credit_rag.assistant.dispatcher import (
    DispatchStatus,
)
from credit_rag.evaluation.qualitative import (
    evaluate_qualitative_answer,
)

PROJECT_DIR = Path(__file__).resolve().parents[1]

FACT_STORE_PATH = (
    PROJECT_DIR
    / "data"
    / "processed"
    / "financial_facts.jsonl"
)


CASES = (
    {
        "case_id": "lukoil_risks_2025",
        "question": (
            "Какие основные риски описывает "
            "ЛУКОЙЛ в годовом отчете за 2025 год?"
        ),
        "company": "ЛУКОЙЛ",
        "year": "2025",
    },
    {
        "case_id": "rosneft_risks_2024",
        "question": (
            "Какие основные риски описывает "
            "Роснефть в годовом отчете за 2024 год?"
        ),
        "company": "Роснефть",
        "year": "2024",
    },
    {
        "case_id": "tatneft_strategy_2025",
        "question": (
            "Какие основные стратегические "
            "приоритеты описывает Татнефть "
            "в годовом отчете за 2025 год?"
        ),
        "company": "Татнефть",
        "year": "2025",
    },
)


def main() -> None:
    print("=" * 100)
    print("QUALITATIVE RAG EVALUATION")
    print("=" * 100)

    assistant = CreditAnalystAssistant(
        fact_store_path=FACT_STORE_PATH
    )

    passed_cases = 0

    for index, case in enumerate(
        CASES,
        start=1,
    ):
        print("\n" + "=" * 100)

        print(
            f"{index}/{len(CASES)} "
            f"{case['case_id']}"
        )

        print("=" * 100)

        print(
            f"QUESTION:\n{case['question']}"
        )

        result = assistant.ask(
            case["question"]
        )

        routing_correct = (
            result.status
            == DispatchStatus.COMPLETED
            and result.tool_name
            == "retrieve_docs"
            and result.payload is not None
        )

        if not routing_correct:
            print("\nROUTING: FAIL")
            print(
                f"status: {result.status.value}"
            )
            print(
                f"tool: {result.tool_name}"
            )

            continue

        print("\nROUTING: PASS")

        answer = str(
            result.payload["answer"]
        )

        evaluation = (
            evaluate_qualitative_answer(
                answer=answer,
                expected_company=case["company"],
                expected_year=case["year"],
            )
        )

        print("\nCITATION EVALUATION:")

        print(
            f"answer_not_empty: "
            f"{evaluation.answer_not_empty}"
        )

        print(
            f"citations_found:  "
            f"{evaluation.citations_found}"
        )

        print(
            f"company_correct:  "
            f"{evaluation.company_correct}"
        )

        print(
            f"year_correct:     "
            f"{evaluation.year_correct}"
        )

        print(
            f"pages_valid:      "
            f"{evaluation.pages_valid}"
        )

        print(
            f"citation_pass:    "
            f"{evaluation.passed}"
        )

        print("\nANSWER:")
        print(answer)

        if evaluation.passed:
            passed_cases += 1

    print("\n" + "#" * 100)
    print("QUALITATIVE EVALUATION SUMMARY")
    print("#" * 100)

    print(
        f"Citation integrity: "
        f"{passed_cases}/{len(CASES)} "
        f"({passed_cases / len(CASES):.1%})"
    )


if __name__ == "__main__":
    main()