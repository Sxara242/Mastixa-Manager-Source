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
PRIVATE_ARCHIVE_REFERENCE_RETAINED_LOCALLY
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
PRIVATE_ARCHIVE_REFERENCE_RETAINED_LOCALLY

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

## Android calendar activity display labels — 2026-09-26

Classification: ANDROID. Baseline `88c22ff49a0c96f93151aabd9306859621d7552f`,
worktree `Mastixa-Icon-Diagnosis`, branch `icon-runtime-qa-final`.

Scoped gap CLOSED locally: UnifiedCalendarStore copied canonical Greek activity
category/status values directly into calendar titles/details in English profiles.
Extracted the existing MainActivity mapping into ActivityDisplayLabels and reused
it in both callers: Irrigation, Fertilization, Planned, Completed, Cancelled.
Greek output and unknown/legacy values remain verbatim. Only presentation changes;
no schema, stored values, identity, dates, activity/task or notification logic changes.

Focused reproduction before the fix: CalendarActivityLocalizationTest **1 PASS,
2 FAIL** (English projection and actual calendar cards). After the fix:
**7/7 PASS, 0 failures, 0 skipped**, Gradle successful in 47s:

```powershell
.\gradlew.bat :app:connectedChecksAndroidTest '-Pandroid.testInstrumentationRunnerArguments.class=gr.mastixa.manager.CalendarActivityLocalizationTest,gr.mastixa.manager.UnifiedCalendarStoreTest,gr.mastixa.manager.ActivityUiTest' --console=plain
```

Run from `android`, using installed Temurin 21 and SDK, `ANDROID_SERIAL=emulator-5558`.
Existing Medium_Phone AVD launched headlessly with `-read-only -no-snapshot`;
fixtures are confined to the `.checks` application and cleaned after each test.
Three new tests cover all six canonical category/status combinations, EL/EN/EL/EN
projection switching, EL/EN/EL actual calendar cards, and unknown/blank/whitespace
legacy values. Activity records remain equal and full LocalBackup logical snapshots
(including pending changes) remain byte-identical after each language/render pass.
User-authored Greek text is preserved. Existing calendar and activity UI tests pass.
`git diff --check`: PASS. No full suite, packaging, commit or push.

Phase16J localization and Phase16J overall remain PARTIAL. Remaining audited gaps:
Windows Greek-mode static labels, dynamic alerts, annual-report explanations,
year-correction messages, backup errors and data-quality table display text.
No other localization batch, responsiveness/scaling or accessibility work started.

## Windows year-correction templates — 2026-09-27

Classification: DESKTOP localization only. Recovered HEAD
`4dea1865f863b85075c1b0c9788e5c14270ac031`, branch `icon-runtime-qa-final`.
At recovery only `diagnostics/` and the existing untracked
`tests/test_phase16j_year_correction.py` were present; no production fix existed.
The owner-confirmed baseline was **1 PASS / 5 FAIL**: inactive banner passed;
active banner, begin/finish confirmations, mutation warning and existing-session
error failed. Fragment translation after interpolation changed user-authored
Greek words inside correction reasons, as well as producing mixed-language UI.

Scoped fix: exact catalog templates are translated before inserting years,
reason and current action text. The correction banner and dialogs render plain
text and opt out of a second automatic text translation. Open banners and owned
dialogs refresh on language changes. Known existing-session errors use a complete
template; other start failures use a safe generic message, never raw exception
fragment translation. No correction/domain logic or stored values changed.
The only shared translator change is a four-line QMessageBox opt-in honoring
`mastixaI18nSkipText`, while retaining standard-button translation. Ordinary
message boxes keep their existing behavior.

The recovered six-test module was preserved without edits in this continuation.
Final results (Python 3.14, `PYTHONUTF8=1`, offscreen Qt):

```powershell
python -m unittest tests.test_phase16j_year_correction -v
# 6/6 PASS, 0 failures/errors/skips, 3.009s
python -m unittest tests.test_phase16j_localization tests.test_language_and_logging -v
# 11/11 PASS, 0 failures/errors/skips, 29.012s
python -m unittest tests.test_alpha2_step3_year_context -v
# 12/12 PASS, 0 failures/errors/skips, 2.508s
```

Run the last module in a fresh process: an initial combined run was interrupted
when a controller left active by the language tests caused an older static
QMessageBox mock to wait on a real modal dialog. No assertions were weakened.
Exact-text assertions preserve Greek words, literal HTML-looking tags, braces,
newline, spacing and Unicode in the user reason across EL/EN/EL cycles. Full SQL
dumps and correction-state comparisons remain equal during rendering/switching
and cancelled confirmations; year values and button defaults remain unchanged.
Existing year-context tests confirm physical locks and session behavior.

`git diff --check`: PASS. No Android, schema, migration, MASTER_PROGRESS,
original-checkout or diagnostics changes. No commit/push.
Phase16J localization remains PARTIAL: static labels, alerts, annual-report
explanations, backup errors and data-quality output remain separate gaps. The
application-exit correction warning in year_context_integration.py is outside
this tested module boundary and remains a separate wording follow-up.
No next batch or Phase16J-B work started.

## Windows Data Quality generated results — 2026-09-27

Classification: DESKTOP localization only. Recovered clean tracked/untracked state
at `950fa2217a7e22b8845102d2f639ebfa9acba915`, branch `icon-runtime-qa-final`.
The owner intentionally deleted diagnostics; it remains absent. Reused verified
CI/full-suite checkpoint evidence; Annual Report remains closed.

Issue-generation inventory at that HEAD: **86 _add_issue call sites**:

- A: **51** fully static problem/fix pairs, left unchanged at their call sites.
- B: **35** dynamic sites (34 problem arguments and one concatenated fix),
  covering dates, missing-reference IDs, field/product/equipment/item names,
  partner-name comparisons, stock/quantity formatting and duplicate-field IDs.
  These reduce to **24 distinct complete dynamic templates**.
- C: all **86 record arguments** are canonical/raw identifiers, names or composed
  record labels and remain untouched. Embedded values in B stay opaque. Existing
  source trimming, date/number formatting and persisted enum handling are unchanged.

Baseline: **1 PASS / 8 FAIL / 0 ERROR** across nine focused tests. Static and
dynamic table text, CSV body, labels/count and refreshed status remained Greek.
Existing generic translation can translate status labels temporarily; a targeted
baseline check using the existing English word `Clear` confirmed refresh resets
the label to Greek. Filter/search/order/DB preservation already passed.

Root cause: generated Greek problem/fix text was inserted directly into table/CSV
body cells. The global header-only translation policy is intentional. Composed
dynamic text cannot safely use fragment translation because values may themselves
match catalog entries.

Implementation: a scoped _IssueText string retains its original Greek value plus
owned-template metadata. Existing consumers, equality, source search and sorting
continue to see the canonical string. The presentation boundary reuses existing
localized_messages._text / translate_exact before inserting opaque values. Static
owned fields use exact lookup without fragment fallback. Only the 35 dynamic
arguments were converted; no detection logic was duplicated. The dedicated English
catalog contains 129 distinct static problem/fix texts, 24 dynamic templates and
three count/owned-fallback entries. Existing severity/category/status translations
are reused. Record text is never translated, including existing Greek identifier
prefixes. Existing unmapped equipment/invoice_documents keys are not redesigned.

Table and CSV share _issue_values. CSV keeps five columns, order, semicolon
delimiter and UTF-8 BOM. Status/count bypass generic text translation. One signal
connection at construction re-renders existing issues without queries or detection.
app/language.py and shared helpers are unchanged.

Search explicitly remains casefolded search over canonical Greek severity/category,
record, problem and fix text, independent of UI language. English translated words
do not gain new matches. All category/severity filters, source sort order and issue
counts retain their previous semantics.

Verification (Python 3.14, PYTHONUTF8=1, QT_QPA_PLATFORM=offscreen):

```powershell
python -m unittest tests.test_phase16j_data_quality_localization -v
# 12 PASS / 0 FAIL / 0 ERROR, 4.818s
python -m unittest tests.test_phase16e_cross_module_validation tests.test_alpha2_step4_ui.Alpha2Step4UiTests.test_data_quality_metric_cards_have_safe_vertical_space tests.test_alpha2_step4_ui.Alpha2Step4UiTests.test_data_quality_page_scroll_contains_cards_filters_and_table tests.test_phase16f_realistic_performance -v
# 5 PASS / 0 FAIL / 0 ERROR, 1.723s (separate process)
```

Coverage includes all template catalog entries and placeholder/format-spec parity,
all five columns, clean/warning/error states, dynamic ID/date/numeric wrappers,
two protected partner values, and exact Greek catalog-like words, literal tags,
braces and embedded newlines. Empty owned fallback and identical literal user text
are distinguished. Full logical SQLite snapshots remain identical after refresh,
filtering, live switching and tested export. EL/EN/EL renders exactly once per
change with no database reads and unchanged canonical issues. Existing cross-module
drift and UI tests pass; realistic quality check took 0.115s on the 18,250-row fixture.
AST review confirms all 17 detection methods identical to HEAD after excluding
problem/fix arguments: queries, thresholds, records and conditions are unchanged.

`git diff --check`: PASS. No original-checkout, Android, schema, business-rule,
MASTER_PROGRESS, commit or push changes; no diagnostics recreated. No full desktop
or Android suite rerun. Phase16J remains PARTIAL: Greek-mode static labels and
application-exit correction warning remain pending. Separately, export success/error
dialogs still contain interpolated path/exception text; their generic-dialog
protection is a follow-up, not changed or runtime-validated in this batch.
No next batch or Phase16J-B work started.

## Windows backup/restore error localization — 2026-09-27

Classification: DESKTOP localization only. Recovered clean tracked state at
`616662c01da72a7f1f74491dc537ed4a82ffc8ea` on `icon-runtime-qa-final`;
only existing `diagnostics/` was untracked. Required automatic CI verified green:
Verify desktop and Android run 36283174790; Windows release gate 36283174736.

Reproduction: **0 PASS / 6 FAIL** for missing selected backup, missing live DB,
creation failure, restore failure, invalid SQLite, and unknown raw BackupError.
The UI passed already-composed Greek exception strings to generic fragment
translation, mixing wrapper languages and translating path/raw-detail components.

BackupError now carries owned-template metadata while keeping its type, original
Greek str/args, exception chaining and logging. Only error construction changed
in BackupManager; SQLite copy, validation decisions, rollback, safety snapshots
and retention are unchanged. Presentation translates exact templates before
inserting opaque paths/raw details. Unknown errors remain entirely verbatim.
All five BackupError UI catch sites use this boundary (manual create/restore,
startup, shutdown and profile switching), including outer lifecycle wrappers.
Raw nested exception detail deliberately remains raw, even if it contains Greek.

Reused the protected dialog helpers by moving them from year_context_ui.py into
localized_messages.py, adding Critical icon support. Year-correction imports the
same helpers; no correction behavior changes. LanguageController is unchanged.
No competing translator or raw-string parsing was introduced.

Verification commands (Python 3.14, PYTHONUTF8=1, offscreen Qt):

```powershell
python -m unittest tests.test_phase16j_backup_localization tests.test_phase16d_backup_restore tests.test_phase16j_year_correction tests.test_phase16j_localization -v
# Initial post-fix run: 24/24 PASS (6 new + 7 backup + 6 correction + 5 localization).
python -m unittest tests.test_phase16j_backup_localization -v
# After adding 3 validation/lifecycle coverage tests: 9/9 PASS, 1.575s.
```

Final coverage: **9 focused + 7 existing backup + 11 directly affected localization
tests PASS**, zero failures/errors/skips. Production code remained unchanged
between these successful runs. The added cases exercise integrity results,
missing-table identifiers and actual lifecycle error dialogs with EL/EN/EL live
switching and No/default-button semantics. Exact-string assertions preserve paths,
Greek catalog-like words, HTML-looking tags, braces, newlines and raw SQLite
details. Exception args/causes remain identical; fixture files remain byte-identical
across rendering. Existing tests verify real round-trip recovery, failed-restore
rollback, safety/source preservation at zero retention and distinct snapshots.
Expected injected-failure logs were retained, not suppressed.

`git diff --check`: PASS. Original checkout and diagnostics untouched; no Android,
schema/migration, MASTER_PROGRESS, commit or push changes. Phase16J remains PARTIAL.
Remaining gaps: alerts, annual-report explanations, data-quality results, remaining
Greek-mode static labels and the separate application-exit correction warning.
No next batch or Phase16J-B work started.

## Windows Alerts presentation localization — 2026-09-27

Classification: DESKTOP localization only. Recovered HEAD
`9999e5878e39e7af99d9da326297f19bb4cfd7d2` on `icon-runtime-qa-final`,
with clean tracked files and existing untracked `diagnostics/`. Reused owner's
verified green desktop/Android and Windows release-gate checkpoint.

Baseline: **4 PASS / 6 FAIL**, zero errors, in the initial 10 focused tests.
Failures covered English activity, inventory, equipment and harvest-wait rows,
live language switching, and count immediately after refresh. Generic widget
translation could temporarily display the count in English, but refresh wrote
Greek again. Table body cells intentionally bypass LanguageController translation;
AlertsPage constructed Greek generated strings without localizing them.

AlertsPage now uses `tr` on owned templates before inserting raw values, translates
owned severity/category labels, and refreshes on the existing language-change
signal. The count owns its translation and opts out of generic label translation.
Activity overdue/today/upcoming, inventory exhausted/low stock, service date/meter
details and harvest-wait singular/plural templates are covered. Known activity
enums and hours display are localized; unknown categories remain verbatim.
Fallback subject labels have separate display values so sorting retains its
canonical source subjects. Existing catalog terminology is reused.

Final verification (Python 3.14, PYTHONUTF8=1, offscreen Qt):

```powershell
python -m unittest tests.test_phase16j_alerts_localization -v
```

**12 PASS / 0 FAIL / 0 ERROR / 0 SKIP**, 4.572s. The original 10 cases passed;
two additional cases cover fallback subjects and a legacy category matching a
catalog key. No pre-existing behavioral Alerts tests were found. Shared translator
infrastructure is unchanged, so unrelated localization/full desktop/Android tests
were not rerun. The pre-existing Qt integer-alignment DeprecationWarning remains;
this batch does not change alignment behavior.

Exact assertions preserve `Παραγωγή Ναι Αποθήκευση <b>tag</b> {year}` in field,
item, equipment and product names, descriptions and stored units. Tests verify
dates, quantities, meter numbers, known/legacy category source values, record IDs,
canonical filter keys and severity ordering. All category/severity combinations
retain matching records, counts, action enablement and navigation targets through
EL/EN/EL. Complete logical SQLite dumps remain equal after refresh, filters and
language switching. No database writes occur during presentation.

`git diff --check`: PASS. `app/language.py` and its table-header-only policy are
unchanged. No Android, schema/migration, alert rules/thresholds, MASTER_PROGRESS,
original-checkout or diagnostics changes. No commit/push.
Phase16J remains PARTIAL: annual-report explanations, data-quality results,
remaining Greek-mode static labels and the application-exit correction warning
remain separate gaps. No next batch or Phase16J-B work started.

## Windows Annual Report generated explanations — 2026-09-27

Classification: DESKTOP localization only. Recovered expected HEAD
`5ce7861e489a4a27d3a5975d6bd8d9c596aa1be0` on `icon-runtime-qa-final`;
tracked files were clean, with only existing untracked `diagnostics/`.
Reused the owner's verified green CI checkpoint; Alerts remains closed.

Baseline: **2 PASS / 4 FAIL / 0 ERROR** in six focused tests. Finance categories
and handling remained Greek in English mode. Refresh overwrote the all-products
note with Greek. The product-note case initially also exposed AutoText handling;
moving that assertion after the language cycle independently reproduced actual
English corruption: the product name became `Production Yes Save Expenses...`
while the surrounding explanation retained Greek fragments.

Root causes: the scope QLabel exposed an already-interpolated product name to
generic fragment translation, while finance table body cells intentionally bypass
that translator. AnnualFarmReportPage now reuses localized_messages._text for
exact complete-template translation before interpolation. Its scope label uses
PlainText and mastixaI18nSkipText. Finance-owned category/handling text uses tr
before insertion. A single initialization-time language-change connection refreshes
the existing page. Neither language.py nor shared helper infrastructure changed.

Verification commands (Python 3.14, PYTHONUTF8=1, QT_QPA_PLATFORM=offscreen):

```powershell
python -m unittest tests.test_phase16j_annual_localization -v
# 6 PASS / 0 FAIL / 0 ERROR, 3.668s
python -m unittest tests.test_stabilization.StabilizationTests.test_product_registry_integration_active_inactive_legacy_and_reports -v
# 1 PASS / 0 FAIL / 0 ERROR, 3.897s (fresh process)
```

Tests verify full Greek/English notes and finance explanations, repeated live
EL/EN/EL switching, and exact preservation of
`Παραγωγή Ναι Αποθήκευση Έξοδα <b>tag</b> {year}` in the note, combo/source value,
product breakdown and CSV. Product IDs, selected year, cached report rows,
production/sold/stock/revenue/average values, finance amounts and the absence of
a product net result remain unchanged. Complete logical SQLite snapshots match
after page construction, refresh, filtering, language switching and CSV export.
The existing integration test also verifies renamed/inactive product identity.

CSV does not export these explanations; its product names and numeric rows were
already correct and remain untouched. No calculation, allocation, query, sorting,
navigation, schema, Android or export-format changes. No full desktop/Android suite
rerun. `git diff --check`: PASS. Original dirty checkout and diagnostics untouched.
No commit/push. Phase16J remains PARTIAL: data-quality results, remaining Greek-mode
static labels and the application-exit correction warning are still pending.
No next batch or Phase16J-B work started.

## Windows static sensor/inventory labels — 2026-09-27

Classification: DESKTOP localization only. Recovered clean checkout at
`4928a4b2448c7b880b8f7f27dcfe5f0ba749f368`, branch `icon-runtime-qa-final`.
Reused verified CI checkpoint; diagnostics remains absent.

Narrow inventory/classification:
- A, owned UI: sensor UNDER CONSTRUCTION; inventory title, subtitle, Stock filter
  label, two metric captions, two stock table headers and explanatory note.
  Generated inventory status labels were also untranslated in English table cells.
- B, raw data: item names, category strings/itemData, units and numerical values.
  A category equal to Αποθήκευση actually displayed Save in English, demonstrating
  the need for scoped category-combo protection.
- C, internal: stock variables, SQL aliases, all/positive/low filter keys and
  inventory_stock_report.csv remain unchanged. API, CSV and OK are intentional
  technical/status tokens, not translated Greek prose.
- D, dynamic dialogs: filename/path and exception messages remain separate work.
  No edits to export dialogs or application-exit warnings.

Baseline: **1 PASS / 6 FAIL / 0 ERROR** in seven focused tests. Failures reproduce
Greek sensor/stock wording, generated English statuses, category-name translation
and shared CSV-header wording. Filtering/calculations/database preservation passed.

Implementation: Greek source now uses ΥΠΟ ΚΑΤΑΣΚΕΥΗ and natural απόθεμα labels,
with a small English catalog retaining the established English wording. Existing
LanguageController handles static labels and headers. Only the database category
combo opts out of generic item translation; its owned All option is rendered
separately. A single language-change connection updates that option and displayed
status cells from canonical cached rows. No queries/calculations/filtering changes.
app/language.py and shared helpers are unchanged. The existing sensor test's Greek
status expectation was updated to match the requested wording; its interaction and
navigation assertions were retained.

Verification (Python 3.14, PYTHONUTF8=1, QT_QPA_PLATFORM=offscreen):

```powershell
python -m unittest tests.test_phase16j_static_labels_localization -v
# 7 PASS / 0 FAIL / 0 ERROR, 4.405s
python -m unittest tests.test_sensor_view_ui tests.test_phase16j_localization -v
# 9 PASS / 0 FAIL / 0 ERROR, 1.825s
```

Tests assert exact Greek/English wording through EL/EN/EL on the same pages,
unchanged sensor page indexes/navigation, protected category names including exact
catalog keys, and literal Παραγωγή Αποθήκευση Stock Ναι <b>tag</b> {year} in
item/unit values. All category/stock/search combinations retain canonical keys,
row counts, cached logical values and weighted-cost/stock calculations. Logical
SQLite snapshots remain identical after refresh, switching, filters and CSV export.
No separate pre-existing InventoryReportPage test module was found.

CSV shares the two corrected static headers and keeps its numeric/user values,
structure, order, delimiter and UTF-8 BOM unchanged. CSV body statuses deliberately
remain canonical Greek/OK; localizing those exported values is a separate follow-up
if desired, not silently added to this static-header batch.

`git diff --check`: PASS. No Android, schema, original-checkout, diagnostics,
commit or push changes. No full desktop/Android suite run. Phase16J remains PARTIAL:
application-exit correction warning, export dialogs containing paths/exceptions,
and the final read-only localization closure audit remain. No next batch started.

## Application-exit correction warning — 2026-09-27

Classification: DESKTOP localization only. Recovered clean checkout at
`00b46afab04601864703e7a47d2ca55f46b8e7d9`, branch `icon-runtime-qa-final`.
Reused verified CI checkpoint; diagnostics remains absent.

Actual pre-fix baseline: **4 PASS / 3 FAIL / 0 ERROR** in seven focused tests.
An initial fixture-only run had seven setup errors because year_locks had not been
initialized; the fixture was corrected before obtaining this baseline or editing
production code. Failures reproduced Greek correction-mode wording, fragmented
English (including mixed Greek with "year" / "enabled year"), and the live-modal
wording assertion. All four existing close-semantic cases passed before the fix.

The direct QMessageBox.warning composed text before generic translation. It now
uses the existing protected _message helper with a complete owned template and
separate year/active_year values. Greek uses "η λειτουργία προσωρινής διόρθωσης";
English is complete. Exact tests use locked year 2024 and active year 2027, retain
Yes/No with default No, and verify localized standard buttons. No reason text was
added. app/language.py, localized_messages.py and year_context.py are unchanged.

The close-event ordering is untouched and directly exercised using the real
installed override with a controlled parent closeEvent:
- No ignores the event, never delegates or finishes, and retains the guard/state.
- Yes delegates exactly once. Parent acceptance finishes exactly once, then removes
  the guard. Audit details retain the exact original Greek outcome
  `Τερματισμός προσωρινής διόρθωσης κατά το κλείσιμο εφαρμογής` and original reason.
- Parent rejection retains active correction and the installed guard; no finish.
- Inactive correction shows no warning and delegates accepted/rejected close.
Logical DB snapshots remain identical for No, parent rejection and modal switching.
An event probe confirms guard installation/removal, and recorded call ordering is
parent -> finish -> remove. The same modal cycles EL/EN/EL repeatedly without a
replacement dialog; years, buttons and default remain correct.

Verification (Python 3.14, PYTHONUTF8=1, offscreen Qt):

```powershell
python -m unittest tests.test_phase16j_exit_correction_localization tests.test_phase16j_year_correction tests.test_phase16j_backup_localization.BackupLocalizationTests.test_lifecycle_error_dialogs_live_switch_and_keep_no_semantics -v
```

**14 PASS / 0 FAIL / 0 ERROR**, 6.743s: seven new exit tests, six existing
correction tests and one existing lifecycle/backup-close test. The injected backup
failure emits its expected cancellation log. No full desktop/Android suite run.

`git diff --check`: PASS. Only integration wording/helper call, one English catalog
entry, focused tests and this ledger changed. No original-checkout, Android,
schema, backup behavior, diagnostics, commit or push changes. Phase16J remains
PARTIAL: export dialogs with interpolated paths/exceptions and the final read-only
localization closure audit remain. Neither next task was started.


## Phase16J-A — Export path/exception dialogs (2026-09-27)

DESKTOP only. Recovered clean `icon-runtime-qa-final` at
`3647d38cea891c6f2c4d05b1fb612cdc4e8dff29`; diagnostics absent.
The approved helper extension adds only `information: QMessageBox.Icon.Information`
to the icon mapping. No other shared-helper behavior or app/language.py changed.

Before owner fixes, the 18 focused tests produced **2 PASS / 16 FAIL / 0 ERROR**
(the helper mapping was already added). Real export methods reproduced mixed or
untranslated owned wording and mutation of raw values during generic translation:
`Αποθήκευση` became `Save` inside paths/errors, and `Ναι` became `Yes` in raw errors.
The helper icon/live-switch regression and existing static ZIP verification success
already passed. Fixtures use existing catalog title wording.

Scoped fixes:
- Data Quality CSV: success path and OSError wrapper.
- Reports PDF/Excel: success paths and existing failure wrappers.
- Inventory and Annual CSV: success paths and raw-only exception dialogs/titles.
- Sales CSV: success path only; no new exception handling.
- Portable ZIP: creation error, success path, protected last-export label,
  automatic verification warning, manual verification failure/success.

Owned templates are translated before interpolation through _message/_text.
Paths, raw exceptions and archive-member names remain exact, including Greek,
English, braces, ampersands and markup-like text. The last-export label is plain
text and refreshes on language changes without querying or changing data.
Locally tagged verification strings retain their canonical Greek string value and
carry owned-template metadata for dialog rendering; raw library exceptions stay
plain strings. CRC/schema/required-file checks and archive formats are unchanged.
No new dialog abstraction or global translation behavior was introduced.

Files: six export-owner modules, the approved one-entry localized_messages.py
extension, en_phase16j_export.json, new test_phase16j_export_dialog_localization.py,
three existing CSV localization tests (only their dialog mock target changed), and
this ledger. No MASTER_PROGRESS change was necessary.

Verification (Python 3.14, PYTHONUTF8=1, QT_QPA_PLATFORM=offscreen):

```powershell
python -m unittest tests.test_phase16j_export_dialog_localization tests.test_phase16j_data_quality_localization tests.test_phase16j_annual_localization tests.test_phase16j_static_labels_localization tests.test_phase16j_year_correction tests.test_phase16j_exit_correction_localization tests.test_phase16j_backup_localization -q
```

**65 PASS / 0 FAIL / 0 ERROR**, 29.770s (18 export tests at this point).
After adding two tests for remaining ZIP verification branches:

```powershell
python -m unittest tests.test_phase16j_export_dialog_localization tests.test_phase16a_csv tests.test_language_and_logging.LanguageAndLoggingTests.test_report_export_uses_active_language -v
python -m unittest tests.test_stabilization.StabilizationTests.test_data_export_product_filter_and_unfiltered_export -v
```

**25 PASS / 0 FAIL / 0 ERROR**, 10.781s; **1 PASS / 0 FAIL / 0 ERROR**, 4.663s.
Final coverage: **73 distinct passing tests**, including **20 new focused tests**;
no full desktop/Android suite run. Expected injected backup failures log their
error/traceback during successful backup regression tests.

Same-modal EL -> EN -> EL checks preserve icon, Ok button semantics, exact raw
values, logical DB snapshots, cached rows and selected filters. Real CSV/ZIP bytes
remain identical through switching. Existing CSV tests retain BOM, delimiters,
headers, user values and filtering; the report exporter invocation/path is unchanged
and its existing active-language file-output regression passes. Export payload
construction, row ordering, filenames and manifest/schema are untouched.

`git diff --check`: PASS. Original dirty checkout untouched; no Android, schema,
dependency, icon, installer, diagnostics, commit or push changes.
Phase16J remains PARTIAL. Native QFileDialog/platform wording is outside this batch;
no wider export-dialog sweep was performed. The final HIGH/read-only localization
closure audit remains pending and was not started. Scaling/accessibility remains
outside this phase.

## Phase16J remediation boundary #1 — Windows native file dialogs (2026-09-27)

DESKTOP localization only. Recovered clean `icon-runtime-qa-final` at
`0f5ae2367647f901f89056f432c95de8b9290e44`; diagnostics absent. Reused verified CI;
did not rerun the closure audit. All 20 audit-listed QFileDialog calls still match.

The OS does not translate captions/filter descriptions supplied by the app.
Real production methods intercepted at QFileDialog reproduced **7 PASS / 20 FAIL /
0 ERROR** before production edits (27 tests): every English caption remained Greek.
The seven original preservation/cancellation tests already passed. Three further
tests cover JSON/snapshot paths, GIS output destination, and catalog integrity.

Only captions and descriptive filter labels now use the existing exact `_text`
helper. Technical patterns remain literal. Reused 19 caption keys and the two
descriptor keys `Τιμολόγια` / `Όλα`; added exactly five previously absent keys in
`en_phase16j_file_dialogs.json`: `Εισαγωγή τιμολογίων`, `Όλα τα αρχεία`, `Γεωμετρία`,
`Εικόνες`, `Προφίλ Mastixa`. JSON, placeholder parity, English text, and absence of
duplicate new keys are tested. app/language.py and app/localized_messages.py are
unchanged. OS-native buttons/file-browser chrome and live retitling of an already
open native dialog are outside app ownership and this phase.

All these actual call sites pass exact Greek/English caption assertions on
successive EL -> EN -> EL openings (not an in-dialog language switch):

| Owner | Function | English caption (Greek source preserved in EL) |
|---|---|---|
| app/annual_report.py | export_csv | Save Annual Report |
| app/audit.py | export_csv | Export history CSV |
| app/dashboard.py | restore_backup | Select a backup to restore |
| app/data_export.py | export_zip | Create portable ZIP |
| app/data_quality.py | export_csv | Export data check |
| app/field_finance.py | export_csv | Export cost by field |
| app/gis/dialog.py | import_file | Import boundary |
| app/gis/export_dialog.py | export | Export |
| app/inventory_report.py | export_csv | Save Inventory Report |
| app/invoice_documents.py | choose_files | Import invoices |
| app/invoice_documents.py | export_selected | Export selected invoices |
| app/reports.py | export_pdf | Export report to PDF |
| app/reports.py | export_excel | Export report to Excel |
| app/sales_report.py | export_csv | Save Sales Report |
| app/settings.py | choose_profile_avatar | Profile image |
| app/settings.py | export_profile | Export profile |
| app/settings.py | import_profile | Import profile |
| app/settings.py | choose_backup_folder | Choose backup folder |
| app/upload_center.py | export_selected_snapshot | Export selected snapshot |
| app/upload_center.py | export_json | Export JSON package |

Preservation evidence:
- All 20 actual argument lists retain default paths/names exactly, including frozen
  timestamp ZIP names, years, snapshot IDs, raw profile names and GIS KAEK names.
- All descriptive filters pass exact EL/EN assertions with identical patterns;
  technical CSV/ZIP/PDF/Excel/JSON filters are unchanged. GIS import retains
  geojson/json/kml/gml/xml/zip/dxf; all five GIS export formats are checked.
- Selected adversarial Greek/English/braces/ampersand paths pass unchanged to
  CSV/PDF/XLSX writers, invoice import/export, profile/avatar operations, directory
  text, GIS import/export and JSON/snapshot writers. GIS receives the same EPSG.
- Cancellation at all 20 entry points performs no downstream DB writes, file
  writes, profile operations, restore/import or export. Dashboard still prepares
  its backup directory before the picker: this pre-existing mkdir is deliberately
  preserved and mocked/asserted separately, not described as a new no-I/O promise.
- An AST comparison against HEAD confirms the entire production code is identical
  except for `_text` imports and caption/descriptor expressions; evaluating those
  expressions in Greek recovers the exact original strings. Defaults, formats,
  extension handling, persistence and business logic remain unchanged.
- Existing export tests retain logical DB snapshots and file bytes; existing GIS
  cancellation/failure tests retain database snapshots and previous destination.

Verification: Python 3.14, PYTHONUTF8=1, QT_QPA_PLATFORM=offscreen:

```powershell
python -B -m unittest tests.test_phase16j_file_dialog_localization tests.test_phase16j_export_dialog_localization tests.test_profiles.ProfileManagerTests.test_pin_identity_startup_setting_and_export_import tests.test_profiles.ProfileManagerTests.test_profile_import_under_path_with_uri_characters tests.test_profiles.ProfileManagerTests.test_interrupted_profile_export_preserves_previous_destination tests.test_gis.GeometryTests.test_geojson_crs_and_multiple_features tests.test_gis.GeometryTests.test_kml_hole_and_gml_authority_axis_order tests.test_gis.GeometryTests.test_shapefile_zip_and_linear_dxf tests.test_coordinate_exports -q
python -B -m unittest tests.test_alpha2_step5_ui.Alpha2Step5UiTests.test_invoice_documents_page_hides_all_unfinished_actions -v
```

First command: **60 PASS / 0 FAIL / 0 ERROR**, 15.222s (30 new file-dialog,
20 existing export-dialog, 3 profile, 3 GIS import, 4 coordinate-export tests).
Second command: **1 PASS / 0 FAIL / 0 ERROR**. No pre-existing direct invoice
import/export function tests were found; the new tests exercise their real picker
methods and verify exact downstream arguments, plus the existing page-action gate.
Total: **61 distinct PASS**, no full desktop or Android suite run.

`git diff --check`: PASS. Changed only the 14 listed dialog-owner modules, the new
catalog/test module and this ledger. MASTER_PROGRESS, shared localization helpers,
Android, schema, dependencies, icons and the original dirty checkout are untouched;
diagnostics remains absent. No commit/push.

Phase16J localization remains PARTIAL. Five audit remediation boundaries remain:
1. Windows static selectors/accessibility (owned enum labels, month/inactive labels,
   tab-scroll accessible name).
2. Windows generated table/body presentation and its language refresh.
3. Windows composed UI/raw-value boundaries outside these QFileDialog arguments.
4. Android report movement-type display mapping.
5. Android dashboard product-button raw-name protection.

None of those boundaries, the closure audit, or scaling/accessibility work started.

## Phase16J remediation boundary #2 — Windows static selectors (2026-09-27)

DESKTOP localization only. Recovered clean `icon-runtime-qa-final` at
`19f80dcd0099d0bda8e099e28155ec936298a004`; diagnostics absent. Reused supplied
successful remote CI. The closed QFileDialog batch was not reopened.

All seven audit surfaces match current source:
- equipment.EquipmentPage.reminder_filter: upcoming/overdue labels.
- inventory_report.InventoryReportPage.stock_filter: positive/low labels.
- invoice_documents.InvoiceDocumentsPage.document_type: unknown/purchase/sale.
- products.ProductsPage.status_filter: integer-backed 1/0 static options.
- phase13_calendar_integration.Phase13FarmCalendarPage.month: all 12 month names.
- product_registry.add_product_choices: owned inactive suffix only.
- tab_scroll_fix._ensure_left_scroll_proxy: app-owned accessibleName.
No app-created right-scroll proxy exists; the right native Qt button is unchanged.

Before production edits: **0 PASS / 8 FAIL / 0 ERROR**, with 12 failing language
subcases. Two initial fixture mistakes were corrected before this recorded
baseline: established placeholder wording is "Select a product", and the test
must select the last tab to enable the left scroller. The corrected baseline
reproduced all seven real defects.

Root causes and fixes:
- String-key selectors lacked exact catalog entries; adding entries fixes display
  through existing combo translation, with no edits to their owner modules.
- Numeric product-status/month options lacked both translations and the existing
  mastixaI18nStaticItems opt-in. Only these two static combos opt in; global
  protection for integer-backed user records remains unchanged.
- Product-name/unit composites are correctly protected as raw data. A private,
  combo-owned QObject refreshes only the selected inactive suffix via the existing
  _text("Ανενεργό") key. Raw prefix is never passed to translation. It blocks combo
  signals during display refresh, uses no DB queries, and is reused on population;
  stale selection metadata is cleared. Active/legacy choice behavior is unchanged.
- The left proxy now has a Greek source accessibleName and an exact English key;
  existing controller property translation handles live changes. Its arrow,
  geometry, identity, click delegation and native scroll behavior are unchanged.

New en_phase16j_static_selectors.json contains **22 unique keys**: two reminder,
two stock, three invoice descriptions, two product-status, twelve month and one
accessible-name translation. Reused existing Ανενεργό -> Inactive plus existing
All/All months/Select a product entries. New keys have no duplicate/conflicting
definitions, empty values, Greek English-values, or placeholder mismatches.

New tests exercise actual production widgets/functions through EL -> EN -> EL:
all visible labels, all 12 ordered months, canonical itemData (including exact
integer types), selection, no duplicate/reordered items, no index-change actions,
and unchanged logical DB snapshots. Equipment upcoming/overdue, inventory
positive/low and product active/inactive results remain identical. Calendar month
filtering retains the selected month; existing generated-task/calendar test passes.
Invoice types stay unknown/purchase/sale without writes or import/OCR actions.
Adversarial product names and units containing Greek catalog words, markup-like
text, braces and ampersands remain exact; active products acquire no suffix.
Repopulation does not duplicate suffix callbacks or retain stale suffixes, and
suffix language refresh emits no currentTextChanged or DB reads.

Verification (Python 3.14, PYTHONUTF8=1, QT_QPA_PLATFORM=offscreen):

```powershell
python -B -m unittest tests.test_phase16j_static_selectors_localization -q
```

Initial fixed run: **8 PASS / 0 FAIL / 0 ERROR**, 3.158s. After adding catalog
integrity and single/silent/read-only suffix-refresh tests, final focused run:

```powershell
python -B -m unittest tests.test_phase16j_static_selectors_localization tests.test_phase16j_localization.LocalizationBoundaryTests.test_record_combo_preserves_names_matching_translation_keys tests.test_phase16j_localization.LocalizationBoundaryTests.test_explicit_static_readonly_and_enum_still_translate tests.test_language_and_logging.LanguageAndLoggingTests.test_translated_combo_retains_canonical_source_value tests.test_stabilization.StabilizationTests.test_product_registry_starts_empty_crud_status_legacy_and_navigation tests.test_stabilization.StabilizationTests.test_product_registry_integration_active_inactive_legacy_and_reports tests.test_product_link_performance tests.test_equipment_meter_type_ui_guard tests.test_phase16j_static_labels_localization tests.test_phase13_calendar tests.test_tab_scroll_fix -q
```

**28 PASS / 0 FAIL / 0 ERROR**, 24.977s, process exit 0: 10 new focused tests,
3 combo-controller tests, 3 registry/backfill tests, 2 equipment tests,
7 existing inventory/static-label tests, 1 calendar and 2 native tab-scroll tests.
No full desktop or Android suite run.

`git diff --check`: PASS. Only four production modules (products, calendar
integration, product_registry, tab_scroll_fix), new catalog/test and this ledger
changed. app/language.py and app/localized_messages.py unchanged. No database,
schema, canonical values, business rules, original dirty checkout, Android,
MASTER_PROGRESS, diagnostics, commit or push changes.

Phase16J remains PARTIAL. Four remediation boundaries remain:
1. Windows generated table/body presentation.
2. Windows composed UI / raw-value protection.
3. Android report movement-type display.
4. Android dashboard product-name protection.

None of those boundaries, the final closure audit, or general
accessibility/responsiveness/scaling work was started.

## Phase16J remediation boundary #3 — Windows generated bodies (2026-09-28)

DESKTOP localization only. Recovered clean `icon-runtime-qa-final` at
`0a7b498980dfbc3132e64a707aa6e9975b59eea5`; diagnostics absent. Reused supplied
successful remote CI. Closed native-file-dialog and static-selector boundaries
were not reopened.

All 15 confirmed surfaces exist at this checkpoint. Root cause: the controller
intentionally skips table-body cells. Canonical enum labels and generated Greek
templates therefore reached cells unchanged; products translated only during
ordinary refresh, leaving already-open status cells stale after language changes.

Fixed display owners:
1. activities: known category/status, owned general fallback, irrigation duration,
   and generated count summary; unknown canonical labels remain opaque.
2. equipment: status/reminder labels and owned hours wording, including next-meter
   detail; canonical reminder thresholds and filtering remain unchanged.
3. inventory: all stock states, known movement labels, general fallback and automatic
   marker; item/category/unit/notes and movement source values remain unchanged.
4. labor: general fallback and active/inactive worker display; names/roles/work raw.
5. money: general fallback and automatic marker; existing inherited text filtering
   sees canonical cell text, temporarily restored under blocked signals, then the
   localized display is restored. Search semantics are unchanged.
6. partners: mapped partner-type cell labels; the canonical _type_label mapping
   itself remains unchanged for other callers.
7. plant_tracking_ui: status, health and event/history mappings plus count summary.
8. plant_protection: owned area/day suffixes; numbers and dose-unit values unchanged.
9. audit: known table/action mappings and count wording; raw details remain opaque.
10. farm_calendar / phase13_calendar_integration: section/category, crop-task state,
    owned fallbacks, generated units/counts; titles/notes/dates/IDs remain raw.
11. global_search: owned sections/fallbacks/generated result wording/counts only.
12. field_profile: timeline and cost-category cell projections. The canonical
    field_activity_timeline adapter remains unchanged; localization occurs at its
    table consumer. No raw field identity labels were changed.
13. data_export: preview section/missing-table labels and summary counts only.
14. invoice_documents: known OCR table-status codes and linked-financial-entry
    explanation; unknown codes preserved. Composed OCR suggestion/raw-value labels
    and rejected-import dialogs remain in the next boundary.
15. products: targeted live status-cell rerender, including English initial render.

Owner-local hooks update only explicitly annotated display cells in place using
existing _text. They preserve item objects, selection, ordering, navigation data
and raw values, and block table signals during language rerender. Each page binds
one QObject-owned language-change callback at construction, not during refresh.
Callbacks perform no DB reads/writes. Shared app/language.py and
app/localized_messages.py are unchanged; no generic table translation was added.

Calendar/search display specifications are sidecars, separate from canonical
record dictionaries. Raw user values enter template interpolation only after
translation. Source comparison against HEAD proves unchanged SQL/DB call ASTs,
canonical calendar/search record construction, reminder rules, canonical partner
mapping, navigation methods, ZIP/manifest/export-byte generation and verification.

No audited surface was excluded. Invoice actions remain gated as before; their
production body renderers are tested directly without enabling unfinished actions.

Catalog: **58 new non-conflicting exact entries** in
en_phase16j_generated_tables.json. Existing exact enum/section/unit keys are reused
(including Irrigation, Scheduled, Active, Receipt, Low, Fields and decares).
Validation covers JSON, nonempty values, braces, placeholder/format-specifier/
conversion parity, English values and duplicate-key conflicts. No unrelated
catalog cleanup. The Greek area abbreviation retains its decare/stremma semantics;
numeric formatting and calculations remain unchanged.

Baseline before production edits: **0 PASS / 15 FAIL / 0 ERROR**, with 18 failing
assertions/subcases. Initial test setup issues (audit trigger prerequisites,
supplier-selector isolation and field selection) were corrected before recording
this baseline. Existing catalog wording is reused rather than changed to satisfy
an initially assumed English label.

Tests use actual production widgets/renderers, isolated SQLite fixtures, and
controlled row sources where a renderer needs independent boundary coverage.
They exercise EL -> EN -> EL and preserve adversarial raw Greek/English values,
markup-like text, braces, units, filenames, IDs and dates. Known/unknown enum
coverage includes all OCR codes, all stock states, and catalog-like unknown values.
Search identity/order/navigation payloads remain canonical; translated words do
not become newly searchable. Money filtering is explicitly tested both ways.
Prepared database construction/refresh snapshots match across 14 page owners;
the audit test isolates its pre-existing trigger prerequisites and verifies
render/switch snapshots. Initial existing schema setup is deliberate fixture work.
All live switches tested perform zero writes; targeted rerender tests also prohibit
queries. Existing ZIP regression confirms identical logical archive members/bytes
through language switching, with source export/verification methods unchanged.

Verification: Python 3.14, PYTHONUTF8=1, QT_QPA_PLATFORM=offscreen.

```powershell
python -B -m unittest tests.test_phase16j_generated_tables_localization -q
```

Baseline above; initial fixed run **15 PASS**, expanded run **21 PASS**. Then:

```powershell
python -B -m unittest tests.test_phase16j_generated_tables_localization tests.test_equipment_maintenance_contract tests.test_inventory_quality_gate.InventoryQualityGateTests.test_inventory_page_low_stock_metrics_statuses_and_filter tests.test_plant_tracking_ui.PlantTrackingUiTest.test_page_lists_projected_state_history_and_soft_deleted_records tests.test_phase9d_field_activity_timeline tests.test_phase13_calendar tests.test_phase16a_csv tests.test_phase16j_export_dialog_localization.ExportDialogTests.test_zip_success_last_label_and_bytes tests.test_stabilization.StabilizationTests.test_data_export_product_filter_and_unfiltered_export tests.test_stabilization.StabilizationTests.test_expense_and_inventory_sync_are_idempotent_and_clean_up tests.test_stabilization.StabilizationTests.test_plant_protection_hides_approval_number_but_preserves_legacy_value tests.test_stabilization.StabilizationTests.test_product_registry_integration_active_inactive_legacy_and_reports -q
```

**40 PASS / 0 FAIL / 0 ERROR**, 22.611s, exit 0 (21 new + 19 related existing).
Final inventory-state review found one additional missing exact key, Εξαντλήθηκε;
added Out of stock and its three-state regression, then reran the new module:
**22 PASS / 0 FAIL / 0 ERROR**, 7.503s. Two further invariant tests ran individually:

```powershell
python -B -m unittest tests.test_phase16j_generated_tables_localization.GeneratedBodyTests.test_prepared_database_page_construction_and_refresh_preserve_state -v
python -B -m unittest tests.test_phase16j_generated_tables_localization.GeneratedBodyTests.test_products_english_initial_render_and_single_refresh_hook -v
```

Each **1 PASS / 0 FAIL / 0 ERROR**, 3.680s and 0.613s, exit 0. Final coverage:
**43 distinct passing tests (24 new + 19 existing)**. No full desktop/Android suite.

`git diff --check`: PASS. Changed only 16 scoped production owners, new catalog,
new focused tests and this ledger. No schema/migration/dependency/Android changes;
original dirty checkout untouched; diagnostics absent; MASTER_PROGRESS unchanged.
No commit/push. Phase16J localization remains PARTIAL, with three boundaries left:
1. Windows composed UI / raw-value protection.
2. Android report movement-type display.
3. Android dashboard product-name protection.

No next boundary, final closure audit, or scaling/accessibility work started.

## Phase16J remediation boundary #4 — Windows composed UI/raw values (2026-09-28)

DESKTOP localization only. Continued the existing dirty `icon-runtime-qa-final`
worktree at `fe43b46a260c8a448218d6bac1ebe9b293b3061d`; no reset/recreation.
At resume, 22 production modules were modified and the scoped catalog/test were
untracked. The first 14 regressions had passed after fixes; expanded coverage,
remaining invariants, existing regressions and this ledger were unfinished.
Diagnostics stayed absent and the original dirty refactor/pages checkout was
untouched. No commit/push, Android, schema, dependency or packaging changes.

Baseline before production edits: **1 PASS / 13 FAIL / 0 ERROR** (14 production-
surface tests, 3.855s). Unmarked titles already passed; the other tests reproduced
raw-value corruption in titles, identity labels, paths and exception details.
The owner explicitly approved exactly two opt-in guards in app/language.py:
`mastixaI18nSkipWindowTitle` and `mastixaI18nSkipTitle`. No other behavior in that
module changed. app/localized_messages.py remains unchanged. Unmarked window and
QGroupBox titles still translate normally.

Implementation: existing _text/_message translate complete owned templates before
interpolating raw values. Persistent labels use explicit owner-local template
state and language refresh; QLabel values use PlainText and SkipText. Scoped
QGroupBox titles use SkipTitle; the version title uses SkipWindowTitle. No generic
table-body or selector behavior changed. Crop-program headings reuse the existing
page refresh connection rather than adding a redundant language callback.
Declaration's read-only QLineEdit is kept non-static for generic translation and
renders its saved base status plus the locked-year wrapper explicitly.

Completed owners:
- audit / field_finance: CSV success/error wrappers; CSV writer unchanged.
- upload_center: JSON/snapshot export wrappers, comparison labels/counts and
  valid/invalid integrity status; raw payload keys/values, hashes and IDs preserved.
- invoice_documents: rejected filenames, ZIP success/errors and OCR suggestion
  label composed from owned templates with opaque supplier/date/amount values;
  form locked/edit/new titles protected. Unfinished-action gating unchanged.
- dashboard: farm subtitle, backup status/filename/counts, backup/restore paths.
- settings: profile state/database path; create/import/export/archive/activate
  names and paths; profile errors and backup-folder errors; empty-selection reset.
- version_integration: canonical app/version wrapper plus opaque profile name.
  This wrapper is language-neutral and stays exact through EL/EN/EL.
- field_profile: identity/location/KAEK/area/tree values, including clear/reselect.
- crop_programs: complete program-heading template and protected raw program name.
- sales: insufficient-stock product/quantity warning, with unchanged validation.
- fields: deletion exception; main_window: profile-switch errors and rollback.
- update_integration: installed/current/new/download-ready status and confirmation;
  raw release notes/version/errors preserved. Internal failure signal accepts a
  template/detail pair so worker failures need no translation after composition.
  Network/download/install calls, decisions and default buttons are unchanged.
- locked headings: activities, inventory, labor, income/expenses, plantings,
  production, sales and declaration; edit-state controls remain unchanged.
  Audit naming differed: plantings uses load_record(), not load_batch(), at HEAD.
- year_context_ui: next-year confirmation and already-locked next-year warning;
  the closed temporary-correction implementation remains unchanged.

Catalog: 67 missing exact entries in en_phase16j_composed_ui.json; existing exact
static/enum translations reused. All existing catalogs were searched first.
Validation covers nonempty English, JSON, braces, placeholder/conversion/specifier
parity and absence of conflicting exact keys or Greek in English values. No
unrelated catalog conflict cleanup.

Evidence: adversarial raw Greek catalog words, English words, braces, markup-like
text, names equal to Παραγωγή, Windows paths, exception strings, filenames, hashes,
OCR supplier/date/amount values and JSON comparison data remain exact. Live
EL -> EN -> EL includes repeated generic translation passes and an actual modal
exec/event-loop test. Language switches reject Database.execute and compare
logical database snapshots. Repeated settings/crop refreshes retain single owned
callback behavior. Record headings preserve identities, row source dictionaries,
edit controls and years. Profile cancellation preserves state; failure restores
old profile identity. Existing profile archive/export/import contracts pass.

Year locking: cancelling the initial lock confirmation leaves DB unchanged.
Declining the subsequent next-year prompt preserves the already-approved lock
and keeps the active year unchanged; it does not undo that lock. Accepting advances
only when the next year is unlocked. The already-locked warning preserves that
state. Live switching inside either modal leaves its DB snapshot unchanged.
Yes/No/default semantics are checked explicitly.

File invariants: actual CSV rows/encoding and JSON/snapshot bytes checked; selected
paths and profile-operation arguments remain exact. Invoice export destination,
IDs and returned bytes remain unchanged, with build_export_zip AST unchanged.
Source comparison confirms unchanged SQL/database-call ASTs, all existing
QFileDialog argument ASTs, generated-body helpers, ZIP builder, OCR extraction,
payload hashing and snapshot-integrity functions across all 22 production files.

Verification used installed Python 3.14, PYTHONUTF8=1, QT_QPA_PLATFORM=offscreen:

```powershell
python -B -m unittest tests.test_phase16j_composed_ui_localization -q
```

Final **33 PASS / 0 FAIL / 0 ERROR**, 12.824s, exit 0.

```powershell
python -B -m unittest tests.test_phase16j_file_dialog_localization tests.test_profiles tests.test_alpha2_updates tests.test_crop_program_ui tests.test_phase16j_backup_localization tests.test_phase16j_year_correction tests.test_phase16j_generated_tables_localization -q
```

**88 PASS / 0 FAIL / 0 ERROR**, 26.783s. Three old file-dialog test mocks initially
intercepted QMessageBox.information instead of the now-used _message boundary.
Only those mock targets were updated; every path/payload assertion is unchanged.
Real protected dialog behavior is covered by the new tests.

```powershell
python -B -m unittest tests.test_phase16j_composed_ui_localization tests.test_phase16j_localization tests.test_crop_program_ui -q
```

**45 PASS / 0 FAIL / 0 ERROR**, 14.746s (31 new at that point, 5 existing controller
contracts and 9 crop-program tests). Two additional new tests and strengthened
assertions are included in the final 33-test run above.

```powershell
python -B -m unittest tests.test_alpha2_step3_year_context.Alpha2Step3YearContextTest.test_locking_active_year_can_advance_to_next_working_year -v
```

**1 PASS / 0 FAIL / 0 ERROR**, 0.822s.

```powershell
python -B -m unittest tests.test_stabilization.StabilizationTests.test_sale_creates_updates_and_deletes_exactly_one_income tests.test_stabilization.StabilizationTests.test_year_lock_schema_and_state tests.test_stabilization.StabilizationTests.test_all_modules_import_and_all_pages_refresh tests.test_alpha2_step5_ui.Alpha2Step5UiTest.test_invoice_documents_page_hides_all_unfinished_actions -q
```

The three stabilization checks passed; the final selector above had a singular
class-name typo (one loader error, not a runtime failure). Corrected selector:

```powershell
python -B -m unittest tests.test_phase16j_composed_ui_localization tests.test_alpha2_step5_ui.Alpha2Step5UiTests.test_invoice_documents_page_hides_all_unfinished_actions -q
```

**34 PASS / 0 FAIL / 0 ERROR**, 13.215s (33 new + invoice gating). Across final
coverage: **131 distinct passing tests**, 33 new + 98 existing. Counts are from
multiple focused runs, not one full-suite invocation. Expected failure-injection
logs include profile-switch/backup errors; no unresolved test failures remain.
No complete desktop suite or Android tests were run.

`git diff --check`: PASS; new catalog/test whitespace checks PASS. Git only notes
normal LF-to-CRLF conversion. Production files: activities, audit, crop_programs,
dashboard, declaration, field_finance, field_profile, fields, inventory,
invoice_documents, labor, language, main_window, money, plantings, production,
sales, settings, update_integration, upload_center, version_integration and
year_context_ui. Also changed: this ledger and three mock targets in
 tests/test_phase16j_file_dialog_localization.py; new scoped catalog/test module.

Phase16J localization remains PARTIAL. Remaining remediation boundaries:
1. Android report movement-type display.
2. Android dashboard product-name protection.

Stopped without commit/push, Android work, scaling/accessibility work or final
closure audit.
