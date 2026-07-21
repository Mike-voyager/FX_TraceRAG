---
id: SOP-006
title: Access Control and Credential Rotation
version: "1.1"
last_reviewed: "2026-07-01"
tags: ["security", "access", "credentials"]
---

## Purpose

Manage operator access to operational systems and rotate credentials safely when exposure is suspected.

## Access rules

1. Each operator uses a uniquely issued credential. Never share credentials between operators.
2. Grant the minimum access required for an operator's role.
3. Log every privileged action with the operator ID, system, and timestamp.

## Rotation steps

1. Rotate a credential on suspected exposure. Do not wait for confirmed compromise.
2. Issue a replacement credential to the operator and revoke the old one.
3. Log the incident: the operator ID, the reason for rotation, and the systems whose credentials were rotated.
4. Confirm the old credential is revoked by attempting an authentication with it and verifying denial.

## Audit and review

Access logs are reviewed on a recurring schedule by the operations lead. The review confirms that every privileged action maps to a logged operator ID and that no credential appears in use by more than one operator. Findings from the review are recorded as actions against this procedure.

## Limitations

- Never share credentials. Shared credentials break attribution and are not permitted under this procedure.
- This procedure does not cover service-to-service keys; those are governed by the platform key policy.
- Temporary elevated access must still use a uniquely issued credential and must be revoked at the end of the task.

## Escalation

If suspected exposure affects more than one operator or a privileged account, escalate to the security on-call with the incident log entry and the list of systems involved. Preserve access logs for the investigation.