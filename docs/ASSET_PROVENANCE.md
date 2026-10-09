> Retained historical engineering record, sanitized for public review.
> Current status: [RELEASE_STATUS.md](RELEASE_STATUS.md). This record does not
> establish approval of the current source or a new binary release. Local-only
> receipt paths refer to privately retained evidence, absent from this snapshot.

> Current horizontal native audit — 2026-10-07. The original 41 shipping
> project artwork hashes/owner attestation below remain unchanged. No standalone
> font files or basemap tile packs are packaged, but **16 embedded PDFium/Foxit
> fonts actually ship inside Qt6Pdf.dll**. Each generated source array was
> byte-matched in the native DLL; names, sizes, hashes, source URLs, BSD license
> and original Foxit/PDFium copyright are in embedded-font-provenance.json and
> the collected license index. NotoSansCJK is upstream test-only and excluded.
> These are dependency-provided assets, not project-created artwork. CRS/EPSG
> data rights and native Nth-party/build notices remain blockers in
> WINDOWS_DISTRIBUTION_COMPLIANCE_MATRIX.md. The physical-file scan below does
> not replace this embedded-resource audit.

# Windows asset and resource provenance — 2026-10-07

Scope: Windows `1.0.0-rc.1` preparation. No public distribution approval is
implied. The complete shipping artwork ledger is `asset-provenance.json`:
**41 files: 35 PNG, 5 SVG, 1 ICO**, each with path, SHA-256 and evidence.

| Class | Windows inputs / result |
| --- | --- |
| PROJECT-CREATED / AI-ASSISTED | The 41 artwork inputs under `app/assets/` and `packaging/mastixa_manager.ico`. Owner expressly states project logo/icons/assets were created for Mastixa with ChatGPT/OpenAI assistance. This is an owner attestation, not an independent copyright adjudication. The five SVGs contain simple inline paths without external image/font references. |
| QT/DEPENDENCY-PROVIDED | Qt/CPython/GIS/NumPy libraries, plugin images/resources, embedded DLL/EXE resources, `proj.db`, certifi CA data and emitted PyInstaller/Inno runtime. Upstream licenses remain applicable; a project artwork statement does not cover them. |
| THIRD-PARTY WITH KNOWN LICENSE | Shipped Python component texts and their known native license families are indexed in `../THIRD_PARTY_NOTICES.md` and `../licenses/manifest.json`. OSM attribution applies to explicitly enabled tiles, not a bundled image pack. |
| UNKNOWN PROVENANCE | No unknown artwork is currently inside the 41-file Windows input closure. Exact native dependency sublicenses/source/redist mapping is incomplete and blocks release packaging; known dependency origin does not imply license clearance. Any newly added unknown shipping resource blocks public distribution. |
| TEST/EVIDENCE ONLY — DOES NOT SHIP | Historical EXE/setup/build copies, tests, diagnostic renders, private profile/backup/export files and evidence outside the source checkout are not packaging inputs. |

Full repository filesystem resource scan (excluding `.git`, Python caches,
`.gradle`, `.venv` and `.tools` dependency caches): **334 files**; 41 current
artwork inputs, 166 historical dependency/build resources, 127 nonshipping
evidence/output resources. The per-file audit is outside the checkout in
`WindowsRcPreparationEvidence/resource-inventory.json`. Separate exact old
bundle membership and PYZ component inventory are retained there. Android
resources are not Windows inputs; no Android implementation was performed.

Search covered PNG/JPG/JPEG/SVG/ICO/WebP, TTF/OTF/WOFF/WOFF2, maps/tiles
(MBTiles/GPKG/TIFF/OSM/PBF), PDFs/document/spreadsheet templates, DLL/PYD/EXE,
QRC/RCC and installer graphics. No bundled font files, map tile packs,
PDF/document templates or QRC/RCC files appear in the current Windows source
resource inputs. The Inno installer graphic input is the project ICO;
default wizard art and installer embedded resources are Inno-provided.

Qt PNG/ICO/image-format handlers and software OpenGL are dependency resources,
not project-created artwork. Final native resource/notice membership still
requires reconciliation with the exact selected wheels and Qt SBOM/source tree.
The old bundle is evidence only; it is not a rebuilt RC.

OSM is optional, explicit, visible-tile access with existing attribution in
`app/gis/dialog.py` / `providers.py`; no bulk tiles are packaged. PROJ CRS data
and EPSG terms must be matched to `proj.db` in the exact wheel. PDF exports use
system fonts (including Segoe UI) via Qt; no font file is shipped. Verify actual
font embedding permissions when distributing exports/templates containing fonts.

The release preflight checks exact input membership and hashes against the
ledger. This catches new/changed resources before packaging and does not modify
artwork. Icon background/resolution differences remain report-only polish.
