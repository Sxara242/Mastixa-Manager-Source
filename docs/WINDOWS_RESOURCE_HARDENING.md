> Retained historical engineering record, sanitized for public review.
> Current status: [RELEASE_STATUS.md](RELEASE_STATUS.md). This record does not
> establish approval of the current source or a new binary release. Local-only
> receipt paths refer to privately retained evidence, absent from this snapshot.

# Windows v1 resource hardening — 2026-10-08

DESKTOP / Windows release hardening. Issue #1:
PRIVATE_ARCHIVE_REFERENCE_RETAINED_LOCALLY

This batch changes resource lifetime only. No schema, Android, performance,
native supplier, EPSG, legal gate, packaging, release metadata or build change.

## Root cause and inherited fixes

The native `sqlite3.Connection` context manager commits/rolls back; it does **not**
close the connection. The Phase16F backup-inspection test and older CSV,
backup/restore and stabilization tests used it without deterministic closing.
Those known fixture fixes are already present in HEAD (`88c22ff`), together with
`Database._ClosingConnection` and explicit transaction coverage (`4efac37`).
They are preserved, not reapplied. Current original-path warning validation
passes; historical CI #123 logs were not retrieved.

Remaining production gaps: source connections were acquired before entering
the `try/finally` that closed source and destination. A second-open failure
skipped that cleanup; a destination-close exception also skipped source close.
`Database.connect()` likewise leaked an acquired handle if initial PRAGMA setup
failed. These were proven by failing tests before the fixes.

## SQLite ownership inventory

The full site/owner inventory is in the local evidence directory's
`connection-inventory.json`. Production has ten direct SQLite acquisition sites:

| Owner/path | Class and lifetime | Deterministic close point |
| --- | --- | --- |
| `Database.connect()` | Short-lived local handle returned to caller; Database itself is a reusable path/service, not a live connection | Setup failure now closes before rethrow; successful callers use `_ClosingConnection.__exit__` or explicit close |
| `Database.transaction()`, query/write helpers | Operation-owned transaction; no shared persistent handle | Existing context commits/rolls back then closes, including failed deferred commit |
| `BackupManager._backup_to()` source/destination (2) | Local backup operation, read-only source | Nested `closing` scopes now own each handle immediately; explicit existing destination commit retained |
| `BackupManager._sqlite_copy()` source/destination (2) | Local restore/recovery operation | Same nested closing scopes; source still closes if destination open/close fails |
| `BackupManager._validate_database()` (1) | Local read-only validation | Existing nullable handle plus finally close |
| `ProfileManager.export_profile()` source/snapshot (2) | Local profile snapshot; temporary DB | Nested closing scopes before packaging and TemporaryDirectory cleanup |
| `ProfileManager._validate_sqlite()` (1) | Local read-only package validation | Existing finally close |
| `invoice_storage.referenced_names()` (1) | Local read-only attachment lookup | Existing `contextlib.closing`, including early return/errors |
| Page/store/service objects | Own/reference reusable Database, not `sqlite3.Connection` | All production Database.connect call sites are context-managed; no new close on shared services |
| Migration/projection/identity helpers | Borrow caller-owned connection and transaction | Caller closes; helper must not close it or change transaction ownership |
| Tests | In-memory fixtures, observers, local backup readers, setup DBs | Existing addCleanup, finally, closing plus transaction contexts; new fault tests register cleanup immediately |
| Background/tasks and shutdown | No worker-owned SQLite handle; shutdown backup uses the local backup owners above | No app-wide Database.close is needed; accepted/rejected shutdown and profile switching retain existing behavior |

Unclosed cursors are not separate long-lived resources here: queries materialize
their rows, and connection scopes release statements. No cursor/API rewrite.
No new connection churn or transaction boundary was introduced.

## One narrow secondary sweep

| Finding | Triage | Disposition |
| --- | --- | --- |
| Second SQLite open failure leaves source open in backup, restore, profile export | A: real acquired handle leak/file-lock risk | Fixed with independently entered closing scopes |
| Destination close exception bypasses source close | B: small deterministic cleanup fix | Fixed by the same scopes; fault coverage for both backup/copy owners |
| PRAGMA setup failure leaks a newly acquired Database connection | B: small deterministic cleanup fix | Close on BaseException before rethrow; returned/shared semantics preserved |
| Restore recovery exception silently swallowed | B: swallowed recovery failure | Log exception through existing private local logger; original failure still reaches caller, safety snapshot retained, no successful-restore claim |
| Updater worker finishes after owning page/window deletion and emits from deleted QObject | A: reproduced recurring runtime lifecycle error | Page-owned bridge discards late results after destruction; validity-race handling only suppresses deleted-object RuntimeError; live error/retry behavior retained |
| Older Activity correction fixture reuses a draft after rejected-create reset | B: stale focused persistence fixture | Same failure reproduced with pre-batch Database/backup/profile modules loaded in memory. Fixture now asserts notes/cost reset and re-enters identical input before correction save; inherited application reset behavior remains unchanged |
| Cooperative updater cancellation/join on shutdown | C: broader lifecycle enhancement | Proposed post-v1 only. Existing daemon I/O workers and timeouts retained; controlled workers terminate after I/O completion. No hung worker or persistence corruption observed |
| Registry `.json.tmp` retained if atomic replacement fails | C: bounded staging-file policy | Source inspection: prior registry stays intact, stream closes, next save overwrites the same sibling path. No ongoing handle leak or release blocker; explicit recovery/cleanup policy can be considered post-v1 |

The file sweep inspected context-managed CSV/report/profile ZIP/member/update
streams, NamedTemporaryFile reservations, profile TemporaryDirectory, sibling
export staging and `mkstemp` descriptor closure. Existing success/failure cleanup
and preservation of destination files remain covered. No additional must-fix
file-lifetime defect was found. Map QBuffer is an in-memory local QObject, not a
DB/file handle. Map shutdown stops timer and aborts pending replies; other timers
have QObject parents, with staged construction stopping on hide. No timer,
QThread or QObject cleanup warning was observed in the scoped validation.

Post-v1 proposal (not filed): **Cooperative cancellation of updater I/O when its
owning profile window closes.** Add cancellation checks between download chunks,
retain verified-file promotion and partial-file cleanup, and verify responsive
shutdown/profile switching during stalled I/O. This is an optional enhancement;
the reproduced deleted-signal defect is already fixed here.

## Regression and validation

`tests/test_sqlite_resource_lifetime.py`: second-open failures, destination-close
failures, setup failure, profile export failure, commit/rollback/CRUD/reopen and
Windows rename after close, failed recovery logging/snapshot retention, deferred
foreign-key commit failure and successful transaction reuse.

`tests/test_update_resource_lifetime.py`: actual Python worker threads held by
Events while the real Qt owning page is destroyed; success and error completion
for check/download, worker termination and no installer launch. Existing updater
retry/verification tests exercise live-page results.

The combined 250-test run initially had 249 PASS and one stale Activity fixture
failure, with zero lifecycle warnings. This was not a hardening regression:
`ActivitiesPage.save_activity()` already resets rejected NEW forms in the inherited
dirty baseline, as required by the retained owner acceptance checkpoint. The
fixture reused its cleared draft. The isolated pre-batch-module control reproduces
the failure. Only the fixture is updated; its entire focused module is rerun.
Passed unrelated tests are retained rather than repeating the complete run.

Local harness `../WindowsResourceHardeningEvidence/run_focused.py` records
ResourceWarning and RuntimeWarning, forces GC after **every test's teardown**,
and converts any observed warning to failure. This avoids the ineffective
error-only policy for destructor warnings that can otherwise be unraisable.
A positive control proves Python3.14.8 emits/detects an unclosed native SQLite
context; no production warning is masked. Synthetic DB/temp/data roots only.

Exact test totals/results, preservation hashes and final Git status are in the
leading CODEX_HANDOFF checkpoint and local `final-report.json`. No full 99-scenario
audit, legal qualification, RC build, commit, push, tag, issue closure/comment
posting, publication or upload is performed. The prepared issue comment remains
local for review. New source files must be included in the eventual candidate's
source overlay; existing immutable source archives are not altered here.
