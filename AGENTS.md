# AGENTS.md

## Project

Personal finance tracker with Python/Tkinter, Electron/React, and Android clients. They share a synchronized split JSON directory.

## Commands

```bash
# Desktop
pip install -r requirements.txt
python run.py
FINANCE_DATA_DIR=/path/to/FinanceTrackerData python run.py

# Python persistence tests
python -m unittest tests.test_persistence

# Modern desktop
cd modern-desktop
npm install
npm run typecheck
npm test
npm run build

# Android (Windows; use ./gradlew on Unix)
cd android
.\gradlew.bat test assembleDebug
```

### Windows Gradle

- Start with the smallest relevant task, for example: `.\gradlew.bat :app:testDebugUnitTest --tests com.peterle95.financetracker.data.PhoneTransactionIntakeTest --console=plain`.
- Do not add `--no-daemon`: this project still forks a single-use daemon for its JVM settings, making a cold run slower.
- Allow 120 seconds before treating a compile as stuck. Initial Kotlin/KSP compilation takes 34-70 seconds here and can be silent while compiling.
- If a Gradle command times out, inspect `./gradlew.bat --status` before starting another one. Do not run duplicate builds while its daemon is active.
- Run Gradle from the main agent session, not a subagent, so compile progress and failures remain visible.

### Windows ADB

- Do not use `adb devices` as the first ADB command. Its automatic server startup can retain the agent output pipe and appear stuck.
- Start the server separately with redirected output, then list devices: `& "$env:ANDROID_HOME\platform-tools\adb.exe" start-server *> "$env:TEMP\finance-adb-start.log"` followed by `& "$env:ANDROID_HOME\platform-tools\adb.exe" devices -l`.
- Use a 15-second timeout for each ADB command. Verified cold start is about 2 seconds and device listing about 50 ms here.
- An `offline` device is a result, not a reason to wait. Report it and do not run install or hardware-validation commands until it becomes `device`.
- Run ADB from the main agent session, not a subagent, so startup and device state remain visible.

## Conventions

- Python: PEP 8, Tkinter GUI, matplotlib charts, shared `AppState`
- Modern desktop: Electron 43, React 19, TypeScript, Vite, Tailwind
- Android: Kotlin + Jetpack Compose + Material 3, MVVM, kotlinx.serialization
- Data schema shared: `/shared/finance_data_schema.md`
- Live data is the complete shared directory; `finance_data.json` and `FINANCE_DATA_FILE` are migration compatibility only
- BNPL: `date` = 1st of next month, `behavior_date` = real spend date
- No emoji in code/commits
- Keep responses short, caveman-style when possible

## Key Files

| File | Purpose |
|------|---------|
| `run.py` | Desktop entry point |
| `finance_tracker/state.py` | Python split-data persistence |
| `modern-desktop/` | Electron/React desktop client |
| `android/` | Android app |
| `android/app/src/main/java/com/peterle95/financetracker/data/FinanceDirectoryStore.kt` | Android split-data persistence |
| `shared/finance_data_schema.md` | Cross-platform data contract |
| `categories.json` | Live category registry and transaction-file map (gitignored) |

## Rules

- Read relevant files before editing
- Match existing code style — don't add comments
- Verify the affected client with the commands above
- Never commit unless asked

## Agent skills

### Issue tracker

Issues live in GitHub Issues for `peterle95/finance-tracker`. See `docs/agents/issue-tracker.md`.

### Triage labels

Use default labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout with root `CONTEXT.md` and `docs/adr/`. See `docs/agents/domain.md`.

<!-- OPENWIKI:START -->

## OpenWiki

This repository has a generated `openwiki/` evidence index. It is optional just-in-time context, not required startup reading.

- Treat source code and tests as authoritative. A brief's unknowns and review items are verification gaps, not automatic requirements.
- Prefer the narrowest quiet validation that proves the changed behavior. Preserve complete failure output.

The scheduled OpenWiki GitHub Actions workflow refreshes the repository wiki. Do not hand-edit generated OpenWiki pages unless explicitly asked; prefer updating source code/docs and letting OpenWiki regenerate.

<!-- OPENWIKI:END -->
