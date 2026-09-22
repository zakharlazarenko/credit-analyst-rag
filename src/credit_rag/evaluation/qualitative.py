import re
from dataclasses import dataclass

CITATION_PATTERN = re.compile(
    r"\["
    r"(?P<company>[^,\]]+),\s*"
    r"Годовой отчет\s+"
    r"(?P<year>\d{4}),\s*"
    r"стр\.\s*"
    r"(?P<page>\d+)"
    r"\]"
)


@dataclass(frozen=True)
class ParsedCitation:
    """
    Одна citation из qualitative RAG-ответа.
    """

    company: str
    year: str
    page: int


@dataclass(frozen=True)
class QualitativeAnswerEvaluation:
    """
    Результат deterministic-проверки
    qualitative RAG-ответа.
    """

    answer_not_empty: bool

    citations_found: int

    company_correct: bool
    year_correct: bool
    pages_valid: bool

    @property
    def passed(self) -> bool:
        return all(
            (
                self.answer_not_empty,
                self.citations_found > 0,
                self.company_correct,
                self.year_correct,
                self.pages_valid,
            )
        )


def extract_citations(
    answer: str,
) -> tuple[ParsedCitation, ...]:
    """
    Извлекает citations вида:

    [ЛУКОЙЛ, Годовой отчет 2025, стр. 26]
    """

    citations = []

    for match in CITATION_PATTERN.finditer(
        answer
    ):
        citations.append(
            ParsedCitation(
                company=(
                    match.group("company").strip()
                ),
                year=match.group("year"),
                page=int(
                    match.group("page")
                ),
            )
        )

    return tuple(
        citations
    )


def evaluate_qualitative_answer(
    answer: str,
    expected_company: str,
    expected_year: str,
) -> QualitativeAnswerEvaluation:
    """
    Проверяет структурную корректность
    citations в qualitative-ответе.

    Эта функция НЕ проверяет смысловую
    истинность каждого утверждения.
    """

    citations = extract_citations(
        answer
    )

    answer_not_empty = bool(
        answer.strip()
    )

    company_correct = (
        bool(citations)
        and all(
            citation.company
            == expected_company
            for citation in citations
        )
    )

    year_correct = (
        bool(citations)
        and all(
            citation.year
            == expected_year
            for citation in citations
        )
    )

    pages_valid = (
        bool(citations)
        and all(
            citation.page >= 1
            for citation in citations
        )
    )

    return QualitativeAnswerEvaluation(
        answer_not_empty=answer_not_empty,
        citations_found=len(
            citations
        ),
        company_correct=company_correct,
        year_correct=year_correct,
        pages_valid=pages_valid,
    )