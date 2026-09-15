# Phase 9F cross-client identity fixture

This checkpoint verifies the portable activity identity contract with the same fixture on Windows and Android.

The two clients intentionally use different local IDs for the same synchronized production event. They share only the verified synchronization identity:

- `dataset_id`
- `source_type`
- `source_uuid`
- `field_uuid`

The canonical fixture lives at `tests/fixtures/phase9f_activity_identity.json`. An identical Android instrumentation asset lives at `android/app/src/androidTest/assets/phase9f_activity_identity.json`; the Windows test asserts the two files are byte-identical before using the fixture.

Windows registers the fixture through `app.activity_identity` and verifies `project_field_activities()` returns exactly the expected `sync_ref`. Android registers the same shared UUIDs against different local field/source IDs and verifies `ActivityProjection.project()` returns the same portable identity.

Both tests also verify that changing the local profile scope removes the portable identity claim. This proves local IDs and local scope remain client-local while the verified portable identity remains stable across clients.

This is the Phase 9F5 cross-client fixture checkpoint. It does not infer identity from names, KAEK, dates, `windows_id`, hashes, or import order.
