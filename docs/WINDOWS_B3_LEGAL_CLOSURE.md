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

# EPSG attribution follow-up — 2026-10-08

**BLOCKED BEFORE RC BUILD.** This bounded follow-up retains IGNF3.1.0 and IAU
PASS, B1/B2/B4/B5 legal PASS, and the existing EPSG/B3 BLOCKED decision.
No rights decision is reopened merely because historical paperwork is incomplete.

New evidence: the exact retained PROJ9.8.1 source archive supplies
src/iso19111/factory.cpp, operation/singleoperation.cpp and operation/oputils.cpp.
Source member hashes and four read-only database records are recorded locally in
WindowsB3AttributionReviewEvidence/named-records.json. No database rebuild or
full analysis was performed. The database hash remains
528b9763b57e85ee78f6f30478ef0494902320f1d71d1564bf0d7ec4f30cc002.

## Does PROJ distinguish derived data?

Yes, in specific production paths. singleoperation.cpp:2305-2323 constructs
similar operation properties through addModifiedIdentifier with derivedFrom=true;
oputils.cpp:177-210 constructs DERIVED_FROM authority labels. Alternative-grid
substitution invokes that mechanism; visualization normalization also labels its
derived operation. This improves the earlier description of upstream compliance:
PROJ has explicit runtime dissociation as well as PROJ-authority SQL entries and
source=PROJ aliases. It is inaccurate to say PROJ never marks derived objects.

However, this is conditional marking, not an unconditional label attached to every
customized EPSG record. factory.cpp:6480-6637 reads accuracy and interpolation CRS
from grid_transformation, creates properties through the requested authority, and
optionally substitutes alternative grids. customizations.sql:136-145 overwrites
1312/1462 accuracy from1.0 to2.0 for ranking. The actual stored rows still have
auth_name=EPSG. No statement is made about every possible serialized runtime output;
this review does not execute transformations or load external grids.

[PROJ's official explanation](https://proj.org/en/stable/operations/operations_computation.html)
shows derived and unqualified EPSG labels side by side, including modified2.0m
accuracy in its inverse example. Its own text identifies older example versions
and database sensitivity; the documentation is corroboration, not a substitute
for the actual9.8.1 records/source. The exact source references are
[factory.cpp](https://github.com/OSGeo/PROJ/blob/9.8.1/src/iso19111/factory.cpp),
[singleoperation.cpp](https://github.com/OSGeo/PROJ/blob/9.8.1/src/iso19111/operation/singleoperation.cpp),
[oputils.cpp](https://github.com/OSGeo/PROJ/blob/9.8.1/src/iso19111/operation/oputils.cpp),
and [customizations.sql](https://github.com/OSGeo/PROJ/blob/9.8.1/data/sql/customizations.sql).

## Specific legal decision and limits

The controlling [official EPSG terms](https://epsg.org/terms-of-use.html), revision
2016-04-08, are already fully retained and delivered. Clause1 includes associated
metadata; clause6 grants conditioned copying/distribution. Clause6(vi)/Table1
permits specified equivalent parameter representations. Clause6(vii) separates
other modified data from attribution to the EPSG Dataset. Accuracy changes for
operation ranking are not a Table1 unit/parameter equivalence. The narrow issue is
whether retained authority labels identify only the original operation, sufficiently
dissociating the altered accuracy, or still attribute that altered metadata to EPSG.
No applicable provider interpretation settling that question was located.

The [primary upstream incubation discussion](https://discourse.osgeo.org/t/sac-osgeo-2268-incubation-request-proj/3298)
supports redistribution of dissociated derived data; it does not establish that
every conditional current runtime path or unmarked stored override is dissociated.
Established packaging, MIT coverage of independent PROJ work, unchanged downstream
bytes, factual status and a truthful generic disclosure are relevant but do not
alone settle the identified attribution condition. This is a project distribution
assessment with a specific unresolved material condition, not an infringement
finding or a demand for impossible certainty about every upstream adaptation.

The1312/1462 accuracy-attribution question is sufficient to retain BLOCKED.
900913's deprecated compatibility alias and7001's added interpolation CRS remain
linked questions in the same resolution; their existence alone is not proof of a
prohibited derivative. Source=PROJ aliases, schema translation, own unit annotations
and numerically equivalent transformations are not reopened as generic blockers.
The terms do not impose a blanket ban on referring to EPSG codes or a literal
generic modification sentence. Full IOGP credit, terms and warranty disclaimer
remain selected; no extra notice can be represented as provider-approved clearance.

PROJ is the adapter. Mastixa need not independently reproduce all derivations or
obtain private CI logs; it must preserve applicable grants and recipient notices
and comply with the known attribution condition for the unchanged data it copies.
No database modification, pruning, replacement, new feature or provider message
was made. The same-byte requirement rules out implementing a changed database as
a remedy in this batch. Future resolution needs an applicable supported terms
interpretation for the named unchanged records; a data remedy would require a
separately scoped decision and behavior qualification.

## Retained topics, attribution and remaining gaps

IGNF3.1.0 PASS remains the scoped CRPA public-information/database reuse inference
for the exact historical registry, with IGN/source/date/representation credit and
inherited EPSG terms. Historical publication/license page remains forensic-only;
the distinct ontology Licence Ouverte is not substituted. IAU PASS retains the
exact matching consolidated collection's LGPLv3 source/terms route plus independently
encoded scientific facts. Mixed authors/DOI/collection contributors and PROJ
transformation credit remain required; full GPLv3/LGPLv3/PROJ warranty texts are
selected. Pre2022 paperwork/correction lineage remains forensic-only.
LT2008 causal history, B1 optional producer receipts and B4 bit-identical reproduction
also remain non-blocking. No other legal blockers are added.

Final pre-RC preflight NOT RUN because B3 remains BLOCKED. Current planned-input
safety and metadata checks are recorded in the local follow-up final-report.json;
this is not a scan of a nonexistent RC. Earlier immutable source/evidence archives
are preserved. Only a bounded document/source supplement is created locally.
Raw handoff, before/diff snapshots, machine paths and copied source evidence stay
outside recipient inputs; no automatic deletion or publication is performed.

---

# Final B3-only legal decision — 2026-10-08

**BLOCKED BEFORE RC BUILD.** B3 is BLOCKED only on EPSG adapted-metadata
attribution. IGNF3.1.0 and the actual IAU inputs now have scoped PASS decisions.
B1-LEGAL/B4-LEGAL PASS retained, audit/repro INCOMPLETE and non-blocking;
B2/B5 PASS retained, COMPLETE. Final preflight NOT RUN; no RC build permitted.
This is an evidence-backed project distribution assessment, not provider approval
or a finding that PROJ infringes rights. The PASS reasoning below is identified
as a scoped legal interpretation where no object-specific license survives.

The exact current wheel database remains byte-unchanged, SHA256
528b9763b57e85ee78f6f30478ef0494902320f1d71d1564bf0d7ec4f30cc002.
Earlier full SQL/database correspondence, LT2008, ITRF, NKG, legacy-input and
B1/B2/B4/B5 conclusions are retained. New queries cover only IGNF/IAU-owned rows,
related named PROJ records, and EPSG1312/1462/7001/900913. The full rows, identifiers,
source hashes and counts are in WindowsB3FinalEvidence/topic-map.json.

## A. IGNF3.1.0 — PASS, forensically incomplete but legally sufficient

This is **the IGN France ISO19139/GMX/GML CRS catalogue instance**,
IGNF.v3.1.0.xml, version3.1.0, source update2019-05-24. Its SHA256 is
5c5124123605c4b3ac2035466af9a01e369e538e8ccf6e242ec03c7b99a20657.
It is neither the ontology3.1 dated2019-02-13 nor current registry4.0.1.
The XML contains reference-frame definitions, identifiers, extents, scopes,
conversion and transformation parameters, not an observation/station catalogue.

PROJ9.8.1 scripts/build_db_create_ignf_from_xml.py identifies the historical
librairies.ign.fr/geoportail/resources/IGNF.xml endpoint and its actual mirrored
input. The mirror was introduced2021-04-04, commit83977a6bb9c7bec8cb68b3682b9c2d23fb4395ee.
[The pinned historical object remains public](https://raw.githubusercontent.com/rouault/proj-resources/83977a6bb9c7bec8cb68b3682b9c2d23fb4395ee/IGNF.v3.1.0.xml)
and matches the retained hash. The official historical download now fails;
the old provider publication page/license has not been recovered. The mirror
tree has only that XML, with no README/LICENSE. No embedded rights/grant notice
was found in the retained XML. PROJ's COPYING covers its own source/data work;
it is not treated as an IGN sublicense or a replacement for inherited conditions.

The [official IGN/CNIG register workflow, slide10](https://cnig.gouv.fr/IMG/documents_wordpress/2021/11/1_Geopos-14octobre2020-Registres.pdf)
identifies generation from IGN's BDG AUX, publication through geodesie.ign.fr,
archiving at DPSG, and later addition of corresponding EPSG codes. The
[official register description](https://geodesie.ign.fr/linformation-geodesique)
confirms its reference-system role. [IGN's legal notice](https://geodesie.ign.fr/mentions-legales)
identifies a public administrative establishment; its
[public-service geodetic mission](https://geodesie.ign.fr/gravimetrie)
is tied to decree2011-1371. This registry is a published public-service reference
instrument, not an identified competing industrial/commercial database product.

Applicable statutory route, already in force before the2019 source date:

- [CRPA L321-1/L321-2/L321-3](https://www.legifrance.gouv.fr/codes/id/LEGIARTI000033219118):
  reuse of published public information; third-party intellectual-property
  exclusion remains; qualifying public-administration database rights cannot
  prevent reuse, with the competing industrial/commercial exception preserved.
- [CRPA L322-1](https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000032255220),
  effective2016-03-19: source/update date and non-alteration/non-distortion duties.
- [Official data.gouv reuse guidance](https://guides.data.gouv.fr/guides/guide-juridique/reutilisateurs-de-donnees/respecter-les-conditions-de-reutilisation):
  expressly explains the L322-1 default when no license is mentioned.

**Scoped inference:** IGN's own published register composition and factual
definitions fit that statutory route. The provider's own generating/publication
workflow, exact XML and importer identify no independent protected third-party
collection beyond inherited EPSG material already covered by the separate EPSG
analysis. Merely mentioning an ellipsoid, scientific frame, SHOM realization or
EPSG identifier does not copy that provider's separate observation database.
The statute does not waive actual third-party rights; those would require a new
assessment if introduced or identified. PROJ's independent schema conversion,
unit representation and constructed inverse/composed operations are disclosed
and do not purport to update IGN's2019 official catalogue. This preserves source
meaning; it is not permission for arbitrary semantic edits to public information.

IGNF-owned rows: ellipsoid1, extent315, scope12, usage1620, datum76,
vertical datum37, geodetic CRS339, vertical CRS38, conversion174, projected
CRS260, compound CRS227, Helmert702, grid transformation40, other transformation4,
concatenated operation10; one builtin-authority row. Named PROJ constructions and
inherited references are separately listed in the topic map. Grid filenames
remain references: no IGN or other grid payload was added.

Credit **IGN France, IGNF3.1.0, source update2019-05-24, historical input URL,
PROJ XML-to-SQL representation**, distinguish current from historical data, and
retain applicable inherited EPSG/IOGP terms and software disclaimers. No new
statutory warranty or blanket source-mirror condition was found. This is not an
Etalab license claim. No later/current terms explicitly applying retroactively
were proved; neither the ontology nor a2021 generic policy is used to fill that
gap. Recovery of the historical notice is **forensic-only, not RC-blocking**.

## B. Actual IAU inputs — PASS, exact collection basis plus factual use

The182-row PROJ input is scripts/data/naifcodes_radii_m_wAsteroids_IAU2015.csv.
Fields are NAIF id, body, mean radius, three axes, rotation direction, short
reference-landmark name and longitude. [PROJ issue2601](https://github.com/OSGeo/PROJ/issues/2601)
first mentions an older USGS GDAL_scripts repository, then explicitly identifies
thareUSGS/csvForWKT as the planned input. [PR2876](https://github.com/OSGeo/PROJ/pull/2876)
and commitf982d9d3104731727c445930bf14008d1c572d0a introduce the actual2015 input
and independent MIT generator by Even Rouault/Hobu Inc. Do not substitute the
older IAU2000 WKT collection for this actual2015 input.

All182 records and **every field** match both the pinned thareUSGS fork and the
[identified PlanetMap collection at7f693aa1d980d5e3f33b0dd94cd811f4aab3f832](https://github.com/PlanetMap/csvForWKT/tree/7f693aa1d980d5e3f33b0dd94cd811f4aab3f832).
Bytes differ only in newline representation. The fork's CSV history records
scientific corrections from2020 and a2021 refactor. The present producer's
repository includes that identical CSV, AUTHORS and root GNU LGPLv3 license
(its inherited GPLv3 terms also apply). The presently published grant is a
specific available downstream route for this **same collected object**; no claim
is made that the historical fork or scientific paper was already LGPL in2021.
Producer credits: Jean-Christophe Malapert (CNES), Trent Hare (USGS), Benoit
Seignovert (University of Nantes). Exact input, full collection license and
AUTHORS are retained as source-only materials. Full GPLv3/LGPLv3 already ship;
an indexed collection NOTICE is newly selected for recipients. Covered collection
contributions retain those terms, with matching CSV and existing PROJ SQL/generator
source available at later distribution. This does not relicense all PROJ software.

The collection's publication reference is
[Archinal et al., WGCCRE2015, CMDA130:22(2018), DOI10.1007/s10569-017-9805-5](https://link.springer.com/article/10.1007/s10569-017-9805-5).
The [USGS publication record](https://pubs.usgs.gov/publication/70212485)
identifies mixed authorship and scientific recommendations. Its journal
publication has a publisher permissions mechanism, not an established
whole-article open grant. **Article prose, typeset tables, figures and layout are
not copied.** A reprint license is not imposed on separately expressed facts.
[USGS data licensing](https://www.usgs.gov/data-management/data-licensing)
distinguishes facts, creative compilations, government-work territorial limits
and third-party material; its general public-domain policy is not substituted
for permission for this multi-source collection.

Actual-source classification:

| Represented source/content | Classification | Reason and conditions |
| --- | --- | --- |
| Identical PlanetMap/csvForWKT consolidated collection | PERMITTED / ATTRIBUTION AND SOURCE TERMS REQUIRED | Present identified LGPLv3 grant for covered compilation contributions; exact source/author/license retained |
| WGCCRE2015 report recommendations and underlying scientific radii/axes | FACTUAL DATA / NO MATERIAL COPYRIGHT ISSUE | Numerical results and mathematical conventions are independently encoded; original publication expression not shipped; retain authors/DOI |
| NAIF body numbers, astronomical names, reference-landmark identifiers | FACTUAL DATA / NO MATERIAL COPYRIGHT ISSUE | Short identifying facts used as parameter metadata; no kernel, catalogue descriptions or naming-database collection ships |
| Older IAU2000 Earth ellipsoid | FACTUAL DATA / NO MATERIAL COPYRIGHT ISSUE | Only PROJ:EARTH2000 axes6378140m/6356750m, independently represented under PROJ data terms; not the full old CSV/WKT collection |
| PROJ generated sphere/ellipsoid/CRS/projection definitions | PERMITTED / ATTRIBUTION REQUIRED | Independent MIT generator/source grant; retain source facts, transformation disclosure and covered collection terms |

**Collection-rights analysis:** factual status alone is not used to dismiss a
creative compilation or database right. The identified consolidated collection
now has a retained grant and source/terms route. Its short standard fields follow
the scientific task and PROJ transforms their contents; no independent original
observational/astrometric database or protected publication arrangement is
identified as an additional shipped extraction. The report creates/recommends
scientific models from prior research, rather than licensing an identified
third-party observation catalogue copied into Mastixa. This is the scope of the
PASS inference; it is not a universal assertion that collections of facts lack
rights. Current matched producer permission plus the actual factual transformation
is sufficient; unsupported hypothetical underlying rights do not impose permission
for every reported number. Do not use an all-USGS/government-work/public-domain
classification for the collection. No csvForWKT executable/program code or its
generated WKT is copied into Mastixa.

Shipping IAU2015 rows: body97, ellipsoid115, prime meridian97, datum115,
geodetic CRS127, conversion17, projected CRS2074, usage2333, one authority row.
The source generator omits unusable/unsupported cases, constructs longitude
conventions and sphere/biaxial alternatives, and sometimes derives a mean radius.
Full row identifiers and parameter-source map are retained; no scientific accuracy
recertification or whole-database regeneration is claimed.

Attribution: full mixed report authors/DOI, collection contributors, and PROJ
generator/transformations. Disclaimer: applicable LGPLv3/GPLv3 and PROJ no-warranty
texts; no additional publication-specific disclaimer was identified. Remaining
pre2022 grant/correction history is forensic-only, **not RC-blocking**, because
the same collection is presently offered under retained terms. If future content
copies paper expression, generated csvForWKT software, or an independent
protected observational dataset, reassess that new content and obligations.

## C. EPSG — notices PASS; specific adaptation attribution BLOCKED

Controlling source is only the
[official EPSG Terms of Use, revision2016-04-08](https://epsg.org/terms-of-use.html).
The complete controlling legal body/Table1/revision history remain supplied in
licenses/EPSG/TERMS-OF-USE-2016.html. Fresh primary retrieval is retained; web
tool403 is not treated as absence of terms. Clause1 covers geodetic parameters
and associated metadata. Clause6(i)-(iv) covers recipient full terms/no-warranty,
value-added commercial packaging and IOGP ownership. Clause6(v) covers subset
extraction, with essential-element guidance. Clause6(vi)/Table1 permits
specified mathematically equivalent parameter changes. Clause6(vii):

> No data that has been modified other than as permitted in these Terms of Use
> shall be attributed to the EPSG Dataset.

There is no blanket independent prohibition on mentioning an EPSG code/name,
no literal required generic modification sentence and no general dataset source-
mirror obligation. Their absence does not waive the explicit attribution rule.

| Upstream representation | Assessment |
| --- | --- |
| Relational schema/format translation | Defensible representation of retained official meaning; not inherently a forbidden derivative |
| Units, equivalent parameter representations | Table1 numeric-equivalent paths; own proj_short_name is explicitly a PROJ extension |
| Additional alias_name with source=PROJ | Explicitly distinguishes alias author from referenced EPSG target; referring to a target code is not itself a ban |
| PROJ-authored derived operation under PROJ authority | Distinguishes new representation from official EPSG entries; inherited official parameters/terms remain |
| EPSG:900913 | Deprecated PROJ compatibility alias of3857; source clearly explains it, but stored projected_crs authority remains EPSG rather than PROJ |
| EPSG:7001 interpolation CRS4289 | Source supplies missing Bessel/Amersfoort interpolation information; exact metadata attribution treatment still needs supported interpretation |
| EPSG:1312/1462 accuracy=2.0 | Actual upstream overwrite intended to change operation ranking. Accuracy is metadata, not an equivalent unit conversion; authority remains EPSG. This is the material unresolved condition |

The exact PROJ scripts/build_db.py, data/sql/README.md and customizations.sql
separate imports, customizations and many new PROJ records. The public
[PROJ incubation discussion, ticket2268](https://discourse.osgeo.org/t/sac-osgeo-2268-incubation-request-proj/3298)
explicitly recognizes dissociation of non-permitted modifications from EPSG.
It is primary upstream evidence of their interpretation, **not an IOGP waiver**
or a finding on these specific current records. No specific applicable
IOGP/PROJ interpretation settling their remaining authority attribution was found.
General incorporation in a reputable package cannot override a concrete condition.

**Downstream separation:** PROJ is the modifier; Mastixa copies its output
unchanged. Mastixa must retain rights, full terms, ownership and disclaimers and
avoid attributing impermissibly modified content to EPSG. It need not reproduce
all producer history, prove every row anew or possess private CI logs. The
unchanged DB plus supplied notices fulfils copying/information duties, but does
not establish compliance for specifically identified modified EPSG metadata.
Generic truthful upstream disclosure is already provided. Simply calling all
altered fields PROJ in a top-level notice while the distributed records still
identify them as EPSG is not accepted as a proven remedy in this batch.

The blocker is **specific clause6(vii) treatment of1312/1462, with900913/7001
included in the same attribution resolution**. It is not impossible certainty
about every PROJ adaptation, missing historical receipts, or a general derivative-
work ban. No infringement conclusion is asserted. Close it with an applicable
authoritative/supported terms interpretation or a qualified representation that
actually distinguishes those changes while preserving supported CRS imports.
No database pruning, replacement, edit or provider messaging occurred here.

## Gate, material and preservation result

B3 BLOCKED; final pre-RC preflight deliberately NOT RUN. No final RC, installer,
commit, push, tag, external upload or publication. Only B3 legal/docs/metadata
and its required license/source inputs change. B1/B2/B4/B5 flags, native runtime,
app/UI/performance/Android/spec/installer/locks remain unchanged. Prior full source
base and every prior supplement are immutable; the new bounded legal/source delta
does not regenerate a full source snapshot. Current retention/document/SBOM
metadata is reconciled and checked independently.

Exact focused checks, publish-input findings/limits and before/after Git hashes
are in WindowsB3FinalEvidence/final-report.json. The latest CODEX_HANDOFF.md records
the result, exact next action and mandatory future Bitdefender rule. Later actual
artifact/source access and output/functional/privacy checks remain required.

---

# Retained prior B3 decision (superseded for IGNF and IAU)

# Final B3 legal/data-rights review — 2026-10-08

**BLOCKED BEFORE RC BUILD.** B1-LEGAL PASS/B1-AUDIT INCOMPLETE;
B4-LEGAL PASS/B4-REPRO INCOMPLETE; B2/B5 PASS RETAINED. B3 retains only three
independent unresolved legal issues: IGNF3.1.0 collection rights, IAU2015
collection reuse basis and EPSG attributed upstream metadata adaptations.
Final preflight NOT RUN; RC may not be built. The detailed classified decision
ledger is `windows-b3-legal-closure.json`; evidence is in the sibling
`WindowsB3LegalClosureEvidence` directory. This is a bounded evidence/terms
assessment, not a provider permission or a finding of infringement.

## Retained shipping identity and responsibility

The exact pyproj3.8.0/PROJ9.8.1 `proj.db` SHA256 is
`528b9763b57e85ee78f6f30478ef0494902320f1d71d1564bf0d7ec4f30cc002`.
Mastixa redistributes the upstream wheel database byte-for-byte. It neither
patches CRS rows nor generates a Mastixa derivative. The retained39-table/
77707-row source correspondence, four Esri lookup explanations and six NKG2020
national Table3 matches are reused, not rerun. A targeted NKG inherited-step
query reads the database in read-only mode; it is not a full PROJ DB analysis.

PROJ creates the upstream representation; Mastixa carries downstream conditions:
redistribution basis, applicable copyrights/licenses/terms, attribution and
limitations. No applicable condition requires Mastixa to reconstruct every
historical derivation or possess producer CI logs. Unchanged upstream bytes do
not erase rights or contract/database conditions that do flow downstream.

## LT2008 — legal PASS; historical explanation audit-only

The NKG source ty0.11549 differs from upstream SQL/shipping ty0.115495 by
0.000005m. Earliest retained NKG resource and initial SQL already differ. Fresh
public PROJ PR2494 body, review comments, issue comments and initial commit add
no explanation. Primary NKG publication/history evidence and Lithuanian-author
publication search provide no authoritative cause. No precision extension,
rounding, revision, correction, transcription or convention is asserted.

The retained NKG CC-BY4 grant permits adaptations and requires credit/license
and change indication. It does not require a causal history proof. Existing
credits plus explicit PROJ/LT change disclosure satisfy the relevant notice
dimension; the exact historical reason is a non-blocking forensic follow-up.
The NC-ND publication license of the separate2008 article is not substituted for
the explicit CC-BY4 NordicTransformations data grant.

## IGNF3.1.0 — collection rights unresolved

Actual input: IGN France historical registry XML3.1.0/2019-05-24, retained SHA
`5c5124123605c4b3ac2035466af9a01e369e538e8ccf6e242ec03c7b99a20657`.
PROJ's pinned XML-to-SQL importer and DB metadata identify it exactly. The
current official XML4.0.1/2026-03-23 is a different dataset version. A newly
retained [IGN ontology3.1/2019-02-13](https://data.ign.fr/def/ignf/20190213.htm)
lists Licence Ouverte, but licenses the ontology/schema, not explicitly this
historical registry instance. The old official XML endpoint now returns404.
This is not evidence that no historical grant exists.

No sufficient version/scope-specific registry grant is present in retained
source/distribution materials. PROJ data MIT grants its own work; it cannot
alone resolve an independently protected collection extracted from IGN.
Individual factual constants need not each be licensed, but whole-registry
collection/third-party scope is still unresolved. Required next evidence:
applicable grant covering this historical registry and inherited conditions,
or a supported registry-specific lawful-use/database-rights assessment. No
particular private letter is mandatory. Credit IGN/version/input/PROJ adaptation
now; do not invent a redistribution/derivative license or waive unknown terms.

## IGN/ITRF versus IERS — narrow factual-use basis

The exact independent init inputs are ITRF.TP and the inverse2005-to2000 table
for ITRF2000, Transfo-ITRF2008_ITRFs.txt for ITRF2008, and
Transfo-ITRF2014_ITRFs.txt for ITRF2014. Provider: IGN ITRF Product Centre and
parameter authors. IERS coordinates the scientific frame/conventions; it is
not automatically the publisher/licensor of every IGN object. ITRF2020 follows
PROJ's EPSG generator and remains under EPSG conditions separately.

The included2000/2008/2014 content is computed Helmert coefficients, rates and
epochs expressed in PROJ init syntax, with documented unit/sign changes. No
original journal prose, illustrations, station observations or SINEX catalogue
is shipped. The [official2014 parameter table](https://itrf.ign.fr/docs/solutions/itrf2014/Transfo-ITRF2014_ITRFs.txt)
describes derived frame relationships and standard-model use. PROJ's explicit
MIT data permission covers its independent representation. Scientific methods/
results themselves are distinct from protected explanatory expression.

The scoped inference is that these created numerical relationships do not copy
an independently protected collected station database. The
[CJEU C-203/02 summary](https://curia.europa.eu/juris/showPdf.jsf?docid=64559&doclang=EN)
distinguishes investment creating data from obtaining/collecting existing
independent materials, while preserving rights in qualifying collections.
No applicable reuse restriction was identified in the retained exact headers/
provider evidence. Consequently no permission for each numeric result or a
journal reprint is imposed here. This is a scoped factual-use assessment, not
an IGN/IERS open-data license or public-domain claim. Keep IGN/IERS roles,
exact source references, epochs, conversion disclosure and PROJ notices.
Reassess if actual station datasets/publication expression/restrictive terms
are introduced. No new downstream publication duty was established.

## NKG inherited IERS/EUREF — no independent input collection

The read-only targeted chain finds14 NKG Helmert nodes and external concatenated
steps exclusively EPSG7941 (ITRF2000→ETRF2000) and EPSG8366
(ITRF2014→ETRF2014). NKG national definitions/coefficients have the explicit
NordicTransformations CC-BY4 grant and retained primary-paper/source evidence.
References to EUREF-FIN/EUREF-EST97 and realization identifiers do not ship EPN
RINEX/station/SINEX datasets. PROJ SQL describes/links the frame operations.

Thus IERS and IAG EUREF have no separately unidentified redistribution grant
gap in this actual NKG chain; EPSG inherited terms remain mandatory and are
tracked once in EPSG. Existing credits retain IERS, IGN, EUREF/national
realizations and NKG separately. Current EPN data licensing does not supply a
historical ETRF grant and is not used as the legal basis. No grid payload ships.

## IAU2015 — facts identified; collection reuse unresolved

Exact input is182-row `naifcodes_radii_m_wAsteroids_IAU2015.csv`; fields include
body/NAIF identifier, mean/ellipsoid radii, axes, rotation and prime-meridian
landmarks. PROJ's MIT generator produces planetary ellipsoids/CRS/projections,
applies longitude conventions and derives mean-radius approximations. Source is
[Archinal et al., WGCCRE2015, CMDA130:22(2018)](https://link.springer.com/article/10.1007/s10569-017-9805-5),
DOI10.1007/s10569-017-9805-5; the
[USGS record](https://www.usgs.gov/publications/report-iau-working-group-cartographic-coordinates-and-rotational-elements-2015)
identifies the mixed authorship and scientific recommendations. Article text,
figures and layout do not ship; the current publisher page supplies a permissions
link, not a data-specific reuse grant.

Scientific constants/conventions are not automatically protected expression.
That does not establish this collected multi-provider input's extraction/reuse
basis under all applicable collection/third-party conditions. Unlike computed
ITRF relationships, this input collates multiple prior results. USGS public-domain
policy excepts third-party content and cannot clear the mixed collection alone.
Do not demand a journal reprint license or permission for each fact by default;
resolve the actual collection scope through a data-specific grant or supported
collection-law assessment. Preserve report/authors/DOI and PROJ adaptation credit.
This remains a specific B3 legal uncertainty, not a vague “IAU rights” item.

## Legacy inputs — named basis, no generic blocker

CH/GL27/nad27/nad83/world/other.extra: named original PROJ definitions/headers,
MIT source/data permission and legacy Gerald Evenden origin retained. CH's
Swisstopo grid references do not ship grid bytes. NRCAN/OGC/PROJ definition,
epoch and axis-order constructions are PROJ-authored and retain MIT, names/
origins and inherited EPSG conditions. No copied NRCAN grid or OGC report is
identified. Their inherited EPSG condition is tracked separately, not hidden
by MIT or repeated as an unspecified independent rights blocker.

## EPSG — notices PASS; adaptation/attribution unresolved

The complete [official terms revised2016-04-08](https://epsg.org/terms-of-use.html)
are retained in `licenses/EPSG/TERMS-OF-USE-2016.html`; fresh retrieval confirms
the controlling body. They allow copy/distribution and value-added commercial
packages, require IOGP ownership acknowledgement and informing recipients of
the full terms/no-warranty, and limit attributed modifications. Mastixa's
value is its application, not selling the freely supplied EPSG dataset.

Independent bundled reproduction of the full terms/IOGP credit is required:
proj.db's references and PROJ MIT alone do not inform recipients. Selection
includes the terms, notices and no-warranty. Truthful upstream adaptation
disclosure is included; no prescribed generic modification sentence or blanket
EPSG source-mirror duty was found. No extra Mastixa modification notice is needed
for an edit that Mastixa does not make; upstream changes must still be described
accurately and comply with attribution conditions.

Source explains900913 as a deprecated3857 alias;1312/1462 accuracy becomes2.0
to prefer NTv2 and7001 gains interpolation CRS4289. Attribution conditions cover
associated metadata as well as numerical parameters. These accuracy changes can
affect operation selection; identical fixed coordinate parameters do not prove
permitted metadata attribution. The explicit table of allowed parameter changes
does not expressly settle these accuracy/authority adaptations. No controlling
interpretation was located to close that gap. A disclosure cannot itself grant
permission. Supported terms/source interpretation or authoritative EPSG/PROJ
clarification remains needed; no DB pruning/edit or infringement claim is made.

## B1/B4 and preflight

Retained full texts/notices, release sources/nested patched PDFium source,
binding typesystems/generation/coin/build scripts, GEOS/Shapely producer/repair
materials, OpenBLAS source/recipe/exception and application source base/supplements
satisfy prebuild B1-LEGAL/B4-LEGAL preparation. The dynamically loaded benign
modified Qt6Pdf.dll actually passed startup/PDF/preview from the documented
recipient path; no runtime hash guard prevents compatible LGPL replacement.
General-purpose tool identities, internal CI logs, exact feature-cache/output
comparisons and bit-identical/full publisher rebuilds remain audit follow-up.
Necessary actual source/scripts/patches and source access are not waived.

See `WINDOWS_RELEASE_GATE_POLICY.md`. Only B3 now prevents eligible final
preflight. After the three legal gaps close, run the requested preflight; do
not build RC in this batch. Actual binary/source binding, public source access,
actual output notices/privacy/functional/install/updater validation remain
mandatory in the separately authorized future artifact/distribution batch.
