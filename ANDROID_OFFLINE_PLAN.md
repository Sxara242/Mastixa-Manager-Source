# Mastixa Manager: Android, offline, backup, synchronization and OCR

Status: implementation specification, not implemented functionality.

## Agreed requirements

- Android must support everyday work entirely offline, including document OCR.
- Online backup and Windows–Android synchronization are separate, optional capabilities.
- OCR must populate the appropriate structured fields and route approved documents to the appropriate records.
- Existing Windows data and document attachments must be transferable.

## Local storage and application structure

The local database is the source used by every screen. Saving must not depend on a server, account, subscription check, or connectivity. Store attachments locally per profile. Package the required Greek and English OCR models for offline availability from the first launch.

Separate business rules, database access, OCR extraction and financial posting from PySide6 screens. Current desktop screens execute SQL directly; Android requires a mobile interface and an explicit decision about runtime/code reuse. Do not assume the desktop application can simply be packaged as an APK.

Keep schema migrations centralized and versioned. Import Windows data into a validated staging area before committing, preserving relationships and attachment references. Never overwrite the original database during migration.

## Optional online backup

Create a consistent SQLite snapshot together with attachments and a manifest of versions and checksums. Upload immutable, encrypted backup versions to an authenticated storage provider. Keep local backup/export available when online backup is disabled.

Define encryption key recovery before implementation. Show last successful backup, failures and retention settings. A restore must verify checksums and schema compatibility, create a pre-restore backup and restore database plus attachments together. Backup is not a merge or synchronization mechanism.

## Optional Windows–Android synchronization

Add stable global identifiers, record revisions, device identity, deletion markers and a persistent change queue. Existing local integer IDs need a migration/mapping strategy for foreign keys. Commit each business operation and its queued changes in one local transaction.

The server must authenticate devices, isolate accounts/profiles, deduplicate operations and retain change history sufficient for disconnected clients. Retries must be idempotent. Apply incoming changes transactionally and do not enqueue them again as new local changes. Synchronize attachments by content hash with resumable transfers.

Do not silently overwrite concurrent changes to financial or stock records. Preserve both versions and present a conflict for resolution. Group dependent changes such as invoice, financial posting and stock movements into one logical operation. Define handling for locked years, concurrent stock consumption, deletions, and devices returning after long disconnection.

Expose sync enabled/disabled, pending changes, last success and conflicts. A restore must rebase device sync state deliberately so old records do not resurrect deletions or replay financial entries. Both desktop and Android need the protocol; an Android-only queue is insufficient.

## Offline OCR and correct destinations

Pipeline: camera/file import → orientation and image cleanup → PDF text extraction or page rendering → local OCR → structured extraction → partner/product matching → review → transactional posting.

Keep the original document, page locations, recognized text, extraction version and per-field evidence/confidence. Recognition confidence is not proof of accounting correctness. Handle Greek/English text, Greek decimal formats and multipage documents. Run processing off the UI thread and allow retry/cancellation.

Extract document number, issue date, issuer and recipient identities/tax IDs, currency, net amounts, tax, total and line items with quantity/unit/unit price where present. Validate arithmetic using decimal monetary values. Distinguish issuer from recipient; use the active producer's identity to suggest purchase versus sale. If the identity or document type is uncertain, leave the destination unresolved. Credit notes need explicit reversal handling.

Routing rules:

- Purchases: expense record with date, supplier, document reference, category and total.
- Sales: sale/income integration following the existing application's business rules, without counting revenue twice.
- Stock items: create receipt/consumption movements only after matching the product, unit and quantity; a service or fuel receipt must not become arbitrary inventory.
- Equipment: suggest an equipment link when appropriate; require a resolved match before creating an asset.
- Field allocation: use an explicit selection or established mapping; never invent a field from an ambiguous document.

Populate proposed values automatically. Present unresolved fields and destination before posting. Store the reviewed decision. Posting must be atomic and idempotent, link back to the source document, enforce year locks, and prevent duplicate financial/stock records on retry. Detect exact duplicate files by hash and probable duplicate documents by issuer, document number and date; allow review of false positives.

Optional online OCR may later supplement the local engine only when explicitly enabled. Full offline OCR remains available independently.

## Current gaps confirmed in source

- `app/database.py`: local SQLite with local integer record IDs; no complete cross-device synchronization infrastructure.
- `app/production.py`: UI, validation and persistence are coupled.
- `app/upload_center.py`: local payload preparation only, explicitly no network transmission.
- `app/invoice_documents.py`: external desktop Tesseract; date/supplier/amount hints, manually chosen financial destination; no structured line-item OCR pipeline. PDF files are passed directly to the OCR command without a page-rendering pipeline in this method.
- `app/runtime_paths.py`: desktop-oriented storage paths require platform-specific replacement.

## Delivery sequence and acceptance gates

1. Separate and test business services; centralize schema and define import, global identity and document contracts.
2. Implement the Android offline interface, profile storage, local backup/restore and Windows import.
3. Integrate bundled offline OCR and reviewed, atomic posting, including line-item mappings.
4. Implement encrypted online backup and tested full restore.
5. Implement the shared sync service and both clients, conflict review and attachment transfer.

Before release verify: first launch and OCR in airplane mode; process termination during save/OCR/restore; Greek invoices and unclear images; issuer/recipient distinction; VAT versus grand total; multipage PDF; duplicate import and repeated posting; locked-year rejection; consistent expense/sale/stock effects; offline edits on both devices; conflicting update/delete; interrupted upload; repeated sync without duplicate effects; backup restore with all attachments and deliberate sync-state recovery.

Implementation choices still to settle: Android runtime/UI stack, hosting/storage provider, account and key recovery, and representative invoice samples for measured OCR accuracy. No claim of universal OCR accuracy or completed Android functionality is made by this specification.
