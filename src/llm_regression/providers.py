from __future__ import annotations

import os
from typing import Protocol


class Provider(Protocol):
    model: str

    def generate(self, prompt: str, user_input: str) -> str: ...


class MockProvider:
    """Deterministic provider so the project is runnable without credentials."""

    model = "mock-v1"

    def generate(self, prompt: str, user_input: str) -> str:
        text = user_input.lower()
        if "refund" in text:
            return "Customers can request a refund within 30 days of purchase."
        if "password" in text:
            return "Use the password reset link on the sign-in page."
        if "guarantee" in text or "today" in text:
            return "I cannot guarantee delivery time, but you can check the latest estimate in your order tracking page."
        return "I do not have enough information to answer that accurately."


class OpenAIProvider:
    def __init__(self, model: str) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install OpenAI support with: pip install -e '.[openai]'") from exc
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is required for --provider openai")
        self.client = OpenAI()
        self.model = model

    def generate(self, prompt: str, user_input: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_input},
            ],
        )
        return response.choices[0].message.content or ""
