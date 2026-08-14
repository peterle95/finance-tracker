---
type: workflow
title: Transaction lifecycle
description: End-to-end transaction creation, persistence, category movement, and reliable Wear capture delivery across all clients.
tags: [workflow, transactions, wear]
---

# Transaction lifecycle

Desktop clients create or edit rows in their UI, normalize them, and persist them in the category-owned transaction file. Category rename retains `file_key` and rewrites row category names; moves preserve IDs and unknown fields; deletion is blocked when the source file is populated. BNPL records use booking `date` and optional `behavior_date`.

```mermaid
sequenceDiagram
  participant W as Wear capture
  participant O as Room outbox
  participant T as Wear Data Layer
  participant I as PhoneTransactionIntake
  participant L as Room submission ledger
  participant D as FinanceDirectoryStore
  W->>O: save submissionId and payload
  O->>T: send pending / retry with backoff
  T->>I: /finance/v1/transaction-submissions
  I->>L: validate and get-or-create pending
  I->>D: add transaction with stable transactionId
  D-->>I: committed or failure
  I-->>T: accepted, duplicate, or rejected acknowledgement
  T->>O: delete accepted / retain rejected for correction
```

`WatchOutbox` persists pending/rejected states in Room and migrates legacy SharedPreferences state. `WatchDelivery` retries when the phone capability is unavailable. `PhoneTransactionIntake` serializes calls with a mutex; the ledger makes repeated submission IDs duplicate-safe, rejects invalid payloads, and maps BNPL dates before writing. A write exception returns no acknowledgement, leaving retryable state. Rejected rows retain message/code for correction. Protocol paths and codecs live in [Wear protocol](../android/wear-protocol.md).

Evidence: `WatchDeliveryTest`, `PhoneTransactionIntakeTest`, `TransactionProtocolCodecTest`, Android directory-store tests, `tests/test_persistence.py`, and modern `data-store.test.ts`.
