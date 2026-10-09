# Phase 3 frozen per-source contract

The manifest lists exactly 15 scoped icons: eight validated sources and seven
NEEDS OWNER REVIEW sources that must remain byte-identical to the hotfix original.
No Phase 3 owner visual approval is implied by VALIDATED_SOURCE.

original.png is an exact hotfix blob. independent_protected.png comes from
separately authored original-source cubic paths in source_annotations.json,
created before candidate cleanup. approved_removal.png is the separate reviewed
alpha edit. Conservative overlaps were retained rather than erasing protected
pixels or shrinking the reference. Similar paths in several files reflect
separately inspected originals sharing the same native ring extents.

Tests never run authoring scripts or derive protection from cleanup geometry.
Do not regenerate expected masks/digests to accept a regression. Reproduction
uses tools/build_phase3_icon_masks.py (dev-only; Pillow/NumPy). Authoring history
and visual evidence are in uncommitted diagnostics/phase3, not runtime inputs.
