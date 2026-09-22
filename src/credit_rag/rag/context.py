import re
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from credit_rag.rag.schemas import ChunkDocument


@dataclass(frozen=True)
class ContextSource:
    """
    Представляет один источник, передаваемый в контекст LLM.
    """

    doc_id: str
    company: str
    year: int
    page: int
    chunk_ids: tuple[str, ...]
    text: str


def split_into_sentences(text: str) -> list[str]:
    """
    Разбивает текст на предложения для удаления повторов между чанками.
    """
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", text.strip())
        if sentence.strip()
    ]


def merge_chunk_texts(chunks: Sequence[ChunkDocument]) -> str:
    """
    Объединяет тексты чанков одной страницы и удаляет повторяющиеся предложения.
    """
    sentences: list[str] = []
    seen_sentences: set[str] = set()

    for chunk in sorted(chunks, key=lambda item: item.chunk_index):
        for sentence in split_into_sentences(chunk.text):
            if sentence in seen_sentences:
                continue

            seen_sentences.add(sentence)
            sentences.append(sentence)

    return " ".join(sentences)


def build_context_sources(
    chunks: Sequence[ChunkDocument],
) -> list[ContextSource]:
    """
    Объединяет чанки одной страницы в единый источник.

    Порядок источников определяется первым появлением страницы
    в результатах retrieval.
    """
    grouped_chunks: dict[tuple[str, int], list[ChunkDocument]] = defaultdict(list)
    source_order: list[tuple[str, int]] = []

    for chunk in chunks:
        key = (chunk.doc_id, chunk.page)

        if key not in grouped_chunks:
            source_order.append(key)

        grouped_chunks[key].append(chunk)

    sources: list[ContextSource] = []

    for key in source_order:
        page_chunks = grouped_chunks[key]
        first_chunk = page_chunks[0]

        source = ContextSource(
            doc_id=first_chunk.doc_id,
            company=first_chunk.company,
            year=first_chunk.year,
            page=first_chunk.page,
            chunk_ids=tuple(
                chunk.chunk_id
                for chunk in sorted(
                    page_chunks,
                    key=lambda item: item.chunk_index,
                )
            ),
            text=merge_chunk_texts(page_chunks),
        )

        sources.append(source)

    return sources


def build_context(chunks: Sequence[ChunkDocument]) -> str:
    """
    Формирует структурированный текстовый контекст для LLM.
    """
    sources = build_context_sources(chunks)
    blocks: list[str] = []

    for source_number, source in enumerate(sources, start=1):
        chunk_ids = ", ".join(source.chunk_ids)

        block = (
            f"[SOURCE {source_number}]\n"
            f"doc_id: {source.doc_id}\n"
            f"company: {source.company}\n"
            f"year: {source.year}\n"
            f"page: {source.page}\n"
            f"chunk_ids: {chunk_ids}\n"
            "\n"
            f"{source.text}"
        )

        blocks.append(block)

    return "\n\n---\n\n".join(blocks)