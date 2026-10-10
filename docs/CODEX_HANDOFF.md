# RC2 hosted smoke harness handoff — 2026-10-10

Status: **BLOCKED / unqualified**. No owner acceptance, tag or release.

## Follow-up access check — 2026-10-10

The authenticated GitHub connector successfully read repository metadata and the
branch list again. The actual target branch HEAD is still
`da4ddaa0d9dcd56c353d84b5b78333300bcf42c3`; no newer branch changes were observed.
This read access does not provide a working authenticated Git checkout.

Safe cloud CLI checks:

```text
git ls-remote https://github.com/Sxara242/Mastixa-Manager-Source.git refs/heads/qa/rc2-hosted-native-20261010
  fatal: Failed to connect to proxy port 8080 after 0 ms: Could not connect to server
gh auth status
  Failed to log in to github.com using token (GH_TOKEN)
  The token in GH_TOKEN is invalid.
```

The managed environment reports no configured secrets, runtime variables or
outbound identities; its HTTP policy state is unknown. The gh diagnostic does
not independently prove the underlying credential root cause in this proxy
environment. No token values were read or printed. No proxy bypass, alternate
identity, interactive login or repository mutation was attempted.

Per the owner's instruction to stop when repository access remains unavailable,
no patch transfer to real Git history or actual-checkout tests were performed.
The earlier 37 passing Python tests remain prior snapshot results, not new
checkout validation. The PowerShell fixture remains unexecuted. The only review
file changed in this follow-up is this local handoff; candidate artifacts remain
untouched. `git diff --check` was rerun on the snapshot patch and passes.

Required next action: restore the supported cloud proxy and configured GitHub
CLI authentication, then obtain a genuine checkout, recheck the branch HEAD,
apply only the four-file patch, review and run available tests. Never push the
synthetic snapshot history. Explicit owner approval is still required before
any later push or workflow dispatch. RC2 remains blocked and unqualified.

## Source and execution scope

Repository: `Sxara242/Mastixa-Manager-Source`.
Target branch: `qa/rc2-hosted-native-20261010`.
GitHub branch listing verified its head as baseline
`da4ddaa0d9dcd56c353d84b5b78333300bcf42c3` during this review.
Read root `AGENTS.md`, `CONTRIBUTING.md`, `docs/CONTRIBUTION_RIGHTS.md`
and `docs/BUILDING.md`. The recursive baseline tree contains no nested AGENTS
and no existing `docs/CODEX_HANDOFF.md`; this handoff is new.

Work ran only in the managed Linux cloud workspace. GitHub connector reads
succeeded; HTTPS git clone failed because the configured cloud proxy on port
8080 refused the connection. Selected exact baseline files were obtained through
the connector. The local branch is a **review snapshot with synthetic local
history**, not a clone of upstream ancestry. Never push that history. The patch
must be applied to a genuine checkout of the existing QA branch before pushing.
No owner-PC commands, native installer lifecycle, registry operations, workflow
dispatch/rerun/approval, tagging or publishing were performed.

## Findings and uncertainty

Run: https://github.com/Sxara242/Mastixa-Manager-Source/actions/runs/38055770164

Connector job summaries verify ingress succeeded, noicons failed, and normal,
preservation and purge were skipped. The noicons job log independently confirms
13 safety tests passed and `RuntimeError: installed-smoke native exit 1`.
The owner supplied the retained evidence: `/NOICONS` install succeeded, all 559
installed payload files matched, no unexpected shortcuts appeared, and the
pre-launch resource comparison raised `CommandNotFoundException` for
`Get-FileHash`. The retained smoke stderr/payload report were not independently
downloaded in this workspace; these details remain attributed to that evidence.

Source inspection verifies the resource loop calls `Get-FileHash` before any
application process or isolated smoke directory is created. This is a harness
failure, not demonstrated application runtime failure. The reason the cmdlet was
unavailable in that Windows PowerShell process is **not proven**.

Compatibility review: `Get-ChildItem -File`, `Get-Content -Raw`, ordered maps and
`ConvertTo-Json` require PowerShell 3+; `ReadToEndAsync` requires .NET 4.5+.
Windows PowerShell on supported Windows 10+ normally provides those capabilities.
The wrapper's shortcut observation also uses `Get-FileHash` in `powershell.exe`
when a relevant shortcut exists. The noicons run had no shortcuts, so that hash
path was not exercised. Workflow prerequisite steps use the same cmdlet under
the Actions default PowerShell shell and passed. These remain documented risks;
there is no observed failure warranting a wider patch or shell change.

## Proposed changes

- `packaging/smoke_test_packaged.ps1`: replace only the two resource hash calls
  with `Get-ResourceSha256`, using `File.OpenRead`, `SHA256.Create`, `ComputeHash`
  and hex conversion. Dispose stream/hasher in `finally`. Errors propagate;
  missing files and unequal SHA-256 values still throw before launch.
- `tests/test_packaged_resource_hash.py`: three non-native source contracts.
- `tests/test_packaged_resource_hash.ps1`: parse and extract the actual helper
  and resource loop; run synthetic byte fixtures with a throwing `Get-FileHash`
  shadow. Cover the SHA-256 `abc` vector, matching binary assets/locales, deliberate
  same-length byte mismatch, missing packaged file, direct missing-file hash,
  exclusive-lock read errors on each side, injected ComputeHash error, and handle
  disposal. Never invoke the full smoke script, executable or installer.
- `docs/CODEX_HANDOFF.md`: this handoff.

Hosted wrapper and workflow remain byte-identical to baseline. All guards,
data isolation, registry protection, timeouts, evidence capture and failure-stop
behavior are retained. Application launch/cleanup code is unchanged.

## Validation performed

Python 3.12.14, isolated processes, all PASS:

```text
python -B -m unittest discover -s tests -p test_hosted_installer_qualification.py -v
  13 tests
python -B -m unittest discover -s tests -p test_packaged_resource_hash.py -v
  3 tests
python -B -m unittest discover -s tests -p test_installer_preference_preservation.py -v
  12 tests
python -B -m unittest discover -s tests -p test_installer_shortcut_preservation.py -v
  9 tests
```

`git diff --check` passes for the review patch. Connector source blobs were
checked against baseline Git blob SHA-1 identities for unchanged inspected
files. These checks do not validate candidate binary SHA-256 values.
PowerShell, pwsh and dotnet are unavailable in this Linux workspace. The
PowerShell fixture has **not run**; executable SHA-256 match/mismatch/error
behavior and native qualification require Windows verification. No skipped
or weakened tests stand in for those pending checks. Full application tests,
public-source audit and publication secret scan have not run on this partial
snapshot; publication checks remain required before an authorized push.

## Immutable candidate

No candidate binaries were downloaded, edited, rebuilt or replaced. No version,
packaging configuration, release metadata, AGPL or third-party notice changes.
Inspected installer source remains byte-identical to baseline.
Expected retained identities (not rehashed here):

```text
Installer: e66a1932bcb1a9c7b5ea2371e99cca0561883ba11b72189d3405010d009b8782
Frozen EXE: 3e545d4257d8c15d33d5de0f55b43797f3d1a3690f9a63a69a9a26f647380403
```

## Next steps — owner approval required before push/workflow execution

1. Restore a working cloud Git checkout; verify the QA head is still the recorded
   baseline and apply only the four-file review patch, never synthetic history.
2. Run the focused Python tests, public-source audit, secret scan and diff checks
   in that complete checkout before publication.
3. Obtain explicit owner approval for pushing the reviewed patch to the existing
   QA branch. No push has occurred.
4. Obtain explicit approval for hosted execution. First run the synthetic fixture
   with Windows PowerShell (`powershell.exe -NoProfile -NonInteractive -File
   tests/test_packaged_resource_hash.ps1`) on a GitHub-hosted Windows runner.
   A separate bounded hosted fixture job can be proposed for review if needed;
   the current workflow was not changed to add one.
5. Only after the fixture passes and the owner authorizes the exact scenario,
   run hosted `/NOICONS` qualification against the unchanged retained candidate.
   The existing workflow also chains normal/preservation/purge; those steps are
   not authorized by this task. Review execution scope before dispatching and
   do not authorize or run uninstall or `/PURGEDATA` implicitly.
6. Review new retained evidence. Do not claim RC2 qualified without a new
   successful hosted run and required owner acceptance.
