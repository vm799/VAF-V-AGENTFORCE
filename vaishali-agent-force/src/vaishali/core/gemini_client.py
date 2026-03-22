"""gemini_client.py — Google Gemini 1.5 Flash via REST (httpx).

Free tier: 15 RPM, 1M tokens/day, no credit card.
Get your key at: https://aistudio.google.com/apikey

Keys read from environment (any of these):
  VAF_GOOGLE_AI_KEY
  GOOGLE_AI_KEY
  GEMINI_API_KEY

Usage:
    from vaishali.core.gemini_client import gemini

    if gemini.has_key():
        text = await gemini.complete_async(prompt="Summarise: ...", system="Be concise.")
"""

from __future__ import annotations

import os
import asyncio
from vaishali.core.logging_utils import get_logger

log = get_logger(__name__)

_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
_MODEL = "gemini-1.5-flash"


class GeminiClient:
    """Thin async/sync wrapper around the Gemini REST API using httpx."""

    def __init__(self) -> None:
        self.key: str | None = (
            os.getenv("VAF_GOOGLE_AI_KEY")
            or os.getenv("GOOGLE_AI_KEY")
            or os.getenv("GEMINI_API_KEY")
        )
        if self.key:
            log.info("GeminiClient: API key loaded (%s...)", self.key[:8])
        else:
            log.info("GeminiClient: no key — set VAF_GOOGLE_AI_KEY in .env")

    def has_key(self) -> bool:
        return bool(self.key)

    async def complete_async(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = 1000,
        temperature: float = 0.3,
    ) -> str:
        """Async completion. Returns the text content string.

        Raises:
            ValueError: if no API key configured.
            RuntimeError: on API error.
        """
        if not self.key:
            raise ValueError(
                "No Google AI key. Get a free key at https://aistudio.google.com/apikey "
                "then add VAF_GOOGLE_AI_KEY=... to .env"
            )

        import httpx

        url = f"{_BASE}/{_MODEL}:generateContent?key={self.key}"
        body: dict = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature,
            },
        }
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=body)
            if response.status_code == 429:
                raise RuntimeError("Gemini rate limit hit — free tier is 15 RPM. Wait a moment.")
            response.raise_for_status()
            data = response.json()

        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Unexpected Gemini response shape: {data}") from e

    def complete(self, prompt: str, system: str = "", max_tokens: int = 1000) -> str:
        """Sync wrapper around complete_async."""
        return asyncio.run(self.complete_async(prompt, system, max_tokens))


# Module singleton
gemini = GeminiClient()
