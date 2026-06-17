# Finance Tracker

A personal finance tracker with a Python/Tkinter desktop app and an Android MVP for adding and reviewing transactions on a phone.

## Desktop App

The desktop app remains the source-compatible Python application.

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

On Windows, activate the virtual environment with `venv\Scripts\activate`.

Desktop data is stored in `finance_data.json` at the repo root. That file is intentionally ignored by git.

You can point the desktop app at a synced data file with `FINANCE_DATA_FILE`.

Windows PowerShell:

```powershell
$env:FINANCE_DATA_FILE="C:\Users\Peter\Syncthing\FinanceTrackerData\finance_data.json"
python run.py
```

macOS/Linux:

```bash
export FINANCE_DATA_FILE="$HOME/Syncthing/FinanceTrackerData/finance_data.json"
python run.py
```

## Android App Status

The Android MVP lives in `/android`.

It includes:

- Kotlin and Jetpack Compose UI.
- Material 3 screens for Dashboard, Add, Transactions, and Settings.
- Direct read/write access to one synced `finance_data.json` file through Android's Storage Access Framework.
- DataStore app settings for the connected file URI.
- JSON compatibility with the Python desktop app through kotlinx.serialization.
- BNPL / pay-next-month expense entry that stores the real spending date and books the expense on the 1st of the next month.
- Transactions filtering by booking month, category, type, and description search.

Open `/android` in Android Studio, let Gradle sync, then run the `app` configuration on an emulator or Android phone.

On Windows, Gradle is most reliable when the project is opened from a normal Windows path. If the repo is under `\\wsl.localhost` and Gradle reports a file hashing `Incorrect function` error, copy or clone the repo to a Windows filesystem path for Android Studio, or build from inside WSL with a Linux JDK and Android SDK.

## Syncthing Workflow

The shared file contract is documented in `/shared/finance_data_schema.md`.

Recommended setup:

1. Create a Syncthing folder named `FinanceTrackerData`.
2. Put only `finance_data.json` in that folder.
3. Enable Syncthing file versioning for the folder.
4. On desktop, run with `FINANCE_DATA_FILE` pointing at `FinanceTrackerData/finance_data.json`.
5. On Android, open Settings and tap `Connect synced finance_data.json`.
6. Choose the synced `finance_data.json` file using Android's file picker.

After connection, Android reads from and writes to that file directly. On app start and resume it reloads the file, and Settings also has a manual reload button.

BNPL expenses follow the desktop app's Klarna-style behavior: Android writes the booked transaction `date` as the 1st day of the next month and writes the original spending date to `behavior_date`. The Transactions tab filters by booked `date`, so a BNPL row spent in June and booked on July 1 appears under July.

Avoid editing from desktop and Android at the exact same second. Syncthing is file-based, so close or pause on one device when doing a burst of edits on the other.
