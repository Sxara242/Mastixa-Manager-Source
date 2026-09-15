# Phase 16I — license / distribution readiness

Reviewed 2026-09-13 against `bcedfeea02bb40bfa9032427127ec1cbf1a16aaa`.
Documentation-only continuation. No project license selected or installed;
no application, dependency, packaging, signing or test configuration changed.
This is an evidence-based engineering assessment, **not legal clearance**.
The user decides the project license. Third-party rights cannot be relicensed
by adding a Fieltra LICENSE file.

## Evidence and concrete blockers

1. **Project license decision pending — distribution blocker.** No root LICENSE
   exists. Private repository access does not itself grant public redistribution
   or fork rights. Contributor/asset ownership must support any license chosen.
2. **Qt Virtual Keyboard — high distribution risk, confirmed in inspected
   Windows packages.** Both existing local bundles contain
   `Qt6VirtualKeyboard.dll` and `plugins/platforminputcontexts/qtvirtualkeyboardplugin.dll`.
   QtGui's installed PyInstaller hook collects platforminputcontexts; the current
   spec does not filter this plugin. This explains inclusion despite no direct
   Python VirtualKeyboard import. Upstream offers this module under **GPLv3 or
   commercial terms**, not the ordinary Qt LGPL option. No commercial grant was
   established. Inclusion alone is not a legal finding that every Fieltra file
   is GPL; nevertheless a blanket LGPL-only/non-commercial distribution claim
   is unsafe. Decide on GPL-compatible distribution, establish a valid commercial
   entitlement, or separately review removal if unused. **No removal here.**
   The exact current Windows release artifact is UNVERIFIED; inspected bundles
   are dated 2026-08-29/09-10, not rebuilt from current HEAD.
3. **Third-party license delivery — FAIL / release blocker.** The older Windows
   bundle has no files named LICENSE/COPYING/NOTICE; the Phase8 bundle has NumPy
   notices but lacks corresponding Qt/GEOS/PROJ license files by that scan.
   Current spec explicitly includes assets/locales, with no comprehensive notice
   collection. The current-head runner APK contains only `assets/tessdata/LICENSE`;
   `android/THIRD_PARTY_NOTICES.md` is outside packaged assets. No alternative
   application notice-delivery mechanism was found. Tesseract's AAR and inspected
   runtime JARs do not themselves include the missing full notices. An Apache
   license for OCR models does not discharge JTS/MIT/BSD/LGPL/codec obligations.
   This is a delivery/readiness gap, not evidence that upstream libraries are
   inherently incompatible. A future notice/source-delivery package needs exact
   dependency versions and an artifact-content check; README links alone are
   not a substitute for required license texts.
4. **Asset provenance — UNVERIFIED / release sign-off pending.** Tracked icons
   under `app/assets/icons/mastixa_menu`, branding ICO and small SVG/PNG assets
   lack a rights/provenance ledger. No infringement is established; authorship
   or redistribution rights must be confirmed. No tracked TTF/OTF/WOFF files or
   font files in the inspected APK were found. System-font PDF embedding rights
   and third-party fonts that Qt/PDFium might embed still depend on actual fonts.

No already passing gate was rerun to establish these findings; archive listing,
metadata, packaging source and pinned upstream licensing were sufficient.

## Dependency license inventory

Version numbers below describe the reviewed local environment/cache; final
release closure must use the actual shipped artifact, especially with Python
version ranges. Installed `*.dist-info` licenses/metadata, Gradle POM parents,
pinned upstream native build/license files and existing bundle membership are
the evidence. PASS means license identified, not all distribution duties met.

| Component | Identified license / obligations | Assessment |
|---|---|---|
| PySide6 / Essentials / Addons / shiboken6 6.11.2 | Metadata: LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only; commercial alternative requires entitlement. Per-module Qt rules override simplistic whole-wheel assumptions. | PASS identification; distribution PARTIAL |
| Qt Core/Gui/Widgets/Network/PrintSupport/QML/Quick/SVG/OpenGL | Generally LGPLv3/GPL alternatives; preserve module and embedded third-party notices, source obligations and library replacement/debugging rights under LGPL. | PARTIAL exact bundled subcomponent closure |
| Qt Virtual Keyboard | GPLv3 or commercial. Not covered by assuming all Qt DLLs are LGPL. | FAIL readiness until chosen route resolved |
| Qt PDF / PDFium, image plugins, software OpenGL | Qt PDF has LGPLv3/GPLv2 alternatives; PDFium/Chromium third-party code and codecs have additional notices. `qpdf` was included automatically; no WebEngineCore in inspected bundles. Software renderer's complete embedded license inventory UNVERIFIED. | PARTIAL |
| pyproj 3.8.0 / PROJ | MIT-style; both installed LICENSE and LICENSE_proj inspected. Include copyright/permission notices. | PASS identification |
| PROJ resources / Proj4J-EPSG / `crs-2d.txt` | EPSG dataset has separate IOGP terms, not simply MIT/Apache. See below. | PARTIAL delivery |
| libcurl in pyproj wheel | curl permission license; preserve copyright/permission text, no endorsement implication. | PASS family; exact bundled source/version closure PARTIAL |
| pyproj bundled TIFF / JPEG / zlib / lzma | libtiff permissive notices, IJG/libjpeg terms, zlib, XZ/liblzma mixed/public-domain/permissive terms as applicable. DLL names alone do not establish exact source versions or every license. | UNVERIFIED exact wheel-native notice closure |
| Shapely 2.1.2 / GEOS | Shapely BSD-3-Clause; bundled GEOS **LGPL-2.1** per installed LICENSE_GEOS. Dynamic DLL boundaries do not eliminate notice/source/relinking obligations. | PASS identification; distribution PARTIAL |
| NumPy 2.5.3 | Installed expression BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0; retain its full multi-component license tree. | PASS identification |
| OpenBLAS / LAPACK / GCC runtime in NumPy wheel | Installed LICENSE explicitly identifies BSD-3-Clause, BSD-3-Clause-Open-MPI, and **GPL-3.0-or-later WITH GCC-exception-3.1**. The runtime exception matters; this is not an automatic GPL license requirement for Fieltra. | PASS identified text; exact compiler provenance UNVERIFIED |
| pyshp 2.4.2; ezdxf 1.4.4; pyparsing 3.3.2 | MIT. Native CAD accelerators/embedded algorithms still need their retained upstream notices. | PASS primary license |
| fontTools 4.64.0 | MIT; LICENSE.external also lists SIL OFL test fonts/reserved names. Do not assume test font assets ship solely because their notices are installed. | PASS primary; exact font subset PARTIAL |
| defusedxml 0.7.1; typing_extensions 4.16.0 | PSF/PSFL and PSF-2.0 respectively; retain notices. | PASS identification |
| openpyxl 3.1.5; et-xmlfile 2.0.0 | MIT metadata; no separate license file listed in these installed wheels, so obtain correct upstream text for redistribution. | PASS identification; notice delivery PARTIAL |
| certifi 2026.7.22 | MPL-2.0, certificate bundle/notices. Make covered source available as required; modifications to covered files retain MPL obligations. Not a requirement to publish all unrelated Fieltra source. | PASS identification; delivery PARTIAL |
| CPython 3.12 local bundle and extensions | PSF license plus historical/embedded third-party licenses (expat, compression, libffi, etc.). Do not apply Python's umbrella label to every DLL. CI's Python differs; exact final distribution inventory required. | PARTIAL |
| SQLite (CPython and separate PROJ copy) | SQLite core public-domain dedication; ordinary use has no license fee/source-offer duty. Separately licensed extensions are not assumed covered. | PASS core identification |
| OpenSSL 3 DLLs | Apache-2.0 family; exact version notices required. | PARTIAL exact binary/license matching |
| Microsoft MSVC/UCRT/API-set redistributables | Microsoft redistribution terms, not Fieltra's project license. Confirm eligible redistributable list/source and entitlement; OS components need not be relicensed as app code. | UNVERIFIED legal redistribution closure |
| Android JTS core 1.20.0 | EPL-2.0 / EDL-1.0 dual licensing per parent POM. Assess the permissive EDL/BSD-style route for this distribution instead of assuming EPL source obligations are mandatory. | PASS identification |
| Android Proj4J 1.4.3 | Apache-2.0 per parent POM. Proj4J-EPSG adds separate EPSG terms. | PASS identification |
| GeographicLib-Java 2.1 | MIT, retained copyright/permission text. | PASS identification |
| Tesseract4Android 4.9.0; Tesseract 5.5.1 | Apache-2.0, preserve upstream/wrapper notices and any relevant NOTICE content. Pinned source credits tess-two/Tesseract Tools for Android. | PASS identification; APK notices FAIL |
| Leptonica 1.85.0 | BSD-2-Clause-style text from pinned native source; reproduce copyright/conditions/disclaimer with binary distribution. | PASS identification |
| libjpeg v9f | IJG custom permissive license; prescribed Independent JPEG Group acknowledgment and source/change conditions, not just a generic MIT label. | PASS identification |
| libpng 1.6.48 | libpng license text (PNG Reference Library terms and retained earlier notices). | PASS identification |
| OCR native C++ / Android system zlib | NDK C++ runtime usually LLVM/libc++ terms with exceptions; pinned build uses NDK 27.2.12479018. No separate libc++_shared.so appears, so statically incorporated support must be accounted for. System zlib is provided by Android, not a separate APK file here. | UNVERIFIED complete static closure |
| AndroidX annotation 1.3.0 | Apache-2.0; no Kotlin runtime implied by this pinned annotation dependency. | PASS family; delivery PARTIAL |
| desugar_jdk_libs 2.1.5 | POM: **GPLv2 with Classpath Exception**; preserve applicable source/notices/exception for included runtime code. Exception avoids automatic GPL propagation merely through linking; exact transformed subset/source provision still needs documentation. | PASS identification; distribution PARTIAL |
| Bundled ell/eng tessdata_fast models | Apache-2.0; existing model hashes and shipped LICENSE retained. Models were downloaded from `main`, not an immutable source tag; hashes identify bytes. | PASS license delivery for models; provenance PARTIAL |
| PyInstaller 6.22.2 | GPLv2-or-later with special exception allowing packaged nonfree/commercial applications. Bootloader exception avoids automatically licensing Fieltra as GPL. | PASS identification |
| PyInstaller hooks-contrib 2026.7, altgraph 0.17.5, pefile 2024.8.26, pywin32-ctypes 0.2.3, packaging 26.3, setuptools | Installed hooks-contrib license distinguishes GPL-2.0-or-later standard hooks from Apache-2.0 runtime hooks. Remaining tools: MIT, BSD-3-Clause, Apache-2.0 OR BSD-2-Clause as applicable. Development presence does not mean every tool is redistributed; account for emitted runtime hooks. | PASS license identification; output subset PARTIAL |
| Inno Setup | Installed license permits commercial use/redistribution with original notices and no misrepresentation; setup/uninstaller retain their own rights. Compiler/tool distribution is distinct from app output. | PASS inspected installed terms |
| Gradle / AGP / JDK / Android SDK; test-only JUnit / AndroidX runner | Gradle/AGP predominantly Apache-2.0; JDK GPLv2+Classpath exception; SDK proprietary tool terms; JUnit EPL and runner Apache. Build/test tools are not app runtime dependencies; no need to ship entire toolchains. | PARTIAL relevant output exceptions; not a runtime conflict finding |
| OSM data/tiles | ODbL data attribution plus tile-service policy; project source license does not override provider terms. No bulk prefetch permission implied. | PASS identified obligations; retained map attribution evidence |
| Fieltra icons/branding/SVG/PNG, possible embedded fonts | Rights ledger absent; system font use is distinct from redistributing font files or embedding them in exports. Brand/trademark rights separate from code license. | UNVERIFIED owner confirmation required |

No AGPL dependency was identified in the reviewed graph. This is not a claim
that exhaustive historical, vendored or future-resolution license scanning passed.

## Distribution duties and compatibility

- **LGPL:** ship relevant license texts/notices and satisfy corresponding-source
  obligations for covered libraries. Preserve the ability to replace compatible
  shared libraries and reverse-engineer for debugging their modifications;
  provide relinking/installation information where required. PyInstaller onedir
  DLLs make a compliant route plausible, not automatically proven. Static linking
  requires particular attention. Review store/EULA restrictions against these
  rights. A non-commercial condition must not override third-party LGPL rights.
- **GPL components:** no additional non-commercial restriction on the covered
  combined work. Establish which GPL-only code is actually combined/shipped and
  how obligations are fulfilled. Qt VirtualKeyboard requires a concrete decision;
  runtime exceptions for PyInstaller, GCC and desugar are separate, scoped grants.
- **MPL:** retain notices and make covered source available, including covered
  modifications; larger works may contain differently licensed separate files.
- **MIT/BSD/Apache/codec licenses:** retain the correct copyright, disclaimer and
  license text; carry relevant Apache NOTICE and change notices; do not imply
  endorsement or trademark permission. Source publication is not normally demanded
  by permissive licenses, but their notices are still mandatory as applicable.
- **EPSG:** pinned Proj4J v1.4.3 commit
  `7362c85e34b37cf133e2cbc0a4d3d049b166a720` LICENSE.EPSG was read. Section 2
  restricts profit from the dataset, while **6.3 expressly permits inclusion in a
  commercial package when value comes from added functionality, not the dataset**.
  Pass on terms, acknowledge IOGP ownership, respect subset/modification rules;
  do not mislabel this as a blanket ban on commercial Fieltra use. Final treatment
  of the derived CRS catalog and distribution materials needs sign-off.
- **Assets/platform runtimes:** verify ownership and redistribution grants, font
  embedding conditions, Microsoft redist entitlement and exact native notices.
  A missing evidence trail is UNVERIFIED, not an accusation of infringement.

## Project-license choices — decision remains with the user

OSI open source permits commercial use. A no-commercial-use rule is
**source-available**, not OSI-approved open source. “Use by a working farmer”
and “a vendor selling a competing fork” are different policy choices. A blanket
NC license may restrict ordinary professional farm use; that ambiguity matters
for this application and must be resolved before choosing a license.

| Option | Commercial / redistribution / forks | Source disclosure / OSI | User ownership and Windows/Android trade-off | Dependency risk |
|---|---|---|---|---|
| GPL-3.0 (choose exact version/later wording separately) | Yes / yes / yes under GPL duties | Corresponding source on covered distribution; private changes need not be published. OSI yes. | Strong reciprocal fork/survival rights; cannot ban commercial competitors. More source/build/installation obligations for binary distributors. | Most natural candidate if GPLv3-only Qt code remains, subject to full module/third-party compatibility and contributor rights; not automatic clearance. |
| MPL-2.0 | Yes / yes / yes | Covered-file source on distribution; file-level copyleft. OSI yes. | Keeps improvements to covered files available, allows mixed larger apps; can support independent maintenance without whole-app copyleft. | LGPL compliance remains; GPL combination requires eligible secondary-license route and correct distribution terms, not an NC add-on. Qt GPL-only issue still needs resolution. |
| Apache-2.0 | Yes / yes / yes | No general source-disclosure requirement; notices/patent provisions. OSI yes. | Simple reuse and broad forks, but closed forks are possible. Does not guarantee future changes stay available. | Compatible routes exist with LGPL duties; GPLv3 combined distribution adds GPL obligations. Apache project labeling alone does not clear VirtualKeyboard or third-party notices. |
| PolyForm Noncommercial 1.0.0 | Commercial use generally no; redistribution and changes/forks under permitted purposes/terms | No general reciprocal source-disclosure requirement; source availability must be supplied deliberately. OSI no. | Matches a strict NC goal, but limits professional use, paid maintenance and some legitimate forks; weaker long-term independence. Cannot claim all open-source freedoms. | Cannot impose NC on GPL-covered combined works; resolve GPL-only Qt first, preserve LGPL rights. Exact scope/exceptions require legal review. |

No option is selected. If user ownership and sustainable independent forks are
the priority, GPL/MPL are candidates; if NC is non-negotiable, first specify
whether commercial **use** or commercial **resale** is prohibited. Do not invent
a custom exception or install a LICENSE without the owner's decision.

## Closure and next checkpoint

**PROJECT LICENSE DECISION = DEFERRED BY OWNER.** The owner deliberately defers
the final decision until possible FUTO collaboration/support interest is known.
This is not a technical security failure. It does not waive any distribution
obligation. Phase16J is now explicitly authorized; public release is not cleared.
The authoritative persistent blocker list is in MASTER_PROGRESS.md.

**Phase 16I: PARTIAL.** Native review found no new demonstrated automatic upload
or tracking activation needing a code fix. Formal proof of every third-party
byte remains UNVERIFIED and is not by itself a blocker. Actual blockers are the
project-license decision, Qt GPL-only packaging route, complete notices/source
delivery and rights/provenance sign-off for assets/platform components.

Deferred distribution checkpoint: owner chooses intended commercial-use/fork
policy and license route; then resolve exact packaged Qt membership and assemble versioned
third-party notices/source-access materials. Only packaging/runtime changes would
justify targeted checks and relevant fresh CI/gates. This audit made none and
did not itself start Phase 16J. The subsequent owner instruction authorizes 16J
after committing/pushing this documentation checkpoint. Production signing/release artifacts and optional live
Supabase assurance retain their separate previously documented limits.

## Primary sources consulted

- [Qt module licensing](https://doc.qt.io/qt-6/licensing.html),
  [Virtual Keyboard](https://doc.qt.io/qt-6/qtvirtualkeyboard-index.html),
  [PDF licensing](https://doc.qt.io/qt-6/qtpdf-licensing.html),
  [Qt LGPL obligations](https://www.qt.io/development/open-source-lgpl-obligations).
- [LGPLv3 text](https://opensource.org/license/lgpl-3-0),
  [GPLv3 text](https://opensource.org/license/gpl-3.0),
  [MPL FAQ](https://www.mozilla.org/en-US/MPL/2.0/FAQ/),
  [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0),
  [OSI definition](https://opensource.org/osd),
  [PolyForm NC](https://polyformproject.org/licenses/noncommercial/1.0.0).
- [Pinned OCR source and licenses](https://github.com/adaptech-cz/Tesseract4Android/tree/4.9.0/tesseract4android/src/main/cpp),
  [pinned EPSG terms](https://github.com/locationtech/proj4j/blob/7362c85e34b37cf133e2cbc0a4d3d049b166a720/LICENSE.EPSG),
  [desugar license](https://github.com/google/desugar_jdk_libs/blob/master/LICENSE)
  (local 2.1.5 POM independently identifies GPLv2+Classpath; master is not binary provenance).
- [SQLite dedication](https://www.sqlite.org/copyright.html),
  [curl license](https://curl.se/docs/copyright.html),
  [PyInstaller exception](https://pyinstaller.org/en/stable/license.html),
  [Microsoft redistributable identification](https://learn.microsoft.com/en-us/cpp/windows/determining-which-dlls-to-redistribute?view=msvc-170).
- [OSM copyright](https://www.openstreetmap.org/copyright),
  [tile policy](https://operations.osmfoundation.org/policies/tiles/).
  Installed Inno `license.txt` and wheel license files were read locally; online
  documentation is not substituted for the license of the actual shipped binary.
