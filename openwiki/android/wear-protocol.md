---
type: device protocol
title: Wear transaction protocol
description: Versioned watch-to-phone transaction messages, category snapshot synchronization, durable delivery, and acknowledgement handling.
tags: [wear, protocol, android]
---

# Wear transaction protocol

`shared-protocol/TransactionProtocol.kt` defines `PROTOCOL_VERSION = 1`, `CATEGORY_SCHEMA_VERSION = 1`, and paths `/finance/v1/transaction-submissions`, `/finance/v1/transaction-acknowledgements`, and `/finance/v1/categories`. A `TransactionSubmission` carries `protocolVersion`, UUID `submissionId`, `type`, ISO `transactionDate`, positive finite `amount`, bounded `category`, bounded `description`, and `isBnpl`; acknowledgements carry the submission ID, `Accepted`/`Duplicate`/`Rejected`, and optional code/message. `CategorySnapshot` carries schema version, revision, and expense/income lists. Strict JSON decoding rejects unknown keys, wrong versions, malformed JSON, invalid values, unsupported BNPL combinations, and encoded payloads over 100,000 bytes. Versions must equal 1; there is no negotiation or forward fallback.

Phone `CategorySnapshotPublisher.publish` serializes category changes under a mutex, ignores older request sequences, increments a persisted revision only when content changes, publishes urgent data at `/finance/v1/categories`, and persists revision/content after successful transport. Watch `WatchCategoryCache` starts with `CategorySnapshotDefaults`, persists the last valid payload, rejects malformed snapshots, accepts only newer revisions for normal updates, and treats authoritative refresh data specially. Unreachable refresh leaves the cached/default snapshot intact. `CategorySnapshotPublisherTest` and `WatchCategoriesTest` cover publication, revision/stale handling, validation, defaults, and category state; this path is separate from transaction outbox delivery.

`WatchCapture` creates validated submissions. `WatchDelivery.kt` stores submissions in Room `watch_submission_outbox`; rows are `PENDING` or `REJECTED`. Durable-before-send storage survives process death/disconnect; sender capability discovery and `WatchDeliveryWorker` provide retry/backoff. Accepted/duplicate acknowledgements delete rows; rejection retains code/message and persisted outcome. `replaceRejected` atomically replaces only the matching rejected row, while `migrateLegacy` imports old SharedPreferences state once under a mutex. `TransactionProtocolCodecTest`, `WatchDeliveryTest`, and `PhoneTransactionIntakeTest` prove the delivery path.
