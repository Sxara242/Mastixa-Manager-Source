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
