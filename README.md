# Finance Tracker

Personal finance tracker with Python/Tkinter, Electron/React, and Android/Jetpack Compose clients. All clients use the split JSON directory contract in [`shared/finance_data_schema.md`](shared/finance_data_schema.md).

## Python desktop

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

On Windows, activate with `venv\Scripts\activate`. By default the app uses `shared/`. To use Syncthing:

```powershell
$env:FINANCE_DATA_DIR="C:\Users\Peter\Syncthing\FinanceTrackerData"
python run.py
```

```bash
export FINANCE_DATA_DIR="$HOME/Syncthing/FinanceTrackerData"
python run.py
```

`FINANCE_DATA_FILE` is retained only to locate and migrate a legacy monolithic file. New setups use `FINANCE_DATA_DIR`.

## Modern desktop

```bash
cd modern-desktop
npm install
npm run dev
```

Choose the shared finance data **directory** on first launch. The app remembers it. See [`modern-desktop/README.md`](modern-desktop/README.md) for checks and packaging.

## Android

Open `android/` in Android Studio, let Gradle sync, and run the `app` configuration. In Settings choose **Connect synced directory**, then select the Syncthing folder with Android's directory picker. The app persists tree access and reloads on startup and resume.

Command-line verification from `android/`:

```powershell
.\gradlew.bat test assembleDebug
```

## Syncthing setup

1. Create a folder such as `FinanceTrackerData` and enable file versioning.
2. Put the complete split set directly in it: `categories.json`, five other static JSON files, and every registered expense/income transaction file.
3. Point Python at the folder with `FINANCE_DATA_DIR`.
4. Select the same folder in modern desktop and Android.
5. Let Syncthing finish before editing on another device. Resolve reported conflict or orphan files manually.

Do not sync only the legacy `finance_data.json`. If that is the only data present, selecting its directory triggers one-time migration; the legacy file remains unchanged as recovery input.

BNPL expenses use the first day of the next month as `date` and the real spend date as `behavior_date`. Normal month filters use `date`.
