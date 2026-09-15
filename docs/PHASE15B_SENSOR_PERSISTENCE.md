# Phase 15B — Sensor Persistence Foundation

Phase 15B persists the transport-free Phase 15A sensor contract locally on Windows and Android. It intentionally does **not** add HTTP/MQTT polling, credentials, background networking, or UI.

## Tables

Both clients use the same three logical tables:

- `sensor_devices`: device metadata, optional field link, active/disabled state, soft delete.
- `sensor_channels`: stable metric/unit identity for each device.
- `sensor_observations`: append-only measurements ordered by UTC timestamp and id.

The SQLite observation column is named `numeric_value` (mapped to the contract field `value`) so logical-backup validation can distinguish numeric sensor data from text columns named `value` elsewhere in the schema.

## Invariants

- A non-empty `field_id` must reference a field in the same profile database when the device is created or restored.
- Device deletion is soft: channels and observations remain intact and the device can be restored.
- New observations are rejected while a device is disabled or deleted.
- Observation ids are immutable and duplicates are rejected.
- Once a channel has observations, `device_id`, `metric`, and `unit` cannot change. Its display `label` may still be edited. This prevents historical values from silently changing meaning.
- All domain validation still flows through the shared Phase 15A contract, including canonical units, UTC timestamps, finite numbers and the `custom.` metric namespace.
- API keys, passwords, bearer tokens, endpoint secrets and polling state are not stored in these tables.

## Migration strategy

The stores create these tables additively and lazily. Android keeps the core `FarmStore` database version unchanged, matching the established crop-program and plant-tracking extension pattern and reducing migration blast radius.

## Backup boundary

Windows file-level SQLite backups naturally include these tables once they exist. Phase 15C adds the Android logical-backup schema integration as schema 18, including backward restore compatibility for schema 17 and older backups. No ingestion/UI path is enabled until that backup gate is green.

## Tests

Windows and Android tests cover persistence, deterministic projection, immutable observations, frozen observed-channel identity, device soft-delete/restore, disabled-device ingestion blocking, custom metrics, field validation and profile isolation. Phase 15C adds logical-backup round-trip, backward compatibility, signed sensor values and relationship/atomic-rejection coverage.
