# Public development migration

The owner authorizes the current post-rc.1 / pre-rc.2 AGPL-3.0-only development
snapshot once privacy, licensing, third-party notice, hygiene and workflow audits
pass. Known Windows source-test failures block rc.2 build and qualification;
they do not block this development-source publication.

The public repository already has public-only snapshot history. Preserve that
history and add this audited filesystem snapshot as a normal commit. Do not
copy private Git metadata, refs, commits or ancestry, add private remotes, merge
private history, force-push or rewrite the protected archival repository.

After the first audited push, verify actual GitHub Actions runs: Windows and
Ubuntu hosted jobs must start, no self-hosted runner may be requested, and
normal CI must produce no installers or uploads. The public repository then
becomes the primary active development repository. All Phase 5 fixes and rc.2+
source, tests, docs, PRs and CI changes belong in its clean public checkout.
Record the baseline commit, origin and checkout path outside published source;
verify the protected private checkouts' HEADs, statuses and file hashes.

Preserve the public-source exclusion and privacy rules on every future change.
Never import private profiles, databases, logs, machine configuration, credentials,
signing keys, historical audit evidence directories or private candidate binaries.
Intentional synthetic/binary source inputs require review and hash indexing.

Routine CI runs Windows source tests, legal/preflight checks and Android build/lint
using `windows-latest` and `ubuntu-latest`. No routine installers or uploads.
Optional manually requested Android QA APKs expire after one day. Qualified
Windows installer generation remains a controlled maintainer step.

Windows rc.2 remains unbuilt and unqualified. Do not publish an rc.1 installer as
current or create a misleading rc.2 release/tag. A binary release needs qualified
supplier inputs, frozen/install validation, matching covered source/build/patch/
replacement materials with durable equivalent access, and explicit owner
acceptance. Android remains in development and needs its own release audit.

First-party material is AGPL-3.0-only; third-party licenses remain in force.
The owner retains separate commercial licensing rights. External merge intake
remains closed until an executed rights grant is recorded; DCO alone is insufficient.
