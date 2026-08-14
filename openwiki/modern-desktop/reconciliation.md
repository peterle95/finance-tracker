---
type: integration domain
title: Bank reconciliation
description: German bank CSV decoding, category suggestions, tolerance-based matching, and reconciliation results in the modern desktop client.
tags: [reconciliation, csv, typescript]
---

# Bank reconciliation

`src/shared/reconciliation.ts` detects separators/headers, parses German amounts and dates, maps payee/purpose keywords to categories, and matches bank transactions to finance rows. Exact dates and amounts yield `matched`; amount matches within a three-day date window yield `possible`; unmatched rows yield `missing`. Amount tolerance is €0.02. `DataStore.chooseBankCsv` supplies file bytes and the renderer applies results.

`reconciliation.test.ts` covers encoding/CSV variants, amount/date parsing, suggestions, and match statuses. Python has a parallel service documented in [Python services](../python-desktop/services.md).
