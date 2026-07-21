---
id: SOP-001
title: Device Calibration Procedure
version: "1.0"
last_reviewed: "2026-07-01"
tags: ["calibration", "device", "maintenance"]
---

## Purpose

Calibrate a field device against a known reference so that measurements remain within accepted tolerance.

## Preconditions

Calibration requires a stable device state. Confirm there is no active incident recorded against the device before starting. Do not calibrate during an active incident.

## Calibration steps

1. Confirm the device is powered, idle, and not in an active incident. If an incident is open against the device, stop and resolve it first.
2. Mount the certified reference standard and let the device equilibrate for the stabilization period stated in the device manual.
3. Record the reference value read from the standard and the operator ID performing the calibration in the calibration log.
4. Run the calibration routine and capture the as-found and as-left readings.
5. If the as-found reading is outside tolerance, document the deviation and raise a maintenance ticket before returning the device to service.

## Record keeping

Every calibration produces a log entry containing the device identifier, the reference value, the operator ID, the as-found and as-left readings, and the timestamp. Calibration records are retained for the device retention period and are the source of truth for whether a device is in tolerance.

## Limitations

- Do not calibrate during an active incident. A device in an unresolved incident state must not be recalibrated.
- Calibration does not adjust firmware or change the device configuration.
- A device that fails calibration twice in a row must not be returned to service until the metrology team clears it.

## Escalation

If two consecutive calibration runs fail to bring the device within tolerance, escalate to the metrology team with the reference value, operator ID, and both reading sets. Remove the device from service until cleared.