> Retained historical engineering record, sanitized for public review.
> Current status: [RELEASE_STATUS.md](RELEASE_STATUS.md). This record does not
> establish approval of the current source or a new binary release. Local-only
> receipt paths refer to privately retained evidence, absent from this snapshot.

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

## Future artifact batch: mandatory Bitdefender rule retained

Owner explicitly authorizes temporary Administrator PowerShell solely to manage
the actual RC build exclusion. Resolve the actual PyInstaller/Inno build/work/
output directory; never invent/rename PROSORINA. Exclude only the entire actual
build/work/output directory through a supported Bitdefender CLI/API/policy if
available. Do not exclude repo root, user profile, drive or unrelated paths;
do not disable Bitdefender or use undocumented registry hacks. Record the exact
exclusion, remove it after artifact validation and verify removal. If manual
action is required, STOP before build, show the exact directory and wait
indefinitely for explicit OK/Done/Continue: no countdown, timeout or auto-continue.
No exclusion or Administrator antivirus action was performed in this batch.

## Required supplier/provider response checklist

### B1

- QtPdf/qpdf exact executed GN target/source/link/patch/compiler/SDK/GN/Ninja graph tied to current hashes
- Eight PySide/shiboken outputs: executed Shiboken/libclang/headers/options/generated-source/compiler receipt or exact reproducible regeneration
- OpenBLAS static GCC/libgfortran exact executed version/source/exception and published artifact-to-DLL correspondence; successful CI job receipt alone is insufficient

### B3

- Esri original generator lookup state (four records now trace to exact input parameters/usage; whole regeneration remains unmatched)
- NKG Lithuania ty0.11549 input vs0.115495 SQL, exact NKG2020/member/inherited-input derivation
- Exact IGNF3.1.0, ITRF2000/2008/2014, IAU2015 and inherited init-data redistribution/derivation terms
- EPSG upstream permitted-modification/numerical-equivalence compliance; unchanged Mastixa bytes do not settle upstream compliance

### B4

- Matching executed QtPdf/binding/GEOS/GCC build/config/patch/generator/toolchain materials
- Rebuild instructions for compatible covered libraries remain incomplete; benign QtPdf resource-variant loading is proven
- Final binary/source binding and public equivalent source access at later authorized build/distribution; not claimed before an artifact exists

For each receipt include exact shipped path/SHA, original source archive/tag/commit,
all patches or an explicit no-patch statement, actual build/generator commands and
flags/tool versions, generated outputs and hashes, and compatible recipient rebuild
steps. For each provider include exact input version/member, SQL/record path,
redistribution/derived/modification permission, attribution/disclaimer and downstream
terms. Evidence must cover the retained bytes; general project URLs are insufficient.
No supplier/provider was messaged on the owner's behalf.
