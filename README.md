# Mastixa Manager

Local farm management for Windows, with an Android application in development.
Profiles, farm records, production, sales, expenses, inventory, equipment,
year locking, reports, backups and GIS tools keep operational data on the device.
Optional map access requires an explicit selection. No cloud account is required.

**Windows x64 is the current release target. Android remains in development.**
This is an **active public AGPL development snapshot**, post-rc.1 / pre-rc.2.
Current Windows source targets **1.0.0-rc.2**.
Windows **1.0.0-rc.2 has not been built or owner-qualified**. rc.1 is historical;
its known owner-acceptance issues have since been addressed in source and require
a new candidate for frozen validation.
No public binary release is approved. See [release status](docs/RELEASE_STATUS.md).

First-party material is designated **AGPL-3.0-only**. The full official text is
in [LICENSE](LICENSE); [licensing scope](docs/LICENSING.md) explains the version
choice and third-party exceptions. Third-party licenses, notices, EPSG/PROJ
terms and covered-library source/replacement obligations remain applicable.
See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and [licenses/](licenses/).

[Sxara242/Mastixa-Manager-Source](https://github.com/Sxara242/Mastixa-Manager-Source)
is the primary active development repository for rc.2 and later versions.
This snapshot introduces no private Git history. The historical private repository
is protected archival/reference material. Future fixes, tests, documentation,
pull requests and CI changes belong here. No release feed is activated.
The rights holder retains the option to offer separate commercial terms later.

## Run and develop

Use Python 3.14 on Windows and install into a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -c requirements-windows-rc.txt
.\.venv\Scripts\python.exe main.py
```

Use a separate test profile during development. See [installation](docs/INSTALLATION.md)
and [development/building](docs/BUILDING.md) for isolated tests, Android prerequisites
and qualified Windows packaging.

## Verification and contributions

GitHub Actions use `windows-latest` for Windows tests and packaging contracts,
and `ubuntu-latest` for source audit and Android build/lint. Android instrumentation
is a separate manual emulator check. Regular CI creates no installers and uploads
no artifacts. Explicit Android QA artifacts expire after one day. Actual release
qualification and corresponding-source delivery remain separate gates.

Bug reports and discussion are welcome. External patches are not accepted for
merge until a written agreement supports AGPL and separate commercial licensing.
A DCO sign-off alone does not grant those rights. See [CONTRIBUTING.md](CONTRIBUTING.md)
and the [contribution-rights baseline](docs/CONTRIBUTION_RIGHTS.md).
Use synthetic examples; do not include credentials, private logs, real databases,
backups or GPS exports in issues or pull requests.
