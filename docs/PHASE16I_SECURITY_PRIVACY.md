# Phase 16I — final security/privacy review checkpoint

Date: 2026-09-13. Baseline `4b63e4d`, clean branch refactor/pages, CI #143
200 Desktop tests + Android build/lint/compile green. Previous general audit and
release/update/offline/CSV gates were not repeated. No schema/Android application/
manifest/packaging/signing changes. Phase16J NOT started.

## Permanent project policy

Fieltra does not contain and will not add telemetry, analytics, advertising,
user tracking, behavioral profiling or silent diagnostics uploads. This includes
anonymous/opt-out/default-disabled variants, marketing identifiers, cloud crash
reporting and diagnostic upload SDKs. This is a permanent design constraint, not
only a release criterion. GPS track recording and plant tracking are explicit
agricultural features, not user behavioral tracking.

Diagnostics remain local, bounded and user-controlled via the log folder; no
automatic submission exists. Any future support report must be a user-initiated
manual export: the user chooses creation, destination and whether to send it.
Core data ownership/access cannot depend on a remote account or kill switch.
Cloud must remain optional and require informed user initiation.

For inspected first-party source/config and resolved SDK graph:
telemetry=NONE; analytics=NONE; tracking=NONE; advertising=NONE;
automatic diagnostic upload=NONE. This statement is scoped evidence, not an
unsupported certification of all native/transitive binaries or the user's OS.

## Findings / reproduction / fixes

1. **High — unbounded profile archive resources / ambiguous members.** Imported
   profile.db/avatar streamed without ceilings; duplicate names silently selected
   ZIP's winning entry. Focused small fixtures with reduced thresholds proved
   missing guards; no giant bomb or real data used. Limits: database 2 GiB,
   avatar 20 MiB, manifest 64 KiB, total their sum; archive compressed size at most
   total + 1 MiB; 2–3 exact permitted members; compression ratio at most 1000:1
   above 1 MiB/member; actual streamed bytes bounded as well as metadata.
   Store/Deflate only; reject duplicate/case-conflicting names, symlink/special
   entries, encryption and unknown member paths. No traversal overwrite was
   demonstrated in the old implementation: arbitrary entries were ignored and
   selected members already went to generated private destinations. Rejection
   is defense in depth, not a fabricated traversal vulnerability. Oversize valid
   profiles require a supported smaller package or separately managed SQLite
   backup; no user data is truncated. Commits `5f6b72f`, `894394a`.
2. **Medium — sensitive exception logging.** A ValueError containing synthetic
   KAEK/token/geometry appeared verbatim in formatted logs. Default main exception
   hook also printed raw values. Formatter now keeps exception type and source
   filename/function/line, omits values/source lines/locals/chained messages and
   stack text, discards other formatter's cached exception text on a record copy.
   Console fallback is generic. Existing safe event messages/counts remain.
   Commits `528b1d8`, `37ec7b2` (windowed/no-stderr compatibility). Arbitrary future log message arguments must still be reviewed;
   this is not automatic detection of all possible sensitive business strings.
3. **Medium — environment-enabled implicit PROJ network capability.** With
   PROJ_NETWORK=ON, a created app transformer had network enabled without an app
   opt-in. No actual external request was needed for reproduction. Explicit
   network.set_network_enabled(False) before transformer creation overrides this;
   environments missing required local grids now fail instead of downloading.
   EPSG reference results/tolerances unchanged. Commit `33a02c5`.

## Targeted evidence

- Initial security characterization: expected failures for missing limits,
  duplicate/special members and leaking exception values; safe valid profile passed.
  The initially missing stream helper was a missing-guard characterization, not
  an end-user crash reproduction.
- Final `tests.test_phase16i_security`: **10/10 PASS** (1.812s), covers name variants,
  duplicates, symlinks, individual/total/ratio/count limits, streamed bytes,
  malformed nested manifest, corrupt DB cleanup, compression policy and valid import.
- Directly affected `tests.test_profiles`: **5/5 PASS**, run with initial archive
  regressions (12/12 combined at that point); subsequent valid-import guard passed.
- `tests.test_diagnostic_privacy`: **4/4 PASS** (includes windowed/no-stderr hook), plus existing diagnostic formatter
  path-redaction test **1/1 PASS**.
- `tests.test_network_privacy`: failed before fix, **1/1 PASS** afterwards with
  environment ON and no real network traffic; relevant `tests.test_crs_reference`
  **2/2 PASS**. Last combined network/CRS/logging run **7/7 PASS** (0.717s).
- Total distinct focused evidence: **23/23 PASS**; not a single 23-test invocation.
- Android resolved runtime dependency graph read successfully; not a test/build.
- The code checkpoint required fresh normal CI; that requirement is now satisfied
  by #144 below. No release/update gate required: packaging and Android code unchanged.

Continuation evidence: CI #144 (`34719309041`) completed SUCCESS for both jobs
on `bcedfeea02bb40bfa9032427127ec1cbf1a16aaa`, confirmed by read-only GitHub
query. No run was restarted. The native/license continuation below is docs-only
and does not invalidate those results or the retained 23 focused tests.

## Other inspected boundaries

Read import/export/restore/profile/logging/GIS/network code; Android manifest,
FarmStore/ProfileStore/UserSession/OfflineOcr/DocumentStore/LocalBackup and relevant
Activity checks; runtime paths, installer/spec/privacy gate and four workflows.
SQL scan: identifiers in reviewed dynamic SQL derive from internal tables/maps;
values parameterized; no user-controlled ATTACH or extension loading found.
Imported SQLite contents remain untrusted and resource/malicious-engine behavior
is not exhaustively fuzzed. Profile paths generated locally; canonical path guards
and escaped read-only SQLite URIs retained. GIS XML uses defusedxml; geometry
archives bounded; Android document streams 5 MiB, backups 50 MiB, ZIP imports bounded.

Android: only INTERNET/network-state, fine/coarse location, notification and boot
permissions. No READ/WRITE/MANAGE_EXTERNAL_STORAGE. allowBackup=false; no exported
service/provider; nonexported notification receiver/map/export/Main; launcher and
plant/sensor shortcuts exported with session/profile checks. Debug artifact is
not a signed production release. Storage contract already verified, unchanged.
SAF provider controls chosen content URI; MIME alone not relied upon for geometry/
backup payload validation. Arbitrary provider implementation and OS diagnostics
remain external. Private cache/files/SQLite used; user-selected exports can leave
device via a provider/share deliberately. No automatic log/diagnostic upload found.

Tracked artifact/key-pattern scan: no DB/APK/AAB/local.properties/private keystore
or recognizable private-key/GitHub/AWS/JWT credentials found; values never printed.
Placeholders/public URLs and synthetic test values are not secrets. This is not
an exhaustive historical secret scan. GitHub repo confirmed PRIVATE; workflows
contents:read, explicit artifact outputs. Self-hosted PR trust and repository
collaborator permissions remain an operational boundary; re-review before public
fork workflows. No runner/security settings changed. Windows privacy gate retains
only intended source/assets and pyproj proj.db exception; no rebuild performed.

## Inventories

- [Network Call Inventory](PHASE16I_NETWORK_INVENTORY.md)
- [Third-Party Privacy Inventory](PHASE16I_THIRD_PARTY_PRIVACY.md)
- [License / Distribution Readiness](PHASE16I_LICENSE_READINESS.md)

## Native / transitive privacy assurance — continuation

The focused continuation inspected installed wheel metadata, 173 PE files from
the existing Phase8 Windows bundle, cached Android class/native inputs and the
existing current-head runner APK. All 16 APK native members match the inspected
AAR. Pinned source explains Leptonica's debug-gated command capability and Qt's
optional TUIO listener. Supporting proxy/TLS and external printing capabilities
are now distinguished from the application's OSM request path in the inventory.
No newly demonstrated automatic upload or telemetry activation required a fix.
Whole-native-binary behavior/provenance remains UNVERIFIED; absence of selected
imports/SDK markers is supporting evidence, not a universal proof.

## License / distribution readiness — continuation

The license inventory and four owner-selectable routes are documented separately.
Concrete issues are GPLv3/commercial VirtualKeyboard in existing Windows packages,
incomplete delivered third-party notices, no chosen project license, and missing
asset/platform redistribution provenance. These are release-readiness blockers;
they are not proof of an exploited vulnerability or malicious dependency.
No license, binary or packaging configuration was changed. Exact current Windows
release membership and final legal compatibility are UNVERIFIED.

## FUTO-ALIGNMENT REVIEW

These are project evidence assessments, never FUTO approval.

| Principle | Status | Evidence / limit |
|---|---|---|
| User ownership | PASS | Local SQLite, profile export/backup/restore; no server access requirement. |
| Local-first | PASS | Local stores, bundled OCR, retained offline evidence, no cloud login prerequisite. |
| Cloud optional | PASS locally / UNVERIFIED live | No configured cloud transport/account; any future RLS needs real backend verification. |
| No user-as-product model | PASS in implementation | No advertising/data-broker/analytics integration found; cannot certify future organizational behavior. |
| No dark patterns | PARTIAL | Local defaults/export/settings inspected, not a complete independent UX evaluation. |
| Minimum permissions | PASS scoped | Actual manifest permissions mapped above; unchanged storage contract. |
| Open/auditable architecture | PARTIAL | Source in private repo; license options now compared, but no owner decision/public fork grant yet. Notices and GPL-only package membership need resolution. |
| No remote control of local data | PASS | No kill-switch/remote entitlement code path found. |
| Portability | PASS scoped | SQLite/profile/CSV/GeoJSON/coordinate exports; existing round-trip evidence retained, feature asymmetries documented. |
| Network transparency | PARTIAL | Native import/source inspection extends the inventory; PROJ boundary remains PASS. Proxy/OS behavior and complete binary provenance UNVERIFIED. |
| Data minimization | PASS scoped | No marketing/session analytics profiles; agricultural and auth data serve user features. |
| User-initiated external actions | PASS scoped | OSM selected by user, SAF/files destinations chosen; configured network backup destinations are user-controlled. |
| No telemetry forever | Policy ADOPTED / implementation PARTIAL assurance | No first-party telemetry or SDK found; permanent prohibition documented. Full transitive/native assurance UNVERIFIED. |

## Residual risks / closure decision

Review and proven local fixes are complete for this checkpoint; **official Phase
16I status: PARTIAL**, not a blanket security certification. No unresolved
reproduced local vulnerability remains. Formal closure/public release still needs:

- exact final shipped artifact/license matching, especially Windows (older
  packages were inspected); theoretical inability to prove every native byte
  is not by itself an acceptance blocker;
- owner's root-license decision; resolve Qt VirtualKeyboard's GPLv3/commercial
  route, deliver complete third-party notices/source access, and confirm asset
  and platform redistribution rights. Focused compatibility review is done;
  distribution obligations are not yet fulfilled. No license changed here;
- release signing/production-artifact review separately (no key generated);
- live Supabase/RLS only if cloud integration is enabled; otherwise explicitly
  excluded, not falsely PASS; OS/provider network behavior stays external;
- full device/ACL/host compromise, power-loss and malicious-native-parser/fuzz
  coverage remain UNVERIFIED, not findings of successful exploitation.

**PHASE 16I STATUS = PARTIAL. PROJECT LICENSE DECISION = DEFERRED BY OWNER.**
The owner will decide after possible FUTO collaboration/support interest becomes
clear; this is not a technical security failure. The later explicit instruction
authorizes Phase16J after this documentation checkpoint is committed/pushed.
Public-release blockers remain recorded in MASTER_PROGRESS.md and the license
readiness report. Suitable as a privacy-first/FUTO-alignment review candidate with
disclosed gaps, not FUTO approved. No license was selected or added.
