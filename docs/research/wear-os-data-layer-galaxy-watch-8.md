# Wear OS Data Layer Research for Issue #72

Research date: 2026-08-03

Scope: resolve the Wear OS communication and category synchronization decision for the phone and watch transaction flow. No app code is implemented here.

## Resolution

- Use `com.google.android.gms:play-services-wearable:20.0.1`. Google Play services release notes list this as the Wearable artifact released on 2026-04-28. Recheck the release notes when implementation starts rather than pinning an old version indefinitely.
- Use `MessageClient` for a user-triggered transaction submission when the phone is reachable. Messages are transient, so the phone should process the submission and return an application-level acknowledgement; the stable submission identity remains necessary for idempotency.
- Use `DataClient` for the current category snapshot. Data Items are synchronized and persist across temporary disconnection, making them a better fit than messages for category state.
- Discover the phone through an advertised capability and `CapabilityClient` with `FILTER_REACHABLE`. Do not assume a node ID, Bluetooth transport, or that the first connected node is the intended phone.
- Keep paths absolute and namespaced: `/finance/transaction-submissions` and `/finance/categories`. If the implementation needs one durable item per pending submission, use `/finance/transaction-submissions/<submission-id>` instead of one mutable shared item.
- Keep every message or Data Item below the documented 100 KB Data Layer limit. A transaction submission and a normal category list are comfortably within that limit; use an `Asset` only for genuinely larger content, not as a default encoding.

## APIs and dependency

The Wearable Data Layer is exposed through Google Play services clients, including `DataClient`, `MessageClient`, `NodeClient`, and `CapabilityClient`. The current official API reference is the `com.google.android.gms.wearable` package:

- [Wear OS data layer overview](https://developer.android.com/training/wearables/data)
- [Google Play services wearable package reference](https://developers.google.com/android/reference/com/google/android/gms/wearable/package-summary)
- [Google Play services release notes](https://developers.google.com/android/guides/releases)
- [MessageClient](https://developers.google.com/android/reference/com/google/android/gms/wearable/MessageClient)
- [DataClient](https://developers.google.com/android/reference/com/google/android/gms/wearable/DataClient)
- [NodeClient](https://developers.google.com/android/reference/com/google/android/gms/wearable/NodeClient)
- [CapabilityClient](https://developers.google.com/android/reference/com/google/android/gms/wearable/CapabilityClient)

The dependency to use at research time is:

```kotlin
implementation("com.google.android.gms:play-services-wearable:20.0.1")
```

The version is from the official release notes, not from a third-party version list. The implementation must verify the latest stable release before coding.

## Node discovery and routing

`NodeClient.getConnectedNodes()` returns currently connected nodes, but enumeration alone does not identify the correct application endpoint. `CapabilityClient` can find nodes that advertise a capability, and `FILTER_REACHABLE` limits the result to nodes currently reachable for communication.

The phone and watch should both declare the same application capability, for example `finance_phone` / `finance_watch` as appropriate to each side, and use the capability result to select the destination node ID. The sender then calls `MessageClient.sendMessage(nodeId, path, data)`; the receiver listens with `WearableListenerService` or an equivalent registered listener.

Relevant official references:

- [NodeClient.getConnectedNodes](https://developers.google.com/android/reference/com/google/android/gms/wearable/NodeClient#getConnectedNodes())
- [CapabilityClient.getCapability](https://developers.google.com/android/reference/com/google/android/gms/wearable/CapabilityClient#getCapability(java.lang.String,int))
- [CapabilityInfo](https://developers.google.com/android/reference/com/google/android/gms/wearable/CapabilityInfo)
- [WearableListenerService](https://developers.google.com/android/reference/com/google/android/gms/wearable/WearableListenerService)
- [Wear OS data layer capabilities guide](https://developer.android.com/training/wearables/data#capabilities)

Discovery is runtime state. The implementation must handle no reachable node, a disconnected node, multiple matching nodes, and a changed node ID. A successful `sendMessage` task is not a domain-level transaction acknowledgement; the phone should send an explicit acknowledgement or expose the processed submission state.

## Message paths and payloads

Data Layer paths are application-defined URI-like paths and should begin with `/`. Use a stable, versioned namespace so phone and watch reject or safely ignore unknown message types. Suggested paths:

| Purpose | Direction | Path | Transport |
| --- | --- | --- | --- |
| New transaction submission | watch to phone | `/finance/v1/transaction-submissions` | `MessageClient` |
| Submission acknowledgement | phone to watch | `/finance/v1/transaction-acknowledgements` | `MessageClient` |
| Current category snapshot | phone to watch, and optionally watch to phone | `/finance/v1/categories` | `DataClient` |
| Category refresh request | watch to phone | `/finance/v1/category-refresh` | `MessageClient` |

Use a compact serialized payload containing a schema/version, `submissionId`, transaction fields needed by phone intake, and an idempotency identity. Do not send the complete `finance_data.json` document for a single watch capture. For categories, send the category names plus a version or updated timestamp; the phone remains the authority for the shared finance data contract.

The official Data Layer documentation states that messages and Data Items have a 100 KB size limit. `Asset` is the documented mechanism for larger binary payloads. This project should stay below the limit and avoid chunking or assets unless real category or transaction requirements change.

- [Wear OS data layer overview and limits](https://developer.android.com/training/wearables/data)
- [MessageClient.sendMessage](https://developers.google.com/android/reference/com/google/android/gms/wearable/MessageClient#sendMessage(java.lang.String,java.lang.String,byte[]))
- [PutDataRequest](https://developers.google.com/android/reference/com/google/android/gms/wearable/PutDataRequest)
- [Asset](https://developers.google.com/android/reference/com/google/android/gms/wearable/Asset)

## Category synchronization choices

### Recommended: one authoritative snapshot Data Item

The phone publishes the current categories as one `DataItem` at `/finance/v1/categories`, with a schema version and category list. The watch observes Data Item changes and replaces its local display list. A Data Item is the right primitive for state that should become available after a temporary disconnect; the listener should also read the current item on startup rather than relying only on a change callback.

Category edits made on the watch should be sent as a request message to the phone. The phone validates and applies the edit to the shared finance data, then republishes the snapshot. This avoids two devices independently overwriting the category authority.

### Alternative: messages only

The watch can request categories and the phone can reply over `MessageClient`. This is simpler for a prototype but loses the request when the peer is unavailable and requires retry/state handling. It is suitable only if categories are always fetched while both apps are active and the watch has a local fallback list.

### Not recommended for this ticket: full shared-file synchronization

Sending the complete `finance_data.json` through the Data Layer would duplicate the existing Syncthing/file contract and create conflict resolution work. The Data Layer should carry watch captures and small category state, not replace the shared file synchronization design.

Official references:

- [Wear OS data items](https://developer.android.com/training/wearables/data/data-items)
- [DataClient](https://developers.google.com/android/reference/com/google/android/gms/wearable/DataClient)
- [DataEventBuffer](https://developers.google.com/android/reference/com/google/android/gms/wearable/DataEventBuffer)
- [MessageClient](https://developers.google.com/android/reference/com/google/android/gms/wearable/MessageClient)

## Galaxy Watch 8 implications

Samsung's official Galaxy Watch8 product page identifies the device and says Watch8 Series or later pairs with a smartphone running Android 11 or later for the cited setup flow. The Data Layer design should therefore require an Android phone and a Wear OS watch app, not a Samsung-only API. The official Wear OS and Google Play services documentation does not identify a separate Galaxy Watch 8 Data Layer transport or message-path API.

Implications for implementation:

- Test on the actual Galaxy Watch 8 and its paired phone; do not infer reachable-node behavior from an emulator.
- Verify that Google Play services and the Wearable module are available and current on both endpoints, and handle API unavailability or no reachable capability.
- Install phone and watch packages with the matching application identity/signing arrangement required by the Wear OS Data Layer setup; do not test with unrelated package IDs and expect discovery.
- Treat LTE/Wi-Fi/Bluetooth connectivity as runtime conditions. A Galaxy Watch 8 model or carrier can be offline even though the API is supported.
- Confirm the phone-side service receives messages when the phone app UI is not foregrounded, and verify reconnect/retry behavior after the watch is temporarily disconnected.

Sources:

- [Samsung Galaxy Watch8 official product page](https://www.samsung.com/us/watches/galaxy-watch8/)
- [Wear OS developer documentation](https://developer.android.com/training/wearables)
- [Google Play services setup](https://developers.google.com/android/guides/setup)
- [Wear OS data layer overview](https://developer.android.com/training/wearables/data)

## Decision for the next implementation ticket

Implement the smallest vertical slice with `play-services-wearable:20.0.1`: capability-based phone discovery, a versioned `MessageClient` transaction submission with explicit phone acknowledgement and idempotent `submissionId`, and a phone-authoritative `/finance/v1/categories` `DataItem`. Add a real Galaxy Watch 8 test matrix for connected, disconnected, app-not-open, and no-capability cases.
