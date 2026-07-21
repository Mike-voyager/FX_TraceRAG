---
id: SOP-002
title: Incident Response and Escalation
version: "1.1"
last_reviewed: "2026-07-01"
tags: ["incident", "escalation", "operations"]
---

## Purpose

Provide a consistent first response to operational incidents and a clear escalation path when local resolution is not possible.

## Classification

Every incident is classified on detection: severity 1 for loss of a production capability, severity 2 for degraded capability, severity 3 for a minor or cosmetic fault. Classification drives the response and the escalation target.

## Response steps

1. Acknowledge the incident in the incident log within the response window for its severity.
2. Record the system state at detection: affected device identifiers, error codes, and the operator ID taking the call.
3. Contain the impact where possible without making irreversible changes.
4. Apply the matching operational procedure, such as device network recovery or backup and restore, when one exists.
5. If no matching procedure exists, or local resolution fails, escalate.

## Communication

For severity 1 incidents, notify the operations lead and the affected subsystem owner immediately on detection. Keep the incident log updated with each action taken so that the on-call engineer inherits a complete timeline. Severity 2 and 3 incidents are logged for the next scheduled review rather than notified individually.

## Limitations

- First responders must not perform irreversible corrective actions such as firmware replacement or data deletion.
- This procedure does not authorize a full device restart; restart scope is governed by the matching procedure.
- An incident is not closed until the system state has been confirmed stable and recorded by the owning operator.

## Escalation

Escalate to the on-call engineer for the affected subsystem with the incident classification, recorded system state, and any containment actions taken. Severity 1 incidents must be escalated immediately and concurrently with containment.