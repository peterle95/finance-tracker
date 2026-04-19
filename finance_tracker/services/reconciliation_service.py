"""
finance_tracker/services/reconciliation_service.py

Service for parsing bank CSV exports and reconciling them against manually
entered transactions. Supports the Sparkasse/German bank CSV format.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

# ---------------------------------------------------------------------------
# Status constants
# ---------------------------------------------------------------------------
STATUS_MATCHED  = "matched"   # Found an exact-enough manual entry
STATUS_POSSIBLE = "possible"  # Amount matches but date is off by 1-3 days
STATUS_MISSING  = "missing"   # No manual entry found at all


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class BankTransaction:
    """A single parsed row from the bank CSV."""
    raw_date: str          # e.g. "20.04.26"
    date: str              # Normalised "YYYY-MM-DD"
    amount: float          # Positive = income, negative = expense
    payee: str
    purpose: str
    tx_type: str           # "Income" or "Expense"
    booking_text: str      # Original Buchungstext field
    currency: str = "EUR"
    raw_row: dict = field(default_factory=dict)

    # Set during matching
    status: str = STATUS_MISSING
    matched_tx: dict | None = None      # The manual transaction it matched
    suggested_category: str = ""
    match_confidence: str = ""          # "exact", "fuzzy_date", "fuzzy_amount"


# ---------------------------------------------------------------------------
# CSV parsing
# ---------------------------------------------------------------------------
_KNOWN_ENCODINGS = ["utf-8", "latin-1", "cp1252", "utf-8-sig"]
_KNOWN_SEPARATORS = [";", ",", "\t"]


def _parse_german_amount(s: str) -> float:
    """Convert '1.234,56' or '-89,25' to float."""
    s = s.strip()
    # Remove thousands separator (dot), then replace decimal comma with dot
    s = s.replace(".", "").replace(",", ".")
    return float(s)


def _parse_german_date(s: str) -> str:
    """
    Convert DD.MM.YY or DD.MM.YYYY to YYYY-MM-DD.
    Returns the original string if parsing fails.
    """
    s = s.strip()
    for fmt in ("%d.%m.%y", "%d.%m.%Y"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return s


def _detect_encoding_and_sep(filepath: str) -> tuple[str, str]:
    """Sniff encoding and separator."""
    for enc in _KNOWN_ENCODINGS:
        for sep in _KNOWN_SEPARATORS:
            try:
                with open(filepath, encoding=enc, newline="") as f:
                    sample = f.read(4096)
                dialect = csv.Sniffer().sniff(sample, delimiters=sep)
                # Quick sanity check: parsed header should have >3 columns
                reader = csv.reader(io.StringIO(sample), delimiter=sep)
                header = next(reader, [])
                if len(header) > 3:
                    return enc, sep
            except Exception:
                continue
    return "latin-1", ";"   # safe fallback for German bank exports


def parse_bank_csv(filepath: str) -> tuple[list[BankTransaction], dict[str, Any]]:
    """
    Parse a German bank CSV export (Sparkasse / DKB / N26 style).
    Returns (transactions, meta) where meta contains column-mapping info.
    """
    encoding, sep = _detect_encoding_and_sep(filepath)

    rows: list[dict] = []
    with open(filepath, encoding=encoding, newline="") as f:
        reader = csv.DictReader(f, delimiter=sep)
        for row in reader:
            rows.append(dict(row))

    if not rows:
        return [], {"error": "Empty file or unrecognised format."}

    # --- column mapping (Sparkasse names first, generic fallbacks) ---
    def _find_col(candidates: list[str], row: dict) -> str:
        """Return the first matching column name, or ''."""
        keys_lower = {k.strip().lower(): k for k in row}
        for c in candidates:
            if c.lower() in keys_lower:
                return keys_lower[c.lower()]
        return ""

    sample = rows[0]
    col_date    = _find_col(["Buchungstag", "Buchungsdatum", "Date", "Datum"], sample)
    col_amount  = _find_col(["Betrag", "Amount", "Umsatz"], sample)
    col_payee   = _find_col(["Beguenstigter/Zahlungspflichtiger", "Empfänger", "Payee",
                              "Auftraggeber/Beguenstigter", "Begünstigter/Zahlungspflichtiger"], sample)
    col_purpose = _find_col(["Verwendungszweck", "Purpose", "Beschreibung", "Betreff",
                              "Buchungstext", "Details"], sample)
    col_btext   = _find_col(["Buchungstext", "Transaktionsart", "Typ"], sample)
    col_curr    = _find_col(["Waehrung", "Währung", "Currency"], sample)

    if not col_date or not col_amount:
        return [], {"error": f"Could not find required columns (date/amount). Found: {list(sample.keys())}"}

    transactions: list[BankTransaction] = []
    skipped = 0

    for row in rows:
        raw_date   = (row.get(col_date) or "").strip()
        raw_amount = (row.get(col_amount) or "").strip()
        payee      = (row.get(col_payee) or "").strip() if col_payee else ""
        purpose    = (row.get(col_purpose) or "").strip() if col_purpose else ""
        btext      = (row.get(col_btext) or "").strip() if col_btext else ""
        currency   = (row.get(col_curr) or "EUR").strip() if col_curr else "EUR"

        if not raw_date or not raw_amount:
            skipped += 1
            continue
        try:
            amount = _parse_german_amount(raw_amount)
        except ValueError:
            skipped += 1
            continue

        date_str = _parse_german_date(raw_date)
        tx_type  = "Income" if amount >= 0 else "Expense"

        # Payee field sometimes has trailing whitespace / extra address lines
        payee = " ".join(payee.split())
        purpose = " ".join(purpose.split())

        transactions.append(BankTransaction(
            raw_date=raw_date,
            date=date_str,
            amount=amount,
            payee=payee,
            purpose=purpose,
            tx_type=tx_type,
            booking_text=btext,
            currency=currency,
            raw_row=row,
        ))

    meta = {
        "encoding": encoding,
        "separator": sep,
        "total_rows": len(rows),
        "skipped": skipped,
        "columns_used": {
            "date": col_date,
            "amount": col_amount,
            "payee": col_payee,
            "purpose": col_purpose,
            "booking_text": col_btext,
        },
    }

    return transactions, meta


# ---------------------------------------------------------------------------
# Category suggestion
# ---------------------------------------------------------------------------
# Simple keyword → category map as fallback when no history exists
_KEYWORD_CATEGORIES: list[tuple[list[str], str]] = [
    (["paypal", "ebay"],                              "Shopping"),
    (["klarna"],                                      "Shopping"),
    (["amazon", "amzn"],                              "Shopping"),
    (["rewe", "edeka", "lidl", "aldi", "netto",
      "penny", "kaufland", "dm ", "rossmann"],        "Food"),
    (["restaurant", "cafe", "mcdonald", "burger",
      "pizza", "subway", "starbucks", "bakery"],      "Food"),
    (["spotify", "netflix", "hbo", "disney",
      "prime", "apple", "google play"],               "Entertainment"),
    (["db ", "bahn", "deutsche bahn", "mvg",
      "bvg", "uber", "bolt", "taxi", "flixbus"],      "Transportation"),
    (["strom", "gas ", "internet", "telefon",
      "vodafone", "telekom", "o2 ", "1&1"],           "Utilities"),
    (["krankenkas", "hkk", "tkk", "aok", "barmer",
      "apotheke", "arzt", "zahnarzt", "pharmacy"],    "Healthcare"),
    (["miete", "wohnung", "rent", "hausgeld"],        "Fixed: Rent"),
    (["versicherung", "insurance"],                   "Utilities"),
    (["gehalt", "lohn", "salary", "wage"],            "Salary"),
    (["zinsen", "dividende", "ertrag"],               "Investment"),
]


def suggest_category(payee: str, purpose: str, tx_type: str, state) -> str:
    """
    Suggest a category by:
    1. Checking past manual transactions with the same payee (most common category).
    2. Falling back to keyword matching on payee + purpose.
    3. Returning 'Other' as last resort.
    """
    combined = (payee + " " + purpose).lower()

    # --- 1. History-based suggestion ---
    source = state.incomes if tx_type == "Income" else state.expenses
    payee_lower = payee.lower()
    category_counts: dict[str, int] = {}
    for t in source:
        t_desc = (t.get("description", "") + " " + t.get("category", "")).lower()
        if payee_lower and payee_lower[:10] in t_desc:
            cat = t.get("category", "")
            if cat:
                category_counts[cat] = category_counts.get(cat, 0) + 1
    if category_counts:
        return max(category_counts, key=category_counts.get)

    # --- 2. Keyword fallback ---
    for keywords, category in _KEYWORD_CATEGORIES:
        if any(kw in combined for kw in keywords):
            # Make sure category exists for this type
            available = state.categories.get(tx_type, [])
            # Try exact match first
            if category in available:
                return category
            # Try prefix match
            for avail in available:
                if avail.lower().startswith(category.lower().split(":")[0].strip()):
                    return avail

    # --- 3. Default ---
    defaults = state.categories.get(tx_type, ["Other"])
    return defaults[-1] if defaults else "Other"


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------
_AMOUNT_TOLERANCE = 0.02   # €0.02 tolerance for rounding
_DATE_EXACT_DAYS = 0
_DATE_FUZZY_DAYS = 3


def _dates_close(date1: str, date2: str, max_days: int) -> bool:
    """Return True if two YYYY-MM-DD strings are within max_days of each other."""
    try:
        d1 = datetime.strptime(date1, "%Y-%m-%d")
        d2 = datetime.strptime(date2, "%Y-%m-%d")
        return abs((d1 - d2).days) <= max_days
    except ValueError:
        return False


def _amounts_match(a: float, b: float) -> bool:
    return abs(abs(a) - abs(b)) <= _AMOUNT_TOLERANCE


def match_transactions(bank_txns: list[BankTransaction], state) -> list[BankTransaction]:
    """
    For each bank transaction, try to find a matching manual entry.
    Adds status / matched_tx / match_confidence in place.
    """
    manual_expenses = list(state.expenses)
    manual_incomes  = list(state.incomes)

    # Track which manual transactions have been used to avoid double-counting
    used_manual_ids: set[str] = set()

    for btx in bank_txns:
        source = manual_incomes if btx.tx_type == "Income" else manual_expenses

        exact_match   = None
        fuzzy_match   = None

        for mtx in source:
            mid = mtx.get("id", id(mtx))
            if mid in used_manual_ids:
                continue
            if not _amounts_match(btx.amount, mtx.get("amount", 0)):
                continue
            if _dates_close(btx.date, mtx.get("date", ""), _DATE_EXACT_DAYS):
                exact_match = mtx
                break
            elif fuzzy_match is None and _dates_close(btx.date, mtx.get("date", ""), _DATE_FUZZY_DAYS):
                fuzzy_match = mtx

        if exact_match:
            btx.status           = STATUS_MATCHED
            btx.matched_tx       = exact_match
            btx.match_confidence = "exact"
            used_manual_ids.add(exact_match.get("id", id(exact_match)))
        elif fuzzy_match:
            btx.status           = STATUS_POSSIBLE
            btx.matched_tx       = fuzzy_match
            btx.match_confidence = "fuzzy_date"
            used_manual_ids.add(fuzzy_match.get("id", id(fuzzy_match)))
        else:
            btx.status = STATUS_MISSING

    return bank_txns


# ---------------------------------------------------------------------------
# Summary statistics
# ---------------------------------------------------------------------------
def get_summary(bank_txns: list[BankTransaction]) -> dict[str, Any]:
    if not bank_txns:
        return {}

    incomes  = [t for t in bank_txns if t.tx_type == "Income"]
    expenses = [t for t in bank_txns if t.tx_type == "Expense"]

    matched  = [t for t in bank_txns if t.status == STATUS_MATCHED]
    possible = [t for t in bank_txns if t.status == STATUS_POSSIBLE]
    missing  = [t for t in bank_txns if t.status == STATUS_MISSING]

    dates = []
    for t in bank_txns:
        try:
            dates.append(datetime.strptime(t.date, "%Y-%m-%d"))
        except ValueError:
            pass

    return {
        "total":           len(bank_txns),
        "income_count":    len(incomes),
        "expense_count":   len(expenses),
        "total_income":    sum(t.amount for t in incomes),
        "total_expenses":  sum(abs(t.amount) for t in expenses),
        "net":             sum(t.amount for t in bank_txns),
        "matched_count":   len(matched),
        "possible_count":  len(possible),
        "missing_count":   len(missing),
        "date_from":       min(dates).strftime("%Y-%m-%d") if dates else "—",
        "date_to":         max(dates).strftime("%Y-%m-%d") if dates else "—",
    }