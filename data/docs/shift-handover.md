---
id: SOP-005
title: Shift Handover Procedure
version: "1.0"
last_reviewed: "2026-07-01"
tags: ["handover", "operations", "shift"]
---

## Purpose

Transfer operational responsibility between shifts with a complete, written record so no open work is lost.

## Handover steps

1. Summarize the current system state: devices in maintenance, active procedures, and the overall operational status.
2. List unresolved alerts: each alert identifier, the device it concerns, and the action taken so far.
3. Record any open incidents with their classification, containment actions, and the owning engineer.
4. Note pending work that the incoming shift must complete, including the matching procedure reference.
5. Confirm receipt by the incoming operator and co-sign the handover record.

## Record requirements

The handover record is a single written document that the outgoing operator prepares before transfer. It must be machine-readable enough to be searched later, and human-readable enough that the incoming operator can act on it without verbal clarification. Store the record in the handover log with the shift timestamp and both operator IDs.

## Limitations

- A handover is not complete until the incoming operator acknowledges the unresolved alerts and system state.
- Handover records must not be edited after they are co-signed; corrections go in a new entry.
- Handover must not be performed verbally only; a written record is mandatory even when both operators are present.

## Escalation

If an unresolved alert cannot be safely handed off because its procedure is not defined, escalate to the on-call engineer before transferring responsibility and record the escalation in the handover note.