# Release status — 2026-10-09

**Public AGPL development snapshot: publication audits PASS.**
**Windows public binary release: NO-GO. Android: IN DEVELOPMENT.**

Windows x64 is the current release target. Current source metadata is
`1.0.0-rc.2`, channel `rc`, first-party license `AGPL-3.0-only`, unsigned intent,
offline staging updater. No release feed is activated by this snapshot.

| Gate | Current status | Scope and remaining work |
| --- | --- | --- |
| Windows rc.1 candidate build and artifact validation | PASS, retained historical evidence | rc.1 was built, installed and tested; it is not the owner-accepted final candidate |
| rc.1 owner acceptance | BLOCKED / superseded by source fixes | Owner found defects, including locked-year/correction behavior |
| FIX 1–11 source batch | PASS, retained evidence | 168 focused tests and six native source routes recorded; fixes require a new candidate |
| Windows rc.2 candidate | BLOCKED BEFORE BUILD | Existing preparation is paused for owner confirmation of exact antivirus paths; no rc.2 frozen/installer/owner acceptance exists |
| B1–B5 legal/material preparation and scoped EPSG remedy | PASS in current retained release configuration | Preserve exact locked inputs and notices; B1 audit/B4 reproduction gaps are separately labelled, not waived legal inputs |
| Corresponding source for a new public binary | PENDING | Publish matching covered source/build/patch/replacement materials with final artifact binding and equivalent access |
| Public hosted CI | ACTIVE, runners verified | Baseline d98f041 starts Windows/Ubuntu jobs; source audit passes, initial Android SDK setup fails; complete corrected validation is Phase 5 work |
| Current full Windows source suite | PASS locally; hosted confirmation pending | 133 modules / 994 cases pass; initial hosted findings and corrections tracked in PHASE5_WINDOWS_BLOCKERS.md |
| Android | IN DEVELOPMENT | Build/lint and instrumentation do not qualify a public Android release; complete binary notices/native and CRS rights review remains required |

The rc.1 application SHA-256 recorded in retained evidence is
`edfe925e40d648ee1e95a51421b52dc1a10b84b4ec234b313fb9429a0e6c0619`;
installer SHA-256 is
`f96b20fbad16aad79f50398b000fe9e7dd6c0ac1715332bee54e55e44ba9bc47`.
Those hashes describe historical binaries and do not bind this current source.

Public development CI uses Windows source tests and Linux Android build/lint.
Packaging contracts and release preflight run without producing installers.
Actual release builds remain a deliberate maintainer step using qualified,
hash-locked suppliers. A hosted runner's Python install is not a substitute for
the qualified PSF/FireDaemon packaging inputs. See [BUILDING.md](BUILDING.md).

Historical audit documents preserve earlier decisions and local receipt paths.
Use this page for the current release conclusion. Local evidence directories,
private Git history, production profiles and candidate binaries are absent from
the public snapshot. No private repository mutation or publication is implied.
The public repository is now the primary active development repository after
the audited source push and actual hosted-runner verification. Phase 5 and all
rc.2 work use its public checkout. Windows source failures block rc.2 build,
not this explicitly authorized development-source publication. Hosted CI has not
yet been claimed green. See [Phase 5 diagnosis and validation](PHASE5_WINDOWS_BLOCKERS.md).
