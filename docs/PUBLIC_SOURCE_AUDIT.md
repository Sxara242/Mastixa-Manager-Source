# Public source audit — 2026-10-09

**Development-source publication audits PASS; rc.2 binary release remains blocked.**

This page records the initial published development baseline `d98f041`.
Subsequent public fixes and current validation are tracked in
[PHASE5_WINDOWS_BLOCKERS.md](PHASE5_WINDOWS_BLOCKERS.md).

Scope: RELEASE-INFRA / SHARED documentation and CI, with DESKTOP and ANDROID verification.
Windows x64 is the current release target. Android remains in development.

| Check | Result | Evidence and limit |
| --- | --- | --- |
| First-party license | PASS | Full AGPL version 3 text matches the upstream SPDX mirror after surrounding whitespace normalization; version choice is AGPL-3.0-only |
| Rights baseline | PASS owner attestation | Owner confirmed both historic identities and first-party authority; third-party material excluded; external merge intake closed pending written rights grants |
| Secret/privacy audit | PASS bounded checks | Source path/pattern/hash review plus Gitleaks 8.30.1 with archive/decode inspection; signed public download URLs removed, real local paths sanitized |
| Third-party texts and Windows preflight | PASS | Inherited license texts retained byte-for-byte; Gradle original source-wrapper license added; EPSG/PROJ notices, source/replacement, CRT/TLS/Mesa safeguards preserved |
| Workflow validation | PASS static | Four workflows pass actionlint 1.7.12; actual hosted runner execution will be verified after the authorized development-source push |
| Android development build/lint | PASS local Windows SDK/cache | Debug APK and instrumentation APK compilation/lint pass; JVM unit task has no sources; emulator/actual upgrade and Android release notice delivery remain pending |
| Windows packaging/legal tests | PASS | 78 tests, including real smoke-runner failure paths and legal/native safety contracts |
| Full Windows source corpus | BLOCKED | 123/133 modules PASS; 9 FAIL; 1 TIMEOUT; 970 completed test cases, including failed cases |
| Existing rc.1 binaries | PASS hash preservation | Retained EXE/setup hashes match; owner acceptance found defects and requires rc.2 |
| Current rc.2 binary readiness | BLOCKED | No rc.2 build/frozen/installer/owner acceptance; qualified public supplier bootstrap and final matching source delivery remain pending |
| Original checkout preservation | PASS | Both HEAD/status/file maps unchanged: 515 protected files and 1,005 approved-worktree files verified |

## Exact Windows source/test blockers

| Module | Result | Failed cases |
| --- | --- | --- |
| `tests.test_batch5_ui` | FAIL | `test_product_unit_requires_explicit_choice (tests.test_batch5_ui.Batch5UiTests.test_product_unit_requires_explicit_choice)
` |
| `tests.test_money_sort_localization` | FAIL | `test_expenses_english_startup (tests.test_money_sort_localization.MoneySortLocalizationTests.test_expenses_english_startup) (kind='expenses', language='en')
`<br>`test_expenses_live_language_cycle_preserves_sort_and_data (tests.test_money_sort_localization.MoneySortLocalizationTests.test_expenses_live_language_cycle_preserves_sort_and_data) (kind='expenses', language='el')
`<br>`test_expenses_live_language_cycle_preserves_sort_and_data (tests.test_money_sort_localization.MoneySortLocalizationTests.test_expenses_live_language_cycle_preserves_sort_and_data) (kind='expenses', language='en')
`<br>`test_expenses_live_language_cycle_preserves_sort_and_data (tests.test_money_sort_localization.MoneySortLocalizationTests.test_expenses_live_language_cycle_preserves_sort_and_data) (kind='expenses', language='el')
`<br>`test_expenses_live_language_cycle_preserves_sort_and_data (tests.test_money_sort_localization.MoneySortLocalizationTests.test_expenses_live_language_cycle_preserves_sort_and_data) (kind='expenses', language='en')
`<br>`test_income_english_startup (tests.test_money_sort_localization.MoneySortLocalizationTests.test_income_english_startup) (kind='income', language='en')
`<br>`test_income_live_language_cycle_preserves_sort_and_data (tests.test_money_sort_localization.MoneySortLocalizationTests.test_income_live_language_cycle_preserves_sort_and_data) (kind='income', language='el')
`<br>`test_income_live_language_cycle_preserves_sort_and_data (tests.test_money_sort_localization.MoneySortLocalizationTests.test_income_live_language_cycle_preserves_sort_and_data) (kind='income', language='en')
`<br>`test_income_live_language_cycle_preserves_sort_and_data (tests.test_money_sort_localization.MoneySortLocalizationTests.test_income_live_language_cycle_preserves_sort_and_data) (kind='income', language='el')
`<br>`test_income_live_language_cycle_preserves_sort_and_data (tests.test_money_sort_localization.MoneySortLocalizationTests.test_income_live_language_cycle_preserves_sort_and_data) (kind='income', language='en')
` |
| `tests.test_owner_ui_acceptance` | FAIL | `test_constrained_tables_keep_long_values_accessible (tests.test_owner_ui_acceptance.OwnerUiAcceptanceTests.test_constrained_tables_keep_long_values_accessible) (key='annual_report')
` |
| `tests.test_phase16j_accessibility_focus` | FAIL | `test_dark_theme_overrides_focus_ring_without_duplicate_theme_pass (tests.test_phase16j_accessibility_focus.FocusAccessibilityTests.test_dark_theme_overrides_focus_ring_without_duplicate_theme_pass)
`<br>`test_light_theme_has_visible_focus_for_common_keyboard_controls (tests.test_phase16j_accessibility_focus.FocusAccessibilityTests.test_light_theme_has_visible_focus_for_common_keyboard_controls)
` |
| `tests.test_phase16j_annual_localization` | FAIL | `test_csv_product_and_numeric_values_preserved (tests.test_phase16j_annual_localization.AnnualLocalizationTests.test_csv_product_and_numeric_values_preserved)
`<br>`test_numeric_report_identity_and_database_preserved (tests.test_phase16j_annual_localization.AnnualLocalizationTests.test_numeric_report_identity_and_database_preserved)
` |
| `tests.test_phase16j_coordinate_ui` | FAIL | `test_dynamic_selection_mode_and_failure_messages_follow_language (tests.test_phase16j_coordinate_ui.CoordinateLocalizationTests.test_dynamic_selection_mode_and_failure_messages_follow_language)
` |
| `tests.test_phase16j_file_dialog_localization` | FAIL | `test_arguments_annual_report_export_csv (tests.test_phase16j_file_dialog_localization.FileDialogTests.test_arguments_annual_report_export_csv) (language='el')
`<br>`test_arguments_annual_report_export_csv (tests.test_phase16j_file_dialog_localization.FileDialogTests.test_arguments_annual_report_export_csv) (language='en')
`<br>`test_arguments_annual_report_export_csv (tests.test_phase16j_file_dialog_localization.FileDialogTests.test_arguments_annual_report_export_csv) (language='el')
` |
| `tests.test_phase16j_generated_tables_localization` | FAIL | `test_money (tests.test_phase16j_generated_tables_localization.GeneratedBodyTests.test_money) (language='el')
`<br>`test_money (tests.test_phase16j_generated_tables_localization.GeneratedBodyTests.test_money) (language='en')
`<br>`test_money (tests.test_phase16j_generated_tables_localization.GeneratedBodyTests.test_money) (language='el')
`<br>`test_crop_task_state_category_count_and_navigation_data (tests.test_phase16j_generated_tables_localization.GeneratedBodyTests.test_crop_task_state_category_count_and_navigation_data)
`<br>`test_money_search_stays_canonical (tests.test_phase16j_generated_tables_localization.GeneratedBodyTests.test_money_search_stays_canonical)
` |
| `tests.test_phase16j_static_selectors_localization` | FAIL | `test_equipment_reminder_filter (tests.test_phase16j_static_selectors_localization.StaticSelectorTests.test_equipment_reminder_filter) (language='el')
`<br>`test_equipment_reminder_filter (tests.test_phase16j_static_selectors_localization.StaticSelectorTests.test_equipment_reminder_filter) (language='en')
`<br>`test_equipment_reminder_filter (tests.test_phase16j_static_selectors_localization.StaticSelectorTests.test_equipment_reminder_filter) (language='el')
`<br>`test_equipment_reminder_filter (tests.test_phase16j_static_selectors_localization.StaticSelectorTests.test_equipment_reminder_filter) (language='el')
`<br>`test_equipment_reminder_filter (tests.test_phase16j_static_selectors_localization.StaticSelectorTests.test_equipment_reminder_filter) (language='en')
`<br>`test_equipment_reminder_filter (tests.test_phase16j_static_selectors_localization.StaticSelectorTests.test_equipment_reminder_filter) (language='el')
` |
| `tests.test_stabilization` | TIMEOUT | 120-second bound at `test_production_stock_rejects_reduction_below_sales`; incomplete module |

These results require source/test reconciliation. They are not automatically classified as product defects or waived as stale tests. A fresh money-localization process reproduced its failure. No application behavior was changed to hide failures.
The long-lived discovery run stalled while Qt callbacks accessed deleted fixture databases. The final runner uses a new temporary profile/process per module, executes both unittest classes and plain functions, and fails on any failure, empty module or timeout.

## Prepared changes

- Full first-party LICENSE plus replacement LICENSE.md, NOTICE.md and SOURCE_AVAILABLE.md; no old noncommercial condition is applied to this new snapshot.
- README, installation/building/release status, contribution policy and owner-rights ledger; Android explicitly remains in development.
- Four hosted-runner workflows, source/Gitleaks checks, bounded Windows test runner, Android build/lint and manual instrumentation; no routine installers or uploads; manual debug APK retention is one day.
- Private local paths, three signed public-download URLs and private CI links sanitized in the public copy; private originals retained.
- Gradle original license and verified wrapper/distribution checksums; development-only Pillow requirement; private/signing/data ignore rules strengthened.
- Two map user-agent repository references now identify the public source repository. Other first-party application behavior is unchanged.

## Publication and binary boundaries

The clean export/ZIP includes no Git metadata, private history, profiles, production databases, logs, signing keys, supplier binaries, candidate EXEs/APKs or generated build caches. Reviewed synthetic CSV-export ZIPs, OCR models and the original Gradle wrapper are intentional source inputs, indexed by SHA-256.
Archive/per-file hashes and the exact added/modified/removed public-file inventory are retained outside the source snapshot. The public-only review clone retains only existing public history; the private repositories were not committed, pushed or modified.
The owner explicitly authorizes this development-source publication before Windows source blocker closure. The nine failing modules and stabilization timeout must be diagnosed and resolved from the public repository in Phase 5 before rc.2 is built. Hosted CI follows the source push; it has not been claimed green. A binary release additionally needs rc.2 qualification, owner acceptance and final artifact/source/SBOM binding with durable matching covered-source access. Android needs its own complete release-rights/notice/native audit.
See [PUBLICATION_PLAN.md](PUBLICATION_PLAN.md), [RELEASE_STATUS.md](RELEASE_STATUS.md), [LICENSING.md](LICENSING.md) and [CONTRIBUTION_RIGHTS.md](CONTRIBUTION_RIGHTS.md).

Secret scanners and owner attestations have bounded scope; no assertion of exhaustive secret absence or independent copyright adjudication is made.

Inherited legal formatting is preserved exactly; `.gitattributes` disables normalization for LICENSE and licenses/. First-party historical Markdown whitespace was cleaned while retaining intended line breaks.
