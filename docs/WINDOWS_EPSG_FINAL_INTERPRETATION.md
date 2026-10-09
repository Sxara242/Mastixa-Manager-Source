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

# Final EPSG 6(vii) downstream assessment — 2026-10-08

**EPSG BLOCKED; B3 BLOCKED; BLOCKED BEFORE RC BUILD.** RELEASE-INFRA / DESKTOP.
The blocker is the identified attribution of PROJ-adjusted accuracy for operations
1312/1462, including direct serialized representations. It is not missing historical
explanation, lack of a supplier approval letter, or a requirement to prove universal
compliance of every database row. No infringement finding is made. B1/B2/B4/B5
legal PASS, IGNF/IAU PASS and all other retained conclusions remain unchanged.
Final pre-RC preflight is NOT RUN because B3 is not PASS. No RC is built.

## Controlling text and precise scope

The [current official EPSG terms](https://epsg.org/terms-of-use.html) were retrieved
over HTTPS in this batch (HTTP200). The page is still revised 8 April 2016; its
SHA256 is 7f11216ab229388bb6230f60dfa0dbe6426ec43f28a73944f32f6fb47e7bb7c7,
identical to the retained official page. The selected recipient copy is
licenses/EPSG/TERMS-OF-USE-2016.html. Full text remains supplied; the following
mapping does not replace it.

Clause 6(vii), exactly:

> No data that has been modified other than as permitted in these Terms of Use shall be attributed to the EPSG Dataset.

| Provision | Conduct and obligation |
| --- | --- |
| 1, definition of the data | Covers geodetic parameters AND associated metadata, including subsets. Accuracy is not outside the term merely because it is metadata. |
| 2 and 6(iii) | EPSG Facilities are supplied without charge; commercial software inclusion is allowed where commerciality concerns the provider's added value, not sale of the EPSG Dataset itself. |
| 4–5 | Use accepts the terms, including use without registry click acceptance. Obtaining the data through PROJ does not create a downstream exemption. |
| 6 opening words | Affirmative permission to use, copy and distribute, subject to the stated conditions. |
| 6(i)–(ii) | Supply the terms to recipients; preserve the IOGP liability disclaimer and AS-IS/no-warranty text. |
| 6(iv) | Acknowledge IOGP ownership of EPSG Dataset material, including permitted modifications. This is distinct from attributing an independent override to EPSG. |
| 6(v) | Subsets are allowed; completeness advice refers to essential elements in Guidance Note7-1 AnnexA. |
| 6(vi), Table1 | Enumerated numerically equivalent ellipsoid/projection/transformation parameter representations are permitted. Table1 is not general permission for any edit that happens to leave one fixed operation's coordinates unchanged. |
| 6(vii) | Other modified material must not be attributed to the EPSG Dataset. It is an attribution restriction, not a blanket ban on deriving or redistributing independently identified adapted material. |

The obligation reaches the modifier when producing/attributing adaptations and
the copier/distributor when distributing that representation. Mastixa bears the
conditions of its own copying/distribution; it does not become PROJ's original
modifier. The provision attaches to modified material, including affected fields,
not automatically to every unchanged record in the database. Neither a complete
database renaming rule nor a prescribed database-column format appears in it.

The text does **not** expressly mandate removing every EPSG code or setting every
auth_name to something else. Reference to the original operation, datum, unit,
method or CRS can be accurate. Conversely, keeping a code for interoperability
does not automatically prove that altered metadata is dissociated. Attribution
must be assessed from the actual object/representation and accompanying information.
This interpretation is drawn from the text; it is not a new IOGP policy.

## Four objects, separately

Codes are scoped by object type. Operation7001 below is not ellipsoid7001.
Source values refer to the EPSG v12.029 import in the retained PROJ9.8.1 source,
not a claim that current registry data has never changed. The attempted guessed
official operation JSON endpoints returned404 and supply no source values.
The authoritative upstream importer, generated SQL, comments and commits are
the source for the values below.

| Object | EPSG import / source | Current PROJ database | Classification and authority |
| --- | --- | --- | --- |
| grid_transformation1312, NAD27 to NAD83(3) | accuracy1.0m; NTv1; method9614; source4267, target4269 | accuracy2.0m; same method/source/target/grid; auth_name EPSG, code1312 | Accuracy reinterpretation for operation ranking; not a coordinate-parameter conversion or newly measured accuracy. No stored DERIVED_FROM marker. Upstream-only. |
| grid_transformation1462, NAD27 to NAD83(5) | accuracy1.0m; NTv1; method9614; source4267, target4269 | accuracy2.0m; same method/source/target/grid; auth_name EPSG, code1462 | Same ranking workaround; no stored DERIVED_FROM marker. Upstream-only. |
| grid_transformation7001, ETRS89 to NAP height(1) | accuracy0.01m, deprecated1; interpolation CRS absent | accuracy/deprecation unchanged; interpolation_crs_auth_name EPSG, code4289 added; operation EPSG:7001 retained | Implementation metadata enrichment / upstream correction of missing interpolation context. EPSG:4289 correctly identifies the Amersfoort CRS; adding the link is PROJ's act. Not an unofficial operation or accuracy override. |
| projected_crs900913, Google Maps Global Mercator | No projected CRS900913 in the EPSG-generated projected_crs.sql; official equivalent3857 | Hand-created alias, EPSG authority/code900913, deprecated1; usage authority PROJ; equivalent to3857 | Non-EPSG convenience/legacy alias with retained compatibility identifier. Not an official EPSG-issued deprecated code. Its deprecated flag is PROJ's flag. |

The 1312/1462 edit is exactly traced to
[commit b8f8a708c2299ba55b3d4754aa75633e3ee5897b](https://github.com/OSGeo/PROJ/commit/b8f8a708c2299ba55b3d4754aa75633e3ee5897b),
Even Rouault, 2019-12-25 15:23:31 UTC. His commit explains that retaining NTv1
availability after removing supersession filtering made NTv1's1.0m outrank NTv2's
1.5m when both were valid/available; worsening NTv1's advertised accuracy to2m
makes NTv2 preferred. This is maintainers' deliberate selection workaround, not
unexplained corruption or a Mastixa edit. Do not infer that every transformation
result stays identical: changed ranking can select a different operation.

The 7001 addition is traced to
[commit61cf8c5b29c82ab7e46b207bd125eaad49c03021](https://github.com/OSGeo/PROJ/commit/61cf8c5b29c82ab7e46b207bd125eaad49c03021),
Even Rouault, 2019-05-06. Its purpose is applying the vertical grid on Amersfoort
before the horizontal shift. The source cites the RDTRANS2008/NAPTRANS2008 usage
document and guards against silently overriding an already populated interpolation
CRS. No assertion of an EPSG-approved revision follows from this source comment.

The 900913 SQL insertion already appears in
[commit d928db15d53805d9b728b440079756081961c536](https://github.com/OSGeo/PROJ/commit/d928db15d53805d9b728b440079756081961c536),
Even Rouault, 2018-11-14, the initial SRS database integration. That establishes
PROJ's database insertion date, not the invention date of the legacy Google alias.
Current read-only CRS construction confirms equality with3857. Mathematical
equivalence does not make900913 an official EPSG identifier.

## PROJ model, intent and actual representation

The exact retained PROJ9.8.1 archive supplies scripts/build_db.py,
data/sql/grid_transformation.sql, projected_crs.sql, customizations.sql,
data/CMakeLists.txt, COPYING, and the previously retained ISO19111 sources.
The importer copies EPSG operation accuracy into generated SQL. The build then
applies hand-generated customizations, leaving the inspected two accuracy fields
under EPSG identifiers. The build files install the resulting PROJ database;
this is not a Mastixa-local patch or an official EPSG database export.

PROJ's compliance/representation model contains explicit independent PROJ
definitions, source=PROJ aliases and conditional DERIVED_FROM(EPSG) identifiers.
oputils.cpp:addModifiedIdentifier and singleoperation.cpp:createSimilarProperties
can distinguish adapted operations. factory.cpp:createGridTransformation reads
the record accuracy/interpolation CRS under the requested authority and only
certain alternative-grid paths produce derived identifiers. Other independent
SQL entries use PROJ authority. This is intentional provenance separation in
specific paths, not evidence of universal marking or a documented waiver for
every adjusted-accuracy object.

The [OSGeo incubation exchange](https://discourse.osgeo.org/t/sac-osgeo-2268-incubation-request-proj/3298)
on2019-03-29 explicitly discusses6(vii) and redistribution of dissociated modified
data. It is primary upstream practice, not an IOGP approval or policy about the
two later2019 accuracy edits. PROJ COPYING covers PROJ's own source/data work;
it does not erase inherited EPSG conditions. Existing distribution by other
projects corroborates upstream practice but is not an independent legal exception.

New bounded read-only construction/serialization of the four objects supplies a
concrete difference from the earlier database-only checkpoint. Direct
CoordinateOperation.from_epsg(1312/1462) exports WKT with OPERATIONACCURACY[2.0]
and ID[EPSG,1312/1462], and PROJJSON with accuracy2.0 and authority EPSG. The
record's remarks do not identify the ranking override. No DERIVED_FROM label
appears on these direct objects. Therefore it is not supported to assert that
EPSG authority is necessarily confined to an unaltered original object while
every adapted field is separately identified. No grids or transformations were
executed or downloaded. Other runtime paths may label derived operations;
this finding is limited to the measured direct representations.

7001 exports its supplied interpolation CRS4289 with EPSG operation identity;
900913 exports the compatibility EPSG identifier. Neither is conflated with
1312/1462. Their documented origin improves explanatory attribution but does not
establish that every EPSG-labeled adaptation has provider approval. They are
not additional independently asserted RC blockers in this batch.

## Downstream result and possible notice

Mastixa may redistribute EPSG-containing data under clause6 when its conditions
are met. It need not independently regenerate PROJ, inspect every upstream row,
possess private build logs, or obtain an approval letter as a general prerequisite.
It must actually supply the full terms/disclaimer/ownership notice, describe
the included product truthfully, and address a specific known attribution problem.
Upstream notices help satisfy recipient obligations but unchanged upstream bytes
do not exempt a downstream copier from6(vii).

A statement that the database is PROJ-derived and not the official EPSG Dataset
is accurate. The terms do not prescribe that literal sentence. A generic statement
that some metadata may differ is weaker than explicit identification of the
modified field. Neither statement can be presented as proven cure for known
direct exports that still present overridden accuracy under EPSG authority.
Absence of an IOGP letter is not itself the blocker; the unresolved substantive
attribution in these representations is. No authoritative material located in
this scoped review settles that an external generic notice qualifies them.

Minimum accurate **candidate** disclosure, if a notice-based remedy is later
established as sufficient (factual provenance wording, not custom license terms):

> The EPSG Dataset is owned by IOGP. Mastixa includes PROJ9.8.1's database, which
> incorporates EPSG-derived data and is not the official EPSG Dataset. PROJ,
> rather than EPSG/IOGP, supplies the2.0m ranking accuracy for operations1312/1462
> (the imported EPSG values are1.0m), the interpolation CRS addition for7001,
> and the unofficial deprecated900913 compatibility alias of3857. Mastixa makes
> no further database changes. Consult epsg.org for official current definitions.
> The full EPSG Terms of Use and their disclaimers are supplied separately.

This draft is retained here; it is **not** claimed as an approved clearance or
added redundantly to THIRD_PARTY_NOTICES. Existing full terms, IOGP credit,
disclaimer and PROJ-adaptation disclosure remain selected. Settings' existing
Open Source legal button opens THIRD_PARTY_NOTICES; no UI change is needed to
deliver a future approved notice. No new provider terms are invented.

**EPSG BLOCKED** for the current unchanged representation: there is no established
notice-only downstream basis resolving the named modified-accuracy attribution.
The clause does not explicitly name auth_name, forbid all EPSG code references,
or require deleting the entire database. A defensible dissociation must operate
at the relevant material/representation level; conditional marking elsewhere
does not settle these known direct objects. This is a bounded release assessment,
not a court finding about PROJ or a claim that all upstream adaptations violate6(vii).

## Narrowest next action and boundaries

The exact blocker resides in grid_transformation(EPSG,1312/1462).accuracy and
their direct WKT/PROJJSON representation. A notice remedy must specifically
disattribute those fields and establish that accompanying provenance suffices
for the emitted objects; generic attribution alone is not enough to certify it.
A concrete data alternative is restoring only those two accuracy values to the
imported1.0m, retaining the genuine operation identifiers. That eliminates this
specific override, but can change operation ranking and requires focused selection
and affected-import validation. Relabeling derived operations instead requires
reference/lookup handling; a two-column auth_name edit alone is not a qualified
solution. 7001/900913 must be separately accounted for in any chosen remediation.
Do not prune the database or apply any unqualified change automatically.

No database edit is made: non-compliance is not adjudicated, the requested batch
prioritizes an unchanged database, and a notice-only clearance has not been
established. The next concrete decision is a scoped assessment of the above
field-specific notice against the direct EPSG-ID representations; failing that,
qualify the two-accuracy restoration with separate7001/900913 treatment. No full
PROJ audit, B1/B2/B4/B5/IGNF/IAU reopening, or final RC build is needed for that step.

## Verification and future build rule

Focused receipts: ../WindowsEpsgFinalInterpretationEvidence/{primary-receipts.json,
history-receipts.json,named-records.json,representation.json,final-report.json}.
The unchanged proj.db hash is
528b9763b57e85ee78f6f30478ef0494902320f1d71d1564bf0d7ec4f30cc002.
Prior39-table/77707-row correspondence is retained without reanalysis.
Publish safety concerns selected planned binary inputs and the new bounded source
overlay, not a nonexistent RC or approval to publish historical raw evidence.
No automatic deletions, commit, push, tag, upload, publication or build occurs.

For any future separately authorized build, temporary Administrator PowerShell is
authorized solely for supported Bitdefender exclusion management of the exact
actual PyInstaller/Inno build/work/output directory. Never create/rename a folder
PROSORINA, exclude repository/profile/drive/unrelated directories, disable global
protection or use undocumented registry hacks. Record the exact exclusion;
remove it after artifact validation and verify removal. If manual action is
required, STOP before build, show the exact path, and wait indefinitely for owner
OK/Done/Continue; no countdown, timeout or automatic continuation.
