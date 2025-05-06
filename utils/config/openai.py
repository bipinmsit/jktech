import openai
from utils.config.env import secret_key
import time
from openai.error import RateLimitError, OpenAIError
from fastapi import HTTPException

openai.api_key = secret_key

openai.logging = "debug"


def generate_answer_with_llm(
    context: str, question: str, retries: int = 3, delay: int = 5
):
    messages = [
        {"role": "system", "content": "You are a helpful assistant..."},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
    ]

    for attempt in range(retries):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
            )
            return response["choices"][0]["message"]["content"].strip()
        except RateLimitError as e:
            print(f"[Attempt {attempt+1}] Rate limit hit: {e}")
            time.sleep(delay * (2**attempt))  # exponential backoff
        except OpenAIError as e:
            print(f"[Attempt {attempt+1}] OpenAI error: {e}")
            break
    raise HTTPException(status_code=429, detail="Rate limit exceeded after retries.")
