# Issue #75: Reliable Watch Delivery Constraints

Research date: 2026-08-03  
Scope: Wear OS watch capture -> phone intake only. No app code implemented.

## Resolution

Use a durable local outbox on the watch and a durable phone-side intake record. A
submission needs a stable delivery identity. Send attempts may repeat after a
disconnect or process death, so the phone must atomically recognize an already
processed identity and avoid booking the transaction twice. A successful phone
intake should produce an explicit application acknowledgement; the watch removes
the outbox row only after that acknowledgement is durably recorded. Retry
unacknowledged rows with bounded/backed-off work when connectivity is available.

This is an at-least-once design, not an exactly-once transport guarantee.

## Constraints From Official Documentation

### Lifecycle and background execution

- Android can kill a cached app process at any time to reclaim memory, and
  `Activity.onDestroy()` is not guaranteed when the process is killed. In-memory
  queue state or cleanup in lifecycle callbacks cannot be the source of truth.
  Persist the capture before attempting delivery. Source: [Processes and app
  lifecycle](https://developer.android.com/guide/components/activities/process-lifecycle).
- WorkManager is intended for persistent background work and supports constraints
  plus retry policies, including exponential backoff. It is suitable for draining
  persisted outbox rows, but it does not make the network protocol itself
  reliable. Source: [Task scheduling / persistent
  work](https://developer.android.com/develop/background-work/background-tasks/persistent).
- A Worker returns `Result.retry()` when work should be tried later. The retry
  policy is configured on the work request, so transient connectivity failure
  should leave the outbox row pending and request retry rather than delete it.
  Source: [Getting started with
  WorkManager](https://developer.android.com/develop/background-work/background-tasks/persistent/getting-started).

### Reconnect and transport choice

- Wear OS `MessageClient.sendMessage()` is best-effort, has no built-in retry,
  requires the target node to be connected, and can fail with
  `TARGET_NODE_NOT_CONNECTED`. The documentation's transport comparison lists
  messages as having no persistence and no retry. It must not be the only copy of
  a finance transaction. Source: [Send messages between a handheld and wearable
  device](https://developer.android.com/training/wearables/data/messages).
- Wear OS `DataClient` synchronizes `DataItem`s between phone and wearable when a
  network connection exists; the data is buffered and synchronized when the
  connection is re-established. This is the documented reconnect behavior to
  prefer when the payload can be represented as synchronized data. Source: [Sync
  persistent data](https://developer.android.com/training/wearables/data/data-items).
- A Data Layer path is a unique identifier for a data item. Therefore, one fixed
  path represents one mutable synchronized item, not an append-only queue. A
  queued submission needs a unique path per submission or, more simply, a local
  outbox plus explicit send/ack protocol. Source: [Data Layer
  overview](https://developer.android.com/training/wearables/data/data-layer).

### Local persistence

- Android recommends Room for non-trivial structured data that must remain
  available locally/offline; Room provides an abstraction over SQLite and a
  database containing persisted entities and DAOs. Store pending payload,
  stable submission identity, attempt metadata, and acknowledgement state in
  durable storage rather than process memory. Source: [Save data in a local
  database using Room](https://developer.android.com/training/data-storage/room).
- Room requires each entity to have a primary key, and supports unique indexes.
  Use the stable submission identity as the phone intake's uniqueness boundary
  (or a composite key if the domain requires one), so deduplication is enforced
  by the database rather than a racy read-then-insert check. Source: [Define
  entities using Room](https://developer.android.com/training/data-storage/room/defining-data).

### Retry and acknowledgement

- `MessageClient` provides no built-in retry or persistence, so an application
  retry loop must retain the outbox row until an acknowledgement is received.
  Retrying after an unknown result is unavoidable: a disconnect can happen after
  the phone accepts a submission but before the watch observes the response.
  Sources: [MessageClient transport behavior](https://developer.android.com/training/wearables/data/messages)
  and [Android process lifecycle](https://developer.android.com/guide/components/activities/process-lifecycle).
- The official Wear OS Data Layer documentation describes transport and
  synchronization, not transaction-level commit acknowledgements or exactly-once
  processing. Therefore, define an application-level acknowledgement containing
  the stable submission identity and only mark the watch row delivered after the
  matching acknowledgement is persisted. This is a design consequence of the
  documented transport limits, not an Android guarantee.
- Use WorkManager constraints/backoff for deferred attempts; do not spin a tight
  reconnect loop from a watch activity or assume a callback will run before
  process death. Source: [Persistent background
  work](https://developer.android.com/develop/background-work/background-tasks/persistent).

### Deduplication

- Android's transport documentation does not promise exactly-once delivery or
  exactly-once receiver execution. Because retries are required and their result
  can be ambiguous, the receiver must be idempotent: look up the stable identity,
  atomically insert/book only if unseen, and return an acknowledgement for both
  the first acceptance and a duplicate. This is an application protocol
  requirement derived from the documented best-effort/no-retry behavior.
- Enforce the identity with a Room primary key or unique index. A duplicate
  submission then cannot create a second intake record even if two retry paths
  race. Source: [Room primary keys and unique
  indexes](https://developer.android.com/training/data-storage/room/defining-data).

## Minimal Protocol Shape

1. Watch transaction capture: generate a stable submission identity and commit
   the complete payload to the local outbox before sending.
2. Watch sender: attempt delivery when the phone node is reachable; retain the
   row on failure or timeout and retry with WorkManager/backoff.
3. Phone receiver: in one durable transaction, insert the identity if new and
   perform phone intake only for that new identity. If already present, do not
   book again.
4. Phone acknowledgement: return the identity and accepted/duplicate result.
5. Watch completion: delete or mark the outbox row delivered only after the
   matching acknowledgement is durable; otherwise retry safely.

## Sources

- [Processes and app lifecycle](https://developer.android.com/guide/components/activities/process-lifecycle)
- [Task scheduling / persistent work](https://developer.android.com/develop/background-work/background-tasks/persistent)
- [Getting started with WorkManager](https://developer.android.com/develop/background-work/background-tasks/persistent/getting-started)
- [Send messages between a handheld and wearable device](https://developer.android.com/training/wearables/data/messages)
- [Sync persistent data](https://developer.android.com/training/wearables/data/data-items)
- [Data Layer overview](https://developer.android.com/training/wearables/data/data-layer)
- [Save data in a local database using Room](https://developer.android.com/training/data-storage/room)
- [Define entities using Room](https://developer.android.com/training/data-storage/room/defining-data)
