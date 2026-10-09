> Retained historical engineering record, sanitized for public review.
> Current status: [RELEASE_STATUS.md](RELEASE_STATUS.md). This record does not
> establish approval of the current source or a new binary release. Local-only
> receipt paths refer to privately retained evidence, absent from this snapshot.

# Promoted OpenSSL supplier delta — 2026-10-07

**BLOCKED BEFORE RC BUILD. B5 BLOCKED solely for the retained Mesa/native maintenance/security/build qualification gap. The OpenSSL supplier/promotion/frozen subgate is PASS.** B1-B4 statuses remain blocked; only the two CRT input records in B2 change; neither native notices nor corresponding-source readiness is true. RELEASE-INFRA / DESKTOP, Windows x64. No final RC, installer, commit, push, tag, upload or publication.

| Stack | Before -> promoted release input | Result |
| --- | --- | --- |
| Python | CPython 3.14.6 / OpenSSL 3.5.7 -> complete PSF CPython 3.14.8 / OpenSSL 3.5.9 | ACCEPTABLE FOR RC for OpenSSL; coherent runtime + unchanged 23-wheel lock qualified |
| Qt | Qt/PySide6 6.11.2 + accidental Poppler OpenSSL 3.6.4 -> same Qt/PySide + FireDaemon OpenSSL 3.5.9 LTS | ACCEPTABLE FOR RC for OpenSSL; 305 exported resolver symbols and frozen runtime qualified |

The supported patched3.5.9 LTS replacement fixes the reviewed3.6.4 issues; semantic minor numbering is not a Qt dependency. No Qt/PySide update, Qt rebuild or commercial Qt is required for this TLS change. Mesa remains a separate existing blocker; this batch does not transfer it to another gate or certify it.

The historical3.14.6/3.5.7 + Poppler3.6.4 rows below are superseded for active release inputs. Both promoted stacks use independently supplier-qualified 3.5.9. Exact binary/source/configuration/rights pins and loaded paths: WINDOWS_TLS_NATIVE_QUALIFICATION.md.23-wheel lock unchanged, installed offline in the pinned release build venv. Mesa provenance/maintenance gap remains unchanged.

---

# Windows runtime qualification — 2026-10-07

**B5 BLOCKED.** No installed dependency was updated. Runtime identity is separate
from a reproducible build and from security acceptance. This continuation uses
the retained inventory; no broad dependency or usage audit was repeated.

## Exact wheel archive qualification

`windows-qualified-wheels.json` records exact filename, version, platform/ABI
tags, immutable PyPI file URL, published and downloaded SHA-256, archive RECORD,
METADATA hash and installed-file comparison. All **23 archives PASS**: the 17
retained shipping families, the PySide6 meta-package and five build-only
prerequisites (altgraph, packaging, pefile, pywin32-ctypes, setuptools). Build-only
prerequisites are not added to the shipping inventory. Qt binaries and opengl32sw
are byte-identical to their qualified wheel members; native GIS and NumPy
members also match. Pip script rewriting and `.data` relocation are handled;
the fontTools man page is checked at its installed data-scheme destination.

`requirements-windows-rc-hashed.txt` pins these inputs with one exact wheel hash
each, without changing the existing requirements architecture. A future fresh
Windows x64 CPython environment must use `--require-hashes --only-binary=:all:`;
the verification report supplies filenames/URLs to avoid platform ambiguity.
This lock reproduces the **retained** input identities; it does not approve the
old OpenSSL inputs. No package installation was performed. Source/compiled
metadata for Qt/PDFium/Mesa/OpenBLAS still needs the supplier materials in B1/B4.

CPython identifies as 3.14.6 / `tags/v3.14.6:c63aec6`, MSC v.1944, build
2026-06-10 10:26:10. Individual shipping DLL hashes and exact source archive
receipts exist. Still required: original signed official Windows installer or
equivalent supplier package, its immutable origin/hash/signature evidence,
extracted-file correspondence and exact build/patch receipt. The installation
directory and version string alone are insufficient provenance.

## OpenSSL instances and RC decision

| Instance | Actual shipping files | Application reachability | Qualification / required action |
| --- | --- | --- | --- |
| CPython OpenSSL 3.5.7 | `_internal/libssl-3.dll`, `libcrypto-3.dll`, used by `_ssl.pyd` / `_hashlib.pyd` | Python HTTPS updater when an explicit HTTPS feed/download is used; staging default is offline. Crypto routines remain callable. | **UPDATE REQUIRED**: supplier-qualified CPython-compatible 3.5.9 or later patched 3.5 input; original interpreter receipt still missing. |
| Qt OpenSSL 3.6.4 | `_internal/libssl-3-x64.dll`, `libcrypto-3-x64.dll`, Qt `qopensslbackend.dll` | Optional explicitly enabled OSM tiles use QNetworkAccessManager HTTPS. Retained frozen check selected the OpenSSL backend and loaded both stacks. | **UPDATE REQUIRED**: explicitly pinned Qt-compatible 3.6.5 or another qualified patched supported build. Replace ambient Poppler/tool PATH discovery with approved reproducible input. |

All four DLL hashes are in `windows-distribution-manifest.json`. The `-x64`
pair came from ambient bundled tool dependencies, **not** the PySide6 wheel.
Distinct filenames/backend consumers explain why both versions ship. Pyproj's
curl reports Schannel; it is not a third OpenSSL instance. No OpenSSL EXE ships.

[Official downloads](https://openssl-library.org/source/) checked on 2026-10-07
list 3.5.9 and 3.6.5 as latest patches. The 3.5 LTS line runs to 2030-04-08;
3.6 ends support on 2026-11-01. Both current DLL pairs are behind security patches.
Do not move to a new minor line silently; plan 3.6 maintenance before its expiry.

The full relevant interval is **3.5.7 → 3.5.8 (2026-08-25) → 3.5.9
(2026-09-29)** for Python, and **3.6.4 → 3.6.5 (2026-09-29)** for Qt.
The official [3.5](https://openssl-library.org/news/openssl-3.5-notes/)/
[3.6 release notes](https://openssl-library.org/news/openssl-3.6-notes/),
[2026-08-13](https://openssl-library.org/news/secadv/20260813.txt),
[2026-08-25](https://openssl-library.org/news/secadv/20260825.txt) and
[2026-09-29 advisories](https://openssl-library.org/news/secadv/20260929.txt)
were reconciled to their exact affected ranges. There are **23 affected CVEs
for 3.5.7 (one High, three Moderate, nineteen Low)** and **13 for 3.6.4
(one High, twelve Low)** in that interval. These are library applicability
counts, not reachable-exploit counts. No newer compatible patch was listed on
2026-10-07. `windows-openssl-qualification.json` records each range and disposition.
Targeted source inspection covers updater and GIS HTTPS, not arbitrary future
plugins or a full native CVE audit. It inspected `app/update_manager.py`,
`app/update_integration.py`, `app/gis/map_view.py` and `app/gis/providers.py`;
these use urllib HTTPS and Qt TLS, without custom OpenSSL CMS/CMP/QUIC/DTLS,
private-signing or EVP cipher calls. No malicious-server/exploit test is claimed.

| Fix included in 3.5.8 | Severity | Applicability / inspected Mastixa path |
| --- | --- | --- |
| CVE-2026-18798 | Moderate | Python affected; QUIC server initial-packet path absent. Qt 3.6.4 already fixed. |
| CVE-2026-63072 | Moderate | Python affected; CMS key-unwrapping API absent. Qt already fixed. |
| CVE-2026-63076 | Moderate | Python affected; CMP password-based protection path absent. Qt already fixed. |
| CVE-2026-14456, 63075 | Low | Python affected; QUIC listener/ACK-retention paths absent. Qt already fixed. |
| CVE-2026-14457 | Low | Python affected; raw-public-key certificate-less configuration absent. Qt already fixed. |
| CVE-2026-54874 | Low | Python affected; DTLS future-epoch buffering path absent. Qt already fixed. |
| CVE-2026-63073, 63074 | Low | Python affected; CMP client/server paths absent. Qt already fixed. |
| CVE-2026-75803 | Low | Python affected; affected EVP_Cipher empty AEAD API absent. Qt already fixed. |

The [2026-08-05 OCSP advisory CVE-2026-54876](https://openssl-library.org/news/secadv/20260805.txt)
affects 3.6 before 3.6.4 and explicitly excludes 3.5: neither current instance
is affected. The 3.5.8 notes additionally correct CCM authentication tags for
empty ciphertext; the 3.5.9/3.6.5 notes correct stale success from AES-SIV
`EVP_DecryptFinal`. These non-CVE fixes were considered separately; the inspected
application has no direct corresponding EVP cipher calls. The earlier June
patches are already included in the identified shipped versions; no unsupported
claim about supplier backports is substituted for their version ranges.

The following table covers the September advisory (both instances):

| Advisory | Severity | Exact applicability to this Windows workload |
| --- | --- | --- |
| CVE-2026-84782 | High | Both versions affected; DTLS retry path absent from inspected Mastixa calls. Not a shipping-library exemption. |
| CVE-2026-84783 | Moderate | OpenSSL 4.0 only; neither shipped instance affected. |
| CVE-2026-35189 | Low | Both affected; certificate processing reachable by HTTPS. Cannot clear. |
| CVE-2026-35191, 42772, 54873, 75804, 84784 | Low | QUIC paths absent from inspected calls. |
| CVE-2026-54872, 77696 | Low | Relevant private signing paths absent from inspected calls. |
| CVE-2026-54875 | Low | ARM64/RISC-V condition excludes this x64 target. |
| CVE-2026-72897 | Low | Server context-switch condition absent. |
| CVE-2026-75805 | Low | CMP client condition absent. |
| CVE-2026-75806 | Low | DTLS association condition absent; TLS conformance aspect separate. |

The High advisory is not dismissed because no exploit is known. Its required
DTLS path is distinguished from reachable certificate processing. No Critical
advisory was found in the reviewed post-version release notices. This is not
proof that all native components are vulnerability-free. Both instances have
the single classification **UPDATE REQUIRED**; absent specialized paths do not
override the reachable certificate-processing issue or incomplete supplier origin.

Updating these native inputs changes interpreter/native ABI, TLS loading,
trust-store behavior and potentially Qt backend choice. It requires a separate
bounded update batch: retain supplier binaries/source/build hashes, lock explicit
TLS inputs, validate both stacks with certificate-verifying HTTPS, updater,
native loading and frozen startup/input/PDF checks. Do not merely overwrite DLLs
in the owner's runtime, force Schannel, or treat an sdist as a patched binary.

## Mesa / LLVM fallback

`windows-mesa-provenance.json` links wheel `opengl32sw.dll` SHA-256
`34b444c016289b560662ff896deceb7f4b2c0723aed3d319ae167c9186ce42b3`
to [Qt's official Mesa 11.2.2 x64 prebuilts](https://download.qt.io/development_releases/prebuilt/llvmpipe/windows/).
The 2022 signed archive matches Qt's published SHA-256. All eight PE code/data
sections and the build timestamp match both the original 2016 and re-signed
prebuilts. Whole-file hashes differ; section correspondence does not establish
the same signing wrapper or a reproducible compilation.

The [Qt build recipe](https://wiki.qt.io/MesaLlvmpipe) explains the embedded
Mesa 11.2.2 / LLVM 3.6.2 strings. [Qt 6.11 graphics documentation](https://doc.qt.io/qt-6.11/windows-graphics.html)
identifies software fallback when system OpenGL is unavailable/blacklisted, or
when explicitly requested. This does not make it active on all normal hardware.
It was absent from the retained normal frozen startup/input/PDF loaded-module
list. No accelerated or forced software-context acceptance was established.

Exact Mesa upstream license HTML, LLVM 3.6.2 UIUC text and regex candidate notice
are now indexed. Supplier patches, compiler flags and complete static-component
notices remain missing; upstream version sources alone do not prove full build
correspondence. LLVM has additional per-file licenses. This 2016 fallback has
no evidenced current security maintenance; no absence-of-CVEs clearance is made.
Keep **BLOCKER** status until supplier/security qualification or a separately
proven safe exclusion/replacement. Packaging was not changed in this batch.
