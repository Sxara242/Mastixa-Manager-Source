# Phase 15A — Sensor/API Shared Contract

Phase 15 starts with a transport-neutral data contract shared by Windows and Android. The goal is to accept future weather stations, soil probes, tank sensors and external APIs without tying farm data to one vendor or network protocol.

## Scope

15A adds three pure domain records:

- **Device** — local identity, optional field link, human name, provider, optional provider-side id, active/disabled state and notes.
- **Channel** — one metric emitted by one device.
- **Observation** — one immutable numeric reading for one channel at a canonical UTC timestamp.

There is no database migration, UI, HTTP client, MQTT client or vendor integration in 15A. Those are intentionally later slices built on this contract.

## Canonical metrics and units

Common farm metrics are normalized before they enter the shared model:

| Metric | Canonical unit |
| --- | --- |
| `air_temperature` | `celsius` |
| `soil_temperature` | `celsius` |
| `air_humidity` | `percent` |
| `soil_moisture` | `percent` |
| `rainfall` | `millimeter` |
| `battery` | `percent` |
| `water_level` | `millimeter` |
| `pressure` | `hectopascal` |
| `wind_speed` | `meter_per_second` |
| `soil_ec` | `microsiemens_per_cm` |
| `soil_ph` | `ph` |

Unknown metrics are allowed only under the `custom.` namespace, for example `custom.leaf_wetness`. This keeps vendor extensions possible without silently colliding with future canonical names.

## Observation rules

- `observed_at` is canonical UTC seconds: `YYYY-MM-DDTHH:MM:SSZ`.
- numeric values must be finite.
- quality is `good` or `suspect`; suspect data is preserved rather than silently discarded.
- observation ids are immutable identities. A connector retry must reuse the same id so persistence can be idempotent later.
- channel ids and observation ids must be unique within the projected device dataset.
- observations cannot reference unknown channels.
- channels cannot belong to another device.
- projection order is deterministic: channels by id; readings within a channel by `(observed_at, id)`.

## Security boundary

API keys, passwords, bearer tokens, MQTT credentials and other secrets are **not** part of this shared domain contract. 15A stores only provider/external identity needed to describe normalized farm data. Future connector configuration must keep credentials outside portable domain snapshots and avoid exposing them through reports or interoperability exports.

## Offline-first behavior

The normalized contract has no network dependency. Future adapters may fetch data from HTTP, webhook, MQTT, files or manual import, but once normalized the same records are usable offline by both clients.

## Shared fixture

`shared/fixtures/phase15_sensor_data.json` is consumed by both Python and Android instrumentation tests. It verifies identical normalization, canonical units, UTC handling, deterministic ordering, latest-value projection and quality propagation.

## Phase 15 progression

The implementation was deliberately split into small compatibility gates:

1. **15B persistence** — profile-isolated devices, channels and immutable observations.
2. **15C backup compatibility** — Android logical-backup schema integration and backward-compatible restore validation.
3. **15D ingestion boundary** — atomic, idempotent normalized import with no vendor lock-in and no secrets in farm-domain data.
4. **15E user-facing sensor view** — latest readings/history and stale/suspect indicators on Windows and Android.

Any real vendor/API connector should come only after these shared semantics are stable.
