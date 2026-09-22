from credit_rag.evaluation.qualitative import (
    evaluate_qualitative_answer,
    extract_citations,
)


def test_extract_citations() -> None:
    answer = (
        "Компания отмечает климатические риски "
        "[ЛУКОЙЛ, Годовой отчет 2025, стр. 25]. "
        "Также рассматриваются физические риски "
        "[ЛУКОЙЛ, Годовой отчет 2025, стр. 26]."
    )

    citations = extract_citations(
        answer
    )

    assert len(citations) == 2

    assert citations[0].company == "ЛУКОЙЛ"
    assert citations[0].year == "2025"
    assert citations[0].page == 25

    assert citations[1].company == "ЛУКОЙЛ"
    assert citations[1].year == "2025"
    assert citations[1].page == 26


def test_valid_qualitative_answer_passes() -> None:
    answer = (
        "Компания отмечает климатические риски "
        "[ЛУКОЙЛ, Годовой отчет 2025, стр. 25]."
    )

    result = evaluate_qualitative_answer(
        answer=answer,
        expected_company="ЛУКОЙЛ",
        expected_year="2025",
    )

    assert result.answer_not_empty is True
    assert result.citations_found == 1
    assert result.company_correct is True
    assert result.year_correct is True
    assert result.pages_valid is True
    assert result.passed is True


def test_wrong_company_fails() -> None:
    answer = (
        "Компания отмечает риски "
        "[Роснефть, Годовой отчет 2025, стр. 25]."
    )

    result = evaluate_qualitative_answer(
        answer=answer,
        expected_company="ЛУКОЙЛ",
        expected_year="2025",
    )

    assert result.company_correct is False
    assert result.passed is False


def test_answer_without_citations_fails() -> None:
    result = evaluate_qualitative_answer(
        answer="В предоставленных источниках недостаточно информации.",
        expected_company="ЛУКОЙЛ",
        expected_year="2025",
    )

    assert result.citations_found == 0
    assert result.passed is False