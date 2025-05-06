import openai
from utils.config.env import secret_key
import time
import asyncio
from openai.error import RateLimitError, OpenAIError
from fastapi import HTTPException

openai.api_key = secret_key

async def generate_answer_with_llm(context, question, retries=3):
    for attempt in range(retries):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[...]
            )
            return response.choices[0].message.content
        except RateLimitError:
            await asyncio.sleep(2 ** attempt)
        except OpenAIError as e:
            print(f"OpenAI API error: {e}")
            break
    raise HTTPException(status_code=500, detail="LLM service unavailable")