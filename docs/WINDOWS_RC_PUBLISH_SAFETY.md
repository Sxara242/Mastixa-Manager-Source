> Retained historical engineering record, sanitized for public review.
> Current status: [RELEASE_STATUS.md](RELEASE_STATUS.md). This record does not
> establish approval of the current source or a new binary release. Local-only
> receipt paths refer to privately retained evidence, absent from this snapshot.

# Narrow B3 package-input safety review — 2026-10-08

Only current planned package inputs and the new B3 legal/source delta are examined.
Personal profiles/backups, QA-real copies, logs/screenshots/credentials and sibling
evidence directories remain outside the package allowlist; nothing is deleted.
Source-only collection CSV/license/AUTHORS must not enter the binary data TOC.
The selected IAU NOTICE contains public scientific credits/URLs, with no owner path.
Full source/privacy scans and actual artifact checks remain future distribution duties.
See WindowsB3FinalEvidence/final-report.json for the current result and limits.

---

> Current legal gate2026-10-08: B1-LEGAL/B4-LEGAL PASS; B1-AUDIT/B4-REPRO INCOMPLETE (non-blocking); B3-LEGAL BLOCKED.
> Prior private-CI/bit-identical/full-rebuild prerequisites are superseded by WINDOWS_RELEASE_GATE_POLICY.md.
> Required matching source/controlling scripts/replacement rights and future public source access remain mandatory.
> Exact review: WINDOWS_B3_LEGAL_CLOSURE.md. No RC build/preflight authorized by this note.

# Windows RC publish-safety and future commit scope — 2026-10-07

No commit, push, tag, release/feed publication or RC packaging was performed.
The approved checkout and protected original keep their owner data; synthetic
temporary profiles were used for all runtime checks. No keys, certificates,
PFX/passwords, DBs, real backups or private logs were copied into source inputs.

Tracked/untracked audit: 673 tracked files, 76 untracked files
at the scan checkpoint; no private-file/path or high-confidence credential
signature findings among those source files. There are 9 ignored
private paths/files; they remain local-only and were not copied or published.
This targeted signature scan does not prove absence of every possible secret.

Each untracked file is classified in the external `publish-safety.json`:
`app/`, `docs/`, `packaging/`, `updates/`, `licenses/`, LICENSE/CONTRIBUTING/notices
are repository source/test/docs; `tests/` are permanent regression tooling.
There is no new temporary evidence or owner DB in the nonignored source scope.
The full audit and preservation hashes remain outside the checkout.

Workspace-level evidence classification (not Git-untracked source):

| Item family | Classification / future action |
| --- | --- |
| `WindowsRcPreparationEvidence`, `Batch10ReleaseEvidence`, `Batch6Measurements`, `Batch7Evidence`, `FirstOpenEvidence`, `UiRevampEvidence`, `UsageAuditEvidence`, `StagedConstructionEvidence` and measurement text files | Temporary diagnostic/evidence, not source commit scope. Review before sharing because logs/state may include local paths or profile-derived metadata. |
| `RealProfileEvidence`, `Backups`, `Phase4_PreApply_Backup*`, `RuntimeQA*`, `MastixaManager.zip` | Sensitive/local-only or potentially private archives. Must not commit, package or publish. No automatic deletion. |
| `ReleaseArtifacts`, `ReleaseQA_*`, `SQLiteQA_*` | Historical builds, QA runtimes and evidence. Not source commit scope; review for QA/private contents. |
| Original checkout `icon_backup_20260915_010230/` | Untracked artwork backup; temporary diagnostic/local preservation. Do not commit wholesale; should be ignored in a later explicitly authorized change to that protected checkout. |
| `data/`, `backups/`, `dist/`, `build/`, `.venv/`, logs, DBs, profile exports, signing keys | Already ignored source-checkout local/private/output files. Do not force-add. |

Recommended future commit scope, only after separate commit authorization:

1. Review all retained Windows source/test changes as a coherent checkpoint;
   this batch does not discard or auto-commit the earlier UI/workflow work.
2. Include RC licensing/version/updater/build files, CONTRIBUTING policy,
   official LICENSE and `licenses/` manifest/texts, focused regression tests,
   provenance/third-party/source/feed docs and release metadata. Every necessary
   new `app/` module/localization file must accompany its calling code.
3. Keep temporary helpers, screenshots, hashes, copied QA profiles/runtimes and
   historical artifacts out. Review/sanitize the historical handoff and other
   evidence references for private/machine-specific details before public source
   publication; do not publish the entire workspace or raw evidence folders.
4. Re-run source/privacy/legal gates on the selected exact scope. Exact native
   notices/source closure remains blocked; do not mark this a public release.

No deletion or new broad gitignore change was needed in the approved checkout.
The per-workspace item list is `workspace-evidence-classification.json` outside
the checkout. Preservation checks verify hashes without logging data contents.
