# Galaxy Watch 8 validation

Hardware results are unverified until this matrix is executed on the paired phone and watch.

## Prerequisites

- Windows PowerShell, Android SDK, current platform tools and build tools.
- A Galaxy Watch 8 paired to an Android phone, with Google Play services current on both.
- Developer options and ADB debugging enabled on both devices.
- Phone and watch APKs built from the same revision and signed with the same certificate.
- `ANDROID_HOME`, `PHONE_SERIAL`, and `WATCH_SERIAL` set for the current PowerShell session.

## Build, install, and identity checks

Run from `android\`:

```powershell
.\gradlew.bat :shared-protocol:test :wear:testDebugUnitTest :app:testDebugUnitTest assembleDebug
& "$env:ANDROID_HOME\platform-tools\adb.exe" devices -l
& "$env:ANDROID_HOME\platform-tools\adb.exe" -s $env:PHONE_SERIAL install -r .\app\build\outputs\apk\debug\app-debug.apk
& "$env:ANDROID_HOME\platform-tools\adb.exe" -s $env:WATCH_SERIAL install -r .\wear\build\outputs\apk\debug\wear-debug.apk
& "$env:ANDROID_HOME\platform-tools\adb.exe" -s $env:PHONE_SERIAL shell pm path com.peterle95.financetracker
& "$env:ANDROID_HOME\platform-tools\adb.exe" -s $env:WATCH_SERIAL shell pm path com.peterle95.financetracker
& "$env:ANDROID_HOME\platform-tools\adb.exe" -s $env:PHONE_SERIAL shell dumpsys package com.peterle95.financetracker | Select-String "versionName|versionCode|signatures"
& "$env:ANDROID_HOME\platform-tools\adb.exe" -s $env:WATCH_SERIAL shell dumpsys package com.peterle95.financetracker | Select-String "versionName|versionCode|signatures"
& "$env:ANDROID_HOME\build-tools\35.0.0\apksigner.bat" verify --print-certs .\app\build\outputs\apk\debug\app-debug.apk
& "$env:ANDROID_HOME\build-tools\35.0.0\apksigner.bat" verify --print-certs .\wear\build\outputs\apk\debug\wear-debug.apk
```

Confirm both package paths exist and the APK signer certificate digests match.

## Manual matrix

For every capture, confirm the acknowledgement on the watch and exactly one resulting transaction in the split JSON directory.

- Category sync with the watch UI closed.
- Expense, income, and BNPL expense capture.
- Capture with the phone UI closed.
- Disconnect, capture, reconnect, and wait for retry.
- Kill the phone process, then capture; repeat after killing the watch process.
- Reboot phone and watch with a pending capture.
- Submit two captures quickly and confirm both outcomes appear.
- Trigger a rejection, correct it, and confirm only the correction is accepted.
- Test no reachable `finance_phone` capability, then restore it and confirm retry.
- Test multiple matching phone nodes; confirm a nearby node wins, then stable node-ID order when proximity ties.
- Inspect jobs and logs while retrying:

```powershell
& "$env:ANDROID_HOME\platform-tools\adb.exe" -s $env:WATCH_SERIAL shell dumpsys jobscheduler com.peterle95.financetracker
& "$env:ANDROID_HOME\platform-tools\adb.exe" -s $env:WATCH_SERIAL logcat -d | Select-String "FinanceTracker|Wearable|WorkManager"
& "$env:ANDROID_HOME\platform-tools\adb.exe" -s $env:PHONE_SERIAL logcat -d | Select-String "FinanceTracker|Wearable"
```

- Inspect the affected split transaction file and processed-submission state after each retry; confirm one transaction per submission ID and no duplicate entries.
