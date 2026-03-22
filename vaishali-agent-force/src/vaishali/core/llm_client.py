"""LLM client with API key rotation, retry, and usage tracking.

Supports Anthropic Claude as primary provider.
Keys are read from environment:
  VAF_ANTHROPIC_KEY_1, VAF_ANTHROPIC_KEY_2, ... (up to 5)
  or VAF_ANTHROPIC_KEY / ANTHROPIC_API_KEY as single key fallback

Usage:
    from vaishali.core.llm_client import llm

    response = llm.complete(
        prompt="Summarise this finance data: ...",
        system="You are Owlbert, a finance analyst.",
        max_tokens=500,
        agent="finance",       # for cost tracking
    )
    # response: LLMResponse(content=str, tokens_in=int, tokens_out=int, model=str, key_index=int)
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from vaishali.core.logging_utils import get_logger

log = get_logger(__name__)


@dataclass
class LLMResponse:
    """Response from LLM completion."""

    content: str
    tokens_in: int
    tokens_out: int
    model: str
    key_index: int  # which key was used (for debugging)
    latency_ms: int


@dataclass
class UsageRecord:
    """Single LLM API usage record for tracking and billing."""

    timestamp: str
    agent: str
    tokens_in: int
    tokens_out: int
    cost_usd: float  # estimated: input $3/M, output $15/M for claude-3-5-haiku
    model: str


class LLMClient:
    """Production LLM client with key rotation, retry, and usage tracking."""

    def __init__(self):
        """Initialize client, load keys from environment, load usage history."""
        self.keys: list[str] = []
        self.current_key_index: int = 0
        self.usage_log: list[UsageRecord] = []
        self.usage_path: Path = Path(__file__).parent.parent.parent.parent / "data" / "llm_usage.json"

        # Load API keys from environment
        self._load_keys()

        # Load usage history
        self.load_usage()

        if self.keys:
            log.info(f"LLMClient initialized with {len(self.keys)} API key(s)")
        else:
            log.warning("LLMClient initialized with no API keys configured")

    def _load_keys(self) -> None:
        """Load all API keys from environment variables."""
        # Try VAF_ANTHROPIC_KEY_1..5
        for i in range(1, 6):
            key = os.environ.get(f"VAF_ANTHROPIC_KEY_{i}") or os.environ.get(f"ANTHROPIC_KEY_{i}")
            if key:
                self.keys.append(key)

        # Fallback: VAF_ANTHROPIC_KEY or ANTHROPIC_API_KEY
        if not self.keys:
            key = os.environ.get("VAF_ANTHROPIC_KEY") or os.environ.get("ANTHROPIC_API_KEY")
            if key:
                self.keys.append(key)

    def has_keys(self) -> bool:
        """Return True if at least one API key is configured."""
        return len(self.keys) > 0

    def complete(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = 1000,
        agent: str = "unknown",
        model: str = "claude-haiku-4-5-20251001",
    ) -> LLMResponse:
        """Send synchronous completion request with automatic key rotation on rate limit.

        Retry logic:
        - On 429 (rate limit): rotate to next key, wait 1s, retry up to len(keys) times
        - On 529 (overloaded): exponential backoff (1s, 2s, 4s), max 3 retries
        - On 500/502/503: retry once after 2s
        - Other errors: raise immediately

        Args:
            prompt: The user prompt.
            system: System message / role description.
            max_tokens: Maximum tokens in response.
            agent: Agent name for usage tracking (e.g., "finance", "education").
            model: Model name (default: haiku for cost savings).

        Returns:
            LLMResponse with content, token counts, latency.

        Raises:
            ValueError: If no API keys configured.
            RuntimeError: If all retries exhausted.
        """
        if not self.has_keys():
            raise ValueError(
                "No Anthropic API keys configured. "
                "Set VAF_ANTHROPIC_KEY_1, VAF_ANTHROPIC_KEY, or ANTHROPIC_API_KEY."
            )

        import httpx

        start_time = time.time()
        last_error = None

        # Retry with key rotation and exponential backoff
        for attempt in range(len(self.keys) + 2):  # +2 for extra retry on 5xx
            key_index = (self.current_key_index + attempt) % len(self.keys)
            key = self.keys[key_index]

            try:
                response = self._call_anthropic(
                    key=key,
                    prompt=prompt,
                    system=system,
                    max_tokens=max_tokens,
                    model=model,
                )

                # Success: update key index, record usage, return
                self.current_key_index = key_index
                latency_ms = int((time.time() - start_time) * 1000)

                usage = UsageRecord(
                    timestamp=datetime.utcnow().isoformat(),
                    agent=agent,
                    tokens_in=response.tokens_in,
                    tokens_out=response.tokens_out,
                    cost_usd=self.estimate_cost(response.tokens_in, response.tokens_out, model),
                    model=model,
                )
                self.usage_log.append(usage)
                self.save_usage()

                return LLMResponse(
                    content=response.content,
                    tokens_in=response.tokens_in,
                    tokens_out=response.tokens_out,
                    model=model,
                    key_index=key_index,
                    latency_ms=latency_ms,
                )

            except httpx.HTTPStatusError as e:
                last_error = e
                status = e.response.status_code

                if status == 429:  # Rate limit: rotate key and retry
                    log.warning(f"Rate limit (429) on key {key_index}, rotating...")
                    time.sleep(1)
                    continue

                elif status == 529:  # Overloaded: exponential backoff
                    backoff = 2 ** min(attempt, 2)  # 1s, 2s, 4s
                    log.warning(f"Overloaded (529), backoff {backoff}s...")
                    time.sleep(backoff)
                    continue

                elif status in (500, 502, 503):  # Server error: retry once
                    if attempt < 1:
                        log.warning(f"Server error ({status}), retrying...")
                        time.sleep(2)
                        continue
                    else:
                        raise

                else:  # Other errors: fail immediately
                    raise

            except Exception as e:
                last_error = e
                raise

        # All retries exhausted
        raise RuntimeError(
            f"LLM completion failed after {attempt + 1} attempts. Last error: {last_error}"
        )

    async def complete_async(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = 1000,
        agent: str = "unknown",
        model: str = "claude-haiku-4-5-20251001",
    ) -> LLMResponse:
        """Async version of complete().

        Uses asyncio to run the sync version in a thread pool.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.complete(
                prompt=prompt,
                system=system,
                max_tokens=max_tokens,
                agent=agent,
                model=model,
            ),
        )

    def _call_anthropic(
        self,
        key: str,
        prompt: str,
        system: str,
        max_tokens: int,
        model: str,
    ) -> LLMResponse:
        """Make raw HTTP call to Anthropic API.

        Returns parsed response with content and token counts.
        Raises httpx.HTTPStatusError on API errors.
        """
        import httpx

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        body = {
            "model": model,
            "max_tokens": max_tokens,
            "system": system or "",
            "messages": [{"role": "user", "content": prompt}],
        }

        try:
            client = httpx.Client(timeout=30.0)
            response = client.post(url, headers=headers, json=body)
            response.raise_for_status()

            data = response.json()

            # Extract response content and token counts
            content = ""
            if data.get("content"):
                for block in data["content"]:
                    if block.get("type") == "text":
                        content += block.get("text", "")

            usage = data.get("usage", {})
            tokens_in = usage.get("input_tokens", 0)
            tokens_out = usage.get("output_tokens", 0)

            return LLMResponse(
                content=content,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                model=model,
                key_index=0,  # Will be set by caller
                latency_ms=0,  # Will be set by caller
            )

        except Exception as e:
            log.error(f"Anthropic API call failed: {e}")
            raise

    def estimate_cost(self, tokens_in: int, tokens_out: int, model: str) -> float:
        """Estimate USD cost for tokens.

        Pricing (as of 2024):
        - Haiku: $0.80 / $4 per M tokens (input / output)
        - Sonnet: $3 / $15 per M tokens
        - Opus: $15 / $75 per M tokens
        """
        model_lower = model.lower()

        if "haiku" in model_lower:
            input_cost = 0.80 / 1_000_000
            output_cost = 4.0 / 1_000_000
        elif "sonnet" in model_lower:
            input_cost = 3.0 / 1_000_000
            output_cost = 15.0 / 1_000_000
        elif "opus" in model_lower:
            input_cost = 15.0 / 1_000_000
            output_cost = 75.0 / 1_000_000
        else:
            # Default to haiku
            input_cost = 0.80 / 1_000_000
            output_cost = 4.0 / 1_000_000

        return round(tokens_in * input_cost + tokens_out * output_cost, 6)

    def get_usage_today(self) -> dict:
        """Return usage stats for today."""
        today = datetime.utcnow().date()
        today_logs = [
            log for log in self.usage_log
            if datetime.fromisoformat(log.timestamp).date() == today
        ]

        total_tokens_in = sum(log.tokens_in for log in today_logs)
        total_tokens_out = sum(log.tokens_out for log in today_logs)
        total_cost = sum(log.cost_usd for log in today_logs)

        # Break down by agent
        by_agent: dict[str, dict] = {}
        for log in today_logs:
            if log.agent not in by_agent:
                by_agent[log.agent] = {
                    "calls": 0,
                    "tokens_in": 0,
                    "tokens_out": 0,
                    "cost_usd": 0.0,
                }
            by_agent[log.agent]["calls"] += 1
            by_agent[log.agent]["tokens_in"] += log.tokens_in
            by_agent[log.agent]["tokens_out"] += log.tokens_out
            by_agent[log.agent]["cost_usd"] += log.cost_usd

        return {
            "total_calls": len(today_logs),
            "total_tokens_in": total_tokens_in,
            "total_tokens_out": total_tokens_out,
            "total_cost_usd": round(total_cost, 4),
            "by_agent": by_agent,
        }

    def save_usage(self) -> None:
        """Persist usage_log to data/llm_usage.json, keeping last 30 days."""
        # Keep only last 30 days
        cutoff = datetime.utcnow() - timedelta(days=30)
        self.usage_log = [
            log for log in self.usage_log
            if datetime.fromisoformat(log.timestamp) >= cutoff
        ]

        self.usage_path.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(log) for log in self.usage_log]
        with open(self.usage_path, "w") as f:
            json.dump(data, f, indent=2)

    def load_usage(self) -> None:
        """Load usage history from data/llm_usage.json."""
        if not self.usage_path.exists():
            return

        try:
            with open(self.usage_path) as f:
                data = json.load(f)
            self.usage_log = [UsageRecord(**item) for item in data]
        except Exception as e:
            log.warning(f"Failed to load usage history: {e}")
            self.usage_log = []

    def keys_status(self) -> list[dict]:
        """Return status for each configured key (for monitoring)."""
        status = []
        for i, key in enumerate(self.keys):
            # Count calls and errors for this key
            key_calls = [log for log in self.usage_log if self.keys[i] == key]

            status.append(
                {
                    "index": i,
                    "masked_key": f"{key[:8]}...{key[-4:]}",
                    "call_count": len(key_calls),
                    "last_used": (
                        key_calls[-1].timestamp if key_calls else "never"
                    ),
                }
            )
        return status


# Module-level singleton
llm = LLMClient()
