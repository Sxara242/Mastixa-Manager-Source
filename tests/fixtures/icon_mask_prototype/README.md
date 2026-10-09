# Phase 2 source contract fixtures

The four PROTOTYPE_READY sources in manifest.json were approved for retention by
the owner after Phase 2. Originals are exact hotfix blobs from commit
5c9316b460a8c036c48a776f611fa916c358b06a. Production, calendar, and annual_report
fixtures assert that the three deferred assets remain unchanged and use fallback.

original.png is the immutable source. approved_removal.png is the allowed alpha
edit. independent_protected.png is a separately annotated original-source guard,
with native coordinates in independent_source_annotations.json. It is not derived
from the cleanup mask. protected.png is the initial candidate's complement,
retained solely to demonstrate that the independent guard rejected 246 boundary
pixels; it is NOT the protection oracle.

Tests never regenerate these files or their expected digests. Changes require
explicit source-boundary review. tools/build_icon_mask_prototype.py is a dev-only
reproducer, not runtime code. Comparison images and diagnostic authoring history
live under uncommitted diagnostics/phase2 and are not required by these tests.
