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

## Android App Status

The Android MVP lives in `/android`.

It includes:

- Kotlin and Jetpack Compose UI.
- Material 3 screens for dashboard, add transaction, transactions, insights, and settings.
- Room local transaction storage.
- DataStore category settings.
- `finance_data.json` import/export with kotlinx.serialization.

Open `/android` in Android Studio, let Gradle sync, then run the `app` configuration on an emulator or Android phone.

On Windows, Gradle is most reliable when the project is opened from a normal Windows path. If the repo is under `\\wsl.localhost` and Gradle reports a file hashing `Incorrect function` error, copy or clone the repo to a Windows filesystem path for Android Studio, or build from inside WSL with a Linux JDK and Android SDK.

## Moving Data Between Desktop And Android

The shared file contract is documented in `/shared/finance_data_schema.md`.

Desktop to Android:

1. Copy the desktop `finance_data.json` to your phone.
2. Open the Android app.
3. Go to Settings.
4. Tap Import and choose the copied file.

Android to desktop:

1. Open Settings in the Android app.
2. Tap Export and save as `finance_data.json`.
3. Copy the file back to the repo root on the desktop.
4. Start the desktop app with `python run.py`.

Import/export is manual in the MVP. There is no cloud sync or shared live database yet.
