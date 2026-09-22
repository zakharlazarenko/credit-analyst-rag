import re

from credit_rag.rag.schemas import ChunkDocument, PageDocument


def split_text_with_overlap(
    text: str,
    chunk_size: int = 1200,
    overlap: int = 200,
) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if overlap < 0:
        raise ValueError("overlap cannot be negative")

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks = []

    start = 0

    while start < len(text):
        end = min(
            start + chunk_size,
            len(text),
        )

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(text):
            break

        start = end - overlap

    return chunks


def chunk_page(
    page_document: PageDocument,
    chunk_size: int = 1200,
    overlap: int = 200,
) -> list[ChunkDocument]:
    text_chunks = split_text_by_sentences(
        page_document.text,
        chunk_size=chunk_size,
        overlap=overlap,
    )

    chunks = []

    for chunk_index, text in enumerate(
        text_chunks,
        start=1,
    ):
        chunk = ChunkDocument(
            chunk_id=(
                f"{page_document.doc_id}"
                f"_p{page_document.page:04d}"
                f"_c{chunk_index:03d}"
            ),
            doc_id=page_document.doc_id,
            company=page_document.company,
            year=page_document.year,
            doc_type=page_document.doc_type,
            page=page_document.page,
            chunk_index=chunk_index,
            text=text,
        )

        chunks.append(chunk)

    return chunks

def split_into_sentences(text: str) -> list[str]:
    sentences = re.split(
        r"(?<=[.!?])\s+",
        text,
    )

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]

def split_text_by_sentences(
    text: str,
    chunk_size: int = 1200,
    overlap: int = 200,
) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if overlap < 0:
        raise ValueError("overlap cannot be negative")

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    sentences = split_into_sentences(text)

    chunks = []
    current_sentences = []
    current_length = 0

    for sentence in sentences:
        sentence_length = len(sentence) + 1

        if (
            current_sentences
            and current_length + sentence_length > chunk_size
        ):
            chunks.append(" ".join(current_sentences))

            overlap_sentences = []
            overlap_length = 0

            for previous_sentence in reversed(current_sentences):
                previous_length = len(previous_sentence) + 1

                overlap_sentences.insert(
                    0,
                    previous_sentence,
                )

                overlap_length += previous_length

                if overlap_length >= overlap:
                    break

            current_sentences = overlap_sentences
            current_length = overlap_length

        current_sentences.append(sentence)
        current_length += sentence_length

    if current_sentences:
        chunks.append(" ".join(current_sentences))

    return chunks

def chunk_corpus(
    documents: list[PageDocument],
    chunk_size: int = 1200,
    overlap: int = 200,
) -> list[ChunkDocument]:
    chunks = []

    for document in documents:
        page_chunks = chunk_page(
            document,
            chunk_size=chunk_size,
            overlap=overlap,
        )

        chunks.extend(page_chunks)

    return chunks

if __name__ == "__main__":
    from credit_rag.rag.ingestion import load_corpus

    documents = load_corpus()

    chunks = chunk_corpus(
        documents,
        chunk_size=1200,
        overlap=200,
    )

    print()
    print(f"PAGE DOCUMENTS: {len(documents)}")
    print(f"CHUNKS: {len(chunks)}")

    print()
    print("FIRST CHUNK:")
    print(chunks[0].model_dump(exclude={"text"}))
    print(chunks[0].text[:500])

    print()
    print("LAST CHUNK:")
    print(chunks[-1].model_dump(exclude={"text"}))
    print(chunks[-1].text[:500])