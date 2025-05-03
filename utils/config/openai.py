import openai
from utils.config.env import secret_key

openai.api_key = secret_key


def generate_answer_with_llm(context: str, question: str):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that answers questions based on resume content.",
            },
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
    )
    return response["choices"][0]["message"]["content"].strip()
