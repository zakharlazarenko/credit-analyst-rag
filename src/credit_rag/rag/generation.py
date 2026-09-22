from ollama import chat

MODEL_NAME = "qwen3:4b-instruct"


def generate_answer(
    system_prompt: str,
    user_prompt: str,
    model_name: str = MODEL_NAME,
) -> str:
    """
    Генерирует grounded-ответ с помощью локальной LLM через Ollama.
    """
    response = chat(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        stream=False,
        options={
            "temperature": 0,
            "num_predict": 500,
        },
    )

    return response.message.content.strip()