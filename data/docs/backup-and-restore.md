---
id: SOP-003
title: Backup and Restore Procedure
version: "1.3"
last_reviewed: "2026-07-01"
tags: ["backup", "restore", "maintenance"]
---

## Purpose

Produce restorable backups of device configuration and data, and perform restores only under controlled conditions.

## Backup steps

1. Confirm the device is in a stable, non-incident state before taking a backup.
2. Export the configuration and data snapshot to the backup store.
3. Record the checksum of the snapshot and the operator ID in the backup log.
4. Verify the backup by reading it back and comparing its checksum to the recorded value.

## Restore steps

1. Confirm that an approved maintenance window is scheduled and active. Restore requires an approved maintenance window; do not restore outside one.
2. Select the target snapshot and verify its checksum before restore. If the checksum does not match, stop and do not proceed.
3. Apply the restore inside the maintenance window and record the start and end times.
4. Validate the restored configuration by running the device self-check.

## Retention

Backups are retained according to the device retention class. Expired snapshots are purged from the backup store, and the purge is logged with the snapshot identifier and the operator ID. A purged snapshot cannot be restored and must not be referenced in a restore request.

## Limitations

- Restore must not run outside an approved maintenance window.
- A snapshot whose checksum cannot be verified must not be restored.
- Backups taken during an active incident are flagged and excluded from routine restore selection.

## Escalation

If the restore validation fails, retain the pre-restore snapshot, raise a severity 2 incident, and escalate to the maintenance lead with the snapshot identifier and the self-check results.