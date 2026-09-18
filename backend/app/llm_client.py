from __future__ import annotations

import os
from pathlib import Path
from typing import TypeVar

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)
load_dotenv(Path(__file__).resolve().parents[1] / ".env")


class LLMConfigurationError(RuntimeError):
    pass


class LLMUpstreamError(RuntimeError):
    pass


class LLMClient:
    """Single Gemini wrapper. Invalid or non-JSON model output is discarded."""

    def __init__(self) -> None:
        self.model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

    async def generate_json(self, prompt: str, schema: type[T]) -> T:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise LLMConfigurationError(
                "GEMINI_API_KEY is not configured. Add it to backend/.env and restart the backend."
            )
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "responseJsonSchema": schema.model_json_schema()},
        }
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(url, params={"key": api_key}, json=body)
        if response.is_error:
            try:
                message = response.json().get("error", {}).get("message", response.text)
            except ValueError:
                message = response.text
            raise LLMUpstreamError(f"Gemini API returned {response.status_code}: {message}")
        try:
            raw = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMUpstreamError("Gemini returned no usable candidate content") from exc
        return schema.model_validate_json(raw)


llm_client = LLMClient()
