# Android JSON performance

Issue: https://github.com/peterle95/finance-tracker/issues/109

## Outcome

**Worked.** Reporter confirmed on 2026-10-04 that the app is now clearly faster.
No remaining slowness was reported. Issue #109 is intentionally left open.

The reported symptoms are 3–4 seconds before real finance data appears on the
phone and noticeably slow JSON saves, despite a responsive interface.

## Confirmed mechanism and measurement gaps

The SAF adapter queries the child directory for each file access. The split store
reads transaction files twice on load and reloads the entire dataset after saves.
Static-owner mutations also load everything before editing. These costs are
serialized under the repository mutex.

The investigation in #109 measured a synthetic 60-category fixture with six
static files: 128 reads for reload, 129 for add, and 254 for a budget edit.
Simulated 25 ms directory-operation latency produced roughly four-second
loads/saves. These are store probes, not measurements of the reporter's phone.
The repository warning scan adds further I/O to those original save counts.

Actual phone/provider cold first-data, warm refresh, and verified save timings
remain to be measured. Build duration is not application latency.

## Chosen approach

1. Refresh a filename-to-document-URI index once per logical directory operation.
   Maintain it on create/delete and retry a stale document ID after re-enumeration.
2. Read each registered transaction file once during load, retaining missing-file
   creation, ID normalization, migration checks, and read-after-write verification.
   Assemble the document from JSON elements instead of encoding and reparsing it.
3. Reread the latest touched owners before mutations. Publish verified changes
   into the loaded document without rereading unrelated files. Preserve external
   rows, stable IDs, unknown fields, category moves/renames, and warnings. Include
   net worth when editing loans or validating savings allocations.
4. Keep the last good document during refresh, coalesce overlapping refreshes,
   and expose loading/error state separately from empty data. Explicit refresh
   remains the full reconciliation boundary for Syncthing changes. Reassess a
   private cold-start snapshot only after measuring the storage improvements.

## Attempt 1 — 2026-10-04

Recorded before changing production code. Working branch: `optimize`.

Planned checks:

- Focused `FinanceDirectoryStoreTest` operation counts and preservation/failure
  cases, followed by SAF external-replacement coverage.
- `cd android; .\gradlew.bat :app:testDebugUnitTest --tests com.peterle95.financetracker.data.FinanceDirectoryStoreTest --console=plain`
- `cd android; .\gradlew.bat test assembleDebug --console=plain`
- Compare synthetic counts/timings using the same 60-category fixture. Check for
  an available device and record any hardware-verification limitation.
- Review the implementation before committing and pushing.

### Implementation

- SAF enumerates and indexes document IDs once at the beginning of a store
  operation. Creates/deletes update the index. A missing cached ID triggers one
  re-enumeration/retry; permission and provider errors still fail the operation.
- Loads read the six static owners and each transaction file once. The loaded
  registry also supplies warning expectations. JSON elements go directly into
  the codec, avoiding the full pretty-print/parse round trip.
- Mutations reread their owners, verify writes, then publish from the loaded
  file snapshot plus changed owners. That snapshot is only presentation state;
  shared-file writes use freshly read owners. Update/delete try the known owner
  first and fall back to a scan after an external move. Scanned owners also
  update presentation state so the old location cannot leave a duplicate.
- Loans reread both loan/net-worth owners. Savings allocations reread goals and
  net worth so external allocations/balance changes still constrain spending.
- Refreshes reconcile every owner under the existing mutation mutex. Concurrent
  refresh callers share one request. Last-good data remains visible; a status
  banner identifies loading, refresh, and failed refreshes.
- Added Robolectric as a test-only dependency to exercise real Android resolver
  and document APIs against a controllable provider while hardware is offline.

### Synthetic measurements — 2026-10-04

Fixture: six static files plus 60 registered categories, one existing ID-assigned
row per category; no migration. Counts include verification reads. New save
measurements also call the warning path, which now performs no additional I/O.
The new timing probe delays every directory operation by a nominal 25 ms; JVM
warm-up and Windows scheduling affect elapsed time.

| Operation | Original reads from #109 | New reads | New listings | New writes | Initial optimized elapsed |
|---|---:|---:|---:|---:|---:|
| Cold store reload | 128 | 66 | 1 | 0 | 2,239 ms |
| Warm store reload | 128 | 66 | 1 | 0 | 2,127 ms |
| Add transaction | 129 | 3 | 1 | 1 | 168 ms |
| Update in same category | Not measured | 3 | 1 | 1 | 170 ms |
| Delete transaction | Not measured | 3 | 1 | 1 | 155 ms |
| Budget edit | 254 | 2 | 1 | 1 | 140 ms |

The baseline source was exactly the investigated commit
`bafde0f3fe597cc97e23a0778f96aa36d6407780`. The new load-count test failed there
before the fix and passed afterward. The original investigation's roughly
4,040–4,585 ms load and 4,060–4,070 ms add timings came from its disposable
probe; they were not rerun on a phone or with this new test harness. Do not
treat these elapsed-time columns as a controlled real-device comparison.

SAF provider tests independently confirm one child query for initial enumeration,
zero additional queries for repeated reads/writes/creates/deletes in that
operation, and one extra query per stale-ID recovery. The store probe measures
logical listings, not actual provider latency or rendering time.

Runnable timing probe (PowerShell, from `android/`):

```powershell
$env:FINANCE_TEST_IO_DELAY_MS = '25'
.\gradlew.bat :app:testDebugUnitTest --tests com.peterle95.financetracker.data.FinanceDirectoryStoreTest.syntheticLatencyProbe --console=plain
Remove-Item Env:FINANCE_TEST_IO_DELAY_MS
```

Read the probe output in
`android/app/build/test-results/testDebugUnitTest/TEST-com.peterle95.financetracker.data.FinanceDirectoryStoreTest.xml`.
Gradle/build time is excluded from the printed operation durations. Use
`--rerun-tasks` when rerunning only the environment-dependent probe unchanged.

### Verification and remaining gaps

- Focused store/SAF tests passed after red/green checks for duplicate loads,
  whole-dataset save reads, externally moved transactions, and overlapping
  refreshes. Coverage also checks external owner rows/unknown fields, loan
  balances, current savings limits, migration, missing registered files,
  conflict/orphan warnings, and last-good state after failed verification.
- Final full check: `.\gradlew.bat test assembleDebug --continue --console=plain`
  ran 67 tests: 65 passed, 2 failed. All 18 store/SAF/repository regression tests
  passed. `assembleDebug` completed and produced
  `android/app/build/outputs/apk/debug/app-debug.apk`. `--continue` allowed APK
  assembly after the test failure; the overall command correctly exited failing.
- Both full-suite failures were reproduced on the unchanged baseline commit in
  a detached temporary worktree, using the two affected test classes:

  | Existing failure | Expected | Actual |
  |---|---|---|
  | `BudgetMathTest.negativeCarryoverIncludesPreviousMonthDeficit` | `800.0` | `2800.0` |
  | `TransactionUiLogicTest.monthFilterUsesBookingDateNotBehaviorDate` | `[bnpl, july-income]` | `[july-income, bnpl]` |

  Baseline command:
  `.\gradlew.bat :app:testDebugUnitTest --tests com.peterle95.financetracker.BudgetMathTest --tests com.peterle95.financetracker.TransactionUiLogicTest --console=plain`.
  Baseline result: 14 tests, the same 2 failures. These tests and their domain
  implementations were not changed by this attempt.
- The first full build exceeded the tool's four-minute limit during packaging.
  `gradlew --status` confirmed no active daemon before retrying. The later
  completed command above separates that operational interruption from the
  pre-existing assertion failures.
- Final Standards review: no open findings. Final Spec review: no open code
  findings. Reporter acceptance has now been received (see below); quantitative
  real-device timings were never measured.
- ADB reported only `emulator-5554 offline`. No install or device timing was
  attempted. The reporter's phone/provider/dataset remains unmeasured
  quantitatively; acceptance is qualitative.
- The loaded document is rebuilt in memory after edits; unrelated shared files
  are reconciled on explicit/startup/resume refresh. A private cold-start
  snapshot is deferred until actual phone measurements justify it.

The issue remains open per the reporter's request, even though the outcome is
now recorded as **Worked**.

### Review corrections and final probe — 2026-10-04

The first review found three incremental-publication cases. Each was reproduced
with a failing check and corrected: external moves must remove obsolete cached
copies when editing the destination; newly read ID-less rows must receive
verified, persisted IDs; and successful partial saves must retain earlier
refresh errors until reconciliation succeeds. Follow-up review found that a
successful cold-recovery reload during a save must clear that error and update
the load timestamp. Full-load publication is now shared by connect, refresh,
and first-save initialization. All four regressions passed in the final full run.

The same 25 ms synthetic probe was rerun after those corrections:

| Operation | Final reads / listings / writes | Final elapsed |
|---|---|---:|
| Cold store reload | 66 / 1 / 0 | 2,257 ms |
| Warm store reload | 66 / 1 / 0 | 2,114 ms |
| Add | 3 / 1 / 1 | 315 ms |
| Update | 3 / 1 / 1 | 171 ms |
| Delete | 3 / 1 / 1 | 168 ms |
| Budget edit | 2 / 1 / 1 | 159 ms |

This is a single synthetic sample, not a phone result or a latency guarantee.
It retains the earlier sample above rather than replacing the attempt history.

## Reporter verification

Asked:

> Did this work on your phone: does your data appear quickly after opening, and are
> JSON saves now fast enough? Please answer yes, no, or partially, and tell me what
> remains slow. I need your answer to complete this task and record the result in
> `ANDROID_JSON_PERFORMANCE.md`.

Answer received 2026-10-04: yes — "this worked, that app is now clearly faster."
No remaining slow areas were reported. Outcome recorded as **Worked** above.
Issue #109 remains open at the reporter's request; it was not closed.
