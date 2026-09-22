from sentence_transformers import SentenceTransformer

MODEL_NAME = "intfloat/multilingual-e5-small"


def load_embedding_model() -> SentenceTransformer:
    """
    Загружает embedding-модель из локального Hugging Face cache.
    """
    return SentenceTransformer(
        MODEL_NAME,
        local_files_only=True,
    )


if __name__ == "__main__":
    model = load_embedding_model()

    texts = [
        "query: Как ЛУКОЙЛ управляет климатическими рисками?",
        (
            "passage: Вопросы, связанные с изменением климата, "
            "контролируются на уровне Совета директоров. "
            "В Компании создана рабочая группа по декарбонизации "
            "и адаптации к изменениям климата."
        ),
        (
            "passage: Компания применяет сценарный подход "
            "к прогнозированию и использует механизм внутренней "
            "цены на углерод."
        ),
        (
            "passage: Головной офис компании расположен "
            "в Российской Федерации. Указаны телефон и "
            "контактная информация аудитора."
        ),
    ]

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
    )

    print("EMBEDDINGS SHAPE:", embeddings.shape)

    query_embedding = embeddings[0]

    for index in range(1, len(texts)):
        passage_embedding = embeddings[index]

        similarity = query_embedding @ passage_embedding

        print()
        print(f"PASSAGE {index}")
        print(f"SIMILARITY: {similarity:.4f}")
        print(texts[index])