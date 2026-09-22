from __future__ import annotations

import json
import os
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

from agno.models.message import Message
from agno.models.openai import OpenAIChat


def _reasoning_details(payload: Any) -> list[dict[str, Any]]:
    details = getattr(payload, "reasoning_details", None)
    if details is None:
        model_extra = getattr(payload, "model_extra", None)
        if isinstance(model_extra, dict):
            details = model_extra.get("reasoning_details")
    if not isinstance(details, list):
        return []

    normalized: list[dict[str, Any]] = []
    for detail in details:
        normalized_detail = (
            detail.model_dump(exclude_none=True) if hasattr(detail, "model_dump") else detail
        )
        if isinstance(normalized_detail, dict):
            normalized.append(normalized_detail)
    return normalized


class OpenRouterChat(OpenAIChat):
    """OpenAI-compatible client that preserves reasoning blocks across tool calls."""

    def _format_message(
        self,
        message: Message,
        compress_tool_results: bool = False,
    ) -> dict[str, Any]:
        formatted = super()._format_message(message, compress_tool_results)
        provider_data = message.provider_data or {}
        details = provider_data.get("reasoning_details")
        if isinstance(details, list) and details:
            formatted["reasoning_details"] = details
        elif message.reasoning_content:
            formatted["reasoning"] = message.reasoning_content
        return formatted

    def _parse_provider_response(self, response: Any, response_format: Any = None) -> Any:
        observe(response, self.id)
        model_response = super()._parse_provider_response(response, response_format)
        details = _reasoning_details(response.choices[0].message)
        if details:
            if model_response.provider_data is None:
                model_response.provider_data = {}
            model_response.provider_data["reasoning_details"] = details
        return model_response

    def _parse_provider_response_delta(self, response_delta: Any) -> Any:
        observe(response_delta, self.id)
        model_response = super()._parse_provider_response_delta(response_delta)
        if response_delta.choices:
            details = _reasoning_details(response_delta.choices[0].delta)
            if details:
                if model_response.provider_data is None:
                    model_response.provider_data = {}
                # Agno merges list-valued provider data in stream order. Keeping each
                # block unchanged is required when the assistant message is sent back
                # after a tool result.
                model_response.provider_data["reasoning_details"] = details
        return model_response


active_consumption: ContextVar[dict | None] = ContextVar("consumption", default=None)


def observe(response, model: str) -> None:
    context = active_consumption.get()
    if context is None:
        return
    usage = getattr(response, "usage", None)
    if hasattr(usage, "model_dump"):
        usage = usage.model_dump(mode="json")
    event = {
        "observed_at": datetime.now(UTC).isoformat(),
        "run_key": context["run_key"],
        "defense": context["defense"],
        "model": model,
        "generation_id": getattr(response, "id", None),
        "usage": usage,
    }
    # Stream chunks without usage still retain the ID for later reconciliation.
    identity = (event["generation_id"], json.dumps(usage, sort_keys=True))
    if identity in context["seen"]:
        return
    context["seen"].add(identity)
    context["events"].append(event)
    if path := os.environ.get("QUESTIONNAIRE_USAGE_JOURNAL"):
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())


def summarize(events: list[dict]) -> dict:
    calls = {}
    for event in events:
        calls[event["generation_id"]] = event
    usages = [e["usage"] for e in calls.values() if isinstance(e["usage"], dict)]
    costs = [u["cost"] for u in usages if u.get("cost") is not None]
    return {
        "generation_count": len(calls),
        "usage_count": len(usages),
        "cost_count": len(costs),
        "observed_prompt_tokens": sum(u.get("prompt_tokens") or 0 for u in usages),
        "observed_completion_tokens": sum(u.get("completion_tokens") or 0 for u in usages),
        "observed_cost_usd": sum(costs) if costs else None,
        "coverage_note": "Observed responses only; missing usage and SDK retries require provider reconciliation.",
    }
