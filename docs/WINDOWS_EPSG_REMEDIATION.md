> Retained historical engineering record, sanitized for public review.
> Current status: [RELEASE_STATUS.md](RELEASE_STATUS.md). This record does not
> establish approval of the current source or a new binary release. Local-only
> receipt paths refer to privately retained evidence, absent from this snapshot.

# EPSG remediation decision — 2026-10-08

RELEASE-INFRA / DESKTOP, Windows only. **EPSG PASS; B3 PASS** for this scoped
prebuild attribution assessment. B1/B2/B4/B5 legal PASS and IGNF/IAU PASS retained.
Final preflight and publish-safety receipts determine candidate-build eligibility;
this decision neither builds nor accepts an artifact. Earlier unchanged-database
BLOCKED decisions describe the supplier representation before this remedy.

## Path A: external disclosure alone is insufficient

The [official EPSG terms](https://epsg.org/terms-of-use.html), revision 2016-04-08,
were retrieved successfully in this batch. Their substantive body is unchanged
against the supplied complete terms; the website chrome/dataset version changed.
Clauses 1 and 6 cover associated metadata, copying/distribution, ownership,
recipient terms and disclaimers. Clause 6(vii) separates modifications outside
the permitted equivalence cases from attribution to the EPSG Dataset.

The clause prescribes no application-page location, footer format, database
column, mandatory point-of-export sentence, or blanket EPSG-code deletion.
Nevertheless, an exported object can circulate apart from its application notice.
A general About/legal notice leaves the known EPSG-ID accuracy 2.0 objects
unqualified. A reader could reasonably take that value as EPSG's published
accuracy. An external field-specific notice alone has the same detached-export
problem. Neither is accepted as sufficient to close this gate.

The selected interpretation is that an accurate original EPSG operation reference
can coexist with independently attributed modified metadata, provided the object
itself explicitly says which field PROJ changed and that EPSG did not supply that
value. This follows the distinction between ownership/source reference and
attribution of the modification in clauses 6(iv)/6(vii). It is a documented scoped
terms interpretation, **not an IOGP approval, legal precedent or infringement
finding**. The [primary OSGeo discussion](https://discourse.osgeo.org/t/sac-osgeo-2268-incubation-request-proj/3298)
corroborates dissociation as upstream practice; it does not approve these records.

## Path B: selected self-contained provenance overlay

The application has CRS imports/calculations, but no operation-WKT/PROJJSON export
route to wrap. An application-only wrapper would leave recipients' direct native
PROJ/pyproj objects and the redistributed database unqualified. No monkeypatch or
second database with competing accuracy semantics is introduced. The last-resort
derived database copy is therefore the smallest integrated remedy covering the
actual shipping data and native serialization together.

`packaging/epsg_provenance.py` copies the exact hash-locked supplier database into
the actual PyInstaller work directory. Only these fields change:

| Object | Changed fields | Retained behavior / exported representation |
| --- | --- | --- |
| EPSG operation 1312 | Append description/provenance only | Accuracy stays 2.0 m internally and externally. WKT REMARK and PROJJSON remarks expressly attribute it to PROJ, distinguish the imported EPSG v12.029 1.0 m, and qualify EPSG:1312 as the original definition reference. |
| EPSG operation 1462 | Append description/provenance only | Same exact handling, original operation reference EPSG:1462. |
| EPSG operation 7001 | Append description/provenance only | WKT/JSON explicitly attribute the interpolation association to PROJ. Genuine EPSG:4289 still identifies Amersfoort; accuracy 0.01 m, deprecation, grids and parameters stay unchanged. |
| Legacy CRS 900913 | Authority EPSG to PROJ; explicit unofficial name/description; corresponding usage object authority | Direct CRS lookup/export is PROJ:900913. It is mathematically equivalent to official EPSG:3857. Deprecation remains PROJ's flag; original EPSG datum/unit/base-CRS references stay accurate. |

For 900913, a description-only attempt was rejected: PROJ's projected CRS factory
does not read that column for serialization. A name-only caveat would leave the
false root issuer authority. The actual selected fix changes the alias's root
authority and its one usage reference, without changing its coordinate definition.

Native `CRS.from_epsg(900913)` now deliberately rejects the unofficial identifier;
`CRS.from_authority("PROJ", 900913)` returns the independently attributed alias.
Mastixa's narrow input compatibility rule maps the named historical numeric,
EPSG/PROJ-string, OGC URN and OGC URL forms to official EPSG:3857. Persisted string
inputs and current imports therefore continue to calculate correctly, without a
profile/schema migration. The canonical stored/presented result is EPSG:3857.
Unrelated CRS strings and all genuine EPSG definitions retain their behavior.

This is an intentional compatibility distinction, not a claim that 900913 was
ever an EPSG-issued code. No unrelated object is silently relabeled.

Supplier input SHA256:
`528b9763b57e85ee78f6f30478ef0494902320f1d71d1564bf0d7ec4f30cc002`.
Qualified derived output SHA256:
`590adc683437a59896e8841255129b572b082008eebf1c0d5225e6c5e207c064`.
The original wheel, supplier database, PROJ DLL and package versions are unchanged.
The existing 39-table correspondence applies to that supplier input; this is a
documented overlay, not a claim that its output is an unmodified supplier database.

## Candidate classification

| Candidate | Classification | Reason |
| --- | --- | --- |
| General application notice only | LEGALLY INSUFFICIENT for gate closure | Does not qualify the known detached EPSG-attributed exports. |
| External field-specific notice only | LEGALLY INSUFFICIENT for gate closure | Cannot rely on the notice always accompanying the raw object/database. |
| Restore accuracy to 1.0 m in the runtime database without selection qualification | TECHNICALLY UNSAFE as proposed | Deliberate NTv1/NTv2 preference workaround would be reversed. |
| Display/export 1.0 m while using 2.0 m internally | LEGALLY INSUFFICIENT as a standalone remedy | Leaves raw redistributed metadata unqualified and can obscure actual runtime accuracy semantics. |
| Mark modified fields inside direct WKT/JSON; keep 2.0 m and real operation references | LEGALLY SUFFICIENT in this scoped assessment; ACCEPTABLE WITH DOCUMENTATION | The modification's author/value is explicitly separated from the genuine EPSG source reference at the point of representation. |
| Application-only wrapper | LEGALLY INSUFFICIENT for the shipped raw database | No existing operation-export hook; raw native consumers bypass it. |
| Move unofficial alias 900913 to PROJ authority, preserving Mastixa input compatibility | LEGALLY SUFFICIENT in this scoped assessment; ACCEPTABLE WITH DOCUMENTATION | Removes false EPSG issuer identity while retaining equivalent coordinates and explicit provenance. |
| Hash-locked metadata-only derived copy implementing those two remedies | LEGALLY SUFFICIENT in this scoped assessment; ACCEPTABLE WITH DOCUMENTATION | Smallest remedy covering storage and all native exports without accuracy/ranking changes. |

No provider permission letter is imposed as an additional gate. This assessment
does not claim universal clearance for future datasets or modified serializers.
Adding a serialization path that strips the field provenance and attributes the
override to EPSG requires renewed review.

## User-visible/legal locations

THIRD_PARTY_NOTICES identifies the PROJ-derived data, the four named treatments,
Mastixa's markings and official-current-data access through epsg.org. The existing
Settings Open Source/legal link already opens that document; no UI redesign is
required. Full unchanged EPSG terms/IOGP ownership/no-warranty remain selected.
This document and the exact overlay recipe/lock accompany corresponding source.

The operation's WKT REMARK/PROJJSON remarks carry field-specific provenance.
The independent alias carries PROJ authority and an explicit unofficial name.
Mastixa's existing parcel/report exports do not present these operation accuracy
fields; no unrelated report footer is required by the controlling text or added.

The official 1.0 m comparison is the EPSG v12.029 input imported by PROJ9.8.1,
confirmed by the retained authoritative importer/generated SQL and customization
commit. It is **not a claim that the current online registry's later version has
been queried for a fresh value**. Recipients are directed to epsg.org for current
official data. No Table 1 permission for accuracy overrides is invented.

## Focused qualification and limits

Direct native construction/export verifies the two unchanged 2.0 m fields and
their in-object provenance, 7001's unchanged interpolation/accuracy, and the
independently identified alias. Original versus derived JSON objects differ only
in the intended provenance fields for the three operations. Two independent
copies reproduce the exact pinned database bytes; its SQLite integrity passes.

Separate processes avoid cached factory results. Available/unavailable operation
order, accuracy, grid references and executable pipeline definitions match for
Canada, Quebec, Netherlands and the active Greek transformation route. External
NTv/vertical grids are absent, as in the shipping supplier input; no external grid
is fetched and no grid-dependent coordinate execution is claimed. The unchanged
selection fields/parameters and exact native code preserve ranking with the same
grid availability. Legacy alias coordinate output equals official EPSG:3857;
Mastixa legacy input runs against the derived data in a separate process.

Analysis requires exactly one database at its expected destination and replaces
only that input. Unknown suppliers, conflicting existing work, duplicates,
relocations and unmarked final outputs fail closed. Future bundle validation
must find the single derived hash, alongside retained native/TLS/CRT guards.
The SBOM records the generated database separately and retains all native hashes.
The final source delta includes the editable recipe, lock, compatibility change
and focused tests; earlier local source archives remain immutable.

EPSG and B3 PASS apply to the retained issue scope after resolving all four named
representations; no other retained EPSG issue remains. B1/B2/B4/B5, IGNF/IAU,
LT2008 forensic classification and source/replacement duties are not reopened.
Final preflight/publish-safety results and Git preservation are recorded in the
current handoff and local WindowsEpsgRemediationEvidence/final-report.json.
No final RC/installer, commit, push, tag, publication, external upload or antivirus
change occurs in this batch.

## Mandatory future build rule

Owner-authorized temporary Administrator PowerShell access is solely for
supported Bitdefender exclusion management of the exact actual PyInstaller/Inno
build/work/output directory. Never create/rename PROSORINA, exclude the repo,
profile, drive or unrelated folders, disable protection globally, or use
undocumented registry hacks. Record the exact exclusion; remove it after
artifact validation and verify removal. If manual action is necessary, STOP
before build, show the exact path and wait indefinitely for explicit owner
OK/Done/Continue; no countdown, timeout or automatic continuation.
