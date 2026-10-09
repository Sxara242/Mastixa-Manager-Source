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

> Current2026-10-08 upstream receipt review: B1/B4 BLOCKED for requested exact
> correspondence; unavailable CI logs are not an independent legal requirement.
> B3 rights/terms basis remains unresolved; B2/B5 PASS RETAINED.
> See WINDOWS_UPSTREAM_RECEIPT_CLOSURE.md, windows-upstream-receipt-closure.json,
> WINDOWS_DEPENDENCY_REBUILD.md and windows-release-retention-manifest.json.
> Older producer-log/full-rebuild blocker wording below is superseded.

# Final named provider and modification disposition — 2026-10-08

B3 remains BLOCKED. Four original Esri lookup branches and six NKG2020 national
parameter sets are now closed; see windows-producer-rebuild-receipts.json.
CH/GL27/nad27/nad83/world/other.extra are named PROJ definition files covered by
the explicit PROJ COPYING source/data grant; no external grid payloads ship.
ITRF2000 (ITRF.TP/ITRF2005 inverse), ITRF2008 (Transfo-ITRF2008_ITRFs.txt),
ITRF2014 (Transfo-ITRF2014_ITRFs.txt) retain independent IGN/IERS grant gaps.
ITRF2020 is generated from EPSG. IGNF.v3.1.0.xml and IAU2015 report constants retain
their named independent input-grant gaps. LT2008's five-micrometre y discrepancy
is present at initial PROJ SQL introduction; its reason is not proved.

EPSG: Mastixa has no build/runtime database edits and ships wheel bytes unchanged.
Observed modifications are upstream PROJ-only. EPSG terms2016 permit specified
parameter changes with equivalent geodetic results and forbid attributing other
impermissibly modified data to EPSG. Full terms/IOGP ownership/no-warranty must be
delivered. There is no mandatory literal generic modification sentence in those
terms. Mastixa's own accurate disclosure below identifies upstream changes; it
does not resolve the900913 alias/1312/1462 accuracy-attribution compliance issue.

Recipient disclosure: The EPSG Dataset is owned by IOGP. Mastixa includes its
representation supplied by PROJ9.8.1/pyproj3.8.0, with upstream PROJ adaptations,
including alias900913, unit annotations, interpolation-CRS metadata and accuracy
metadata changes for operations1312/1462. Mastixa makes no further database edits.
The complete EPSG Terms of Use and their no-warranty conditions are included.

NKG attribution: Häkli, P., Evers, K., Jivall, L., Nilsson, T., Himle, S., Kollo, K.,
Liepiņš, I., Paršeliūnas, E., Vestøl, O., and Lidberg, M. (2023), NKG2020
transformation, DOI10.1515/jogs-2022-0155, Table3/section6.3, CC-BY4.0; national
parameters converted from ppb/mas into PROJ ppm/arcseconds. Prior NKG2008 source
attribution and full CC-BY4 license remain. Inherited provider rights are separate.

---

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

Current EPSG classification: mechanical import plus upstream augmentation/customization; no Mastixa edits. Updates to EPSG1312/1462 accuracy and interpolation CRS require full permitted-change review, in addition to900913 alias/short names. Targeted authority impact/input receipts in windows-crs-resources.json.

---

# Final CRS decision — 2026-10-07

**B3 BLOCKED.** Actual shipped resources remain byte-unchanged. Exact PROJ9.8.1
source SQL concatenation matches the upstream checksum and shipping database
canonical rows in all39 tables/77707 rows; this proves data correspondence, not
all original grants. EPSG v12.029 full terms/IOGP attribution remain delivered.
`customizations.sql` adds EPSG900913 alias of3857 and other customizations; complete
permitted-modification/numerical-equivalence compliance remains unproved. No
infringement conclusion is inferred from the existence of an alias.

Esri ArcGIS Pro3.6 v3.6.0 commit3d731f6b37e1cfa50d235886f6a26973ae17201b:
retain full Apache2 license and Esri copyright; exact archive has no separate
NOTICE. PROJ transforms its input through build_db_from_esri.py. NKG input README
7303593512f0133cde17324496dddec4616bcdc7 grants CC BY4; retain full terms and
credit Nordic Geodetic Commission (NKG), NordicTransformations. PROJ nkg.sql is
hand-written transformation metadata. Exact input-to-derived-record relationship
still needs supplier evidence; a software MIT grant is not substituted for it.

IGNF3.1.0 exact XML is retained but no exact dataset redistribution grant was
established; general website policies are insufficient. ITRF init headers and
IAU2015 DOI/constants origin remain distinct unresolved input terms. NRCAN and
OGC are PROJ-created definitions with EPSG inheritance; they do not automatically
close EPSG terms. CH contains definitions/references to absent Swisstopo grids;
grid licenses are not imposed on nonexistent grid bytes. No tilepack, external
grid payload, owner geospatial data or network download is added. Resource-by-
resource authoritative decision in windows-crs-resources.json; B3 stays blocked.

---

# Shipping CRS data and attribution — 2026-10-07

**B3 BLOCKED.** The exact qualified pyproj 3.8.0 wheel supplies PROJ 9.8.1
`pyproj/proj_dir/share/proj/proj.db`, SHA-256
`528b9763b57e85ee78f6f30478ef0494902320f1d71d1564bf0d7ec4f30cc002`.
`windows-crs-resources.json` enumerates all **29** shipping files in that PROJ
resource directory, including CRS tables/init files, schemas, configuration and
build metadata. Pyproj C/PYX/PXD files outside it are software sources, not new
datasets. No dataset bytes or GIS behavior were changed.

| Database authority | Actual version/origin | Data terms / remaining action |
| --- | --- | --- |
| EPSG | v12.029, 2025-10-02 | Official full 2016-04-08 terms retrieved and supplied; check PROJ-generated/customized records against permitted modification rules. |
| ESRI | ArcGIS Pro 3.6, 2025-12-01 | Official projection-engine-db-doc Apache-2.0 grant located. Pin the exact input revision with copyright/NOTICE and modification correspondence. |
| IGNF | 3.1.0, 2019-05-24 | DB points to the exact mirrored IGN XML. Original version-specific dataset grant/attribution remains unproven; current website metadata is insufficient. |
| IAU_2015 | IAU 2015 constants, DOI 10.1007/s10569-017-9805-5 | PROJ generator MIT and derived-data grant are known; resolve original constants/data attribution separately from the article's publication license. |
| NKG | 1.0.w, 2025-02-13 | CC-BY-4.0 explicit upstream grant found in the contemporaneous README at commit 7303593512f0133cde17324496dddec4616bcdc7. Map exact NKG/member attributions and derivation for hand-generated nkg.sql. |
| NRCAN | PROJ 9.8.1 custom registry | Resolve exact Canadian source metadata/data terms. Referenced grid filenames are not evidence that grid bytes ship. |
| OGC | PROJ 9.8.1 definitions | PROJ data MIT text supplied; reconcile external definition/descriptive input terms. |
| PROJ | 9.8.1 original/custom definitions | COPYING expressly grants MIT terms for PROJ data; preserve source/file copyrights and inherited registry conditions. |

The [exact PROJ source README](https://github.com/OSGeo/PROJ/blob/9.8.1/data/sql/README.md)
identifies database generators/registries. The software MIT license does not
override third-party data conditions. The exact local database authority list
also includes NRCAN and OGC; do not omit these by copying the README summary.

The [official EPSG terms](https://epsg.org/terms-of-use.html) were successfully
retrieved from the authoritative endpoint in this continuation. The full legal
body, mathematical modifications table and revision history are preserved in
`licenses/EPSG/TERMS-OF-USE-2016.html`, with source/hash indexed. It is self-contained,
with no external scripts, fonts or images. The prior 403 is superseded.

The EPSG Dataset is owned by the International Association of Oil & Gas
Producers (IOGP). Preserve that attribution and supply the terms to recipients.
Redistribution is conditional, including rules for commercial added value and
numerically equivalent modifications; unrestricted MIT treatment is incorrect.
Mastixa ships the unmodified wheel data, which is already a PROJ-generated
representation with source customizations. Its relationship to those permitted
changes remains a specific closure item; no new acceptance or relicense is made.
The retrieved terms do not impose a generic copyleft source-mirror obligation.

`ITRF2020` explicitly derives from EPSG. `ITRF2000/2008/2014` carry IGN/ITRF
source references; `CH` references Swisstopo grids and `GL27`/`nad27`/`nad83`/
`world`/`other.extra` have their own retained PROJ file headers. The per-resource
ledger keeps these input rights unresolved where needed. No Swisstopo/IGN/NKG
grid payload, sample dataset or offline tile pack is included. PROJ-data 1.24
in metadata denotes compatibility, not shipment of the entire PROJ-data pack.

Required GIS paths use EPSG 4326/2100 and the PROJ database. Removing the
database or pruning its authorities is not justified by absence of user-facing
registry selection. No exclusion was made. Optional OSM HTTPS visible-tile use
retains existing © OpenStreetMap contributors attribution; cached user tiles
are not installer inputs. No provider/automatic network behavior was added.

Close B3 by retaining each exact original data grant and appropriate attribution,
modification and data-access conditions in the ledger and bundled notices.
Rights that remain UNKNOWN are still blockers; locating EPSG alone is insufficient.
