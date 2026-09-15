# Phase 16J — accessibility / responsiveness / localization

Started 2026-09-13 after Phase16I docs checkpoint
`f08b1232074aa152dc03aa4653bb554029ba13eb` was committed, pushed and remote-verified.
Phase16I remains PARTIAL; owner deliberately deferred the project license.
The permanent public-release blocker list in MASTER_PROGRESS.md remains binding.
No release/update/16I/CSV/GIS/offline gate was rerun. Phase16K not started.

## 16J-A1 — Windows translation boundaries: COMPLETE scoped block

Inspection: LanguageController, profile chooser/settings, declaration status,
read-only invoice filename, integer-ID field/product selectors and existing
language tests. Two reproduced defects:

- **Medium:** generic translation changed displayed database/file paths and
  record names that matched dictionary words (e.g. `Παραγωγή` -> `Production`).
  No stored-record mutation was proved; displayed user data/copyable paths were
  wrong. Read-only QLineEdit now translates values only with explicit existing
  `mastixaI18nStaticText` opt-in (declaration status opts in). Integer-ID combo
  entries remain user data unless explicitly static; UUID profile selectors opt
  out of item translation. Placeholder/static enum translation stays active.
- **Accessibility:** accessibleDescription was not included in the live language
  update although accessibleName/toolTip/whatsThis were. Added the same retained
  source/update mechanism for that property.

New `tests.test_phase16j_localization` initially reproduced 3 failing methods
(7 failure entries across language-cycle subtests) out of 4. After minimal fixes:
**4/4 PASS**, plus **4/4 existing directly affected localization tests PASS**;
combined **8/8**, 35.278s. Existing methods: live profile language switching,
English key pages, profile chooser native language names, canonical combo source.
Both el -> en -> el and en -> el -> en cycles are covered on existing widgets.
Tests use temporary profiles/offscreen Qt, not real user data.

## Systematic inspection / pending acceptance

Update: the help catalog gaps below are now resolved by 16J-A2; original scan
counts are retained as before-fix evidence, not current missing counts.

- Windows AST scan across `app/**/*.py` found **84 exact-unmapped Greek UI literal
  occurrences** at selected constructors/setters/dialog calls. This is a candidate
  list, not 84 proven failures: fragment translation, dynamic values and obsolete
  code require classification. Includes mixed bilingual GIS/export dialogs.
- `HELP_TEXTS` has **91 entries**, **17 without an exact English translation**.
  These need full-phrase review rather than assuming fragment substitution is
  adequate. The existing info indicator is a QLabel `ⓘ` + tooltip, not necessarily
  a keyboard/click-operable help button; interaction/accessibility remains pending.
- Android literal `t("...")` calls had **0 missing exact Greek-source keys** in
  `assets/en.json`. This is NOT localization PASS: `words`/`w` helpers, hard-coded
  strings, dynamic messages, errors, notifications and direct View setters are
  outside that narrow scan. AppLanguage/MainActivity/ParcelMapActivity inspected;
  map track state currently displays a raw state code and needs classification.
- Ignored `.tools/phase16j-*-ui-candidates.json` contains inspection locations.
  These are local audit scratch files, not application inputs or shipped assets.

| Acceptance area | Status / evidence |
|---|---|
| Greek localization | PARTIAL: existing UI plus boundary cycles; English/bilingual literals remain to audit |
| English localization | PARTIAL: selected existing pages PASS; new/dynamic/rare paths not fully covered |
| Info/help texts | PASS scoped Windows catalog: 91 general + 5 contextual entries; PARTIAL globally (Android/other dialogs and help interaction pending) |
| Language switching | PASS for scoped Windows boundary/key-page checks; PARTIAL globally, Android unverified |
| Windows responsiveness/scaling | UNVERIFIED this phase; no native multi-DPI/window-size visual pass yet |
| Windows accessibility | PARTIAL: description switching fixed; focus order, keyboard info access and contrast pending |
| Android responsiveness/accessibility | UNVERIFIED this phase; no emulator/runtime checks performed |

## Historical resume checkpoint (2539a1a)

Owner stop instruction: approximately 19% usage remains. Checkpoint safety only;
do not start help translation, responsiveness/scaling or another subsection now.

CURRENT HEAD (verified code checkpoint, before this documentation follow-up):
`bec01b57f6cad19b600298fada8148e018f797ae`.

COMMIT: `bec01b57f6cad19b600298fada8148e018f797ae` —
`Phase 16J: preserve user values during UI language changes`.
The following documentation-only commit records this SHA and uses `[skip ci]`;
its own final HEAD must be obtained with `git rev-parse HEAD` (not a self-referential
hash embedded in this file). Both are to be pushed normally to `refactor/pages`.

TESTS PASS: **8/8**, 35.278s: four new LocalizationBoundaryTests plus the four
existing directly affected methods listed above. No tests repeated after PASS.

COMPLETED: only the two reproduced Windows issues: displayed user record names /
read-only paths protected from translation, and accessibleDescription participates
in live language switching. No database/schema/write behavior changed.

WORKING TREE at checkpoint preparation: clean after `bec01b5`; only this resume
documentation is being updated. Verify Git on resume; discard no user changes.

EXACT NEXT ACTION: complete the 17 Windows HELP_TEXTS English full-phrase gaps,
add focused catalog + open-tooltip/help language-cycle coverage, then classify
the remaining hard-coded Windows/Android UI strings. Do not rerun the 8 passing
tests unless subsequent changes affect their boundaries.

REMAINING: full 16J-A translation quality/completeness and Android language
switching; 16J-B scaling/layout; 16J-C focus/help/touch/accessibility. Fresh normal
CI is justified by application changes but **explicitly deferred by the owner**
for usage safety; the final documentation commit skips CI for this push. CI #144
remains the prior baseline, not validation of these two new fixes. No release,
update, full desktop or Android gate was run in this subsection.
**Phase16J PARTIAL; not ready to close or start Phase16K.**

## 16J-A2 — complete Windows help translations: COMPLETE scoped block

Resumed from clean `2539a1ac474f275a4aac8e1e4d48de0cadd5e702` after reading
Git history and this ledger. No earlier phase restarted.

- Added 18 complete English phrases to `app/locales/en_phase16j.json`: the 17
  general gaps plus DataExportPage's contextual status explanation. Reviewed the
  resulting 96 English explanations for meaning/readability; existing technical
  names, units, KAEK and protocol identifiers remain unchanged.
- **Reproduced bug:** rich-text help escapes `&` as `&amp;`, but dictionary
  replacement compared unescaped source phrases, causing partially Greek
  English tooltips despite existing full translations. Rich-text replacement now
  matches escaped source and escapes the translated value as well; no data writes.
- New `tests.test_phase16j_help`: **2/2 PASS**. All 96 catalog entries require a
  nonempty complete English translation. All 96 existing tooltip widgets cycle
  el -> en -> el -> en -> el -> en with exact escaped content and no stale strings.
  Before fixes both methods failed; after only catalog additions, the rich-text
  method still failed, proving an implementation fix was necessary.
- Because `LanguageController._translate_fragments` changed, the prior 8 directly
  affected localization checks were legitimately rerun: **10/10 total PASS**,
  34.450s. No unrelated tests, Android runtime, full CI or release/update gate.
- This is not a claim that every help dialog or Android message is covered.
  Keyboard/click access to QLabel info markers, other Windows literals, dynamic
  errors and Android localization remain pending.

## Historical A2 resume checkpoint

CURRENT HEAD at start of this block: `2539a1ac474f275a4aac8e1e4d48de0cadd5e702`.
LAST COMMIT for the completed block: the logical commit containing this A2 section;
obtain the final commit SHA from Git (a document cannot embed its own Git hash).
WORKING TREE: commit only the translator, new English catalog, new help tests and
these two ledgers; preserve any subsequent unrelated changes.
COMPLETED: A1 data/accessibility-description boundaries; A2 Windows 96-entry help
catalog and rich-text language switching.
TESTS PASS: latest focused run 10/10, above. Do not rerun without affected changes.
REMAINING: Windows mixed-language/new/dynamic UI; Android full localization/help
and switching; responsiveness/scaling; final keyboard/touch/accessibility checks.
NEXT EXACT ACTION: localize the mixed-language CoordinateExportDialog using the
existing Greek-source catalog mechanism, preserve output/schema/protocol values
and field names, and add UI-only language-cycle tests. Then continue the remaining
Windows/Android candidate audit. No CSV/GIS behavior matrix is needed for text-only
changes unless an actual dependency is affected.
Fresh normal CI is deferred until Phase16J completes, per latest owner instruction.
Intermediate recovery pushes use `[skip ci]`; CI #144 is only the earlier baseline.
**Phase16J PARTIAL. Phase16K not started.**

## 16J-A3 — coordinate export dialog: COMPLETE scoped block

- Reproduced bilingual titles/messages on the committed dialog using the new
  tests against an in-memory copy of HEAD's source (no checkout/revert): 2 methods,
  7 failed assertions, no infrastructure errors.
- Greek source captions + the existing English catalog now cover buttons, mode
  choices, preview headers, empty state, counts and actionable failure summaries.
  User parcel names/KAEK and the exported file-format headers remain unchanged.
- Existing open dialog tested in both language cycles, dynamic selection/mode and
  controlled preview failure. Synthetic DB dump unchanged after each test.
- `tests.test_phase16j_coordinate_ui`: **2/2 PASS**, 0.546s.
- Directly affected existing
  `CoordinateExportTests.test_cancel_and_failed_writes_preserve_destination_and_database`:
  **1/1 PASS**, 0.199s. Atomic destination protection remains intact.
- No full format/GIS matrix or prior unrelated PASS gates repeated. Native OS file
  picker localization and real multi-DPI visuals remain unverified.

## Historical A3 resume checkpoint

CURRENT HEAD before A3: `4f44505` (A2 help translations/rich-text fix).
LAST COMMIT: logical A3 commit containing this section; resolve full SHA with Git.
WORKING TREE: A3 touches only export dialog, English catalog, focused test and
these two ledgers. Completed commits are recoverable; no user data changed.
COMPLETED: A1 user-data/accessibility-description boundaries; A2 96 help entries;
A3 coordinate export dialog language cycles and failure UI.
TESTS PASS: A2 10/10; A3 2/2 + directly affected existing 1/1. No full CI run.
REMAINING: other Windows dynamic/mixed-language UI, Android localization/help and
switching, Windows/Android scaling and practical keyboard/touch access.
NEXT EXACT ACTION: inspect/fix ParcelMapDialog mixed-language UI and combined
user-name/status labels, using focused UI tests and preserving GIS/provider data.
Fresh normal Desktop + Android CI remains deferred until Phase16J is complete.
Intermediate recovery commits use `[skip ci]`. Phase16J PARTIAL; 16K not started.

## 16J-A4 — main parcel-map dialog: COMPLETE scoped block

- Reproduced that language switching translated a parcel name (`Παραγωγή /
  Αποθήκη`) and geometry source filename inside the combined map summary.
  Two new methods against the unchanged HEAD source fail 12 subtests.
- Main map captions/provider choices now use Greek UI sources and the English
  catalog. Provider identities/configuration and GIS source data are unchanged.
- The combined summary opts out of automatic text replacement and translates its
  template before interpolating domain values; a language-change signal refreshes
  only that label, without resetting the map or fetching/replacing geometry.
- `tests.test_phase16j_map_ui`: **2/2 PASS**, 0.472s. Saved and empty maps cycle
  both directions, retain names/KAEK/source filenames, localize main controls and
  preserve the complete synthetic database dump.
- Scope is the main dialog only. Nested coordinate/point/track/provider-warning
  dialogs still contain bilingual strings and need a subsequent focused block.

## Historical A4 resume checkpoint

CURRENT HEAD before A4: `7121937` (coordinate export UI checkpoint).
LAST COMMIT: A4 logical commit containing this section; resolve SHA from Git.
WORKING TREE: main map dialog/catalog/new focused test plus these two ledgers.
COMPLETED: A1 boundary fixes; A2 help catalog; A3 coordinate export; A4 main map.
TESTS PASS: A2 10/10; A3 2/2 + 1/1; A4 2/2. No unrelated passing gates rerun.
REMAINING: nested GIS dialogs and other Windows rare/dynamic UI; Android
localization/help/switching; responsiveness/scaling; keyboard/touch accessibility.
NEXT EXACT ACTION: complete nested GIS dialogs with localized UI-only captions and
messages, preserving point/track protocol types and user titles/notes.
Fresh normal Desktop/Android CI deferred to full Phase16J closure. Intermediate
checkpoints skip CI. Phase16J PARTIAL; 16K not started.

## 16J-A5 — nested GIS dialog language paths: COMPLETE scoped block

- Three new methods reproduce failures against A4's committed implementation.
- Removed bilingual UI captions from CRS/manual-entry, point list/editor, track
  selection/empty state, provider warnings and unavailable offline-pack messages.
  UI point-type labels map to the unchanged POINT_TYPES values by existing index;
  titles/notes, coordinate input, KAEK and source filenames remain domain data.
- Point list type labels refresh when language changes; the modal disconnects its
  refresh callback after closing. Main map geometry/provider behavior is unchanged.
- Failed import/manual save/point save/delete show localized actionable summaries
  instead of raw backend exception text. Provider capability/status is unchanged;
  no fresh Cadastre lookup or network/offline gate was run or claimed.
- **3/3 new tests PASS**, 0.925s, after correcting a native Qt method mock and a
  missing Cadastre title translation. Existing 2 map tests passed in the preceding
  same-block run, so current module evidence is **5/5 PASS** across those runs.
- Coverage: both language cycles in point list/editor and manual entry; UI-only
  provider/offline/empty/error message rendering (6 cases); malformed geometry
  import; unchanged synthetic DB; unchanged user title/notes and type identity.
- Dialog event loops/file pickers are intercepted in these focused offscreen
  checks. Native picker language, physical keyboard/screen-reader use and visual
  scaling remain manual/unverified. No full GIS/CSV/Android suite repeated.

## Historical A5 resume checkpoint

CURRENT HEAD before A5: `2ef08ad` (main map summary checkpoint).
LAST COMMIT: A5 logical commit containing this section; get full SHA from Git.
WORKING TREE: only nested map UI/catalog/map tests plus these two ledgers.
COMPLETED: A1 data/accessibility boundaries; A2 96 Windows help entries; A3 export
UI; A4 main map; A5 nested GIS UI language paths.
TESTS PASS: A2 10/10; A3 2/2 + 1/1; A4/A5 map module 5/5 (latest 3/3).
REMAINING: other Windows rare/dynamic literals and Android localization/help;
language-cycle coverage beyond scoped paths; scaling and final accessibility.
NEXT EXACT ACTION: classify the saved Windows/Android hard-coded string inventory
against actual translation lookup; finish remaining localization before starting
scaling/accessibility checks. Preserve the earlier PASS gates.
Full Phase16J remains PARTIAL. No fresh full CI until closure; intermediate
checkpoints use `[skip ci]`. Phase16K not started.

## 16J-A6 — remaining literal Windows UI catalog: COMPLETE scoped block

- Rescanned actual Python AST call arguments for titles, labels, buttons,
  placeholders, form captions, help/accessibility text, static status/messages
  and file/input dialogs. Excluded retired `pagesbackup.py`, dynamic expressions,
  stored values, SQL, protocol constants and file-format fields.
- Actual translation lookup reproduced **35 unique Greek UI sources** still
  containing Greek in English mode. Added full English translations: edit titles
  across activities/fields/equipment/inventory/labor/partners/plantings/production/
  products/sales; backup/quality/status messages; invoice preview; plant placeholders;
  sensor explanations/headings; upload state/errors; nested map titles.
- `tests.test_phase16j_ui_catalog`: **2/2 PASS**, 0.412s. AST-based test examines
  more than 500 real static UI occurrences and requires complete English output.
  Separate live title/placeholder/help/status cycles retain editable user text.
- This is **scoped static-source coverage**, not full runtime localization PASS.
  English-only literals on Greek screens, composed/f-string messages, enum/table
  display values and native dialogs still need classification. A missing-string
  scan cannot prove translation quality or completeness of every runtime path.
- No production Python/Android code changes in A6, only English catalog and tests.
  No full suite/CI or unrelated earlier gate repeated.

## Historical resume checkpoint — owner-requested usage safety stop

Owner update: approximately 27% usage remained; finish only the opened Windows
localization block, then leave a pushed, recoverable checkpoint. No new Android,
responsiveness or accessibility audit started after that instruction.

CURRENT HEAD (verified pushed application/test checkpoint): `89069ff466b7f910e07ae8b7b4d583cbb89ca29f`.
COMMIT: `89069ff` — Phase 16J: fill remaining static Windows UI translation gaps.
PUSH: PASS to `https://github.com/Sxara242/Mastixa-Manager.git`, branch
`refactor/pages`; Git push acknowledged the update to this exact code SHA.
The sandboxed remote read lacked Windows credentials; repeating it in the same
permitted context as push confirmed documentation HEAD
`d3923f374adbade78fa0592d503922b3aad065cb`, whose parent is the code SHA above.
WORKING TREE: clean after the application checkpoint; this final documentation
follow-up records the result and is committed/pushed separately with `[skip ci]`.
The documentation-only final HEAD is obtained with `git rev-parse HEAD`;
the last tested application checkpoint in its ancestry is the SHA above.
COMPLETED COMMITS (all pushed): `4f44505` help/rich text; `7121937` export dialog;
`2ef08ad` main map; `ca87a15` nested GIS; `89069ff` static UI catalog.
Pushed paths are only source/catalog, four focused test files and two QA ledgers.
No databases, APKs, generated artifacts, caches, local config or secrets included.
COMPLETED: A1 boundaries; A2 help catalog/rich text; A3 coordinate export; A4 map
summary/data protection; A5 nested GIS dialogs; A6 static Windows UI catalog gaps.
TESTS PASS: 20 distinct focused methods during this continuation: A2 10/10
(includes 8 directly affected existing boundary checks), A3 2/2 + 1/1 existing
export cancellation/failure, A4/A5 5/5 map methods, A6 2/2. Latest block 2/2 PASS.
REMAINING: Greek-mode English-only literals, dynamic/rare Windows UI and enum
labels; Android localization/help/language switching; Windows/Android scaling and
practical keyboard/touch/screen-reader verification; final normal CI after closure.
NEXT EXACT ACTION: verify pushed HEAD/status, then audit English-only and dynamic
Windows UI sources against actual language output (start with plant form axis
captions and native/default dialog buttons). Do not repeat the completed help,
map or catalog tests unless a new change directly affects them. Then Android.
Full Phase16J remains PARTIAL; no fresh full CI, release/update gate or Phase16K.

## Android localization / system-surfaces audit and notification test checkpoint

CURRENT HEAD before this documentation-only commit:
`b12b8b505740a5888e4384f4b6b3495c4810534d`.
Audited external change chain: `2fb9df3bf5f689adf6e075d7ebec88c2951b56bd`
through `cec644c59e0a0b75e4eea2122fc8661a1d5aaa7f` (13 commits).
Local branch was updated by verified fast-forward only; no reset/rebase/merge
commit. The earlier resume note was stale and is retained as history above.

COMPLETED inspection:
- MainActivity error boundaries use localized generic backend failures while
  UiValidationException preserves deliberately localized UI validation text.
  The stabilized instrumentation test separates main-thread actions from idle
  waits, retaining specific-validation, raw-error-exclusion and profile-data checks.
- Crop-task channel labels/descriptions follow the profile language; stable ID
  `crop_task_reminders_v1`, notification ID/tag formula and preference keys remain.
  No channel deletion or replacement of user settings was introduced.
- Launcher shortcuts use English default resources and Greek `values-el` resources;
  shortcut IDs/actions remain unchanged. These system resources follow Android
  resource locale, independently of profile-selected in-app wording.
- No store/schema/migration, filename, domain ID or persisted business/protocol
  value changes were found in this chain. Plant status/health labels are display
  mappings; record values remain canonical. Shared Windows translator unchanged.

CI #157 (`34755926415`) on `cec644c`: **Desktop PASS; Android PASS**.
https://github.com/Sxara242/Mastixa-Manager/actions/runs/34755926415
No successful CI or Windows help/map/catalog gate was manually rerun.

Runtime #34 (`34755926412`) failed due to a **test-only notification publication
race**, not an application regression. Targeted reproduction failed at
`CropTaskNotificationTest.java:79`, `assertTrue(found)` (expected true, actual false).
The assertion failed at 12:30:49.681; the system enqueued the correct notification
at 12:30:50.046. Expected/actual ID `940231632`, tag `crop-task-phase13c-notify`
and channel `crop_task_reminders_v1` agree; system counters showed one enqueue,
one post, zero updates and zero blocks. Earlier channel localization and dedup
assertions had passed. The same test diff against green `52f1ed2` retained the
immediate active-notification assertion that caused the race.
https://github.com/Sxara242/Mastixa-Manager/actions/runs/34755926412

TEST FIX COMMIT: `b12b8b505740a5888e4384f4b6b3495c4810534d`.
Only `android/app/src/androidTest/java/gr/mastixa/manager/CropTaskNotificationTest.java`
changed. Bounded polling uses an interval up to **50 ms**, a **5 s** timeout and
monotonic `SystemClock.elapsedRealtime()`. Failure reports expected ID/tag/channel
and all actual active notification IDs/tags/channels. No large fixed sleep.
Production notification code: **UNCHANGED by this fix**.
Notification channel ID/settings: **UNCHANGED**.
Dedup contract: **3 -> 0 PASS**; channel localization assertions retained.

TARGETED VERIFICATION (same method, existing emulator, no restart/reset):
- Run #1: **1/1 PASS**, Gradle successful in 19s.
- Run #2 (requested flake check): **1/1 PASS**, Gradle successful in 27s.
No full runtime suite or manual CI #157 rerun.

REMOTE RUNTIME VALIDATION: **PENDING** until the next push. The owner requests one
branch push containing both the test fix and this separate docs-only commit, so
one new validation cycle covers them together. Do not amend the test fix commit.

REMAINING: observe new runtime + Desktop/Android CI on the pushed HEAD. Only after
both pass may this scoped Android localization/system-surfaces checkpoint close.
Phase16J overall remains PARTIAL: systematic Android wording audit (including real
translatable hardcoded UI strings), remaining language switching, then scaling and
accessibility. No Phase16K, responsiveness or accessibility work started here.
NEXT EXACT ACTION: push `refactor/pages` once, inspect the newly triggered runtime
and CI results without manually repeating passed tests; then update remote status
and continue the Android wording audit if both are green.

## Remaining Android display wording — 2026-09-13

CURRENT HEAD before this block: `3fc199d3d0b10898190053bfa392513a2aa81d8c`,
`refactor/pages`, clean and pushed. CI #160 (Desktop + Android) and runtime #37
are PASS on that checkpoint. The older PENDING note above is historical:
runtime #35 / CI #158 and runtime #36 / CI #159 also completed successfully.
None of these gates was manually repeated.

COMPLETED in this block:
- Coordinate-export explanatory preview captions and coordinate-mode selector
  follow the profile language. CoordinateExport encoders, file schemas/headers,
  CRS identifiers, coordinates and filenames are unchanged.
- GPS states have EL/EN display labels; persisted `recording`, `paused`, `stopped`
  values and GpsTrack transitions are unchanged.
- The map owner sets a single-language content description using the active
  profile. Provider, tiles, GPS and gestures are unchanged.
- Greek maintenance alert prefixes use `συντήρηση`; year-lock explanation uses
  `αντιγράφου ασφαλείας`. Canonical navigation IDs remain unchanged.

TESTS PASS: `RemainingLocalizationUiTest`, **4/4**, existing emulator-5558,
no restart/reset, no skipped tests. Focused Gradle run completed in 1m 6s.
- EL/EN actual preview, source/WGS84 modes, GeoJSON explanation; table/header
  equality, CSV/GeoJSON/KML byte equality, filename and DB snapshot preservation.
- EL/EN map description and all three track display labels; stored state, title,
  identity/count and DB snapshot remain unchanged by rendering.
- Overdue/upcoming maintenance alert wording; identity, severity, dates and
  user-authored equipment/service text remain unchanged.
- EL/EN year-lock screen and working canonical `Τοπικό backup` navigation.

REMOTE VALIDATION: pending the single push of this localization block. The
normal CI/runtime workflows must validate its commit; do not dispatch duplicates.
REMAINING / NEXT EXACT ACTION: inspect those automatic results, then perform a
final read-only Android wording audit. Declare localization complete only if no
real translatable UI gaps remain; only then start 16J-B scaling and 16J-C
accessibility. Phase16J remains PARTIAL; Phase16K has not started.
No telemetry, analytics, tracking, advertising or automatic diagnostic uploads.
