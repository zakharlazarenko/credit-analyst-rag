from pathlib import Path

from credit_rag.assistant.assistant import (
    CreditAnalystAssistant,
)
from credit_rag.evaluation.evaluator import (
    build_summary,
    evaluate_case,
)
from credit_rag.evaluation.stress_cases import (
    STRESS_CASES,
)

PROJECT_DIR = Path(__file__).resolve().parents[1]

FACT_STORE_PATH = (
    PROJECT_DIR
    / "data"
    / "processed"
    / "financial_facts.jsonl"
)


def main() -> None:
    print("=" * 100)
    print("CREDIT ANALYST ASSISTANT — STRESS EVALUATION")
    print("=" * 100)

    assistant = CreditAnalystAssistant(
        fact_store_path=FACT_STORE_PATH
    )

    print(
        f"\nStress cases: {len(STRESS_CASES)}"
    )

    results = []

    for index, case in enumerate(
        STRESS_CASES,
        start=1,
    ):
        print("\n" + "=" * 100)

        print(
            f"{index}/{len(STRESS_CASES)} "
            f"{case.case_id}"
        )

        print("=" * 100)

        print(
            f"QUESTION: {case.question}"
        )

        result = assistant.ask(
            case.question
        )

        evaluation = evaluate_case(
            case=case,
            result=result,
        )

        results.append(
            evaluation
        )

        status = (
            "PASS"
            if evaluation.passed
            else "FAIL"
        )

        print(
            f"\nRESULT: {status}"
        )

        print(
            f"intent:    "
            f"{evaluation.intent_correct}"
        )

        print(
            f"status:    "
            f"{evaluation.status_correct}"
        )

        print(
            f"tool:      "
            f"{evaluation.tool_correct}"
        )

        print(
            f"arguments: "
            f"{evaluation.arguments_correct}"
        )

        if evaluation.numeric_checked:
            print(
                f"numeric:   "
                f"{evaluation.numeric_correct}"
            )

        if evaluation.errors:
            print("\nERRORS:")

            for error in evaluation.errors:
                print(
                    f"- {error}"
                )

    results_tuple = tuple(
        results
    )

    summary = build_summary(
        results_tuple
    )

    print("\n" + "#" * 100)
    print("STRESS EVALUATION SUMMARY")
    print("#" * 100)

    print(
        f"Overall E2E:       "
        f"{summary.passed_cases}/"
        f"{summary.total_cases} "
        f"({summary.overall_accuracy:.1%})"
    )

    print(
        f"Intent accuracy:   "
        f"{summary.intent_correct}/"
        f"{summary.total_cases} "
        f"({summary.intent_accuracy:.1%})"
    )

    print(
        f"Tool accuracy:     "
        f"{summary.tool_correct}/"
        f"{summary.total_cases} "
        f"({summary.tool_accuracy:.1%})"
    )

    print(
        f"Argument accuracy: "
        f"{summary.arguments_correct}/"
        f"{summary.total_cases} "
        f"({summary.argument_accuracy:.1%})"
    )

    print(
        f"Numeric accuracy:  "
        f"{summary.numeric_correct}/"
        f"{summary.numeric_total} "
        f"({summary.numeric_accuracy:.1%})"
    )


if __name__ == "__main__":
    main()