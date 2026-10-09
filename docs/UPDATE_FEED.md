# Windows updater: RC preparation

Architecture: explicit user check -> project JSON metadata -> project GitHub
Release installer -> SHA-256 verification -> explicit installation confirmation.
No profile/usage data is uploaded. No update executes silently.

This candidate configuration is **offline staging** (`UPDATE_FEED_MODE=staging`).
The default check reads the bundled `updates/staging/rc.json`, reports the current
version and offers no download. No production feed has been published or tested.
Tests inject HTTPS feed responses and installer bytes without network or launch.

Schema 1 fields: `schema=1`, `product="Mastixa Manager"`, `version`, `channel`,
HTTPS `release_url` (release notes reference), `notes`, optional `windows` and
optional `android`. A downloadable `windows` object has `filename` (safe EXE
basename), HTTPS `url`, and the exact 64-hex `sha256` of the final artifact.
Null asset means no direct download; no placeholder checksum is deployable.

Channels include `stable` and `rc` (legacy alpha/beta parsing is preserved).
Version suffix and channel must agree. A selected stable feed must be stable;
a selected RC feed must be RC. Version ordering: alpha < beta < rc < stable at
the same numeric version, with numeric prerelease serials. Same/older versions
are no-update states. RC-to-stable graduation requires an explicit release
configuration decision; RC users are not silently moved to stable here.

For remote staging QA call `fetch_update_info(test_https_url,
expected_channel="rc", opener=test_opener)`; operational downloadable assets
must be on `github.com/Sxara242/Mastixa-Manager-Source/releases/download/`.
Default future remote metadata location is the project-controlled
`https://raw.githubusercontent.com/Sxara242/Mastixa-Manager-Source/main/updates/rc.json`;
stable uses `updates/stable.json`. These locations are configuration proposals,
not claims that anonymous production endpoints currently exist.

Before enabling remote mode, approve/publish exact versioned binary and source
materials, record final hashes, verify anonymous feed/download access and real
older-to-new upgrade in an isolated profile. Changing `UPDATE_FEED_MODE` to
remote is a separate reviewed release action. Never publish the staging fixtures.

Failed downloads and checksum mismatches remove partial files, report failure
and leave same-session retry enabled. Verification precedes installer promotion;
the existing Yes/No confirmation precedes launch. SHA checks integrity against
the feed, not independently authenticated publisher identity. Candidate is
UNSIGNED; Unknown Publisher/SmartScreen warnings are expected. No keys or
signing secrets are needed for this internal RC.
