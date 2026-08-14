# Finance Tracker Context

This context covers recording personal finance transactions across the phone app and its Galaxy Watch companion.

## Language

**Watch capture**:
A transaction input created on the watch for delivery to the phone.
_Avoid_: Watch transaction, watch-side record

**Phone intake**:
The phone's handling of a watch capture before it becomes part of the shared finance data.
_Avoid_: Sync import, watch sync

**Transaction submission**:
A watch capture plus its stable delivery identity, sent to the phone for processing.
_Avoid_: Event, message

**Booking date**:
The date stored for a transaction and used by month-based finance calculations.
_Avoid_: Transaction date when referring to the original spending date of a BNPL expense

**Behavior date**:
The original spending date retained for a BNPL expense whose booking date is in the following month.
_Avoid_: Spend date when the distinction from booking date matters
