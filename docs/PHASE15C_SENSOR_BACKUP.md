# Phase 15C — Android Sensor Backup Gate

Phase 15C makes persisted sensor data safe to use before any real connector, polling, background ingestion, or sensor UI is enabled.

## Logical backup schema 18

Android logical backup schema 18 appends three tables after the schema-17 planting history:

1. `sensor_devices`
2. `sensor_channels`
3. `sensor_observations`

Schema 17 and every older supported schema remain readable. Restoring a schema-17 backup intentionally clears the newer sensor tables because those tables did not exist in that portable format yet. The core `FarmStore` SQLite version remains unchanged; the three sensor tables are still additive/lazy extension tables.

## Validation before restore

The staging database validates sensor rows before touching the live profile:

- device/channel/observation identities and Phase 15A domain semantics;
- optional device-to-field references;
- channel-to-device and observation-to-channel relationships;
- canonical metrics/units and `custom.` namespace rules;
- strict UTC observation timestamps and `good`/`suspect` quality;
- finite numeric values, including valid negative readings such as temperatures below zero.

A malformed sensor payload is rejected before the restore transaction starts, so the existing profile remains unchanged.

## Security boundary

Only transport-free farm data is backed up. API keys, bearer tokens, passwords, endpoint secrets and polling/session state are not columns in any sensor backup table.

## Compatibility

- Windows needs no new portable schema because its established full-SQLite backup already includes sensor tables.
- Android schema 18 restores full sensor history.
- Android schema 17 and older restore with empty sensor tables while preserving every table supported by that historical schema.

This closes the backup-safety gate required before Phase 15 can add guarded import/poll adapters.
