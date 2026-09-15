# Phase 15E — Sensor View

Phase 15E exposes the stable Phase 15 sensor data to users on Windows and Android without adding a vendor connector or background network dependency.

## User-facing scope

Both clients now provide a read-only **Sensors / API** view backed by the profile-local sensor store. The view shows:

- sensor device name, provider, field link and active/disabled state,
- each channel's latest normalized value and canonical unit,
- latest UTC observation time and total observation count,
- observation history including quality and source reference,
- explicit **suspect** and **stale** indicators.

The Android view is available as a dedicated activity and static launcher shortcut. The Windows view is appended after the existing Phase 14/15 extension pages so older page indexes remain stable.

## Stale and suspect semantics

Presentation state is derived only; observations are never rewritten.

- no reading -> neither stale nor suspect,
- `quality=suspect` -> suspect indicator,
- latest reading strictly older than 24 hours -> stale indicator,
- exactly 24 hours old is still treated as fresh,
- suspect and stale are independent and may both be shown.

The 24-hour threshold is a Phase 15E presentation default, not a stored observation property. A later device/channel configuration layer may make this cadence configurable without changing historical sensor data.

`shared/fixtures/phase15_sensor_view.json` is consumed by Windows and Android tests so both clients classify the same timestamps identically.

## Offline and security behavior

The view reads only local normalized data. It does not contact the internet, poll a provider, store credentials, or expose API keys/tokens/passwords. Provider credentials remain outside the portable farm-domain tables, backups and reports established by the earlier Phase 15 slices.

## Verification

Windows tests cover latest values, stale/suspect presentation, history, empty state and startup page-index stability. Android instrumentation covers the real activity, stale/suspect rendering, history dialog and the signed-in shortcut path.

A real HTTP/MQTT/vendor adapter remains optional future work. Phase 16 can now focus on interoperability, reporting and release hardening using this completed sensor foundation.
