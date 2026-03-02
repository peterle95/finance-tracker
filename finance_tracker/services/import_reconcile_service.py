from __future__ import annotations

"""Utilities for CSV import and transaction reconciliation."""

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from dateutil import parser as date_parser
from difflib import SequenceMatcher


def load_csv(path: str) -> List[Dict[str, str]]:
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def parse_flexible_date(value: str) -> str:
    if not value:
        raise ValueError("Date is required")
    parsed = date_parser.parse(value, dayfirst=False, fuzzy=True)
    return parsed.strftime("%Y-%m-%d")


def parse_amount(value: str) -> float:
    if value is None:
        raise ValueError("Amount is required")
    cleaned = str(value).strip().replace("€", "").replace("$", "").replace("£", "")
    cleaned = cleaned.replace(" ", "")

    if cleaned.count(",") > 0 and cleaned.count(".") > 0:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif cleaned.count(",") > 0 and cleaned.count(".") == 0:
        cleaned = cleaned.replace(",", ".")

    return abs(float(cleaned))


def map_csv_rows(rows: List[Dict[str, str]], mapping: Dict[str, str], default_category: str = "Other") -> List[Dict]:
    mapped = []
    for idx, row in enumerate(rows, start=1):
        date_value = row.get(mapping.get("date", ""), "")
        amount_value = row.get(mapping.get("amount", ""), "")
        description_value = row.get(mapping.get("description", ""), "")
        category_key = mapping.get("category")
        category_value = row.get(category_key, "") if category_key else ""

        parsed = {
            "csv_row": idx,
            "date": parse_flexible_date(date_value),
            "amount": parse_amount(amount_value),
            "description": (description_value or "").strip(),
            "category": (category_value or default_category).strip() or default_category,
            "raw": row,
        }
        mapped.append(parsed)
    return mapped


def _description_matches(csv_desc: str, tracked_desc: str) -> bool:
    if not csv_desc or not tracked_desc:
        return True
    a = csv_desc.lower().strip()
    b = tracked_desc.lower().strip()
    if a in b or b in a:
        return True
    return SequenceMatcher(None, a, b).ratio() >= 0.65


def reconcile_rows(csv_rows: List[Dict], state) -> Dict[str, List[Dict]]:
    tracked = []
    for e in state.expenses:
        tracked.append({**e, "type": "Expense"})
    for i in state.incomes:
        tracked.append({**i, "type": "Income"})

    csv_matches, csv_untracked = [], []
    used_ids = set()

    for row in csv_rows:
        match = None
        for txn in tracked:
            if txn.get("id") in used_ids:
                continue
            if txn.get("date") != row.get("date"):
                continue
            if abs(float(txn.get("amount", 0)) - float(row.get("amount", 0))) > 0.001:
                continue
            if not _description_matches(row.get("description", ""), txn.get("description", "")):
                continue
            match = txn
            break

        if match:
            used_ids.add(match.get("id"))
            csv_matches.append({"csv": row, "tracked": match})
        else:
            csv_untracked.append({"csv": row})

    orphaned = [txn for txn in tracked if txn.get("id") not in used_ids]

    return {
        "matched": csv_matches,
        "untracked": csv_untracked,
        "orphaned": orphaned,
        "summary": {
            "matched": len(csv_matches),
            "untracked": len(csv_untracked),
            "orphaned": len(orphaned),
        },
    }


def likely_duplicate(row: Dict, state, description_threshold: float = 0.85) -> Optional[Dict]:
    all_txns = list(state.expenses) + list(state.incomes)
    row_desc = (row.get("description") or "").lower().strip()
    for txn in all_txns:
        if txn.get("date") != row.get("date"):
            continue
        if abs(float(txn.get("amount", 0)) - float(row.get("amount", 0))) > 0.001:
            continue
        existing_desc = (txn.get("description") or "").lower().strip()
        if not row_desc and not existing_desc:
            return txn
        ratio = SequenceMatcher(None, row_desc, existing_desc).ratio()
        if ratio >= description_threshold or row_desc in existing_desc or existing_desc in row_desc:
            return txn
    return None
