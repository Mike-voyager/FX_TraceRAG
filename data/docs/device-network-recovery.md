---
id: SOP-004
title: Device Network Recovery
version: "1.2"
last_reviewed: "2026-07-01"
tags: ["network", "incident", "device"]
---

## Purpose

Restore network connectivity for a field device that has lost communication with the control plane, without performing an unapproved full device restart.

## Trigger conditions

Apply this procedure when a device reports a network connectivity lost event, a heartbeat timeout, or an operator confirms the device is unreachable from the management console.

## Recovery steps

1. Record the error state: capture the device identifier, timestamp, error code, and the operator ID initiating recovery. Log these in the incident log before taking action.
2. Verify the physical link: confirm the network cable is seated, the link LED is active, and the port status on the switch is up. Do not proceed past this step until the physical layer is confirmed healthy.
3. Restart only the network service on the device. Do not reboot the device itself; a full device restart is not approved under this procedure and may disrupt running batches.
4. Validate connectivity: ping the gateway and the control plane, then run a test handshake. Confirm the device re-registers with the management console.
5. If the connectivity test fails, repeat steps 3 and 4 once. Escalate to the network engineering on-call after two failed attempts.

## Limitations

- This procedure restores network service only. It does not reconfigure IP addressing, routing, or firewall rules.
- A full device restart must not be performed as part of routine network recovery.

## Escalation

After two failed recovery attempts, escalate to network engineering with the recorded error state, the restart attempts made, and the last known good connectivity timestamp. Do not attempt further restarts while the escalation is open.