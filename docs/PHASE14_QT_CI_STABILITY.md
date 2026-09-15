# Phase 14 Windows Qt CI stability

The repeated Windows CI abort happened while full `MainWindow` startup integration tests were tearing down native PySide6/Qt objects in the shared unittest process. The workflow already forces `QT_QPA_PLATFORM=offscreen`, and the Phase 14 test already drained posted/deferred-delete events; those mitigations did not make the native teardown deterministic.

The startup-extension tests now validate only their actual contract with a lightweight base-window stub: existing indices stay fixed, Crop Program is appended at index 32, Individual Plants is appended at index 33, and both entries are added to the recording group. Real `CropProgramsPage` and `PlantTrackingPage` behavior remains covered by their dedicated Qt UI tests.

This avoids constructing a second full application window solely to test list-append wiring, removes the native Qt teardown path that intermittently killed the Windows runner, and reduces rather than increases CI resource use. It does not add a runner, dependency, sleep, retry loop, `app.exec()`, or production-code workaround.
