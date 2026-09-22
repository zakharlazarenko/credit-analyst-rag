from credit_rag.rag.pipeline import RAGPipeline


def main() -> None:
    pipeline = RAGPipeline()

    question = (
        "Какие меры ЛУКОЙЛ использует для удержания "
        "и мотивации работников в 2024 году?"
    )

    answer = pipeline.answer_question(
        question=question,
        company="LUKOIL",
        year=2024,
    )

    print("\n" + "=" * 100)
    print("ВОПРОС")
    print("=" * 100)
    print(question)

    print("\n" + "=" * 100)
    print("ОТВЕТ")
    print("=" * 100)
    print(answer)


if __name__ == "__main__":
    main()