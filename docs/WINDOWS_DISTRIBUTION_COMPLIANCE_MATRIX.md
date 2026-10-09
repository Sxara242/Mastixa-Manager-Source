> Retained historical engineering record, sanitized for public review.
> Current status: [RELEASE_STATUS.md](RELEASE_STATUS.md). This record does not
> establish approval of the current source or a new binary release. Local-only
> receipt paths refer to privately retained evidence, absent from this snapshot.

# EPSG remediation implemented — 2026-10-08

RELEASE-INFRA / DESKTOP. **EPSG PASS; B3 PASS** for the documented scoped
clause6(vii) attribution assessment. B1/B2/B4/B5 legal PASS retained, B1 audit/B4
repro INCOMPLETE non-blocking; IGNF/IAU PASS retained, LT2008 forensic-only.
Older BLOCKED/unchanged-database sections below are historical supplier checkpoints.

Path A (external notices alone): INSUFFICIENT. Path B selected: hash-locked
metadata-only derived shipping database. Operations1312/1462 retain internal
accuracy2.0m and their genuine EPSG source references, with direct WKT REMARK /
PROJJSON remarks explicitly attributing that field to PROJ and distinguishing
imported EPSG v12.029 accuracy1.0m. Operation7001 similarly marks the PROJ-added
interpolation association while retaining genuine EPSG4289. Unofficial900913
moves to PROJ authority with its usage reference and explicit unofficial name;
Mastixa historical inputs canonicalize to official EPSG3857. Native EPSG900913
lookup deliberately rejects the nonofficial code; PROJ900913 remains equivalent.

Original supplier proj.db remains byte-unchanged. The build-work derived copy is
pinned to590adc683437a59896e8841255129b572b082008eebf1c0d5225e6c5e207c064.
Accuracy, grids, interpolation context, operation parameters and native code
remain unchanged; scoped operation selection matches. Analysis/output guards
reject unmarked, unknown, duplicate or relocated databases. Complete EPSG terms,
IOGP ownership/no-warranty remain selected; existing Settings legal link delivers
the updated notices. No unrelated footer/UI/Android change.

This is a supported terms-based release assessment, not IOGP approval or an
infringement determination. See WINDOWS_EPSG_REMEDIATION.md for candidate
classifications, representation evidence, compatibility distinction and limits.
Final preflight and publish-safety results: current CODEX_HANDOFF.md and local
WindowsEpsgRemediationEvidence/final-report.json. No RC/artifact exists or was built.

---

# Final EPSG6(vii) downstream decision — 2026-10-08

**BLOCKED BEFORE RC BUILD. EPSG BLOCKED; B3 BLOCKED.** RELEASE-INFRA / DESKTOP.
B1/B2/B4/B5 legal PASS retained; B1 audit/B4 repro remain INCOMPLETE and
non-blocking. IGNF/IAU PASS, LT2008 forensic-only and all other settled topics
are retained. This decision supersedes historical broader blocker statements.

The current official terms were retrieved successfully and match the retained
2016 revision. Clause6(vii) prohibits attributing non-permitted modifications to
the EPSG Dataset; it does not expressly ban all EPSG identifiers or prescribe an
auth_name replacement. Direct PROJ serialization now confirms accuracy2.0 with
EPSG IDs1312/1462 and no override notice in the remarks. Their maintainer change
is exactly traced to Even Rouault's2019-12-25 commitb8f8a708: ranking workaround
to prefer NTv2 over NTv1, whose imported EPSG accuracy is1.0. It is not a Table1
parameter-equivalence edit. Unchanged downstream copying does not waive6(vii).
7001 is interpolation-context enrichment (2019-05-06);900913 is an unofficial
deprecated PROJ compatibility alias of3857, not an EPSG-issued deprecated code.
These are separate cases, not additional generic blockers or infringement findings.

No rule requiring every-row inspection, private logs or supplier approval letters
was found. A specific attribution problem still needs resolution. A generic
not-the-official-dataset notice does not establish separation in these known
EPSG-ID exports. A field-specific candidate notice and two-accuracy restoration
alternative are documented, without asserting either as an approved unchanged-
database cure or applying any data modification. Existing full terms/IOGP credit/
disclaimer/notices and the Settings legal link remain intact; no UI change.

Detailed clause/record/downstream analysis and exact next decision:
[WINDOWS_EPSG_FINAL_INTERPRETATION.md](WINDOWS_EPSG_FINAL_INTERPRETATION.md).
Evidence: sibling WindowsEpsgFinalInterpretationEvidence, final-report.json.
Final preflight **NOT RUN: B3 BLOCKED**. RC may be built **NO**.
No RC, commit, push, tag, publication, upload or automatic deletion.

---

# Final narrow B3 decision — 2026-10-08

**BLOCKED BEFORE RC BUILD.** RELEASE-INFRA / DESKTOP. Current decision supersedes
the older three-topic blocker wording below. B1/B2/B4/B5 legal PASS retained;
B1 audit and B4 reproduction remain INCOMPLETE and non-blocking. B3 remains
BLOCKED solely on the named EPSG adaptation-attribution condition.

| B3 Topic | Status | Legal basis | RC blocking? |
| --- | --- | --- | --- |
| IGNF3.1.0 | PASS | French CRPA statutory public-information/database reuse; source/date/meaning preservation; inherited EPSG terms separately retained | no |
| IAU | PASS | Present LGPLv3 grant for the exactly matching consolidated collection; covered source/credits/terms retained; independent factual scientific parameters, not a paper reprint or government-work claim | no |
| EPSG | BLOCKED | Redistribution/notices basis established; clause6(vii) attribution for upstream accuracy/authority modifications remains material | yes |

Final pre-RC preflight: **NOT RUN**, because B3 is BLOCKED. RC may be built: **NO**.
The unchanged shipping proj.db SHA256 is528b9763b57e85ee78f6f30478ef0494902320f1d71d1564bf0d7ec4f30cc002.
Full earlier39-table/77707-row evidence and B2/B5 qualification are retained.
Only two authority subsets and the named EPSG records were queried read-only.
No full inventory/functional audit/source snapshot/native qualification was rerun.

The IAU NOTICE is now a selected recipient input; exact collection CSV, LGPL
license and AUTHORS are source-only inputs. Current source/legal hashes and
SBOM metadata are reconciled in the bounded delta supplement. Original source
base and all prior supplements remain immutable. Actual artifact/source access,
output notices/privacy and functional checks remain mandatory after a later build.

Legal detail and exact table/row/source map: WINDOWS_B3_LEGAL_CLOSURE.md,
windows-b3-legal-closure.json and sibling WindowsB3FinalEvidence/topic-map.json.
Publish-safety and preservation results: sibling WindowsB3FinalEvidence/final-report.json.

Forensic-only gaps: historical IGNF license page; IAU pre2022 license/correction
lineage; retained LT2008 causal history, B1 private producer correspondence and
B4 bit-identical reproduction. None independently blocks RC.

Exact next step: resolve EPSG clause6(vii) for operations1312/1462 accuracy and
authority attribution900913/7001, through applicable primary interpretation or
a qualified non-attribution remedy preserving CRS behavior. Then B3 and eligible
preflight; no database modification, RC build or external message in this batch.

Future Bitdefender rule retained: temporary Administrator PowerShell solely for
supported exclusion management of the exact actual PyInstaller/Inno build/work/
output directory; never create/rename PROSORINA, exclude repository/profile/drive,
disable protection globally or use undocumented registry hacks. Record the path,
remove exclusion after build and validation and verify removal. If manual action
is necessary, STOP before build, present the exact path and wait indefinitely for
explicit owner OK/Done/Continue; no countdown, timeout or automatic continuation.

All inherited dirty work is preserved; no commit/push/tag/publication/upload/RC.

---

# Final B3 legal closure and RC gate reclassification — 2026-10-08

**BLOCKED BEFORE RC BUILD.** RELEASE-INFRA / DESKTOP. This is the current
decision; contrary B1/B4/CI/LT gate wording below is historical and superseded.

| Gate | Legal status | Audit/Repro status | RC blocking? | Remaining action |
| --- | --- | --- | --- | --- |
| B1 | PASS | INCOMPLETE | no | Optional exact QtPdf producer/config/private CI/output correspondence |
| B2 | PASS RETAINED | COMPLETE | no | none |
| B3 | BLOCKED | INCOMPLETE | yes | IGNF3.1.0 collection rights; IAU2015 collection reuse; EPSG attributed metadata adaptations |
| B4 | PASS | INCOMPLETE | no | Optional full/bit-identical producer reproduction; mandatory final artifact/source access binding at later distribution |
| B5 | PASS RETAINED | COMPLETE | no | none |

B1-LEGAL and B4-LEGAL PASS are prebuild material/replacement decisions from
retained evidence. Required source/scripts, notices and replacement rights are
not waived. B1-AUDIT/B4-REPRO incompleteness cannot alone block RC. B3 still can.
Final pre-RC preflight **NOT RUN** because B3-LEGAL is BLOCKED. RC may be built:
**NO**. No RC, installer, commit, push, tag, publication or external upload.

LT2008:0.11549 ->0.115495, delta5 micrometres, upstream-only. PR2494 and public
review/history supply no causal explanation. No rounding/correction assertion.
CC-BY change indication/credit retained; exact causal history is audit-only.
IGNF ontology3.1/2019-02-13 Licence Ouverte is a distinct object from the shipped
IGNF registry3.1.0/2019-05-24, not a license substitution. ITRF2000/2008/2014
computed coefficients have a scoped factual-use/PROJ definition-file basis.
NKG inherited IERS/EUREF steps use EPSG7941/8366, not independently shipped
IERS/EPN datasets. IAU constants are facts, but the actual collection's reuse
basis remains unresolved. EPSG recipient terms/ownership/no-warranty are included;
permitted attributed upstream accuracy/interpolation metadata remains unresolved.

Details, evidence, limitations and issue classifications: WINDOWS_B3_LEGAL_CLOSURE.md
and windows-b3-legal-closure.json. Gate policy: WINDOWS_RELEASE_GATE_POLICY.md.
Only required legal/security gates drive packaging/windows-rc.json; audit scores
are informational. The guard fails closed on missing/non-PASS legal gates.
Retained B2/B5/runtime qualification and full functional audit are not rerun.

Next step: resolve only the three named B3 legal issues with applicable grants
or supported lawful-use/terms analysis; then eligible final preflight. Reusing
retained data/source evidence is required. No private CI hunting or full audit.
Future source/material delivery must bind to the actual authorized artifact and
provide equivalent freely accessible matching source alongside its distribution.

Future build Bitdefender rule: owner-authorized temporary Administrator PowerShell
access solely for documented exclusion management of the exact actual
PyInstaller/Inno build/work/output folder; never create/rename PROSORINA, exclude
repository/profile/drive, disable protection globally or use undocumented registry
hacks. Remove exclusion after artifact validation and verify removal. If manual,
STOP before build, show exact path and wait indefinitely for explicit owner
OK/Done/Continue; no countdown, timeout or automatic continuation.

---

# Upstream receipt and legal-requirement review — 2026-10-08

**BLOCKED BEFORE RC BUILD.** Current RELEASE-INFRA / DESKTOP checkpoint;
supersedes the stricter missing-CI wording in historical sections below.

| Gate | Status | Legal blocker? | Evidence | Remaining action |
| --- | --- | --- | --- | --- |
| B1 | BLOCKED | no | Matching release sources; published binding CI commands; exact OpenBLAS chain retained | Resolve requested QtPdf executed-feature/source correspondence by minimum supplier release/config alternative; output/job/compiler comparisons are audit-only |
| B2 | PASS RETAINED | no | Existing CRT/import/prerequisite receipts unchanged | none |
| B3 | BLOCKED | yes | Named provider inputs and full EPSG terms retained; current IGNF4.0.1 distinguished from shipping3.1.0 | Establish historical provider/inherited rights and EPSG permitted-attribution basis; explain LT2008 separately as reproducibility requirement |
| B4 | BLOCKED | no | GEOS3.13.1/Shapely2.1.2 source/build/job chain;42 binding build/coin scripts; retention manifest and recipient supplement | Requested exact producer correspondence inherits B1; final binary/source binding belongs to later authorized artifact batch |
| B5 | PASS RETAINED | no | Existing TLS3.5.9/Mesa qualification unchanged | none |

Here "no" means that possession of the unavailable CI/compiler/generated-output
receipt is not independently legally mandatory. It is not a declaration of
unconditional library or public-release clearance. Required corresponding source,
controlling scripts, notices and dynamic replacement remain mandatory. B1/B4
remain open against the owner's stronger exact-correspondence conditions. The
release decision is independently blocked by B3 rights/terms uncertainty, not
solely by internal CI-log unavailability. "yes" is unresolved rights/compliance
basis, not a finding of infringement. No perfect-provenance approval is invented.

New receipts: pinned Shapely commit5fb639d1056888d135fe56bfaf750c9648addeec,
GEOS source3.13.1, release run17978107042 / AMD64 job51136576633,
Windows2022/MSVC shared Release CMake/Ninja and delvewheel1.11.1 wheel loader.
No GEOS source patch command occurs in its pinned recipe. Public artifact list
is empty; exact environment/job-to-wheel digest remains audit-only. The existing
wheel/RECORD and B2 original-to-normalized GEOS hashes are retained without rerun.
The official PySide coin script supplies Windows Python3.10.0 and setup.py build
options;42 build/coin files are retained.18 deterministic outputs remain a limited
QtPrintSupport sample, not a producer-output comparison or full binding build.

GCC/Rtools: GNU10.3 source/exception and exact10.3.0-9804 tool/package receipts
remain retained. Exact9804 PKGBUILD/patch mapping and internal OpenBLAS object/job
logs were not publicly mapped. Build-compiler patches are not automatically
corresponding source for an application that does not redistribute that compiler;
the eligible GCC-exception combination does not create a separate runtime-source
delivery duty. Current R-project ucrt3/MXE is not falsely substituted for9804.

GNU GPL3 section1 permits omission of automatically regenerable outputs and
excludes general-purpose tools; the FSF FAQ explicitly rejects a same-hash binary
requirement. Keep necessary matching inputs/scripts. Exact CI logs, timestamps,
historical signing/compiler hashes and full publisher rebuild tests are optional
evidence. Source patches or non-regenerable build inputs actually necessary to
modify/build a covered library remain required; no such obligation is waived.

CRS: no data was changed. Current official IGNF XML is4.0.1/2026-03-23,
SHA d821b095346bbbb705d73c40f660730aafdb0f337bb3319395088509081537f5;
the retained3.1.0/2019 input SHA5c512412... is distinct. Current API access/website
policies are not a historical dataset grant. IERS official legal page supplies
a disclaimer, not a redistribution license. USGS public-domain policy excepts
third-party copyrighted material; it cannot prove the mixed-author IAU report
constants' complete rights chain. Conversely, unprotected scientific facts do
not automatically require a publisher permission: a supported factual-data /
database-rights / contract analysis is an acceptable alternative to supplier
letters. IGN, IERS, ITRF, IAU and EUREF remain separately named in the ledger.

EPSG: exact source comments explain900913 as a deprecated3857 alias and1312/1462
accuracy2.0 edits as preference for NTv2; fixed transformation parameters are not
changed by those accuracy edits, but operation selection may change. This is
source explanation, not IOGP approval. The terms include associated metadata and
forbid attributing impermissibly modified data to EPSG. Complete terms/ownership/
no-warranty and truthful PROJ adaptation disclosure are present; no mandatory
generic modification sentence was found. Exact permitted-attribution basis is
still unresolved; blanket PROJ MIT and coordinate equivalence alone do not close it.

LT2008 remains0.11549 versus0.115495 in original source/SQL. The5-micrometre
difference is not authoritatively explained; no rounding/correction convention
was invented. This is an owner reproducibility gate, not a requirement to possess
a historical explanation under CC-BY. Existing change indication/credit remains.

Machine decisions with category, exact missing receipt, owner, reason, possession
duty, sufficient alternatives and legal/audit disposition:
`windows-upstream-receipt-closure.json`. Recipient commands:
`WINDOWS_DEPENDENCY_REBUILD.md` and existing `WINDOWS_QTPDF_REBUILD.md`.
The757-file source candidate is immutable; the deterministic source supplement
and `windows-release-retention-manifest.json` describe the retained release kit.
The kit is local, unpublished and not bound to a nonexistent final RC artifact.

Final pre-RC preflight **NOT RUN**; RC build allowed **NO**. No full audit,
B2/B5/OpenSSL/Mesa/inventory, generator rerun, UI/Android, final RC, publication,
commit/push/tag, supplier message or antivirus change. Future exact-folder-only
Bitdefender rule remains, including indefinite manual owner confirmation.

Next action: seek the specifically scoped historical provider/EPSG rights basis
and NKG/PROJ LT reason; use the ledger's minimum Qt release-source/configuration
alternative for exact correspondence instead of demanding internal CI logs.
Only after all gates PASS may preflight run. Focused validation/Git evidence is
in `../WindowsUpstreamReceiptEvidence/final-report.json`.

---

# Final supplier/provider and rebuild evidence — 2026-10-08

**BLOCKED BEFORE RC BUILD.** RELEASE-INFRA / DESKTOP. This is the current
checkpoint; preceding narrow receipts and older sections below are retained
history. B2/B5 stay PASS RETAINED with unchanged inputs and no reruns.

| Gate | Status | Evidence | Remaining action |
| --- | --- | --- | --- |
| B1 | BLOCKED | PDFium baseline/final source delta;18 deterministic binding outputs; pinned Rtools GCC/gfortran10.3.0-9804 | Exact QtPdf executed GN/features/toolchain/job hash chain; binding producer outputs/options; OpenBLAS executed static-object/job mapping and9804 source patches |
| B2 | PASS RETAINED | Existing canonical CRT/import/prerequisite receipts unchanged | none |
| B3 | BLOCKED | Original four Esri lookup branches explained; six NKG2020 national parameter matches; ten init files individually identified | LT2008 reason; IGNF3.1.0/IGN-IERS/IAU independent grants; inherited NKG inputs; EPSG modified-attribution resolution |
| B4 | BLOCKED | Usable conditional functional QtPdf recipe; actual deterministic QPdfDocument MOC stage; practical replacement PASS retained | Missing exact producer/generator/GEOS materials; full functional DLL build/load not demonstrated; complete source retention remains open |
| B5 | PASS RETAINED | Existing TLS/Mesa/native qualification and policies unchanged | none |

New receipts: windows-producer-rebuild-receipts.json and sibling
WindowsProducerRebuildEvidence. Recipient commands and explicit prerequisites:
WINDOWS_QTPDF_REBUILD.md. PDFium upstream revision1afaa1a380fcd06cec420f3e5b6ec1d2ccb920dc
to final Qt treea73e60360d4a1b21df9b41b59d46db1ab489d42a has2880 identical,
54 changed and1620 omitted members. Final release sources already contain changes;
no extra patch application or producer execution is inferred from the delta.

Official Shiboken6.11.2 runs produced18 byte-identical C++/header outputs twice
(one timing log differs). Producer-generated C++ does not exist in the retained
source archive. Exact producer headers/options/output/binary receipt is still
missing. QPdfDocument MOC ran twice successfully with identical output SHA
deede3ee28fb8d3ea42feea2e1df06bd838d7f02ada47497a7de59d19b2f857d.
No Qt6Pdf DLL rebuild/load was performed. Full SDK import environment/VS2022
and exact producer config are not present as a qualified complete rebuild setup;
the batch stops at the meaningful generator stage instead of a blind large build.

Rtools2022-02-06 archive and executable/package receipts establish UCRT GCC and
gfortran10.3.0-9804. The earlier generic GCC8.3 assumption would be wrong for this
UCRT recipe. GNU10.3 source/runtime exception retained. No standalone GCC/runtime
DLL or proved libstdc++ node is introduced. Eligible static-runtime combination
does not itself impose a separate runtime-source delivery blocker. Missing exact
executed OpenBLAS/static-object and patched9804 toolchain correspondence remains
a provenance/build-material issue, not an invented standalone-runtime obligation.

Esri import parent2b73f93d6ea4a1a41773cface1c1ac9c8f13679e has EPSG9408/9409
target11134; current lookup has4258. Exact SELECT branches for108066/108067/108118/
108126 yield no original match, with positive target11134 controls. This closes
the four-record original lookup explanation without whole database regeneration.
Six NKG2020 national Helmert sets match Häkli2023 Table3 after ppb/mas conversion;
the primary paper grants CC-BY4.0 to the transformation and associated data.
LT2008: earliest NKG resource already0.11549 and first PROJ SQL already0.115495;
no authoritative reason proves rounding/correction/transcription. Do not edit data.

Named init resources CH/GL27/nad27/nad83/world/other.extra have explicit PROJ
source/data MIT definition-file coverage and original references; referenced grid
payloads do not ship. ITRF2000/2008/2014 name exact IGN/IERS parameter sources and
unit/sign changes; independent input grants remain unproved. ITRF2020 is generated
from EPSG. IGNF3.1.0 and IAU2015 constants likewise still lack exact input grants.
There is no generic unnamed init blocker. Additional inherited IERS/EUREF input
rights and EPSG-specific modification conditions remain separately named.

Mastixa ships the upstream wheel proj.db byte-for-byte, does not patch it at build
or runtime, and adds no EPSG rows. All observed data edits are upstream PROJ-only.
The upstream representation is modified, including alias900913 and accuracy1312/
1462 edits. Full EPSG terms, IOGP ownership and no-warranty notice remain required.
The terms contain no prescribed generic 'modified by' sentence; a truthful PROJ
modification disclosure is added. Such disclosure does not authorize impermissible
EPSG attribution. The two accuracy edits/alias need authoritative permitted-use
resolution; numerical source correspondence is not that legal permission.

Current active source candidate refresh includes the newly missing rebuild and
receipt documents. The original755 candidate and older745/741 captures remain
immutable. Deterministic hashes/file list are outside the checkout in the new
receipt, avoiding self-reference. Required producer inputs remain explicit BLOCKED
in the retention manifest. SBOM138 components/101 native/1216 pure/456 data and
189 dependency required legal entries +root LICENSE remain unchanged; no inventory
or qualification gate was rerun.

Final pre-RC preflight: **NOT RUN**, since B1/B3/B4 are BLOCKED. RC build allowed:
**NO**. Focused generation, source delta, four lookup controls, six national
parameters, attribution/retention consistency and preservation checks are recorded
in WindowsProducerRebuildEvidence/final-report.json. No app/UI/Android/native input,
installer/updater/guard, B2/B5 policy, staged entry, commit/push/tag/publication,
upload, final RC or antivirus setting was changed. The detailed future Bitdefender
rule below remains mandatory, including indefinite explicit owner confirmation
for manual exclusion management and removal verification.

Next owner action: obtain QtPdf/PySide/shiboken/OpenBLAS/Rtools9804/GEOS matching
executed build/config/generator/patch/output receipts and the named IGN/IERS/IAU/
LT2008/EPSG input explanations or grants. Nothing was sent to those providers.
Only after B1/B3/B4 PASS with B2/B5 retained PASS may final preflight run.

---

# Final narrow B1/B3/B4 closure — 2026-10-08

**BLOCKED BEFORE RC BUILD.** RELEASE-INFRA / DESKTOP, Windows x64. This section
supersedes older blocker wording. B2 and B5 are PASS RETAINED, without reruns or
input/policy changes. `native_notices_complete=false` and
`corresponding_source_ready=false` remain unchanged. RC may not be built.

| Gate | Status | Evidence | Remaining action |
| --- | --- | --- | --- |
| B1 | BLOCKED |39 exact shipping PE nodes +3 embedded nodes; exact absent-node decisions; pinned OpenBLAS publish run/x64 ILP64 job | Executed QtPdf GN/patch/compiler graph, binding generation/build correspondence and static GCC source/version/artifact receipts |
| B2 | PASS RETAINED | Zero Microsoft DLL/installer shipment; independent x64 VC Redist >=14.51.36247.0; canonical-import frozen receipts unchanged | none |
| B3 | BLOCKED | Unchanged proj.db; retained39-table/77707-row correspondence;4 Esri transform+usage input matches;6 NKG2008 parameter matches | Original Esri lookup state; LT ty difference/NKG2020; IGNF/ITRF/IAU/init terms; EPSG modification compliance |
| B4 | BLOCKED | Benign modified QtPdf DLL actually loaded by frozen Mastixa from documented path; startup/PDF/preview PASS; deterministic source mechanism retained | Missing matching producer/generator/build materials and complete rebuild instructions; later artifact/source delivery binding |
| B5 | PASS RETAINED | Qualified TLS3.5.9/Mesa exclusion receipts and inputs unchanged | none |

QtPdf graph: `windows-native-closure-graph.json` maps39 shipping PEs and3
embedded nodes from the retained101-native manifest. qpdf->Qt6Pdf->Core/Gui/Network
is actual; QtPdfWidgets DLL and Python QtPdf/PdfWidgets wrappers do not ship.
OpenBLAS is imported by NumPy `_multiarray_umath` and `_umath_linalg`, not QtPdf.
Static GCC/libgfortran remains an actual compiled node despite absent standalone
GCC runtime/compiler binaries. Unknown compiler/GN/patch/generated-output values
are explicit, not guessed from a release tag or source-tree presence.

Exact OpenBLAS source commit78fc0eaf now has public producer publish run31317225529,
x64/ILP64 job93254323637 and successful install-rtools/build/wheel steps. Published
artifact metadata was retained. CI artifact digest is not a wheel/DLL digest;
the logs API returned403 and linked public step endpoints404. Exact executed
GCC/runtime/version/source and wheel-to-job linkage remain unproved. The Qt
Windows6.11.2 index supplied no exact QtPdf build receipt. Binding source contains
159 retained input entries but no matched generated-wrapper output/command receipt;
exact regeneration was not demonstrated.

CRS:4 Esri grid-transform and usage rows now map exactly to pinned original CSV
names/parameters/accuracy/bounds. The original PROJ generator skips them when the
current EPSG lookup already has matching operations; original producer lookup-state
reconstruction remains open.6 NKG2008 seven-parameter sets match resources/NKG at
the pinned CC BY4 commit. P1_2008_FO does not ship. Lithuania differs specifically
in ty: input0.11549 vs original PROJ SQL/shipped DB0.115495. NKG2020/member/inherited
inputs remain unqualified. The whole39-table/77707-row comparison was reused;
current proj.db SHA528b9763b57e85ee78f6f30478ef0494902320f1d71d1564bf0d7ec4f30cc002
is unchanged. No Mastixa-specific data edits exist. EPSG upstream modifications
still need permitted-change/numeric-equivalence evidence. IGN current registry/legal
pages, ITRF parameter page and USGS article metadata establish provenance, not the
missing exact IGNF3.1.0/ITRF/IAU/init data grants. PROJ MIT is not substituted for
those grants. Full existing Esri/NKG/EPSG legal texts and required attribution remain.

No selective data exclusion was made. `app/gis/geometry.py` accepts general
CRS.from_user_input and importers accept declared/embedded .prj CRS, so non-use of
an authority cannot be proved merely from default EPSG4326/2100. Deleting rows
without transitive foreign-key/operation and supported-import qualification would
not satisfy the owner constraint. Removing all CRS support is not an option.

Practical replacement is now proven for an owner-authorized benign identifiable
QtPdf variant; details/recipient steps are in WINDOWS_LIBRARY_REPLACEMENT.md.
Frozen startup, visible window, PDF export, invoice preview and exact modified
module-path/hash checks PASS. This closes the practical load-path/guard question;
it does not supply missing producer/generator/GEOS/GCC rebuild materials.
Updater explicit overwrite/backup/reapply behavior is documented. No packaging
change was needed, and build-time supply-chain guards remain unchanged.

Per-release retention package: windows-corresponding-source-package.json defines
application snapshot, exact dependency archives, scripts/config/patch/generator/
toolchain/build receipts, normalization recipes, notices/licenses, SBOM/hashes and
recipient instructions. Required missing producer materials remain marked BLOCKED.
New missing closure graph/recipient instructions and the B2 build transformation
must enter a new deterministic local source candidate; original745-file archive
and both old matching generations remain immutable. No public offer, upload or
final binary/source binding is claimed. SBOM remains explicitly incomplete for
unknown embedded code; counts138=137 shipping+1 external prerequisite are retained.

Final pre-RC preflight: **NOT RUN**, because B1/B3/B4 remain BLOCKED. Focused legal/
source/graph consistency checks are not a passed final preflight. No final RC,
commit, push, tag, publication, external message or antivirus change occurred.
Exact tests, source snapshot and start/end Git/byte preservation are recorded in
`../WindowsNarrowClosureEvidence/final-report.json` and `preservation-final.json`.

Exact next owner action: obtain the listed QtPdf/PySide/shiboken/GEOS/OpenBLAS GCC
producer/build/generator materials and provider/upstream CRS rights/correspondence
statements (see WINDOWS_NARROW_CLOSURE.md). A later narrowly authorized receipt
closure can verify them. Only when B1/B3/B4 PASS with B2/B5 PASS retained may final
preflight run. Do not build a final RC from this checkpoint.


---

# B2 CRT normalization — 2026-10-08

**B2 PASS.** RELEASE-INFRA / DESKTOP, Windows x64. B1/B3/B4 remain BLOCKED;
B5 PASS RETAINED, unchanged. **BLOCKED BEFORE RC BUILD.** This leading section
supersedes older B2 grant/CRT-shipping findings below; those are historical.

Chosen route: zero Microsoft CRT DLL/installer shipment; recipient independently
installs official x64 VC Redist >=14.51.36247.0. Mastixa Setup checks registry
Installed/version plus5 canonical System32 files and rejects missing/older
prerequisites. No auto-download, global installation or Microsoft file rename.
All13 former CRT cases are NOT SHIPPED;5 unsigned third-party importers are
deterministically normalized to msvcp140.dll with exact input/output SHA256 locks.
Production policy matches the successfully validated central frozen bytes.
Planned native114->101; pure1216/data456 retained; SBOM137 shipping components
plus1 explicitly external runtime prerequisite. The44 OS exclusions are unchanged.

Exact per-file/importer/provenance/model/test/rights decision:
`WINDOWS_CRT_NORMALIZATION.md`, `windows-crt-normalization.json`,
`packaging/crt_policy.py`, `packaging/windows-crt-policy.json`, and sibling
`../WindowsB2NormalizationEvidence/`. Source suppliers/wheel lock are untouched.
Frozen baseline/app-local/central checks,1243-symbol correspondence, actual
CRT-path tracing and controlled-search/clean-no-Redist simulation PASS.
No pristine VM or final RC was created. Native Inno prerequisite probe aborts
before installation. Later actual RC install/upgrade acceptance remains required.

Community2026 entitlement is documented separately from recipient runtime
installation. No Microsoft code/installer is redistributed by this route;
recipient installation carries Microsoft's terms. Conditional official app-local
deployment passed diagnostics but is NOT adopted. Its protective downstream
assent conditions would remain necessary if later chosen.

Original retained source-candidate ZIPs still describe their prior captured
bytes. They were not relabeled/refreshed and do not match this new checkpoint.
B4 source/replacement gaps and both readiness flags remain unchanged/false.
No full audit, B1/B3/B4/B5 rerun, UI/performance/Android change, RC build,
commit/push/tag/publication, global install or antivirus change. Next release
action: close the retained B1/B3/B4 gaps, then final preflight; RC requires a
later authorized artifact batch and the retained Bitdefender rule.

---

# B2 Community installation re-evaluation — 2026-10-07

**B2 BLOCKED.** RELEASE-INFRA / DESKTOP; B2 only. This section supersedes the
historical VS Code-only/no-Visual-Studio finding and older blanket lack-of-own-license
claims below. B1/B3/B4 remain BLOCKED at their retained external-rights checkpoint;
B5 PASS RETAINED, unchanged. No RC build, installer execution, dependency audit,
B5/OpenSSL/Mesa qualification, commit, push, tag or publication.

Visual Studio Community 2026 **18.10.3**, installation build **18.10.12224.181**,
stable/non-prerelease, installed at `C:/Program Files/Microsoft Visual Studio/18/Community`.
Only MSVC toolset directory: **14.51.36231**; actual x64 compiler **19.51.36260.0**.
Installed Desktop development with C++, latest x64/x86 tools, VC Redist and
Windows 11 SDK **10.0.26100.0** are confirmed from local setup metadata.
Owner attests legal installation and accepted Community terms; sign-in is not
the entitlement evidence.

Redist root: `C:/Program Files/Microsoft Visual Studio/18/Community/VC/Redist/MSVC/14.51.36231`.
`v145/` is the installed installer alias directory. Exact x64 release CRT files
are in `14.51.36231/x64/Microsoft.VC145.CRT/`; versions are **14.51.36247.0**.
Official `vc_redist.x64.exe` and `vc_redist.x86.exe` at that root are both
14.51.36247.0, valid Microsoft signatures. x64 SHA256:
`843068991daaa1f73ad9f6239bce4d0f6a07a51f18c37ea2a867e9beca71295c`;
x86 SHA256: `f0bab33a302b3cdb2e11113760d016f54fd3d2632c65ba7834fac4f0abd7f1a3`.
The x64 installer matches the retained official Microsoft download exactly.

The [Community2026 license](https://visualstudio.microsoft.com/license-terms/vs2026-ga-community/)
dated October1,2025 grants conditional object-code redistribution from its
[2026 Distributable List](https://learn.microsoft.com/en-us/visualstudio/releases/2026/redistribution).
The local Community package `_package.json` license link2327616 resolves to that
edition's license page; installed `Licenses/1033/Redist.txt` points to the same
2026 list. Original DOCX SHA256:
`02ac07637f4a513a807cd3721c7620433fc483bc049d25784b0c10c54b05e1fb`.
The list covers files under `VC/redist` subject to the license, prohibits
modification and excludes debug_nonredist. The standalone runtime install/use
license is not the distribution grant; the accepted Community license supplies it.

**Conditional right established for Mastixa's use of listed unmodified official
release code.** It does not establish a blanket right for every older supplier
copy or changed filename. Mastixa supplies primary application functionality.
Before distribution, external recipients/distributors must agree to protective
Microsoft terms; Microsoft indemnification and other distribution restrictions
also apply. Current Inno `LicenseFile=..\LICENSE` accepts only the application
AGPL license. Protective Microsoft assent remains unproved. Keep CRT terms
separate from AGPL/LGPL rights; preserve covered-library replacement rights.

Raw local metadata, original Microsoft downloads, all official Redist file paths,
versions/hashes, signature receipts and the13 current source-file comparisons:
`../WindowsB2CommunityEvidence/`. Exact current per-file decision:
`windows-microsoft-runtime.json` (`community_2026_evaluation` and each shipping
file's `community_2026` object). No shipping byte or filename was changed.

| Gate | Retained status | Exact remaining gap |
| --- | --- | --- |
| B1 | BLOCKED | QtPdf executed GN/compiled dependency/patch/toolchain graph; binding generation/header/config/producer receipt; executed OpenBLAS/GCC runtime/toolchain receipt |
| B2 | BLOCKED |2 exact canonical files covered,11 current copies UNKNOWN; older-original correspondence,3 rename permissions/canonical dependency rebuild, protective downstream assent and qualified CRT route |
| B3 | BLOCKED | Exact Esri4 discrepant transformations/usage and NKG member derivation; IGNF3.1.0/ITRF/IAU and inherited init-data rights; EPSG permitted-modification/numerical-equivalence conditions |
| B4 | BLOCKED | Executed QtPdf/binding/GEOS/GCC build/generator/patch/toolchain materials; usable recipient-built modified-library replacement; final source/artifact binding and delivery |
| B5 | PASS RETAINED | No changes or reruns |

Both readiness flags remain false. Final pre-RC preflight NOT RUN. **BLOCKED
BEFORE RC BUILD.** Other gate statuses/materials are preserved; no B1/B3/B4
re-evaluation was undertaken. Retained source-candidate ZIPs describe their
prior captured source/docs and remain unchanged; these new B2 documentation
bytes are not claimed to match those archive hashes.

Exact next step: obtain supplier canonical originals/redistribution receipts and
Microsoft filename-rename authorization, or qualify a bounded third-party
canonical-import rebuild/repackage with licensed official CRT deployment.
Prepare separate protective Microsoft recipient/distributor terms. Keep B2
blocked until all13 current entries are covered or explicitly replaced/removed
under that tested route. Only after B1–B4 PASS may final preflight precede an RC
build. No commit/push/tag/publication is authorized by this checkpoint.


---

# External rights / supplier evidence checkpoint — 2026-10-07

**BLOCKED BEFORE RC BUILD.** Authoritative current supplement, RELEASE-INFRA / DESKTOP. B5 PASS retained without changes or reruns. Full decisions/evidence: `WINDOWS_EXTERNAL_RIGHTS_CLOSURE.md`, `windows-external-rights-closure.json`, sibling `WindowsExternalRightsEvidence`. Previous sections below retain their historical checkpoints.

| Gate | Status | Evidence | Remaining action |
| --- | --- | --- | --- |
| B1 | BLOCKED | QtImageformats552 source hashes; exact OpenBLAS producer/source/recipe; binding identity | QtPdf GN/compiled graph; executed binding and GCC/toolchain producer receipts |
| B2 | BLOCKED | Microsoft primary license/docs, PSF Windows binary conditions, host probes |13-file applicable grants/downstream terms or qualified no-CRT/user-installed prerequisite route |
| B3 | BLOCKED | Unchanged proj.db and retained correspondence; targeted EPSG customization/input review | Esri/NKG exact derivation; IGNF/ITRF/IAU/init rights; EPSG modification compliance |
| B4 | BLOCKED | Added matching sources/build scripts/patch; no post-install DLL hash guard; SDK26 smoke retained | Full executed build/generator materials and usable recipient-built modified-library replacement |
| B5 | PASS RETAINED | TLS3.5.9 and Mesa exclusion evidence reused unchanged | none |

Closed: QtImageformats exact source commit/archive and552 supplier hash correspondence; actual8-file binding identity; OpenBLAS exact producer wheel/DLL, pinned source, patch/Windows recipe; static GCC presence; Microsoft own-license vs supplier-distributor distinction and original PSF Windows binary conditions; EPSG upstream modification classification; build-time vs installed-library guard review and explicit update/repair overwrite behavior.

Still blocked: exact QtPdf compiled GN/producer graph; executed binding/GCC toolchain and GEOS build/generator/replacement materials;13 CRT applicable grants/downstream terms or qualified no-CRT route; Esri/NKG exact derivation, IGNF/ITRF/IAU/init rights and complete EPSG modification compliance. Both readiness flags remain false. Final pre-RC preflight NOT RUN, because B1-B4 are not all PASS. RC may not be built.

Owner reports VS Code only; host probes discover no VS/Build Tools. Microsoft installer redistribution/chaining still needs rights; independent recipient download/install avoids Mastixa copying it, but3 hashed MSVCP imports prevent blind removal of13 app-local CRTs. No system installer executed or entitlement assumed.

New required legal/source records justify only a deterministic source-candidate refresh. Original741-file archive and all retained Qt26/database/TLS/Mesa/wheel/usage evidence remain unchanged. Focused validation and exact Git/preservation receipt are in `../WindowsExternalRightsEvidence/final-report.json` and `preservation-final.json`; no full audit or native qualification is repeated.

Exact next owner action: establish the chosen Microsoft distribution route and obtain the listed missing supplier/CRS/replacement receipts. Then close only those gaps; final preflight is permitted only after B1-B4 PASS. No commit/push/tag/publication/final RC build.

---

# Final Windows B1–B4 materials closure — 2026-10-07

**BLOCKED BEFORE RC BUILD.** Authoritative current section; older sections below
remain history. RELEASE-INFRA / DESKTOP, Windows x64,1.0.0-rc.1,rc,AGPL-3.0-only.
No final RC, installer, commit, push, tag, publication, upload or external message.

| Gate | Final status | Closed / exact remaining requirement |
| --- | --- | --- |
| B1 | BLOCKED | Qt Windows SDK SBOM/config/compiler receipts and matching PE sections for26 shipping files; exact Qtbase/SVG producer source retained. Missing complete QtPdf GN target attribution/build/patch graph, bindings receipt and OpenBLAS/GCC runtime closure; QtImageformats SDK source revision remains unpinned. |
| B2 | BLOCKED | Official signed x64 VC14.51.36247.0 installer and terms retained; root2 VCRUNTIME + pyproj MSVCP byte-identical to official container. All13 shipping CRTs still lack proven applicable redistribution grant/recipient eligibility; older8 PySide/shiboken + NumPy/Shapely provenance/repair rights still need supplier originals. |
| B3 | BLOCKED | PROJ9.8.1 SQL/database correspondence39 tables77707 rows PASS; pinned Esri3.6 Apache2 and NKG CC BY4 grants/legal texts retained. Exact Esri/NKG derivation statement, IGNF3.1.0/ITRF and IAU input rights, inherited init-data rights and full EPSG modification/numerical-equivalence conditions remain unresolved. |
| B4 | BLOCKED | Full official QtWebEngine6.11.2 nested source retained; local deterministic Windows application source candidate prepared.26-file SDK DLL substitution smoke PASS. Exact full QtPdf/bindings/GEOS/OpenBLAS build/patch/toolchain/source correspondence and complete usable modified-library replacement materials remain incomplete. |
| B5 | PASS (retained) | Qualified promoted TLS input and exact Mesa/LLVM exclusion reused byte-unchanged; no new qualification performed. |

`native_notices_complete=false`; `corresponding_source_ready=false`.
Final release preflight: **NOT RUN**, because B1–B4 are not all PASS. Focused
regression tests check expected fail-closed behavior; they are not a passed final
preflight. RC may not be built. B5/TLS/Mesa/wheel lock inputs remain unchanged.

Exact primary receipts: `docs/windows-qt-producer-receipts.json`,
`docs/windows-microsoft-runtime.json`, `docs/windows-crs-resources.json`,
`docs/windows-source-retention.json`, `docs/source-artifacts.json`,
`licenses/manifest.json`. Raw authoritative downloads/hash receipts, database
comparison, SDK comparison, build log/TOC, source snapshot and synthetic smoke
outputs are retained in sibling `WindowsFinalB1B4Evidence`.

Legal selection:172 full texts +38 attribution files,210 indexed paths including
root LICENSE.189 REQUIRED AND SHIPS,12 REQUIRED FOR SOURCE PACKAGE ONLY,
2 OPTIONAL/INFORMATIONAL,7 NOT APPLICABLE TO CURRENT SHIPPING SURFACE.
All current `licenses/` files are indexed and hash-checked; binary legal data
selects only REQUIRED AND SHIPS. Old Python/OpenSSL/Mesa/LLVM receipts remain
locally retained and do not re-enter the bundle. QtPdf candidate notices remain
conservatively delivered until compiled GN membership is proved; their inclusion
does not establish that the associated code ships. NotoSansCJK is source-only.

Validation:17 focused release/legal/source tests, isolated diagnostic main.py
startup/visible render/PDF export+invoice preview/PROJ+GEOS/legal selection, and
26-file official-SDK replacement smoke PASS;0 Qt messages. Native114 and pure1216
membership remain unchanged. Planned data455. Diagnostic executable/wrapper are
not release/SBOM members; this is a packaging smoke, not the retained99-scenario
usage audit, a release artifact qualification, or repeated B5 qualification.

Exact next owner action: obtain the original applicable Microsoft grant and
recipient entitlement for the13 CRTs, and supplier statements/materials for the
listed exact QtPdf/binding/GEOS/OpenBLAS build+patch+replacement and CRS/EPSG
derivation/rights gaps. Forbid enabling readiness flags based on URLs alone.
Then close only those material gaps against retained hashes; run final preflight
only after B1–B4 PASS. Build the final candidate only in a later authorized batch.

---

# Mesa/native B5 closure — 2026-10-07

**B5 PASS — FINAL B1–B4 CLOSURE REMAINS.** RELEASE-INFRA / DESKTOP.
Mesa11.2.2 and LLVM3.6.2 are now **EXCLUDE / SAFE TO EXCLUDE** for the current
raster Widgets application. Only `_internal/PySide6/opengl32sw.dll` is removed;
SHA25634b444c016289b560662ff896deceb7f4b2c0723aed3d319ae167c9186ce42b3.
No separate LLVM DLL ships. Exact wheel/RECORD/frozen hash match and Qt supplier
PE-section correspondence prove PySide6 Essentials6.11.2 / Qt llvmpipe origin.
This DLL was automatically collected by PyInstaller, not tooling/PATH leakage.

Normal main.py startup, report PDF export, invoice QPixmap preview, themes and
updater never load it. An added software OpenGL context does load it in the
baseline. Without it, required raster routes pass even with all OpenGL creation
deliberately unavailable. Exact-name binary/data exclusion, post-Analysis and
post-COLLECT/validator guards reject wheel/tool copies and known renamed bytes.
No current supported Mastixa feature needs this optional compatibility fallback.
Legacy supplier maintenance/static build/security remains unqualified; exclusion
removes its shipped code rather than claiming it is patched or vulnerability-free.
Retained Mesa/LLVM legal/source receipts remain historical/reference material.

Focused tests9/9 PASS (0 failures/errors/skips/Qt messages/ResourceWarnings),
isolated and production-policy frozen validation PASS, actual loaded-module
snapshots, raster/no-GL/theme/PDF/input/updater checks, 114 unchanged retained
native hashes, one-file/one-component metadata delta, CycloneDX1.6 schema,
independent deterministic metadata and git diff --check PASS. Expected OpenGL
warnings occur only after an explicit diagnostic context/failure injection.
Installed Bitdefender injection is recorded separately from bundle/system DLLs.
No GPU/VM fleet certification or public updater/installer E2E is claimed.

Current planned membership:114 native /1216 pure /465 data /17 package families /
7 Qt modules /21 plugins; SBOM150 components, embedded coverage still incomplete.
OpenSSL pins/lock/report/evidence and wheel lock are byte-unchanged and reused;
no TLS advisory review, supplier search, promotion or qualification repeated.
B1 producer Qt/PDFium/native notices/build receipts; B2 Microsoft rights and
release-status evidence; B3 remaining CRS/EPSG correspondence; B4 matching
nested source/build/replacement/application archive remain BLOCKED. Both
native_notices_complete and corresponding_source_ready remain false.

Approved worktree Mastixa-Icon-Diagnosis / icon-runtime-qa-final / unchanged
HEAD0a0031cf8ea20b2956944bf8468da9d647701237. Protected MastixaManager and all
unrelated dirty work preserved; no staged changes. Exact Git counts/content
preservation are in sibling WindowsMesaNativeEvidence/preservation-final.json.
Full qualification: docs/WINDOWS_MESA_NATIVE_QUALIFICATION.md. Raw evidence:
WindowsMesaNativeEvidence; prior checkpoint bytes remain below as history.

**Exact next step:** separately authorized final B1–B4 materials closure, reusing
qualified wheel/TLS/Mesa evidence unless inputs change. B5 is complete. Do not
build final RC yet. No final RC, installer, reset, clean, revert, discard,
commit, push, tag, publication or external upload occurred in this batch.

---

# OpenSSL promotion delta — 2026-10-07

**BLOCKED BEFORE RC BUILD. B5 BLOCKED solely for the retained Mesa/native maintenance/security/build qualification gap. The OpenSSL supplier/promotion/frozen subgate is PASS.** B1-B4 statuses remain blocked; only the two CRT input records in B2 change; neither native notices nor corresponding-source readiness is true. RELEASE-INFRA / DESKTOP, Windows x64. No final RC, installer, commit, push, tag, upload or publication.

| Stack | Before -> promoted release input | Result |
| --- | --- | --- |
| Python | CPython 3.14.6 / OpenSSL 3.5.7 -> complete PSF CPython 3.14.8 / OpenSSL 3.5.9 | ACCEPTABLE FOR RC for OpenSSL; coherent runtime + unchanged 23-wheel lock qualified |
| Qt | Qt/PySide6 6.11.2 + accidental Poppler OpenSSL 3.6.4 -> same Qt/PySide + FireDaemon OpenSSL 3.5.9 LTS | ACCEPTABLE FOR RC for OpenSSL; 305 exported resolver symbols and frozen runtime qualified |

The supported patched3.5.9 LTS replacement fixes the reviewed3.6.4 issues; semantic minor numbering is not a Qt dependency. No Qt/PySide update, Qt rebuild or commercial Qt is required for this TLS change. Mesa remains a separate existing blocker; this batch does not transfer it to another gate or certify it.

TLS supplier/security/frozen subgate PASS; original CPython and ambient Qt OpenSSL provenance gaps are superseded. The unchanged Mesa B5 gap remains. Exact pins/source/rights/evidence: WINDOWS_TLS_NATIVE_QUALIFICATION.md and windows-tls-promotion.json. Earlier counts/version records below are historical for affected runtime inputs; other B1-B4 rows remain current.

---

# Windows distribution compliance matrix — 2026-10-07

## Authoritative B1–B5 closure continuation

**BLOCKED BEFORE RC BUILD.** This section supersedes the earlier wheel-candidate,
EPSG-access and Mesa-origin gaps below. No RC, dependency update, installer,
runtime/UI change or publication occurred. Retained 115 native / 1,216 pure
inputs are unchanged. Four added legal resources bring planned data to 462;
the data hash delta is explicit in the manifest. The 151-record SBOM is retained,
with embedded coverage still incomplete; no full regeneration was performed.

| Blocker | Status | Evidence now closed | Remaining action |
| --- | --- | --- | --- |
| B1 | BLOCKED | Exact Qt/PySide/shiboken wheel archives and all installed members verified; qpdf/Qt6Pdf source chain retained; Mesa supplier PE sections matched; upstream Mesa/LLVM legal texts added | Wheel-specific Qt/PDF compiled-feature SBOM, patches/configuration/toolchain and full embedded copyright/NOTICE closure; Mesa static build/notice closure |
| B2 | BLOCKED | Complete 13 shipping CRT / 44 excluded OS-file ledger, original PE names/products/versions/hashes; authoritative Microsoft routes reconciled | Eligible original release REDIST grant/source for each CRT variant; resolve supplier recipient rights and mangled-file modifications; 14.51 release/preview proof |
| B3 | BLOCKED | Official full EPSG terms retrieved and bundled; exact DB metadata/eight authorities plus 29 resource paths mapped; Esri and NKG grants located | Exact remaining registry/init-data terms and attributions; EPSG PROJ-customization correspondence; pin Esri/NKG input/legal mapping |
| B4 | BLOCKED | Hash-verified local source retention manifest linked to shipping binary hashes; concrete version-specific LGPL/AGPL/MPL routes retained | Full nested QtPdf sources and supplier build/patch/configuration materials, OpenBLAS/GCC mapping, compatible Qt/bindings/GEOS replacement evidence; reviewed exact application source archive |
| B5 | BLOCKED | 23 official wheel downloads + published SHA/RECORD/installed-file PASS, complete wheel hash lock; Mesa supplier section correspondence; explicit TLS advisory applicability | Original CPython package/build receipt, explicit Qt TLS binary supplier/hash input, both OpenSSL updates, Mesa security/maintenance qualification |

### B1 — definitive shipped Qt/PDF/native mapping

PySide6 Essentials/Addons/shiboken6 are 6.11.2 with
`cp310-abi3-win_amd64` tags. The Essentials `_config.py` records
2026-08-14T10:05:56+00:00; runtime identifies MSVC 2022 shared x64 release Qt
6.11.2, Python limited API built for 3.10. Every installed archive member,
including every shipping native member, matches the original downloaded wheel.
This proves package identity, not a compiler recipe, absence of upstream patches
or complete embedded SBOM. No wheel carried a Qt/PDFium SPDX/CycloneDX build
SBOM, credits or compiled-feature receipt in the checked archive candidates.

| Actual shipped family | Exact source candidate / notice route | Build closure |
| --- | --- | --- |
| Qt6Core / Gui / Widgets / Network / PrintSupport | qtbase 6.11.2 archive; LGPLv3/GPLv3 plus exact qt-third-party attribution/license candidates, per-file copyright and any supplied NOTICE | Supplier flags/static-vs-system libraries/patches still missing |
| qwindows / qdirect2d / qminimal / qoffscreen, qmodernwindowsstyle, qtuiotouch, qnetworklistmanager, qcertonlybackend / qopensslbackend / qschannelbackend | qtbase 6.11.2 plugins; same Qt route plus compiled third-party/Windows-specific terms. Qt TLS uses separately supplied OpenSSL; Schannel system binaries do not ship | Exact Windows feature/SBOM receipt required |
| Qt6Svg / qsvg / qsvgicon | qtsvg 6.11.2, Qt LGPL and XSVG full copyright/permission text | Source/ABI/build recipe required |
| qgif / qico / qjpeg | qtbase image plugins; Qt terms and actual JPEG/codec copyrights | qjpeg and QtGui codec build/source candidates not yet compiled proof |
| qicns / qtga / qtiff / qwbmp / qwebp | qtimageformats 6.11.2; Qt LGPL and TIFF/WebP/native codec legal candidates | Exact codec versions/options/build recipe required |
| Qt6Pdf / imageformats/qpdf | QtWebEngine a33fa2a897e5ee58e385b3f88dc247d99fca56db, nested chromium 5170777d28bee1ce92cc693a0dbf2ad01492e5cf, PDFium tree a73e60360d4a1b21df9b41b59d46db1ab489d42a | Exact compiled PDF GN/CMake flags, patches and complete nested source missing |
| PySide6 QtCore/Gui/Widgets/Network/PrintSupport .pyd + pyside6 ABI library; Shiboken.pyd + shiboken6 ABI library | pyside-setup-everywhere-src-6.11.2.tar.xz; LGPLv3 binding source/build/replacement route | Exact limited-API/MSVC supplier recipe and compatible replacement evidence missing |
| 96 Qt translations | qttranslations 6.11.2 editable .ts and module terms | Exact source/build correspondence required |
| opengl32sw | Qualified Essentials wheel and Qt-hosted Mesa 11.2.2 prebuilt code/data correspondence; LLVM 3.6.2; new exact upstream base legal texts | Full supplier/static third-party/patch/compiler receipt and qualification missing |

All 21 plugins are accounted for by the rows. QtPdfWidgets DLL/binding and QtPdf
Python binding do not ship; qpdf links Qt6Pdf and enables the required invoice
QPixmap preview. There is no Chromium browser/V8/QtWebEngine DLL payload.
VirtualKeyboard remains excluded. Other native Python/GIS/NumPy/TLS/MSVC
files remain individually mapped in the retained 115-file appendix and the
component-specific B2/B4/B5 ledgers; their distinct terms are not Qt LGPL.

The exact QtPdf source candidates identify PDFium/Chromium BSD copyright,
Abseil Apache, FreeType FTL/GPL option, ICU composite notices, JPEG/PNG/zlib,
OpenJPEG/Little CMS, AGG/fast_float and conditional XFA/V8/Skia/Highway/etc.
The retained sixteen Foxit font byte matches are compiled proof. The source
`BUILD.gn` dependency chain supports codec membership but does not settle
system-codec switches or all conditional components. No all-of-Chromium list
is presented as shipped.

Required distribution material is the actual component's full permission,
copyright and disclaimer text; LGPL also needs GPL/LGPL texts and Qt notice.
Apache NOTICE is required where the selected upstream component provides it;
the presence of an Apache LICENSE alone does not answer that. Composite ICU,
PDFium and FreeType texts and embedded font headers must remain. A separate
credits/About screen is not assumed mandatory for every permissive component;
required notices can be bundled. The existing prominent Qt notice is retained.
Neither 163 collected legal texts nor 35 attribution JSONs prove full closure.

Exact artifact request for B1: **the producer's Windows x64 Qt 6.11.2/PySide6
6.11.2 build SBOM and configure summaries, QtPdf GN args/build.ninja or equivalent
dependency graph, compiler/SDK versions, vendored revisions, patch set and
complete revision-specific license/NOTICE/credits output**, linked to the wheel
hashes in windows-qualified-wheels.json. Obtain the Mesa 11.2.2/LLVM 3.6.2
static dependency/build/legal receipt as well. The official PySide source
directory supplies source archives, not these binary-specific receipts.
If unavailable, a controlled source build with corresponding evidence is
required; adding guesses to notices cannot make B1 PASS.

### B2–B5 supporting dispositions

- B2: `WINDOWS_MICROSOFT_REDISTRIBUTION.md` and `windows-microsoft-runtime.json`
  give all file classifications and the official-installer alternative. Removing
  hashed CRT variants is not low-risk and was not implemented.
- B3: `WINDOWS_CRS_ATTRIBUTION.md` / `windows-crs-resources.json` distinguish
  data grants from generator/software licenses. The prior EPSG 403 is resolved.
- B4: `SOURCE_DELIVERY_PLAN.md` / `windows-source-retention.json` give exact
  archives, binary hash mappings, missing materials and retention/replacement
  routes. No public source offer or mirror has been made.
- B5: `WINDOWS_RUNTIME_PROVENANCE.md`, `windows-qualified-wheels.json`,
  `windows-mesa-provenance.json` and `requirements-windows-rc-hashed.txt` give
  reproducible wheel identities, supplier correspondence and explicit
  **UPDATE REQUIRED** for Python OpenSSL 3.5.7 and Qt OpenSSL 3.6.4. No risky
  native update was silently performed.

Primary references: [Qt LGPL obligations](https://www.qt.io/development/open-source-lgpl-obligations),
[exact PySide source release](https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.11.2-src/),
[Qt llvmpipe supplier](https://download.qt.io/development_releases/prebuilt/llvmpipe/windows/),
[LLVM exact license](https://github.com/llvm/llvm-project/blob/llvmorg-3.6.2/llvm/LICENSE.TXT),
[EPSG terms](https://epsg.org/terms-of-use.html),
[Microsoft REDIST](https://learn.microsoft.com/en-us/visualstudio/releases/2022/redistribution),
[OpenSSL August advisory](https://openssl-library.org/news/secadv/20260825.txt),
[OpenSSL September advisory](https://openssl-library.org/news/secadv/20260929.txt).
Package-specific exact PyPI primary references are stored in the qualified
wheel ledger; registry references are in the CRS ledger. Remaining historical
audit sections and native appendix follow for continuity.

---

**BLOCKED BEFORE RC BUILD**. RELEASE-INFRA / DESKTOP, Windows only.
1.0.0-rc.1 / rc / AGPL-3.0-only / UNSIGNED / offline staging remain unchanged.
No final RC or installer was built; no publication, upload, commit, push or tag.

This audit uses the actual current spec, build/installer scripts and a fresh
PyInstaller 6.22.3 Analysis with CPython 3.14.6 and the retained pinned Windows
wheels. A separately named MastixaDependencyPreview onedir executable, using
the real main.py plus an external synthetic QA wrapper, validates dependency
pruning. It is not an RC and its wrapper/EXE hash is absent from the shipping SBOM.

The authoritative file lists/hashes and inherited license/provenance/status
fields are in `windows-distribution-manifest.json`; source identities/receipts
are in `source-artifacts.json`; embedded font hashes are in
`embedded-font-provenance.json`. Full legal bytes and origins are indexed in
`../licenses/manifest.json`. The native appendix below enumerates every emitted
DLL/PYD. There is no claim that unverified Nth-party feature candidates are
definitely compiled; unresolved supplier evidence is explicitly a blocker.

## Exact shipping boundary and evidence

Seven native Qt modules remain: Core, Gui, Widgets, Network, PrintSupport, SVG,
PDF. Five Python Qt bindings ship: Core, Gui, Widgets, Network, PrintSupport.
QtPdfWidgets/QtPdf Python bindings do not ship; the PDF DLL comes through the
qpdf image plugin. Twenty-one Qt plugins remain. Hidden imports configured by
the project are empty; automatic hook imports and binary collection are included
in the manifest. No collect-all application resource hook or explicit external
EXE/GDAL/WebView/updater binary appears in the spec.

The original fresh Analysis had 165 native entries after the existing VK filter.
The scoped policy removes six orphan DLLs (Quick/Qml/QmlMeta/QmlModels/
QmlWorkerScript/OpenGL) and 44 OS-provided API-set/UCRT files: **50 files,
17,552,624 bytes (~16.74 MiB)**. A PE import/delay-import scan found no remaining
binary importing the six Qt DLLs. Windows source AST/search found no QML/Quick/
OpenGL bindings or dynamic frontend. The native frozen process passed startup,
text input, annual PDF export, QPixmap invoice PDF preview and loaded-DLL absence.
QtGui OpenGL support and opengl32sw fallback remain. Do not conflate exclusion
of Qt6OpenGL.dll with deletion of every OpenGL capability.

All explicit app/assets, locales, legal/source files and staging JSON inputs
are included by directory/file rules. Installer [Files] recursively copies only
the final dist/MastixaManager tree. It does not pull the workspace, owner data,
backups, external audit or QA copies. App ICO is embedded into executable and
installer; it is independently in the 41-artwork provenance ledger. Internal
sources are recorded by sanitized identity, not local machine paths. Build-only
pip/setuptools/altgraph/pefile/pywin32-ctypes/compiler tools are not package
components just because installed. Only emitted PyInstaller/runtime-hook parts
are counted. numpy.testing and pyparsing.testing helpers are dependency-reachable
pure modules; they remain listed, not silently removed solely by their names.

## Component / obligation matrix

PASS means the named audited fact/material is verified, not overall legal or
release clearance. ACTION REQUIRED is a concrete verification/material task;
BLOCKER prevents the RC under current project rules. Native/resource manifests
inherit the following component obligations; the full source version table is
in SOURCE_DELIVERY_PLAN.md and source-artifacts.json.

| Component / actual files | Version / origin | License and text/notice | Source and replacement / attribution | Status |
| --- | --- | --- | --- | --- |
| Mastixa EXE + app PYZ/locales/assets | Current dirty 1.0.0-rc.1 source; executable unborn | AGPL-3.0-only full root LICENSE, Settings/installer notice verified | Exact app source/scripts/config/resources alongside future binary; dirty-source archive and public access are later distribution requirements | ACTION REQUIRED before public distribution; metadata PASS |
| Python runtime, python314.dll/python3.dll, 40+ stdlib/native inputs and base_library/PYZ | CPython 3.14.6, interpreter installation, per-file hashes | Full PSF/historical chain included; compiled extension legal texts additionally included | Permissive source duties; preserve notices. Unmodified binary/source recipe provenance must match selected interpreter | ACTION REQUIRED |
| Python bzip2/libffi/mpdecimal/XZ/zlib-ng/zstd/Expat | 1.0.8 / 3.4.4 / 4.0.0 / 5.2.5 / 2.2.4 / 1.5.7 / 2.8.1, exact CPython source externals or runtime | Exact upstream native texts collected, not generalized PSF | Six external archives hash-checked against upstream CPython SBOM; target zlib runtime reports 1.3.1.zlib-ng, not an invented zlib-ng version | PASS version/source mapping; interpreter qualification ACTION REQUIRED |
| PySide6 Essentials/Addons + shiboken6, 5 Qt binding .pyd and ABI DLLs | 6.11.2, selected wheel RECORD all native hashes matched | LGPLv3 route; full GPLv3/LGPLv3, Qt notice; exact native sublicenses separate | pyside-setup official exact source archived. Need supplier build/config/patch receipt and practical ABI-compatible replacement | BLOCKER B1/B4 |
| Qt base modules/plugins | 6.11.2.0 PE / 6.11.2 runtime; qtbase exact source | LGPLv3; module notice/full text present. 45 versioned Qt source attribution candidates collected; compiled subset/NOTICE closure pending | Exact source archive retained; source/build/replacement materials and conditional MPL data duties must match actual wheel | BLOCKER B1/B4 |
| Qt SVG / icon engine | 6.11.2, wheel RECORD, qsvg/qsvgicon | LGPLv3 plus XSVG HPND variant; exact XSVG license/copyright included | qtsvg exact source retained; match build/ABI instructions | ACTION REQUIRED B4 |
| Qt JPEG/GIF/ICO/ICNS/TGA/TIFF/WBMP/WebP/image and platform/style/TLS/generic plugins | 21 plugins, file list below | Qt LGPL plus codecs' exact separate texts; qjpeg candidate 3.2.0, Qt TIFF 4.7.2, WebP 1.6.0, libpng 1.6.58 based on pinned source | Preserve codec notices, FreeType/HarfBuzz/etc attribution where compiled. Supplier feature mapping required; not all whole-source Qt platforms ship | BLOCKER B1 |
| Qt translations | 96 .qm resources in observed hook collection | LGPL/source-specific translation terms; base Qt notice/text included | Exact qttranslations 6.11.2 archive retained, .ts/source access/build mapping needed | ACTION REQUIRED B4 |
| QtPdf/qpdf/PDFium | 6.11.2.0 PE; QtWebEngine a33fa2a... nested chromium 5170777... and PDFium tree a73e603... | LGPL Qt wrapper; PDFium/Chromium BSD and separate third-party terms, full fetched text/copyright index | Required for invoice QPixmap preview, proven using generated PDF. Full nested source/GN flags/toolchain/patch/SBOM closure missing | BLOCKER B1/B4; runtime use PASS |
| PDFium/Foxit embedded fonts | 16 generated stock-font arrays; exact bytes matched in Qt6Pdf.dll | PDFium BSD source headers, original 2014 Foxit copyright, full PDFium license and verbatim headers included | Version pinned to PDFium tree; font payload hashes in ledger. No standalone font files; no Windows fonts copied | PASS provenance/notice; overall QtPdf closure separate |
| Qt VirtualKeyboard | No current emitted DLL/plugin/QML/data; no runtime module load | GPL-only/commercial module outside shipping surface | Original exclusion preserved; frozen startup/input passed; no commercial route inferred | NOT APPLICABLE |
| Qt SQL/Multimedia/PdfWidgets/OpenGLWidgets/WebEngine and QML modules | Installed in dev wheel but absent from current emission | No corresponding software payload shipped | No Qt SQL driver, FFmpeg/media codec, Qt browser process, QML frontend or Qt WebView distribution | NOT APPLICABLE |
| Qt Quick/QML/OpenGL orphan DLLs | Six 6.11.2 DLLs removed | Not shipped | Removed only after static import/source analysis and frozen absence/runtime checks | NOT APPLICABLE; exclusion PASS |
| Software OpenGL opengl32sw.dll | Wheel RECORD; embedded Mesa 11.2.2 / LLVM 3.6.2 strings | Expected Mesa MIT / LLVM UIUC family; exact complete build notices and any static dependencies not yet verified | Optional QtGui software fallback retained; no safe non-use proof. Obtain Qt prebuilt origin/patch/build/legal receipt. Do not label versionless binary current | BLOCKER B1; security-sensitive |
| Shapely / GEOS | 2.1.2 / 3.13.1 runtime; 2 hashed-name GEOS DLLs | Shapely BSD + LGPLv2.1 GEOS text/Windows notice included | Exact GEOS source retained; `.libs` mangled DLL dependencies and wheel build recipe/replacement validation required | ACTION REQUIRED B4 |
| pyproj / PROJ | 3.8.0 / 9.8.1 runtime; hashed PROJ DLL plus 67 resources | MIT/PROJ upstream legal text included | PROJ exact source retained; GIS functions actually use transforms/geodesy. Separate dataset terms below | ACTION REQUIRED; CRS data BLOCKER B3 |
| GIS curl/TIFF/JPEG/XZ/zlib/SQLite | 8.19.0 Schannel / 4.7.1 / libjpeg-turbo 3.1.4.1 / 5.8.3 / 1.3.1 / 3.53.0 PE | curl / TIFF / IJG+BSD+Zlib / XZ 0BSD/library terms / Zlib / public domain; exact upstream legal files collected | Versions read by native APIs/PE/strings, not generic PROJ docs. No required source for listed permissive routes; preserve notices. Native build receipt/extra dependencies still qualify | ACTION REQUIRED |
| CRS data/proj.db | EPSG v12.029 / source metadata matches PROJ 9.8.1; IAU/ESRI/IGNF/NKG etc source registries | Software MIT does not independently settle registry dataset terms/attribution | Exact data metadata/hash/source mapped; full applicable EPSG/registry redistribution grants/attribution still unresolved. EPSG authoritative terms endpoint returned 403; no account created | BLOCKER B3 |
| GDAL / offline tiles / external OCR | No GDAL DLL, raster pack, MBTiles/GPKG/PBF/tile archive, Tesseract EXE or tessdata input | None shipped | OSM visible tiles explicitly requested online with existing attribution; stored owner tile/cache content not included. PROJ coordinate resources are not basemap tiles | NOT APPLICABLE |
| NumPy / OpenBLAS / GCC runtime | 2.5.3 / scipy-openblas build 0.3.34.106.0; vendored DLL | Composite NumPy BSD, LAPACK BSD, GCC GPL+Runtime Exception texts supplied; all 23 hook-collected dist-info resources preserved | Exception does not automatically impose GPL on Mastixa. Exact underlying native/compiler recipe and modified-runtime/exception applicability still required | ACTION REQUIRED B4 |
| Python and Qt OpenSSL stacks | Python 3.5.7 ssl/crypto DLLs; Qt 3.6.4 -x64 DLLs from tool PATH | Apache-2.0 full exact-version upstream texts added | Python ssl backs urllib updater; Qt TLS backs map networking. Exact two-stack binary origins/hashes captured; no invented single OpenSSL version. Ambient collection needs pinned provenance | BLOCKER B5 qualification; license texts PASS |
| Qt TLS/plugins + CA bundle | qopenssl/qschannel/qcertonly; certifi 2026.7.22 | Qt LGPL; Certifi MPL2 included | Frozen process selected openssl with sanitized system PATH. Schannel uses Windows trust; Python defaults use Windows/default SSL trust. Certifi data ships through pyproj dependency, not a claim updater explicitly uses certifi | PASS inventory; Qt/source qualification remains |
| Python SQLite | sqlite3.dll 3.50.4 + _sqlite3.pyd | SQLite public domain; extension CPython terms | Separate from pyproj SQLite 3.53.0. No QtSql/GDAL SQLite extension ships. System SQLite not assumed | PASS inventory/redistribution route |
| Other Python libraries | pyshp 2.4.2, ezdxf 1.4.4, fontTools 4.65.0, pyparsing 3.3.3, defusedxml 0.7.1, openpyxl 3.1.5, et_xmlfile 2.0.0, typing_extensions 4.16.0 | MIT or PSF chain per exact index; openpyxl/et texts from hash-verified sdists | Preserve copyright/permission/disclaimers. fontTools library is not a font pack. Dev meta-packages not counted without emission | PASS texts/version/member mapping |
| PyInstaller bootloader/emitted hooks/utils + hooks-contrib pyproj runtime hook | 6.22.3 / 2026.7; target bootloader hash in manifest | GPLv2+bootloader exception and applicable Apache terms, exact upstream combined/runtime texts | Exception permits independent application license; full sources retained. Compiler/build-only hook packages are not copied wholesale | PASS mapping/texts; final emitted executable acceptance later |
| Microsoft CRT variants | Root Python 14.42.34438; Qt/shiboken 14.44.35211; Shapely 14.44.35215; NumPy 14.40.33810; pyproj 14.51.36247 | Proprietary Microsoft redistribution terms; no blanket AGPL/LGPL grant | Wheel RECORD origin/versions verified, but permitted redist-source/terms/entitlement receipts missing for each variant. Confirm applicable VS version, do not assume one VS2022 grant covers all | BLOCKER B2 |
| UCRT/API-set/Windows system DLLs | OS-provided on installer MinVersion=10.0 | Not redistributed | Remove UCRT/API sets accidentally found in tool PATH. Kernel32/User32/etc remain OS dependencies. No WebView runtime exists in collection | NOT APPLICABLE; exclusion PASS |
| Owner/project artwork | 41 files, 35 PNG / 5 SVG / 1 ICO; ledger hashes unchanged | Owner-attested project-created/AI-assisted, not a blanket dependency-artwork ownership assertion | No external icon pack/stock image/unowned shipping artwork found; installer ICO same ledger. Unknown new resource would block public distribution | PASS current artwork provenance |
| Referenced system fonts | Segoe UI etc referenced for UI/PDF generation; files not bundled | Windows/font embedding terms apply to user-generated PDF independently | No system-font copying. Embedded PDFium fonts audited separately above; fontTools is code | PASS no font-file redistribution |
| Inno Setup output | Installed revision-history package 6.7.3; installer not generated here | Full upstream Inno text included. Preserve embedded copyright/web addresses; acknowledgement appreciated, not required | Compiler/is7z/tool libraries are not spec inputs. Generated setup/uninstall runtime/default art/compression is compiler-produced; confirm emitted version/resources when a candidate is later built | ACTION REQUIRED artifact validation; no compiler-source offer required merely for installer use |
| Updater | Project Python code + urllib/ssl/hashlib/subprocess | No third-party updater EXE or helper; existing native stacks above | Offline bundled rc/stable fixtures; future project JSON/GitHub Releases -> SHA256 -> explicit install consent. Failure/mismatch cleanup/retry and cancellation checked. No silent install/public feed or real E2E claim | PASS source/dependency tests; artifact acceptance later |

## QtPdf source-derived Nth-party detail

Do not delete qpdf: generated PDFs load successfully in the production invoice
QPixmap path. Report export uses QPrinter; lack of a direct QtPdf Python import
does not demonstrate that QtPdf is unused.

QtWebEngine 6.11.2's nested Chromium snapshot is 140.0.7339.225. The exact
vendored PDFium tree above (not latest pdfium/main) provides these source
identities and legal texts: Abseil 56945519..., FreeType 27c1cb10..., ICU 74.2,
libjpeg-turbo 3.1.0, libpng 1.6.58, zlib 1.3.1, fast_float 7.0.0/cb1d42aa...,
OpenJPEG 2.5.3/210a8a56..., Little CMS 2.15/d0752309..., AGG 2.3 and further
feature-dependent Highway/CPU/features/fp16/dragonbox/BigInt/TIFF candidates.
fxcodec BUILD.gn has direct lcms/OpenJPEG/zlib/jpeg dependencies; fxge includes
AGG and the stock fonts. This extends the generic QtPdf documentation list.
XFA/V8/Skia/system-codec switches change the final fourth-party surface;
source README `Shipped: yes` for upstream PDFium/Chromium is not proof that all
those features are in this wheel. Get the exact wheel's compiled feature/SBOM
receipt to close B1. There is no separate chromium browser process, V8 DLL or
QtWebEngine DLL in the current bundle.

The NotoSansCJK subset is explicitly `Shipped: no` and test-only in its exact
README. Its font file is absent. Its source-audit LICENSE is retained locally
but marked source-only and excluded from bundled legal data. The sixteen Foxit
font arrays, in contrast, were actually byte-matched in the native binary and
are represented in the SBOM/provenance ledger.

## Notice reconciliation

All original 41 indexed legal texts were retained byte-for-byte. Added texts
come from pinned upstream archives/source files, not summaries. Attribution JSON
is indexed separately from full license/copyright text. Counts and duplicates
are given in the generated summary below. Duplicate legal bytes remain in
their original upstream contexts; this is not multiple licensing obligations.
Conditional Qt/PDFium legal candidates are explicitly labelled pending exact
build applicability. Noto source-only material is not treated as shipped code.
No commercial Qt reference file is presented as a commercial entitlement.

Missing closure: exact compiled Qt/PDFium/codec NOTICE/embedded copyright list,
software OpenGL full build notices, source/NOTICE for any selected feature not
covered by collected candidates, dataset attribution/rights and MS redist terms.
Any actual upstream NOTICE must accompany LICENSE; the current collected
license count alone cannot certify completeness. Prepared LGPL notices and
source documents are physically spec inputs; final installer checks remain later.

## Security-sensitive surface / maintenance

PDFium codecs, Qt and GIS image decoders, OpenSSL/Python SSL, SQLite, archive
and compression engines, XML/DXF/shape parsers, NumPy native code and legacy
software OpenGL are retained attack surfaces. Native versions above are exact
where measured; embedded candidates must not be counted as confirmed from
generic documentation. No bundled WebEngine/WebView/FFmpeg/GDAL/updater-helper
attack surface was found. Preserve upstream update paths through pinned wheels,
CPython releases and Qt supplier builds; rerun only affected inventory when
inputs change, not the whole dependency investigation.

OpenSSL 3.5.7 and 3.6.4 are behind the 29 September 2026 security releases
3.5.9 and 3.6.5, which fix issues up to High severity. This is a cheap primary-
source advisory check, not a full CVE audit or proof of Mastixa exploitability.
The app uses HTTPS rather than QUIC/DTLS/CMP, but certificate and other paths
still need targeted qualification. Resolve B5 by selecting patched supported
inputs or documenting exact relevant advisory applicability. No critical
reachable vulnerability was established; no dependency was silently upgraded.
[OpenSSL 3.5 release notes](https://openssl-library.org/news/openssl-3.5-notes/),
[OpenSSL 3.6 release notes](https://openssl-library.org/news/openssl-3.6-notes/).
Qt's supported-release table lists a newer 6.11.3; 6.11.2 is not labelled latest.
The old Mesa/LLVM fallback has no demonstrated active upstream maintenance for
this exact prebuilt DLL; supplier notice/source/security qualification is required.
[Qt release table](https://doc.qt.io/qt-6/qt-releases.html).

## Version / privacy / next release gate

Current Windows metadata, app license/legal UI, PE/ISS versions and staging feed
remain aligned to 1.0.0-rc.1 / rc / AGPL-3.0-only / UNSIGNED. Old alpha/PolyForm
references survive in historical handoff/roadmap/tests and the unchanged Android
checkpoint. Legacy constructor alpha title is overridden by canonical main.py
version integration; report-only debt, not a new packaged-title failure. No
wrong active production feed or new automatic networking was introduced.

Evidence and synthetic runtime live outside source. Project manifests omit local
machine/owner-profile paths and record filenames/hashes, not private data. Only
explicit source resources enter spec/installer. Original artwork/private data,
HEAD/branch/staging and unrelated dirty file hashes are preservation gates.

**B1:** supplier build-specific Qt/PDFium/OpenGL notices/feature/subcomponent
receipt. **B2:** exact MSVC permitted redistribution origin/terms/entitlement.
**B3:** EPSG/other CRS dataset rights/attribution. **B4:** complete corresponding-
source/build/replacement materials and compatible replacement validation.
**B5:** qualify/pin interpreter/wheel/ambient TLS/native inputs and known security
patches. These concrete receipts/materials replace a generic repeat-audit task.

Next owner/release action: obtain these supplier/legal/build receipts and close
the five ledger items in this checkout; rerun readiness preflight and affected
manifest/hash checks. After readiness, a separately authorized fresh RC build
and isolated install/upgrade/uninstall/reinstall/updater acceptance are still
required. Do not start that build or publish in this audit.

## Per-native-file appendix

The 115 DLL/PYD rows below inherit source/notice/replacement duties from the
component table. Full SHA-256, PE dependencies, origin and record-match evidence
are machine-readable in windows-distribution-manifest.json. Version unknown
means not proven, not an invented package internal version.

| File | Version | Origin | License | Status |
| --- | --- | --- | --- | --- |
| _internal/PySide6/MSVCP140.dll | 14.44.35211.0 | wheel-record:PySide6_Essentials@6.11.2:PySide6/MSVCP140.dll | Microsoft proprietary redistributable terms: entitlement/origin unresolved | BLOCKER |
| _internal/PySide6/MSVCP140_1.dll | 14.44.35211.0 | wheel-record:PySide6_Essentials@6.11.2:PySide6/MSVCP140_1.dll | Microsoft proprietary redistributable terms: entitlement/origin unresolved | BLOCKER |
| _internal/PySide6/MSVCP140_2.dll | 14.44.35211.0 | wheel-record:PySide6_Essentials@6.11.2:PySide6/MSVCP140_2.dll | Microsoft proprietary redistributable terms: entitlement/origin unresolved | BLOCKER |
| _internal/PySide6/Qt6Core.dll | 6.11.2.0 | wheel-record:PySide6_Essentials@6.11.2:PySide6/Qt6Core.dll | LGPL-3.0-only; embedded third-party terms pending build mapping | BLOCKER |
| _internal/PySide6/Qt6Gui.dll | 6.11.2.0 | wheel-record:PySide6_Essentials@6.11.2:PySide6/Qt6Gui.dll | LGPL-3.0-only; embedded third-party terms pending build mapping | BLOCKER |
| _internal/PySide6/Qt6Network.dll | 6.11.2.0 | wheel-record:PySide6_Essentials@6.11.2:PySide6/Qt6Network.dll | LGPL-3.0-only; embedded third-party terms pending build mapping | BLOCKER |
| _internal/PySide6/Qt6Pdf.dll | 6.11.2.0 | wheel-record:PySide6_Addons@6.11.2:PySide6/Qt6Pdf.dll | LGPL-3.0-only; embedded third-party terms pending build mapping | BLOCKER |
| _internal/PySide6/Qt6PrintSupport.dll | 6.11.2.0 | wheel-record:PySide6_Essentials@6.11.2:PySide6/Qt6PrintSupport.dll | LGPL-3.0-only; embedded third-party terms pending build mapping | BLOCKER |
| _internal/PySide6/Qt6Svg.dll | 6.11.2.0 | wheel-record:PySide6_Essentials@6.11.2:PySide6/Qt6Svg.dll | LGPL-3.0-only; embedded third-party terms pending build mapping | BLOCKER |
| _internal/PySide6/Qt6Widgets.dll | 6.11.2.0 | wheel-record:PySide6_Essentials@6.11.2:PySide6/Qt6Widgets.dll | LGPL-3.0-only; embedded third-party terms pending build mapping | BLOCKER |
| _internal/PySide6/QtCore.pyd | unknown internal version | wheel-record:PySide6_Essentials@6.11.2:PySide6/QtCore.pyd | LGPL-3.0-only; embedded third-party terms pending build mapping | BLOCKER |
| _internal/PySide6/QtGui.pyd | unknown internal version | wheel-record:PySide6_Essentials@6.11.2:PySide6/QtGui.pyd | LGPL-3.0-only; embedded third-party terms pending build mapping | BLOCKER |
| _internal/PySide6/QtNetwork.pyd | unknown internal version | wheel-record:PySide6_Essentials@6.11.2:PySide6/QtNetwork.pyd | LGPL-3.0-only; embedded third-party terms pending build mapping | BLOCKER |
| _internal/PySide6/QtPrintSupport.pyd | unknown internal version | wheel-record:PySide6_Essentials@6.11.2:PySide6/QtPrintSupport.pyd | LGPL-3.0-only; embedded third-party terms pending build mapping | BLOCKER |
| _internal/PySide6/QtWidgets.pyd | unknown internal version | wheel-record:PySide6_Essentials@6.11.2:PySide6/QtWidgets.pyd | LGPL-3.0-only; embedded third-party terms pending build mapping | BLOCKER |
| _internal/PySide6/VCRUNTIME140.dll | 14.44.35211.0 | wheel-record:PySide6_Essentials@6.11.2:PySide6/VCRUNTIME140.dll | Microsoft proprietary redistributable terms: entitlement/origin unresolved | BLOCKER |
| _internal/PySide6/VCRUNTIME140_1.dll | 14.44.35211.0 | wheel-record:PySide6_Essentials@6.11.2:PySide6/VCRUNTIME140_1.dll | Microsoft proprietary redistributable terms: entitlement/origin unresolved | BLOCKER |
| _internal/PySide6/opengl32sw.dll | Mesa 11.2.2 / LLVM 3.6.2 (embedded strings) | wheel-record:PySide6_Essentials@6.11.2:PySide6/opengl32sw.dll | Mesa MIT and LLVM UIUC; exact notices/build provenance pending | BLOCKER |
| _internal/PySide6/plugins/generic/qtuiotouchplugin.dll | 6.11.2.0 | wheel-record:PySide6_Essentials@6.11.2:PySide6/plugins/generic/qtuiotouchplugin.dll | LGPL-3.0-only; embedded third-party terms pending build mapping | BLOCKER |
| _internal/PySide6/plugins/iconengines/qsvgicon.dll | 6.11.2.0 | wheel-record:PySide6_Essentials@6.11.2:PySide6/plugins/iconengines/qsvgicon.dll | LGPL-3.0-only; embedded third-party terms pending build mapping | BLOCKER |
| _internal/PySide6/plugins/imageformats/qgif.dll | 6.11.2.0 | wheel-record:PySide6_Essentials@6.11.2:PySide6/plugins/imageformats/qgif.dll | LGPL-3.0-only; embedded third-party terms pending build mapping | BLOCKER |
| _internal/PySide6/plugins/imageformats/qicns.dll | 6.11.2.0 | wheel-record:PySide6_Essentials@6.11.2:PySide6/plugins/imageformats/qicns.dll | LGPL-3.0-only; embedded third-party terms pending build mapping | BLOCKER |
| _internal/PySide6/plugins/imageformats/qico.dll | 6.11.2.0 | wheel-record:PySide6_Essentials@6.11.2:PySide6/plugins/imageformats/qico.dll | LGPL-3.0-only; embedded third-party terms pending build mapping | BLOCKER |
| _internal/PySide6/plugins/imageformats/qjpeg.dll | 6.11.2.0 | wheel-record:PySide6_Essentials@6.11.2:PySide6/plugins/imageformats/qjpeg.dll | LGPL-3.0-only; embedded third-party terms pending build mapping | BLOCKER |
| _internal/PySide6/plugins/imageformats/qpdf.dll | 6.11.2.0 | wheel-record:PySide6_Essentials@6.11.2:PySide6/plugins/imageformats/qpdf.dll | LGPL-3.0-only; embedded third-party terms pending build mapping | BLOCKER |
| _internal/PySide6/plugins/imageformats/qsvg.dll | 6.11.2.0 | wheel-record:PySide6_Essentials@6.11.2:PySide6/plugins/imageformats/qsvg.dll | LGPL-3.0-only; embedded third-party terms pending build mapping | BLOCKER |
| _internal/PySide6/plugins/imageformats/qtga.dll | 6.11.2.0 | wheel-record:PySide6_Essentials@6.11.2:PySide6/plugins/imageformats/qtga.dll | LGPL-3.0-only; embedded third-party terms pending build mapping | BLOCKER |
| _internal/PySide6/plugins/imageformats/qtiff.dll | 6.11.2.0 | wheel-record:PySide6_Essentials@6.11.2:PySide6/plugins/imageformats/qtiff.dll | LGPL-3.0-only; embedded third-party terms pending build mapping | BLOCKER |
| _internal/PySide6/plugins/imageformats/qwbmp.dll | 6.11.2.0 | wheel-record:PySide6_Essentials@6.11.2:PySide6/plugins/imageformats/qwbmp.dll | LGPL-3.0-only; embedded third-party terms pending build mapping | BLOCKER |
| _internal/PySide6/plugins/imageformats/qwebp.dll | 6.11.2.0 | wheel-record:PySide6_Essentials@6.11.2:PySide6/plugins/imageformats/qwebp.dll | LGPL-3.0-only; embedded third-party terms pending build mapping | BLOCKER |
| _internal/PySide6/plugins/networkinformation/qnetworklistmanager.dll | 6.11.2.0 | wheel-record:PySide6_Essentials@6.11.2:PySide6/plugins/networkinformation/qnetworklistmanager.dll | LGPL-3.0-only; embedded third-party terms pending build mapping | BLOCKER |
| _internal/PySide6/plugins/platforms/qdirect2d.dll | 6.11.2.0 | wheel-record:PySide6_Essentials@6.11.2:PySide6/plugins/platforms/qdirect2d.dll | LGPL-3.0-only; embedded third-party terms pending build mapping | BLOCKER |
| _internal/PySide6/plugins/platforms/qminimal.dll | 6.11.2.0 | wheel-record:PySide6_Essentials@6.11.2:PySide6/plugins/platforms/qminimal.dll | LGPL-3.0-only; embedded third-party terms pending build mapping | BLOCKER |
| _internal/PySide6/plugins/platforms/qoffscreen.dll | 6.11.2.0 | wheel-record:PySide6_Essentials@6.11.2:PySide6/plugins/platforms/qoffscreen.dll | LGPL-3.0-only; embedded third-party terms pending build mapping | BLOCKER |
| _internal/PySide6/plugins/platforms/qwindows.dll | 6.11.2.0 | wheel-record:PySide6_Essentials@6.11.2:PySide6/plugins/platforms/qwindows.dll | LGPL-3.0-only; embedded third-party terms pending build mapping | BLOCKER |
| _internal/PySide6/plugins/styles/qmodernwindowsstyle.dll | 6.11.2.0 | wheel-record:PySide6_Essentials@6.11.2:PySide6/plugins/styles/qmodernwindowsstyle.dll | LGPL-3.0-only; embedded third-party terms pending build mapping | BLOCKER |
| _internal/PySide6/plugins/tls/qcertonlybackend.dll | 6.11.2.0 | wheel-record:PySide6_Essentials@6.11.2:PySide6/plugins/tls/qcertonlybackend.dll | LGPL-3.0-only; embedded third-party terms pending build mapping | BLOCKER |
| _internal/PySide6/plugins/tls/qopensslbackend.dll | 6.11.2.0 | wheel-record:PySide6_Essentials@6.11.2:PySide6/plugins/tls/qopensslbackend.dll | LGPL-3.0-only; embedded third-party terms pending build mapping | BLOCKER |
| _internal/PySide6/plugins/tls/qschannelbackend.dll | 6.11.2.0 | wheel-record:PySide6_Essentials@6.11.2:PySide6/plugins/tls/qschannelbackend.dll | LGPL-3.0-only; embedded third-party terms pending build mapping | BLOCKER |
| _internal/PySide6/pyside6.abi3.dll | unknown internal version | wheel-record:PySide6_Essentials@6.11.2:PySide6/pyside6.abi3.dll | LGPL-3.0-only | ACTION REQUIRED |
| _internal/Shapely.libs/geos-ae6efa0782962b98e358f10ea539ae5f.dll | 3.13.1 | wheel-record:shapely@2.1.2:Shapely.libs/geos-ae6efa0782962b98e358f10ea539ae5f.dll | LGPL-2.1 (upstream headers govern later-version option) | ACTION REQUIRED |
| _internal/Shapely.libs/geos_c-072b7a9224d16d3e4ab2395bb855b2d3.dll | 3.13.1 | wheel-record:shapely@2.1.2:Shapely.libs/geos_c-072b7a9224d16d3e4ab2395bb855b2d3.dll | LGPL-2.1 (upstream headers govern later-version option) | ACTION REQUIRED |
| _internal/Shapely.libs/msvcp140-90bc62d4947a5878f1dc1057312f3be2.dll | 14.44.35215.0 | wheel-record:shapely@2.1.2:Shapely.libs/msvcp140-90bc62d4947a5878f1dc1057312f3be2.dll | Microsoft proprietary redistributable terms: entitlement/origin unresolved | BLOCKER |
| _internal/VCRUNTIME140.dll | 14.42.34438.0 | CPython 3.14.6 installation:VCRUNTIME140.dll | Microsoft proprietary redistributable terms: entitlement/origin unresolved | BLOCKER |
| _internal/VCRUNTIME140_1.dll | 14.42.34438.0 | CPython 3.14.6 installation:VCRUNTIME140_1.dll | Microsoft proprietary redistributable terms: entitlement/origin unresolved | BLOCKER |
| _internal/_asyncio.pyd | 3.14.6 | CPython 3.14.6 installation:_asyncio.pyd | PSF-2.0 and applicable CPython extension subcomponent terms | ACTION REQUIRED |
| _internal/_bz2.pyd | 3.14.6 | CPython 3.14.6 installation:_bz2.pyd | PSF-2.0 and applicable CPython extension subcomponent terms | ACTION REQUIRED |
| _internal/_ctypes.pyd | 3.14.6 | CPython 3.14.6 installation:_ctypes.pyd | PSF-2.0 and applicable CPython extension subcomponent terms | ACTION REQUIRED |
| _internal/_decimal.pyd | 3.14.6 | CPython 3.14.6 installation:_decimal.pyd | PSF-2.0 and applicable CPython extension subcomponent terms | ACTION REQUIRED |
| _internal/_elementtree.pyd | 3.14.6 | CPython 3.14.6 installation:_elementtree.pyd | PSF-2.0 and applicable CPython extension subcomponent terms | ACTION REQUIRED |
| _internal/_hashlib.pyd | 3.14.6 | CPython 3.14.6 installation:_hashlib.pyd | PSF-2.0 and applicable CPython extension subcomponent terms | ACTION REQUIRED |
| _internal/_lzma.pyd | 3.14.6 | CPython 3.14.6 installation:_lzma.pyd | PSF-2.0 and applicable CPython extension subcomponent terms | ACTION REQUIRED |
| _internal/_multiprocessing.pyd | 3.14.6 | CPython 3.14.6 installation:_multiprocessing.pyd | PSF-2.0 and applicable CPython extension subcomponent terms | ACTION REQUIRED |
| _internal/_overlapped.pyd | 3.14.6 | CPython 3.14.6 installation:_overlapped.pyd | PSF-2.0 and applicable CPython extension subcomponent terms | ACTION REQUIRED |
| _internal/_queue.pyd | 3.14.6 | CPython 3.14.6 installation:_queue.pyd | PSF-2.0 and applicable CPython extension subcomponent terms | ACTION REQUIRED |
| _internal/_socket.pyd | 3.14.6 | CPython 3.14.6 installation:_socket.pyd | PSF-2.0 and applicable CPython extension subcomponent terms | ACTION REQUIRED |
| _internal/_sqlite3.pyd | 3.14.6 | CPython 3.14.6 installation:_sqlite3.pyd | PSF-2.0 and applicable CPython extension subcomponent terms | ACTION REQUIRED |
| _internal/_ssl.pyd | 3.14.6 | CPython 3.14.6 installation:_ssl.pyd | PSF-2.0 and applicable CPython extension subcomponent terms | ACTION REQUIRED |
| _internal/_uuid.pyd | 3.14.6 | CPython 3.14.6 installation:_uuid.pyd | PSF-2.0 and applicable CPython extension subcomponent terms | ACTION REQUIRED |
| _internal/_wmi.pyd | 3.14.6 | CPython 3.14.6 installation:_wmi.pyd | PSF-2.0 and applicable CPython extension subcomponent terms | ACTION REQUIRED |
| _internal/_zstd.pyd | 3.14.6 | CPython 3.14.6 installation:_zstd.pyd | PSF-2.0 and applicable CPython extension subcomponent terms | ACTION REQUIRED |
| _internal/fontTools/misc/bezierTools.cp314-win_amd64.pyd | unknown internal version | wheel-record:fonttools@4.65.0:fontTools/misc/bezierTools.cp314-win_amd64.pyd | MIT | ACTION REQUIRED |
| _internal/fontTools/varLib/iup.cp314-win_amd64.pyd | unknown internal version | wheel-record:fonttools@4.65.0:fontTools/varLib/iup.cp314-win_amd64.pyd | MIT | ACTION REQUIRED |
| _internal/libcrypto-3-x64.dll | 3.6.4 | ambient tool PATH: Poppler dependency/libcrypto-3-x64.dll | Apache-2.0 | BLOCKER |
| _internal/libcrypto-3.dll | 3.5.7 | CPython 3.14.6 installation:libcrypto-3.dll | Apache-2.0 | ACTION REQUIRED |
| _internal/libffi-8.dll | 3.4.4 (CPython source manifest) | CPython 3.14.6 installation:libffi-8.dll | MIT | BLOCKER |
| _internal/libssl-3-x64.dll | 3.6.4 | ambient tool PATH: Poppler dependency/libssl-3-x64.dll | Apache-2.0 | BLOCKER |
| _internal/libssl-3.dll | 3.5.7 | CPython 3.14.6 installation:libssl-3.dll | Apache-2.0 | ACTION REQUIRED |
| _internal/numpy.libs/libscipy_openblas64_-ed4f167a5330424524f45258e7ca2c8d.dll | 0.3.34.106.0 | wheel-record:numpy@2.5.3:numpy.libs/libscipy_openblas64_-ed4f167a5330424524f45258e7ca2c8d.dll | BSD-3-Clause AND BSD-3-Clause-Open-MPI AND (GPL-3.0-or-later WITH GCC-exception-3.1) | ACTION REQUIRED |
| _internal/numpy.libs/msvcp140-a4c2229bdc2a2a630acdc095b4d86008.dll | 14.40.33810.0 | wheel-record:numpy@2.5.3:numpy.libs/msvcp140-a4c2229bdc2a2a630acdc095b4d86008.dll | Microsoft proprietary redistributable terms: entitlement/origin unresolved | BLOCKER |
| _internal/numpy/_core/_multiarray_tests.cp314-win_amd64.pyd | unknown internal version | wheel-record:numpy@2.5.3:numpy/_core/_multiarray_tests.cp314-win_amd64.pyd | BSD-3-Clause and bundled NumPy terms | ACTION REQUIRED |
| _internal/numpy/_core/_multiarray_umath.cp314-win_amd64.pyd | unknown internal version | wheel-record:numpy@2.5.3:numpy/_core/_multiarray_umath.cp314-win_amd64.pyd | BSD-3-Clause and bundled NumPy terms | ACTION REQUIRED |
| _internal/numpy/fft/_pocketfft_umath.cp314-win_amd64.pyd | unknown internal version | wheel-record:numpy@2.5.3:numpy/fft/_pocketfft_umath.cp314-win_amd64.pyd | BSD-3-Clause and bundled NumPy terms | ACTION REQUIRED |
| _internal/numpy/linalg/_umath_linalg.cp314-win_amd64.pyd | unknown internal version | wheel-record:numpy@2.5.3:numpy/linalg/_umath_linalg.cp314-win_amd64.pyd | BSD-3-Clause and bundled NumPy terms | ACTION REQUIRED |
| _internal/numpy/random/_bounded_integers.cp314-win_amd64.pyd | unknown internal version | wheel-record:numpy@2.5.3:numpy/random/_bounded_integers.cp314-win_amd64.pyd | BSD-3-Clause and bundled NumPy terms | ACTION REQUIRED |
| _internal/numpy/random/_common.cp314-win_amd64.pyd | unknown internal version | wheel-record:numpy@2.5.3:numpy/random/_common.cp314-win_amd64.pyd | BSD-3-Clause and bundled NumPy terms | ACTION REQUIRED |
| _internal/numpy/random/_generator.cp314-win_amd64.pyd | unknown internal version | wheel-record:numpy@2.5.3:numpy/random/_generator.cp314-win_amd64.pyd | BSD-3-Clause and bundled NumPy terms | ACTION REQUIRED |
| _internal/numpy/random/_mt19937.cp314-win_amd64.pyd | unknown internal version | wheel-record:numpy@2.5.3:numpy/random/_mt19937.cp314-win_amd64.pyd | BSD-3-Clause and bundled NumPy terms | ACTION REQUIRED |
| _internal/numpy/random/_pcg64.cp314-win_amd64.pyd | unknown internal version | wheel-record:numpy@2.5.3:numpy/random/_pcg64.cp314-win_amd64.pyd | BSD-3-Clause and bundled NumPy terms | ACTION REQUIRED |
| _internal/numpy/random/_philox.cp314-win_amd64.pyd | unknown internal version | wheel-record:numpy@2.5.3:numpy/random/_philox.cp314-win_amd64.pyd | BSD-3-Clause and bundled NumPy terms | ACTION REQUIRED |
| _internal/numpy/random/_sfc64.cp314-win_amd64.pyd | unknown internal version | wheel-record:numpy@2.5.3:numpy/random/_sfc64.cp314-win_amd64.pyd | BSD-3-Clause and bundled NumPy terms | ACTION REQUIRED |
| _internal/numpy/random/bit_generator.cp314-win_amd64.pyd | unknown internal version | wheel-record:numpy@2.5.3:numpy/random/bit_generator.cp314-win_amd64.pyd | BSD-3-Clause and bundled NumPy terms | ACTION REQUIRED |
| _internal/numpy/random/mtrand.cp314-win_amd64.pyd | unknown internal version | wheel-record:numpy@2.5.3:numpy/random/mtrand.cp314-win_amd64.pyd | BSD-3-Clause and bundled NumPy terms | ACTION REQUIRED |
| _internal/pyexpat.pyd | 3.14.6 | CPython 3.14.6 installation:pyexpat.pyd | PSF-2.0 and applicable CPython extension subcomponent terms | ACTION REQUIRED |
| _internal/pyproj.libs/jpeg62-971fedc88cb0e86c3ad978ae1b7646db.dll | libjpeg-turbo 3.1.4.1 | wheel-record:pyproj@3.8.0:pyproj.libs/jpeg62-971fedc88cb0e86c3ad978ae1b7646db.dll | IJG AND BSD-3-Clause AND Zlib | ACTION REQUIRED |
| _internal/pyproj.libs/libcurl-f49442d4be7d953952a0509cdd4501fa.dll | 8.19.0 | wheel-record:pyproj@3.8.0:pyproj.libs/libcurl-f49442d4be7d953952a0509cdd4501fa.dll | curl | ACTION REQUIRED |
| _internal/pyproj.libs/liblzma-3c4c8780fcad6ce56344d2b5594bda5b.dll | 5.8.3 | wheel-record:pyproj@3.8.0:pyproj.libs/liblzma-3c4c8780fcad6ce56344d2b5594bda5b.dll | 0BSD and applicable XZ upstream terms | ACTION REQUIRED |
| _internal/pyproj.libs/msvcp140-7c26614e1d733892c2deac7e245ce115.dll | 14.51.36247.0 | wheel-record:pyproj@3.8.0:pyproj.libs/msvcp140-7c26614e1d733892c2deac7e245ce115.dll | Microsoft proprietary redistributable terms: entitlement/origin unresolved | BLOCKER |
| _internal/pyproj.libs/proj_9-7e5618bddacc5af688a84f477cf114c3.dll | 9.8.1 | wheel-record:pyproj@3.8.0:pyproj.libs/proj_9-7e5618bddacc5af688a84f477cf114c3.dll | MIT | ACTION REQUIRED |
| _internal/pyproj.libs/sqlite3-9415ebc42378ab15b741623972c45846.dll | 3.53.0 | wheel-record:pyproj@3.8.0:pyproj.libs/sqlite3-9415ebc42378ab15b741623972c45846.dll | Public domain | ACTION REQUIRED |
| _internal/pyproj.libs/tiff-69dcdf91c822b00d23e8dbf49655fe78.dll | 4.7.1 | wheel-record:pyproj@3.8.0:pyproj.libs/tiff-69dcdf91c822b00d23e8dbf49655fe78.dll | libtiff | ACTION REQUIRED |
| _internal/pyproj.libs/zlib1-985e9fefa27bf900be8e4df7dcc97287.dll | 1.3.1 | wheel-record:pyproj@3.8.0:pyproj.libs/zlib1-985e9fefa27bf900be8e4df7dcc97287.dll | Zlib | ACTION REQUIRED |
| _internal/pyproj/_compat.cp314-win_amd64.pyd | unknown internal version | wheel-record:pyproj@3.8.0:pyproj/_compat.cp314-win_amd64.pyd | MIT | ACTION REQUIRED |
| _internal/pyproj/_context.cp314-win_amd64.pyd | unknown internal version | wheel-record:pyproj@3.8.0:pyproj/_context.cp314-win_amd64.pyd | MIT | ACTION REQUIRED |
| _internal/pyproj/_crs.cp314-win_amd64.pyd | unknown internal version | wheel-record:pyproj@3.8.0:pyproj/_crs.cp314-win_amd64.pyd | MIT | ACTION REQUIRED |
| _internal/pyproj/_geod.cp314-win_amd64.pyd | unknown internal version | wheel-record:pyproj@3.8.0:pyproj/_geod.cp314-win_amd64.pyd | MIT | ACTION REQUIRED |
| _internal/pyproj/_network.cp314-win_amd64.pyd | unknown internal version | wheel-record:pyproj@3.8.0:pyproj/_network.cp314-win_amd64.pyd | MIT | ACTION REQUIRED |
| _internal/pyproj/_sync.cp314-win_amd64.pyd | unknown internal version | wheel-record:pyproj@3.8.0:pyproj/_sync.cp314-win_amd64.pyd | MIT | ACTION REQUIRED |
| _internal/pyproj/_transformer.cp314-win_amd64.pyd | unknown internal version | wheel-record:pyproj@3.8.0:pyproj/_transformer.cp314-win_amd64.pyd | MIT | ACTION REQUIRED |
| _internal/pyproj/_version.cp314-win_amd64.pyd | unknown internal version | wheel-record:pyproj@3.8.0:pyproj/_version.cp314-win_amd64.pyd | MIT | ACTION REQUIRED |
| _internal/pyproj/database.cp314-win_amd64.pyd | unknown internal version | wheel-record:pyproj@3.8.0:pyproj/database.cp314-win_amd64.pyd | MIT | ACTION REQUIRED |
| _internal/pyproj/list.cp314-win_amd64.pyd | unknown internal version | wheel-record:pyproj@3.8.0:pyproj/list.cp314-win_amd64.pyd | MIT | ACTION REQUIRED |
| _internal/python3.dll | 3.14.6 | CPython 3.14.6 installation:python3.dll | PSF-2.0 and applicable CPython extension subcomponent terms | ACTION REQUIRED |
| _internal/python314.dll | 3.14.6 | CPython 3.14.6 installation:python314.dll | PSF-2.0 and applicable CPython extension subcomponent terms | ACTION REQUIRED |
| _internal/select.pyd | 3.14.6 | CPython 3.14.6 installation:select.pyd | PSF-2.0 and applicable CPython extension subcomponent terms | ACTION REQUIRED |
| _internal/shapely/_geometry_helpers.cp314-win_amd64.pyd | unknown internal version | wheel-record:shapely@2.1.2:shapely/_geometry_helpers.cp314-win_amd64.pyd | BSD-3-Clause | ACTION REQUIRED |
| _internal/shapely/_geos.cp314-win_amd64.pyd | unknown internal version | wheel-record:shapely@2.1.2:shapely/_geos.cp314-win_amd64.pyd | LGPL-2.1 (upstream headers govern later-version option) | ACTION REQUIRED |
| _internal/shapely/lib.cp314-win_amd64.pyd | unknown internal version | wheel-record:shapely@2.1.2:shapely/lib.cp314-win_amd64.pyd | BSD-3-Clause | ACTION REQUIRED |
| _internal/shiboken6/MSVCP140.dll | 14.44.35211.0 | wheel-record:shiboken6@6.11.2:shiboken6/MSVCP140.dll | Microsoft proprietary redistributable terms: entitlement/origin unresolved | BLOCKER |
| _internal/shiboken6/Shiboken.pyd | unknown internal version | wheel-record:shiboken6@6.11.2:shiboken6/Shiboken.pyd | LGPL-3.0-only | ACTION REQUIRED |
| _internal/shiboken6/VCRUNTIME140.dll | 14.44.35211.0 | wheel-record:shiboken6@6.11.2:shiboken6/VCRUNTIME140.dll | Microsoft proprietary redistributable terms: entitlement/origin unresolved | BLOCKER |
| _internal/shiboken6/VCRUNTIME140_1.dll | 14.44.35211.0 | wheel-record:shiboken6@6.11.2:shiboken6/VCRUNTIME140_1.dll | Microsoft proprietary redistributable terms: entitlement/origin unresolved | BLOCKER |
| _internal/shiboken6/shiboken6.abi3.dll | unknown internal version | wheel-record:shiboken6@6.11.2:shiboken6/shiboken6.abi3.dll | LGPL-3.0-only | ACTION REQUIRED |
| _internal/sqlite3.dll | 3.50.4.0 | CPython 3.14.6 installation:sqlite3.dll | Public domain | ACTION REQUIRED |
| _internal/unicodedata.pyd | 3.14.6 | CPython 3.14.6 installation:unicodedata.pyd | PSF-2.0 and applicable CPython extension subcomponent terms | ACTION REQUIRED |

## Generated inventory summary

{'native_files': 115, 'pure_modules': 1216, 'data_files': 458, 'python_distribution_families': 17, 'qt_modules': 7, 'qt_plugins': 21}; 16 byte-matched embedded fonts. Legal index: 159 text/copyright files (124 unique hashes), 35 authoritative attribution JSON files; 35 duplicate byte copies; one source-only Noto text excluded. All statuses remain conservative until B1–B5 close.
