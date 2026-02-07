"""
finance_tracker/services/ai_insights_service.py

Service for generating AI insights based on finance tracker data.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
import json
import urllib.request
import urllib.error

from dateutil.relativedelta import relativedelta


@dataclass
class AIConfig:
    provider: str
    api_base_url: str
    api_key: str
    model: str


def _month_list(end_month: str, months_back: int) -> list[str]:
    try:
        end = datetime.strptime(end_month + "-01", "%Y-%m-%d").date()
    except ValueError:
        end = datetime.now().date().replace(day=1)

    months = []
    for offset in range(months_back - 1, -1, -1):
        month_date = end - relativedelta(months=offset)
        months.append(month_date.strftime("%Y-%m"))
    return months


def _aggregate_transactions(state, months: list[str]) -> dict[str, Any]:
    month_set = set(months)
    expenses = [e for e in state.expenses if e.get("date", "")[:7] in month_set]
    incomes = [i for i in state.incomes if i.get("date", "")[:7] in month_set]

    def totals_by_category(rows: list[dict[str, Any]]) -> dict[str, float]:
        totals: dict[str, float] = {}
        for row in rows:
            category = row.get("category", "Uncategorized")
            totals[category] = totals.get(category, 0.0) + float(row.get("amount", 0.0))
        return totals

    expense_totals = totals_by_category(expenses)
    income_totals = totals_by_category(incomes)

    total_expenses = sum(expense_totals.values())
    total_income = sum(income_totals.values())
    net = total_income - total_expenses

    return {
        "months": months,
        "totals": {
            "income": total_income,
            "expenses": total_expenses,
            "net": net,
        },
        "expense_categories": expense_totals,
        "income_categories": income_totals,
        "transaction_counts": {
            "expenses": len(expenses),
            "incomes": len(incomes),
        },
    }


def build_insights_prompt(state, month_str: str, months_back: int) -> list[dict[str, str]]:
    months = _month_list(month_str, months_back)
    summary = _aggregate_transactions(state, months)

    system_prompt = (
        "You are a financial coach. Use the provided summary to deliver concise, actionable insights. "
        "Focus on trends, category outliers, and next steps. Provide 5-8 bullet points and end with "
        "3 prioritized recommendations."
    )

    user_prompt = (
        "Analyze the following finance summary and provide insights and advice. "
        "Be specific and reference the categories where possible.\n\n"
        f"Summary JSON:\n{json.dumps(summary, indent=2)}"
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def build_chat_messages(
    state,
    month_str: str,
    months_back: int,
    chat_history: list[dict[str, str]],
    user_message: str,
) -> list[dict[str, str]]:
    months = _month_list(month_str, months_back)
    summary = _aggregate_transactions(state, months)

    system_prompt = (
        "You are a financial coach. Use the provided summary to answer questions with clear, "
        "actionable advice grounded in the user's data."
    )
    summary_prompt = (
        "Context summary JSON (use this as the source of truth for the user's finances):\n"
        f"{json.dumps(summary, indent=2)}"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": summary_prompt},
    ]
    messages.extend(chat_history)
    messages.append({"role": "user", "content": user_message})
    return messages


def request_ai_insights(config: AIConfig, messages: list[dict[str, str]]) -> str:
    if config.provider == "google":
        system_text = " ".join(
            message.get("content", "") for message in messages if message.get("role") == "system"
        ).strip()
        contents = []
        for message in messages:
            role = message.get("role")
            if role == "system":
                continue
            if role == "assistant":
                role = "model"
            contents.append(
                {
                    "role": role,
                    "parts": [{"text": message.get("content", "")}],
                }
            )

        payload = {
            "contents": contents,
            "generationConfig": {"temperature": 0.3},
        }
        if system_text:
            payload["system_instruction"] = {"parts": [{"text": system_text}]}

        base_url = config.api_base_url.rstrip("/")
        request_url = f"{base_url}/models/{config.model}:generateContent?key={config.api_key}"
        request_body = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
    else:
        payload = {
            "model": config.model,
            "messages": messages,
            "temperature": 0.3,
        }
        request_url = config.api_base_url
        request_body = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.api_key}",
        }

    request = urllib.request.Request(
        request_url,
        data=request_body,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8") if exc.fp else str(exc)
        raise RuntimeError(f"API request failed ({exc.code}): {error_body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"API connection failed: {exc.reason}") from exc

    if config.provider == "google":
        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError("No response candidates returned from the API.")
        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            raise RuntimeError("Empty response content returned from the API.")
        content = parts[0].get("text", "")
    else:
        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("No response choices returned from the API.")
        message = choices[0].get("message", {})
        content = message.get("content")

    if not content:
        raise RuntimeError("Empty response content returned from the API.")

    return content.strip()
