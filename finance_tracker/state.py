"""
finance_tracker/state.py

Manages the application state, including data loading, saving, and transaction management.
"""

from copy import deepcopy
import json
import os
from pathlib import Path
import re
import tempfile
import unicodedata
from uuid import uuid4


DEFAULT_EXPENSE_CATEGORIES = [
    "Food", "Transportation", "Entertainment", "Utilities",
    "Shopping", "Healthcare", "Money Lent", "Other"
]
DEFAULT_INCOME_CATEGORIES = ["Salary", "Side Gig", "Bonus", "Gift", "Investment", "Other"]

BUDGET_KEYS = {"monthly_income", "fixed_costs", "daily_savings_goal", "category_budgets"}
NET_WORTH_KEYS = {
    "bank_account_balance", "wallet_balance", "savings_balance", "investment_balance",
    "money_lent_balance", "cash_balance", "asset_snapshots"
}
PREFERENCE_KEYS = {"ai_settings", "default_behaviors", "default_ranges"}


class AppState:
    def __init__(self, data_file=None):
        configured_dir = os.environ.get("FINANCE_DATA_DIR")
        configured_file = os.environ.get("FINANCE_DATA_FILE")
        default_dir = Path(__file__).resolve().parent.parent / "shared"
        if data_file is not None:
            self.data_file = Path(data_file)
            self.data_dir = self.data_file.parent
        elif configured_dir:
            self.data_dir = Path(configured_dir)
            self.data_file = Path(configured_file) if configured_file else self.data_dir / "finance_data.json"
        elif configured_file:
            self.data_file = Path(configured_file)
            if self.data_file.exists():
                self.data_dir = self.data_file.parent
            else:
                self.data_dir = default_dir
                self.data_file = self.data_dir / "finance_data.json"
        else:
            self.data_dir = default_dir
            self.data_file = self.data_dir / "finance_data.json"

        self.expenses = []
        self.incomes = []
        self.budget_settings = {}
        self.categories = {}
        self.persistence_warnings = []
        self._category_records = {"Expense": [], "Income": []}
        self._categories_extra = {}
        self._extra_owners = {}
        self._preference_extra = {}
        self._last_persisted = {}
        self._pending_category_deletions = []
        self.load()

    def load(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        categories_path = self.data_dir / "categories.json"
        if not categories_path.exists() and self.data_file.exists():
            self._migrate_legacy()
        elif categories_path.exists():
            self._load_split()
            self.save()
        else:
            if any(self.data_dir.glob("*.json")):
                raise ValueError("categories.json is missing from a non-empty finance data directory")
            self._set_default_state()
            self.save()
        self._find_persistence_warnings()

    def _set_default_state(self):
        self.expenses = []
        self.incomes = []
        self.categories = {
            "Expense": DEFAULT_EXPENSE_CATEGORIES.copy(),
            "Income": DEFAULT_INCOME_CATEGORIES.copy(),
        }
        self.budget_settings = {}
        self._category_records = {"Expense": [], "Income": []}
        self._categories_extra = {}
        self._extra_owners = {}
        self._preference_extra = {}
        self._last_persisted = {}
        self._ensure_defaults()

    def _load_split(self):
        categories_data = self._read_json("categories.json", {})
        self._categories_extra = {
            key: deepcopy(value) for key, value in categories_data.items()
            if key not in {"Expense", "Income"}
        }
        self._category_records = {"Expense": [], "Income": []}
        self.categories = {"Expense": [], "Income": []}
        for trans_type in ("Expense", "Income"):
            seen = set()
            seen_keys = set()
            for item in categories_data.get(trans_type, []):
                record = dict(item) if isinstance(item, dict) else {"name": str(item)}
                name = str(record.get("name", "")).strip()
                if not name or name.casefold() in seen:
                    raise ValueError(f"Duplicate or empty {trans_type} category: {name!r}")
                seen.add(name.casefold())
                record["name"] = name
                record.setdefault("file_key", self._new_file_key(name, self._category_records[trans_type]))
                file_key = str(record["file_key"])
                if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", file_key) or file_key.casefold() in seen_keys:
                    raise ValueError(f"Invalid or duplicate {trans_type} file key: {file_key!r}")
                record["file_key"] = file_key
                seen_keys.add(file_key.casefold())
                self.categories[trans_type].append(name)
                self._category_records[trans_type].append(record)

        budget = self._read_json("budget.json", {})
        net_worth = self._read_json("net_worth.json", {})
        loans = self._read_json("loans.json", [])
        goals = self._read_json("savings_goals.json", [])
        preferences = self._read_json("preferences.json", {})
        self.budget_settings = {
            key: deepcopy(value)
            for source, keys in ((budget, BUDGET_KEYS), (net_worth, NET_WORTH_KEYS), (preferences, PREFERENCE_KEYS))
            for key, value in source.items() if key in keys
        }
        self.budget_settings["loans"] = deepcopy(loans)
        self.budget_settings["savings_goals"] = deepcopy(goals)
        self._extra_owners = {}
        for owner, source in (("budget", budget), ("net_worth", net_worth)):
            extra = deepcopy(source.get("_extra", {}))
            extra.update({
                key: deepcopy(value) for key, value in source.items()
                if key not in (BUDGET_KEYS if owner == "budget" else NET_WORTH_KEYS) | {"_extra"}
            })
            for key, value in extra.items():
                self.budget_settings[key] = deepcopy(value)
                self._extra_owners[key] = owner
        self._preference_extra = deepcopy(preferences.get("_extra", {}))
        self._preference_extra.update({
            key: deepcopy(value) for key, value in preferences.items()
            if key not in PREFERENCE_KEYS | {"_extra"}
        })
        for key, value in self._preference_extra.get("legacy_budget_settings", {}).items():
            self.budget_settings[key] = deepcopy(value)
            self._extra_owners[key] = "preferences"
        self._ensure_defaults()

        loaded = {
            "categories.json": categories_data,
            "budget.json": budget,
            "net_worth.json": net_worth,
            "loans.json": loans,
            "savings_goals.json": goals,
            "preferences.json": preferences,
        }
        self.expenses = []
        self.incomes = []
        for trans_type, target in (("Expense", self.expenses), ("Income", self.incomes)):
            for record in self._category_records[trans_type]:
                filename = self._transaction_filename(trans_type, record["file_key"])
                path = self.data_dir / filename
                if path.exists():
                    transactions = self._read_json(filename, [])
                    loaded[filename] = deepcopy(transactions)
                else:
                    transactions = []
                    self._atomic_write(path, transactions)
                    loaded[filename] = []
                for transaction in transactions:
                    item = deepcopy(transaction)
                    item.setdefault("id", str(uuid4()))
                    item["category"] = record["name"]
                    target.append(item)
        self._last_persisted = loaded

    def _migrate_legacy(self):
        with self.data_file.open("r", encoding="utf-8") as file:
            legacy = json.load(file)
        self.expenses = deepcopy(legacy.get("expenses", []))
        self.incomes = deepcopy(legacy.get("incomes", []))
        for transaction in self.expenses + self.incomes:
            transaction.setdefault("id", str(uuid4()))
        raw_categories = legacy.get("categories", {})
        self.categories = {
            "Expense": list(raw_categories.get("Expense") or DEFAULT_EXPENSE_CATEGORIES),
            "Income": list(raw_categories.get("Income") or DEFAULT_INCOME_CATEGORIES),
        }
        for trans_type, transactions in (("Expense", self.expenses), ("Income", self.incomes)):
            known = {name.casefold(): name for name in self.categories[trans_type]}
            for transaction in transactions:
                name = str(transaction.get("category", "Other")).strip() or "Other"
                if name.casefold() not in known:
                    self.categories[trans_type].append(name)
                    known[name.casefold()] = name
                transaction["category"] = known[name.casefold()]
        self._validate_category_names()
        self._category_records = {"Expense": [], "Income": []}
        self._categories_extra = {
            key: deepcopy(value) for key, value in raw_categories.items()
            if key not in {"Expense", "Income"}
        }
        self.budget_settings = deepcopy(legacy.get("budget_settings", {}))
        self._ensure_defaults()
        known = BUDGET_KEYS | NET_WORTH_KEYS | PREFERENCE_KEYS | {"loans", "savings_goals"}
        self._extra_owners = {key: "preferences" for key in self.budget_settings if key not in known}
        root_extra = {
            key: deepcopy(value) for key, value in legacy.items()
            if key not in {"expenses", "incomes", "budget_settings", "categories"}
        }
        self._preference_extra = {"legacy_root": root_extra} if root_extra else {}
        self._last_persisted = {}
        desired = self._desired_files()
        for filename, data in desired.items():
            if filename != "categories.json":
                self._atomic_write(self.data_dir / filename, data)
        written = {
            filename: self._read_json(filename, None)
            for filename in desired if filename != "categories.json"
        }
        written["categories.json"] = desired["categories.json"]
        if self._migration_semantics(written) != self._current_semantics():
            raise ValueError("Legacy migration verification failed")
        self._atomic_write(self.data_dir / "categories.json", desired["categories.json"])
        self._last_persisted = deepcopy(desired)

    def _ensure_defaults(self):
        settings = self.budget_settings
        settings.setdefault("fixed_costs", [])
        current_income = settings.get("monthly_income")
        if current_income is None:
            settings["monthly_income"] = []
        elif isinstance(current_income, (int, float)):
            settings["monthly_income"] = ([{
                "amount": float(current_income), "description": "Base Income",
                "start_date": "2025-01-01", "end_date": None
            }] if current_income > 0 else [])
        settings.setdefault("daily_savings_goal", 0)
        settings.setdefault("category_budgets", {"Expense": {}, "Income": {}})
        for key in NET_WORTH_KEYS - {"asset_snapshots"}:
            settings.setdefault(key, 0)
        settings.setdefault("asset_snapshots", [])
        settings.setdefault("loans", [])
        settings.setdefault("savings_goals", [])
        settings.setdefault("ai_settings", {"api_key": ""})
        settings.setdefault("default_behaviors", {})
        settings.setdefault("default_ranges", {})
        for fixed_cost in settings["fixed_costs"]:
            fixed_cost.setdefault("start_date", "2000-01-01")
            fixed_cost.setdefault("end_date", None)

    def save(self):
        desired = self._desired_files()
        previous = self._last_persisted
        deleted_transaction_files = {
            filename for filename in previous.keys() - desired.keys()
            if filename.startswith("transactions_")
        }
        self._revalidate_category_deletions(deleted_transaction_files)
        for filename in deleted_transaction_files:
            (self.data_dir / filename).unlink(missing_ok=True)
        for filename, data in desired.items():
            if data != previous.get(filename):
                self._atomic_write(self.data_dir / filename, data)
        self._last_persisted = deepcopy(desired)

    def _desired_files(self):
        self._validate_category_names()
        self._validate_category_deletions()
        self._reconcile_categories()
        budget_extra = self._owned_extra("budget")
        net_worth_extra = self._owned_extra("net_worth")
        preference_extra = deepcopy(self._preference_extra)
        unowned = {
            key: deepcopy(value) for key, value in self.budget_settings.items()
            if key not in BUDGET_KEYS | NET_WORTH_KEYS | PREFERENCE_KEYS | {"loans", "savings_goals"}
            and self._extra_owners.get(key) not in {"budget", "net_worth"}
        }
        if unowned:
            preference_extra["legacy_budget_settings"] = unowned
        else:
            preference_extra.pop("legacy_budget_settings", None)

        files = {
            "categories.json": {
                **deepcopy(self._categories_extra),
                **deepcopy(self._category_records),
            },
            "budget.json": {key: deepcopy(self.budget_settings[key]) for key in BUDGET_KEYS},
            "net_worth.json": {key: deepcopy(self.budget_settings[key]) for key in NET_WORTH_KEYS},
            "loans.json": deepcopy(self.budget_settings["loans"]),
            "savings_goals.json": deepcopy(self.budget_settings["savings_goals"]),
            "preferences.json": {key: deepcopy(self.budget_settings[key]) for key in PREFERENCE_KEYS},
        }
        files["budget.json"]["_extra"] = budget_extra
        files["net_worth.json"]["_extra"] = net_worth_extra
        files["preferences.json"]["_extra"] = preference_extra
        category_lookup = {
            trans_type: {record["name"].casefold(): record for record in records}
            for trans_type, records in self._category_records.items()
        }
        for trans_type, transactions in (("Expense", self.expenses), ("Income", self.incomes)):
            for record in self._category_records[trans_type]:
                files[self._transaction_filename(trans_type, record["file_key"])] = []
            for transaction in transactions:
                record = category_lookup[trans_type].get(str(transaction.get("category", "")).casefold())
                if record is None:
                    raise ValueError(f"Unknown {trans_type} category: {transaction.get('category')!r}")
                transaction["category"] = record["name"]
                transaction.setdefault("id", str(uuid4()))
                filename = self._transaction_filename(trans_type, record["file_key"])
                files[filename].append(deepcopy(transaction))
        return files

    def _reconcile_categories(self):
        for trans_type in ("Expense", "Income"):
            old_records = self._category_records[trans_type]
            unused = list(old_records)
            records = []
            new_names = []
            for name in self.categories[trans_type]:
                match = next((record for record in unused if record["name"].casefold() == name.casefold()), None)
                if match:
                    unused.remove(match)
                    updated = deepcopy(match)
                    old_name = updated["name"]
                    updated["name"] = name
                    records.append(updated)
                    if old_name != name:
                        self._rename_transaction_categories(trans_type, old_name, name)
                else:
                    new_names.append(name)
            if (len(unused) == len(new_names) == 1
                    and old_records.index(unused[0]) == self.categories[trans_type].index(new_names[0])):
                old = unused.pop()
                name = new_names.pop()
                updated = deepcopy(old)
                updated["name"] = name
                records.append(updated)
                self._rename_transaction_categories(trans_type, old["name"], name)
            for name in new_names:
                records.append({"name": name, "file_key": self._new_file_key(name, records + old_records)})
            order = {name: index for index, name in enumerate(self.categories[trans_type])}
            records.sort(key=lambda record: order[record["name"]])
            self._category_records[trans_type] = records

    def _validate_category_deletions(self):
        self._pending_category_deletions = []
        for trans_type in ("Expense", "Income"):
            current = {name.casefold() for name in self.categories[trans_type]}
            unused = [record for record in self._category_records[trans_type]
                      if record["name"].casefold() not in current]
            old = {record["name"].casefold() for record in self._category_records[trans_type]}
            added = [name for name in self.categories[trans_type] if name.casefold() not in old]
            if (len(unused) == len(added) == 1
                    and self._category_records[trans_type].index(unused[0])
                    == self.categories[trans_type].index(added[0])):
                continue
            target = self.expenses if trans_type == "Expense" else self.incomes
            for record in unused:
                index = self._category_records[trans_type].index(record)
                self._pending_category_deletions.append((trans_type, record, index))
                if (any(str(item.get("category", "")).casefold() == record["name"].casefold()
                        for item in target)
                        or not self._transaction_file_is_empty(trans_type, record)):
                    self._restore_category_deletion(trans_type, record, index)
                    raise ValueError(f"Cannot delete category with transactions: {record['name']}")

    def _revalidate_category_deletions(self, deleted_transaction_files):
        for trans_type, record, index in self._pending_category_deletions:
            filename = self._transaction_filename(trans_type, record["file_key"])
            if filename in deleted_transaction_files and not self._transaction_file_is_empty(trans_type, record):
                self._restore_category_deletion(trans_type, record, index)
                raise ValueError(f"Cannot delete category with transactions: {record['name']}")

    def _restore_category_deletion(self, trans_type, record, index):
        categories = self.categories[trans_type]
        if not any(name.casefold() == record["name"].casefold() for name in categories):
            categories.insert(index, record["name"])
        records = self._category_records[trans_type]
        if not any(item["file_key"] == record["file_key"] for item in records):
            records.insert(index, record)
        persisted = self._last_persisted.get("budget.json", {}).get(
            "category_budgets", {}).get(trans_type, {})
        if record["name"] in persisted:
            self.budget_settings["category_budgets"].setdefault(trans_type, {})[
                record["name"]] = deepcopy(persisted[record["name"]])

    def _transaction_file_is_empty(self, trans_type, record):
        path = self.data_dir / self._transaction_filename(trans_type, record["file_key"])
        try:
            with path.open("r", encoding="utf-8") as file:
                transactions = json.load(file)
        except (OSError, ValueError):
            return False
        return isinstance(transactions, list) and not transactions

    def _rename_transaction_categories(self, trans_type, old_name, new_name):
        target = self.expenses if trans_type == "Expense" else self.incomes
        for transaction in target:
            if str(transaction.get("category", "")).casefold() == old_name.casefold():
                transaction["category"] = new_name
        budgets = self.budget_settings.get("category_budgets", {}).get(trans_type, {})
        if old_name in budgets:
            budgets[new_name] = budgets.pop(old_name)

    def _validate_category_names(self):
        for trans_type in ("Expense", "Income"):
            names = self.categories.get(trans_type, [])
            normalized = [str(name).strip() for name in names]
            if any(not name for name in normalized) or len({name.casefold() for name in normalized}) != len(normalized):
                raise ValueError(f"{trans_type} category names must be non-empty and unique")
            self.categories[trans_type] = normalized

    def _owned_extra(self, owner):
        return {
            key: deepcopy(self.budget_settings[key]) for key, key_owner in self._extra_owners.items()
            if key_owner == owner and key in self.budget_settings
        }

    @staticmethod
    def _new_file_key(name, records):
        base = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii").lower()
        base = re.sub(r"[^a-z0-9]+", "-", base).strip("-") or "category"
        used = {record.get("file_key", "").casefold() for record in records}
        key = base
        suffix = 2
        while key.casefold() in used:
            key = f"{base}-{suffix}"
            suffix += 1
        return key

    @staticmethod
    def _transaction_filename(trans_type, file_key):
        return f"transactions_{trans_type.lower()}_{file_key}.json"

    def _read_json(self, filename, default):
        path = self.data_dir / filename
        if not path.exists():
            return deepcopy(default)
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    @staticmethod
    def _atomic_write(path, data):
        temporary = None
        try:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as file:
                temporary = Path(file.name)
                json.dump(data, file, indent=4, ensure_ascii=True)
                file.write("\n")
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary, path)
        finally:
            if temporary and temporary.exists():
                temporary.unlink()

    def _find_persistence_warnings(self):
        self.persistence_warnings = []
        expected = {
            self._transaction_filename(trans_type, record["file_key"])
            for trans_type, records in self._category_records.items() for record in records
        }
        for path in self.data_dir.glob("*.sync-conflict-*"):
            self.persistence_warnings.append(f"Sync conflict file detected: {path.name}")
        for path in self.data_dir.glob("transactions_*.json"):
            if path.name not in expected:
                self.persistence_warnings.append(f"Orphan transaction file detected: {path.name}")
        self.persistence_warnings.sort()

    def _current_semantics(self):
        root_extra = deepcopy(self._preference_extra.get("legacy_root", {}))
        return self._semantic_value(self.expenses, self.incomes, self.categories, self.budget_settings, root_extra)

    def _migration_semantics(self, files):
        categories = {
            trans_type: [record["name"] for record in files["categories.json"][trans_type]]
            for trans_type in ("Expense", "Income")
        }
        expenses = []
        incomes = []
        for trans_type, target in (("Expense", expenses), ("Income", incomes)):
            for record in files["categories.json"][trans_type]:
                target.extend(deepcopy(files[self._transaction_filename(trans_type, record["file_key"])]))
        settings = {}
        for filename, keys in (("budget.json", BUDGET_KEYS), ("net_worth.json", NET_WORTH_KEYS),
                               ("preferences.json", PREFERENCE_KEYS)):
            settings.update({key: deepcopy(files[filename][key]) for key in keys})
        settings["loans"] = deepcopy(files["loans.json"])
        settings["savings_goals"] = deepcopy(files["savings_goals.json"])
        settings.update(deepcopy(files["budget.json"]["_extra"]))
        settings.update(deepcopy(files["net_worth.json"]["_extra"]))
        preference_extra = files["preferences.json"]["_extra"]
        settings.update(deepcopy(preference_extra.get("legacy_budget_settings", {})))
        return self._semantic_value(expenses, incomes, categories, settings,
                                    preference_extra.get("legacy_root", {}))

    @staticmethod
    def _semantic_value(expenses, incomes, categories, settings, root_extra):
        def by_id(rows):
            return sorted(deepcopy(rows), key=lambda row: str(row.get("id", "")))

        return {
            "expenses": by_id(expenses), "incomes": by_id(incomes),
            "categories": deepcopy(categories), "budget_settings": deepcopy(settings),
            "legacy_root": deepcopy(root_extra),
        }

    def add_transaction(self, trans_type: str, date_str: str, amount: float, category: str,
                        description: str, behavior_date: str = None):
        record = {
            "id": str(uuid4()), "date": date_str, "amount": amount,
            "category": category, "description": description
        }
        if behavior_date:
            record["behavior_date"] = behavior_date
        (self.expenses if trans_type == "Expense" else self.incomes).append(record)
        self.save()

    def delete_transaction_by_id(self, trans_type: str, trans_id: str) -> bool:
        target = self.expenses if trans_type == "Expense" else self.incomes
        for index, transaction in enumerate(target):
            if transaction.get("id") == trans_id:
                del target[index]
                self.save()
                return True
        return False
