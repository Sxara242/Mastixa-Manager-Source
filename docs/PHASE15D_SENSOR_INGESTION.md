# Phase 15D — Normalized Sensor Ingestion Boundary

Phase 15D adds the transport-neutral ingestion seam between future external providers and the Phase 15 sensor store. It does **not** add an HTTP client, MQTT client, polling scheduler, vendor SDK or credentials.

## Batch contract

One ingest batch contains:

- one normalized `Device`,
- the normalized `Channel` descriptors used by that batch,
- zero or more immutable `Observation` rows.

Every observation must reference a channel descriptor present in the same batch. The existing Phase 15A contract validates canonical units, UTC timestamps, finite numeric values, quality and the `custom.` namespace before persistence starts.

## Atomicity and retries

The entire batch is one transaction. A provider/device/channel/observation identity conflict rejects the batch and rolls back rows inserted earlier in that same attempt.

Retries are idempotent:

- a new observation id is inserted,
- an existing observation id with the same channel, timestamp, value, quality and source reference is counted as unchanged,
- an existing observation id with different immutable content is an identity conflict and the whole batch is rejected.

This lets a future connector safely retry after a timeout without duplicating measurements or silently rewriting history.

## Local metadata ownership

Connector replay does not overwrite local user metadata. For an existing device, local name, field link, status and notes remain authoritative. Provider identity must match; a missing local `external_id` may be enriched once, while conflicting non-empty external ids are rejected. Existing channel metric/unit/device identity must match, while its local display label is preserved.

A deleted device rejects ingestion. A locally disabled device may keep its history but rejects batches containing new observations. A newly discovered device may reference a field only if that field exists in the same profile.

## Security boundary

The ingestion API accepts normalized farm-domain records only. It has no parameters or persistence for API keys, passwords, bearer headers, MQTT credentials, endpoint secrets or polling state. Those remain outside portable farm data and outside logical backups/exports.

## Cross-client verification

`shared/fixtures/phase15_sensor_ingest.json` is consumed by both Windows and Android tests. The tests cover first import, exact replay, local metadata preservation, identity conflicts, disabled-device rejection, missing-field rejection and transaction rollback after an earlier row in the same batch was tentatively inserted.

## Next slice

Phase 15E can now expose a user-facing sensor view on Windows and Android using the stable contract/store/backup/ingestion layers: latest values, observation history and clear stale/suspect indicators. A real vendor connector remains a later optional adapter rather than part of the farm-domain model.
