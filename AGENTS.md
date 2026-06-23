# AGENTS.md

## Project

Personal finance tracker — Python/Tkinter desktop + Android (Kotlin/Jetpack Compose). Shared `finance_data.json` via Syncthing.

## Commands

```bash
# Desktop
pip install -r requirements.txt
python run.py
FINANCE_DATA_FILE=/path/to/data.json python run.py
```

## Conventions

- Python: PEP 8, single `FinanceTracker` class, tkinter GUI, matplotlib charts
- Android: Kotlin + Jetpack Compose + Material 3, MVVM, kotlinx.serialization
- Data schema shared: `/shared/finance_data_schema.md`
- BNPL: `date` = 1st of next month, `behavior_date` = real spend date
- No emoji in code/commits
- Keep responses short, caveman-style when possible

## Key Files

| File | Purpose |
|------|---------|
| `run.py` | Desktop entry point |
| `finance_tracker/` | Desktop app package |
| `android/` | Android app |
| `shared/finance_data_schema.md` | Cross-platform data contract |
| `finance_data.json` | Data (gitignored) |

## Rules

- Read relevant files before editing
- Match existing code style — don't add comments
- Verify with `python run.py` or Android Studio build
- Never commit unless asked
