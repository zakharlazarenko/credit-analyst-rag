import re
from collections.abc import Sequence

from credit_rag.rag.context import ContextSource

COMPANY_NAMES = {
    "LUKOIL": "ЛУКОЙЛ",
    "ROSNEFT": "Роснефть",
    "TATNEFT": "Татнефть",
}


def build_citation_label(source: ContextSource) -> str:
    """
    Формирует пользовательскую ссылку на источник.
    """
    company_name = COMPANY_NAMES.get(
        source.company,
        source.company,
    )

    return (
        f"[{company_name}, "
        f"Годовой отчет {source.year}, "
        f"стр. {source.page}]"
    )


def format_answer_citations(
    answer: str,
    sources: Sequence[ContextSource],
) -> str:
    """
    Заменяет технические ссылки вида [SOURCE N]
    на пользовательские ссылки на документы.
    """
    pattern = re.compile(r"\[SOURCE\s+(\d+)\]")

    def replace_citation(match: re.Match[str]) -> str:
        source_number = int(match.group(1))
        source_index = source_number - 1

        if source_index < 0 or source_index >= len(sources):
            raise ValueError(
                f"Модель сослалась на отсутствующий SOURCE {source_number}."
            )

        return build_citation_label(
            sources[source_index]
        )

    return pattern.sub(
        replace_citation,
        answer,
    )