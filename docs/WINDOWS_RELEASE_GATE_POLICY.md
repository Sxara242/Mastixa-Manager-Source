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

# Windows RC legal and evidence gate policy — 2026-10-08

This policy supersedes historical requirements that blocked packaging merely for
private producer CI logs, duplicate regenerable output or bit-identical rebuilds.
It applies to the current Windows x64 1.0.0-rc.1 preparation only. The current
decision is **BLOCKED BEFORE RC BUILD**, because B3-LEGAL remains BLOCKED.

The mandatory prebuild conditions are B1-LEGAL PASS (licenses, notices, matching
source identities, redistribution), retained B2 PASS (CRT route), B3 PASS (data
rights/attribution/permitted derivatives), B4-LEGAL PASS (corresponding source and
usable replacement/relink route) and retained B5 PASS (qualified security-critical
inputs). Final preflight runs only after those conditions. Privacy, publish safety,
functional validation and correct unsigned RC/staging inputs remain mandatory.

`packaging/windows-rc.json` records each `distribution_legal_gates` decision.
`validate_windows_release.py` requires an explicit PASS for every B1–B5 legal
gate, as well as notice/source preparation readiness. Missing/unknown legal
decisions fail closed. Audit/reproduction scores are informational and cannot
alone block packaging. Flipping readiness booleans cannot bypass B3.

| Mandatory legal/material evidence | Non-blocking audit quality |
| --- | --- |
| Matching covered-library preferred source/interfaces, controlling generation/build/install scripts, necessary non-regenerable inputs and actual patches | Private CI logs, historical timestamps, exact compiler/linker executable hashes and job-to-output forensic comparisons |
| All applicable license texts, copyrights, attribution/disclaimers and rights for actual shipped inputs | Perfect historical derivation explanations beyond conditions imposed by the relevant data terms |
| LGPL suitable dynamic replacement/relink path and any applicable installation information | Publisher full-library rebuild tests or bit-identical upstream artifacts |
| Accurate versions/source mapping, qualified security-critical inputs, mandatory actual output checks | Exact optional-feature producer reconstruction beyond complete conservative notice/source coverage |
| Matching final artifact/source binding and equivalent freely accessible corresponding source at distribution | Possession of a nonexistent final artifact during prebuild preparation |

This is not an exemption for missing source patches or controlling scripts.
Generated outputs may be omitted only where regenerable from supplied necessary
source and scripts; the shared-library route must be usable. A known mismatch or
non-regenerable absent input reopens B1/B4-LEGAL. No per-library publisher rebuild
test is automatically imposed by the license. The retained modified QtPdf path is
proof of dynamic replacement, not a full source rebuild claim.

GNU GPLv3 section1 distinguishes corresponding source from general-purpose tools
and automatically regenerable outputs. The FSF exact-hash FAQ distinguishes usable
corresponding source from reproducing identical binaries. LGPLv3 section4(d)(1)
and LGPLv2.1 section6(b) provide suitable shared-library routes; other applicable
conditions remain. Exact terms are included in the legal material set.

Sources: [GPLv3](https://www.gnu.org/licenses/gpl-3.0.html),
[FSF source/hash guidance](https://www.gnu.org/licenses/gpl-faq.html#MustSourceBuildToMatchExactHashOfBinary),
[LGPLv3](https://www.gnu.org/licenses/lgpl-3.0.html),
[LGPLv2.1](https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html).

Prebuild legal PASS means material/replacement preparation for a later build;
it is not public-distribution acceptance. After a separately authorized build,
verify actual EXE/setup/source identities, legal inclusion, private-data/secret
absence, install/upgrade/KEEP DATA/updater behavior and final functional evidence.
Provide source alongside any authorized binary distribution; no publication or
source offer is made by these local documents.

The unchanged 757-file application source base and prior source supplement are
retained. The new legal-gate overlay and detached retention manifest incorporate
this batch's documents/guard/tests. Historical inventories are retained, with only
affected metadata/project-document hashes refreshed. No dependency inventory,
native qualification, B2/B5 tests or full functional audit is repeated.

Future Bitdefender exclusion: use owner-authorized temporary Administrator
PowerShell only for documented management of the exact actual PyInstaller/Inno
Setup build/work/output folder. Never create/rename it PROSORINA, exclude the
repository root/profile/drive, disable protection globally or use undocumented
registry changes. Remove the exclusion after artifact validation and verify
removal. A necessary manual action means STOP before build, show the exact path
and wait indefinitely for explicit owner OK/Done/Continue, without countdown,
timeout or automatic continuation. This batch builds no RC.
