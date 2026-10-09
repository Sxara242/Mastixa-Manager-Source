> Retained historical engineering record, sanitized for public review.
> Current status: [RELEASE_STATUS.md](RELEASE_STATUS.md). This record does not
> establish approval of the current source or a new binary release. Local-only
> receipt paths refer to privately retained evidence, absent from this snapshot.

> Current completed B1–B5 closure — 2026-10-07:
> **BLOCKED BEFORE RC BUILD**; B1–B5 all remain BLOCKED with concrete evidence gaps.
> 23 qualified wheel results and lock reused; both shipping OpenSSL stacks need
> updates in a separately authorized native batch. EPSG full terms now bundled.
> See the leading CODEX_HANDOFF.md and compliance matrix for exact current state.
> Prior audit/Batch10 entries below remain historical. No RC or new batch started.

> Current authoritative distribution audit — 2026-10-07:
> **BLOCKED BEFORE RC BUILD**, exactly five readiness blockers B1–B5.
> See the leading CODEX_HANDOFF.md checkpoint and
> WINDOWS_DISTRIBUTION_COMPLIANCE_MATRIX.md for current versions/counts/evidence.
> The prior three-blocker preparation and original Batch10 text below remain
> historical. Accepted usage/performance evidence and updater retry are retained.
> No final RC or installer built; stop after the current audit batch.

> Batch10 historical checkpoint. Version/license/unsigned/feed decisions
> are superseded by the latest Windows RC preparation in CODEX_HANDOFF.md.
> Batch10 download-retry fix and accepted usage/performance evidence are retained.

# Final Windows v1 release gate / Batch 10 — 2026-10-07

**Overall result: BLOCKED BEFORE CANDIDATE BUILD.**

Scope: RELEASE-INFRA + μία επιβεβαιωμένη DESKTOP updater-recovery διόρθωση.
Approved worktree: `<WORKSPACE>/Mastixa-Icon-Diagnosis`,
branch `icon-runtime-qa-final`, HEAD `0a0031cf8ea20b2956944bf8468da9d647701237`.
Δεν υπάρχει αποδεδειγμένο νέο build/compiler failure. Το αποτέλεσμα αφορά την
ετοιμότητα του **τελικού Windows v1 candidate**: έκδοση/channel δεν έχουν
επιλεγεί και η distribution configuration έχει τα συγκεκριμένα κενά παρακάτω.
Ένα εσωτερικό diagnostic alpha build είναι τεχνικά διαφορετικό από εγκεκριμένο
τελικό v1 candidate. Δεν έγινε packaging, signing, feed publication, commit/push
ή Android εργασία. Δεν ξεκίνησε άλλη παρτίδα.

Η νεότερη owner οδηγία κλείνει τα Year Lock/correction/CRUD/year-confirmation,
theme/hover, English Sort και performance θέματα. Τα historical handoff
«PERFORMANCE BLOCKER REMAINS» υπερκαλύπτονται. Το mandatory audit παραμένει
99/99 automated + 38/38 native, `PASS WITH OWNER/ARTIFACT FOLLOW-UP`.
Δεν επαναλήφθηκε, ούτε μεταφέρθηκε ως packaged-candidate acceptance.
Performance επανέλεγχος μόνο πριν από final public release, χωρίς optimization
εκτός αποδεδειγμένου blocker.

## 1. Version / release metadata

**PASS για την υπάρχουσα alpha· OWNER DECISION REQUIRED για v1.**

| Πηγή | Τρέχουσα τιμή / συμπέρασμα |
| --- | --- |
| `app/version.py` | `APP_VERSION=0.40.0-alpha.2`, `RELEASE_CHANNEL=alpha`, tag `v0.40.0-alpha.2` |
| Installer / filename | `MyAppVersion=0.40.0-alpha.2`, `MastixaManager-0.40.0-alpha.2-Setup.exe` |
| EXE PE resources | String FileVersion/ProductVersion `0.40.0-alpha.2`; numeric tuples `(0, 40, 0, 2)` |
| Installer PE resources | VersionInfoVersion/ProductVersion `0.40.0.2` |
| Build script | Διαβάζει το MyAppVersion για output και `.sha256`; δεν έχει δεύτερο hardcoded filename |
| Windows CI gate | Verify/upload/artifact label και trigger branch παραμένουν hardcoded στην alpha.2 |
| Visible version / About equivalent | Window title μέσω `install_version_ui()` και Settings Updates label μέσω APP_VERSION. Δεν βρέθηκε χωριστή About/version page στα inspected navigation/settings sources |
| Updater | User-Agent με APP_VERSION· production payload δεν επιβεβαιώθηκε |
| README / changelog | README alpha.2· νεότερο changelog section alpha.1, χωρίς alpha.2/v1 release notes |

Τα 9 Windows metadata/resource-input checks περνούν. Δεν ορίζεται συγκεκριμένο
Windows v1 candidate tag/channel στην τρέχουσα release configuration. Η αναφορά
«v1/v1.0» στο roadmap δεν επιλέγει stable έναντι prerelease candidate. Δεν έγινε
αυθαίρετο bump. Μετά την owner απόφαση πρέπει να αλλάξουν συντονισμένα
`app/version.py`, ISS string/numeric versions, PE resources, README/release
notes, hardcoded Windows CI verify/upload names και alpha-pinned release tests.
Η αλλαγή του shared version module χρειάζεται καταγραφή parity impact, χωρίς
Android implementation σε αυτό το Windows batch.

Υπάρχει legacy alpha.1 title μέσα στο MainWindow constructor. Το κανονικό
`main.py` εγκαθιστά το canonical version wrapper και το αντικαθιστά. Είναι
source-maintenance debt, όχι αποδεδειγμένο λάθος title στην κανονική εκκίνηση.

## 2. License / legal readiness

| Item | Status | Ακριβές υπόλοιπο |
| --- | --- | --- |
| Mastixa application license | OWNER DECISION REQUIRED | Δεν υπάρχει root LICENSE. Η Phase16I/MASTER_PROGRESS deferral και το Settings license-pending κείμενο παραμένουν ενεργά. Επιλογή policy/license και επιβεβαίωση contributor rights πριν δημόσια διανομή |
| PySide6 / Qt / plugins | ACTION REQUIRED | License texts, prominent Qt notice και κατάλληλο source-access/replacement information για την επιλεγμένη route. Η onedir μορφή δεν αποδεικνύει από μόνη της συμμόρφωση |
| Qt VirtualKeyboard | OWNER DECISION REQUIRED | Exclusion αν περιττό, ή τεκμηριωμένη GPL-compatible/commercial route. Δεν έχει αποδειχθεί commercial entitlement |
| Qt module compatibility, source/relinking duties, EULA | EXTERNAL/LEGAL CONFIRMATION REQUIRED | Το πραγματικό module/native subset και οι τελικοί όροι πρέπει να συμφωνούν· το app LICENSE δεν αλλάζει third-party rights |
| Resource rights / Microsoft redistributables | EXTERNAL/LEGAL CONFIRMATION REQUIRED | Owner provenance/rights και eligible redist origin/entitlement |
| External Windows Tesseract | NOT APPLICABLE για το σημερινό bundle | README: ξεχωριστή προαιρετική εγκατάσταση, δεν προστίθεται στο spec. Αν αλλάξει το τελικό bundle, χρειάζεται νέο inventory |

Τα retained installed metadata αναφέρουν PySide6/Essentials/Addons/shiboken6
6.11.2 και LGPL/GPL alternatives. Τα dist-info περιλαμβάνουν μόνο το
`LicenseRef-Qt-Commercial.txt` στη συγκεκριμένη license-file listing· αυτό
**δεν αποτελεί commercial άδεια ούτε πλήρη open-source notice delivery**.
Οι per-module όροι υπερισχύουν μιας γενικής whole-wheel ετικέτας.
Οι [Qt LGPL οδηγίες](https://www.qt.io/development/open-source-lgpl-obligations)
επιβεβαιώνουν την ανάγκη για κείμενα/notice, source provision και δικαιώματα
replacement/debugging. Η τελική συμβατότητα απαιτεί owner/legal sign-off.

## 3. Qt VirtualKeyboard

**Source use: δεν βρέθηκε. Packaging exclusion: απουσιάζει. Old artifact: PRESENT.**

Scoped scan σε Windows `app/`, `main.py`, `packaging/`: κανένα direct
VirtualKeyboard import, QML keyboard frontend ή QT_IM_MODULE configuration.
Το PyInstaller 6.22.3 QtGui module map συλλέγει `platforminputcontexts`.
Το spec δεν φιλτράρει το plugin/DLL. Στο υπάρχον bundle της 30/9 βρέθηκαν:

- `_internal/PySide6/Qt6VirtualKeyboard.dll`
- `_internal/PySide6/plugins/platforminputcontexts/qtvirtualkeyboardplugin.dll`

Η [επίσημη Qt module documentation](https://doc.qt.io/qt-6/qtvirtualkeyboard-index.html)
προσδιορίζει GPLv3 ή commercial terms. Το παλιό artifact και ο hook εξηγούν
έμμεση inclusion· δεν αποδεικνύουν membership ενός νέου, μη χτισμένου candidate.
Σύσταση: εφόσον η route παραμένει χωρίς Qt VirtualKeyboard, στοχευμένο packaging
exclusion και έλεγχος απουσίας του module/plugin μετά από rebuild, μαζί με startup
και input/plugin regression. Δεν αφαιρέθηκε εδώ: πλήρης low-risk removal στο
emitted artifact δεν έχει ακόμη αποδειχθεί. Διατηρούνται τα υπάρχοντα assets.

## 4. Third-party notices

**ACTION REQUIRED.** Δεν υπάρχουν Windows `THIRD_PARTY_NOTICES`, `LICENSES/`
ή application LICENSE inputs στο spec. Η Source/License tab δηλώνει pending
decision και δεν παρέχει dependency notices. Δεν υπάρχει ISS `LicenseFile`.
Το ιστορικό bundle έχει 419 files και 16 LICENSE-named files, όλα κάτω από
NumPy license metadata· δεν βρέθηκαν αντίστοιχα Qt/GEOS/PROJ texts με αυτόν τον
filename scan. Αυτός ο scan δεν αποδεικνύει απουσία embedded byte notices.

Ελάχιστη τελική delivery: versioned component inventory/notice index, ακριβή
upstream license/NOTICE texts για κάθε shipped component και source-access
materials όπου απαιτούνται, συλλεγμένα από το spec και προσβάσιμα στον χρήστη.
Qt prominent notice χρειάζεται κατάλληλη user-visible θέση. Ξεχωριστό About
screen δεν είναι αυτομάτως αναγκαίο για κάθε εξάρτηση. Installer license screen
εξαρτάται από την επιλεγμένη app/EULA route· δεν αντικαθιστά bundled notices.

Δεν δημιουργήθηκε μερικό αρχείο με ετικέτα «release-ready»: runtime dependencies
είναι ranges, final interpreter/wheels/module subset δεν έχουν κλειδώσει,
Qt route εκκρεμεί και λείπουν authoritative texts για ορισμένα wheels.
Το Phase16I report είναι assessment, όχι κείμενο άδειας προς διανομή.
Το `Batch10ReleaseEvidence/release-inventory.json` καταγράφει τα πραγματικά
installed metadata/license paths και το παλιό artifact ως evidence για τη
συγκεκριμένη επόμενη συλλογή, χωρίς κατασκευασμένες αποδόσεις.

| Component family | Διαθέσιμη τεκμηρίωση / εναπομείνασα υποχρέωση |
| --- | --- |
| pyproj / PROJ | Retained build 3.8.0, compatible QA 3.7.2: LICENSE + LICENSE_proj. Native curl/TIFF/JPEG/zlib/lzma και CRS/EPSG terms χρειάζονται αντιστοίχιση στο τελικό wheel/resource subset |
| Shapely / GEOS | 2.1.2 BSD text και LICENSE_GEOS LGPLv2.1 + Windows notice διαθέσιμα στο retained environment. Πρέπει να παραδοθούν μαζί με applicable source/relinking materials |
| NumPy / BLAS / compiler runtime | 2.5.3 πλήρες multi-component license tree διαθέσιμο, μέρος ήδη στο old bundle. Διατήρηση όλων των applicable notices/exceptions, όχι γενική υπόθεση ότι όλα είναι BSD |
| pyshp / ezdxf / pyparsing / fontTools | Installed license files υπάρχουν. Build snapshot 2.4.2 / 1.4.4 / 3.3.3 / 4.65.0· δεν είναι δεσμευτικές future resolution versions |
| defusedxml / typing_extensions / certifi | Installed texts διαθέσιμα· PSF/MPL terms και covered-source duties από το προηγούμενο project audit χρειάζονται matching delivery |
| openpyxl / et_xmlfile | 3.1.5 / 2.0.0 metadata MIT, μηδέν recorded license files. Απαιτούνται τα σωστά upstream κείμενα για ακριβώς αυτές τις release versions |
| CPython / extensions / native DLLs | PSF και embedded third-party terms: exact interpreter/native inventory, OpenSSL/SQLite και Microsoft redist origin/entitlement πρέπει να καταγραφούν |
| PyInstaller / emitted runtime hooks | 6.22.3, hooks-contrib 2026.7. Exception/retained texts καταγεγραμμένα. Build-only packages δεν θεωρούνται αυτομάτως shipped· bootloader/runtime output πρέπει να αντιστοιχιστεί |
| Inno Setup output | Project audit προσδιορίζει τους inspected tool terms. Compiler/tool redistribution διαφέρει από setup/uninstaller output· confirm applicable emitted notices/version |

## 5. Resource / platform provenance

**EXTERNAL/LEGAL CONFIRMATION REQUIRED.** Inventory: 35 PNG + 5 SVG + 1
packaging ICO, με 41 hashes/paths στο evidence ledger. Δεν βρέθηκε owner rights
ledger ή upstream attribution γι' αυτά. Project-contained asset δεν σημαίνει
τεκμηριωμένη project-created ownership. Καμία διαγραφή/εικαστική αλλαγή.
Τα απλά SVG είναι πιθανό project artwork, αλλά χωρίς ownership evidence δεν
σημειώνονται «cleared». Icons/logos/installer ICO: να μη διανεμηθούν δημοσίως
μέχρι owner rights confirmation. Δεν διαπιστώθηκε infringement.

Δεν βρέθηκαν bundled TTF/OTF/WOFF στα release resource inputs. System fonts
δεν αναδιανέμονται ως font files από αυτό το spec· τυχόν embedding σε πραγματικά
PDF exports χρειάζεται έλεγχο του actual font και των embedding permissions.
OSM: documented provider/attribution στο `app/gis/dialog.py` και `providers.py`,
προαιρετικά visible online tiles, χωρίς packaged bulk/offline imagery inputs.
Τα dependency-provided `proj.db`, Qt plugins/PDFium/software OpenGL, native
GIS/NumPy/CPython DLLs και MSVC/UCRT είναι ξεχωριστή provenance/license κατηγορία.
Δεν επιτρέπεται να χαρακτηριστούν όλα project assets ή συνολικά MIT/LGPL.
Exact native closure: επιβεβαίωση στο actual final artifact, όχι απαίτηση να
αναλυθεί κάθε ιστορικό binary πριν από κάθε private diagnostic build.

## 6. Signing

**OWNER DECISION REQUIRED.** Δεν υπάρχει Windows SignTool/Inno SignTool step,
timestamp workflow ή certificate reference στη release configuration.
Το PyInstaller `codesign_identity=None` δεν ρυθμίζει Windows Authenticode.
Το μόνο signature check είναι για το diagnostic Sysinternals Handle, όχι
για Mastixa. Τα υπάρχοντα EXE/Setup επιστρέφουν `NotSigned`.
Δεν έγινε αναζήτηση private certificates/keys ούτε signing.

Unsigned direct EXE/installer build είναι τεχνικά εφικτό. Δεν βρέθηκε project
requirement που επιβάλλει signing για το σημερινό direct-download σχέδιο.
Owner να επιλέξει unsigned release με αποδοχή των Windows trust warnings ή
signing identity/service/workflow. Certificate existence στο προσωπικό store
δεν ελέγχθηκε· configuration/credentials availability δεν αποδεικνύεται.
Η [Microsoft SmartScreen documentation](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation)
περιγράφει unrecognized-app/unsigned warnings και πιθανό policy/Smart App Control
blocking· μια νέα signed έκδοση επίσης μπορεί να χρειάζεται reputation.
Αν επιλεγεί signing: sign app πριν installer build, sign τελικό setup και
έπειτα SHA256/feed· καμία αλλαγή στα signed bytes μετά το checksum/sign-off.

## 7. Branding consistency

**PASS στις canonical πηγές· ARTIFACT VALIDATION REQUIRED στο νέο binary.**
App/window/updater product, installer/AppPublisher/Start Menu/uninstall display
name: `Mastixa Manager`. EXE/internal name: `MastixaManager` /
`MastixaManager.exe`. Stable AppId διατηρείται. Publisher είναι generic product
name· η επιλεγμένη verified signing identity μπορεί να απαιτήσει owner update.
EXE/installer χρησιμοποιούν `packaging/mastixa_manager.ico`, application window
χρησιμοποιεί `dashboard.png`. Visual read-only review: ίδια dashboard artwork
family, ICO 256×256, PNG 512×512 με διαφορετικό background. Report-only polish.
Το πεδίο `LegalCopyright=Mastixa Manager contributors` δεν αποδεικνύει ownership.
Τα historical legal docs γράφουν Fieltra· δεν βρέθηκε αυτό ως τρέχουσα Windows
product identity στις inspected executable/installer/updater πηγές.

## 8. Updater / production feed

| Level | Status / evidence |
| --- | --- |
| A — source logic | PASS στους scoped tests: strict version order, HTTPS input URLs, schema/product/version validation, safe Windows filename, SHA256-before-promotion, partial cleanup, manual request only |
| B — test/mock feed | PASS: valid/invalid/no-update, checksum mismatch, offline check recovery και download retry, χωρίς πραγματικό download/installer launch |
| C — real production feed | ACTION REQUIRED / UNVERIFIED. Configured URL μόνο: `https://raw.githubusercontent.com/Sxara242/Mastixa-Manager-Source/main/updates/alpha.json`. Δεν υπάρχει `updates/alpha.json` σε αυτό το checkout. Τα web fetch attempts δεν ανέκτησαν το payload· δεν αποδεικνύεται 404 ή production outage |
| D — real end-to-end | ARTIFACT VALIDATION REQUIRED. Older build→new version detection→real URL download→SHA→installer launch→upgrade/restart→data/settings/backups survival δεν εκτελέστηκε |

Manifest schema=1, product, version, channel, HTTPS release_url, notes και
Windows asset filename/url/sha256. Τα downloadable assets απαιτούν 64-hex SHA.
Δεν υπάρχει feed signature ή Authenticode verification στον updater· checksum
ελέγχει byte integrity σε σχέση με το ίδιο feed, όχι ανεξάρτητη publisher identity.
Όχι-newer version εμφανίζει latest και κρύβει download/release actions.
Failures εμφανίζουν message και αφήνουν επανάληψη μετά τη διόρθωση παρακάτω.
Download δεν γράφει στο profile· η εγκατάσταση περνά από τον υπάρχοντα installer.

Owner να ορίσει production channel/feed και να επιβεβαιώσει anonymous HTTPS
access, exact artifact URLs/version/hash. Η UI channel δεν φιλτράρει το feed.
Version parser υποστηρίζει `rc.N`, αλλά manifest channel δέχεται μόνο
alpha/beta/stable. Αν επιλεγεί `rc` feed channel, χρειάζεται στοχευμένη συμβατή
αλλαγή και tests πριν χρησιμοποιηθεί. Δεν επιλέχθηκε αυθαίρετο feed/channel.

**Confirmed workflow fix:** μετά download failure το Install button παρέμενε
disabled. Προστέθηκε μία γραμμή στο `failed()` για re-enable. Red evidence:
2 test methods, 1 passing method και 2 failing download-error subtests, 0 errors.
Green: retry μετά timeout/checksum failure, δεύτερη λήψη, cancellation πριν
launch, offline→no-update recovery. Δεν παρακάμφθηκε verification/confirmation.

## 9. Build / installer prerequisites

**PASS source contracts; ARTIFACT VALIDATION REQUIRED.**
PyInstaller 6.22.3/hooks 2026.7 pinned· runtime requirements παραμένουν ranges.
Gate απαιτεί x64 Windows self-hosted runner, Python314 explicit path και Inno
6.7.3 bootstrap. Δεν υπάρχει worktree `.venv`. Τα expected Python314 και
per-user ISCC paths ανιχνεύονται, χωρίς νέο compile/build qualification.
Τα tests χρησιμοποιούν bundled Python 3.12.14 + retained PySide6 6.11.2 και
compatible QA pyproj/shapely overrides. Δεν αποτελούν Python314 artifact PASS.
Πριν build: καταγραφή επιλεγμένου interpreter, resolved wheel versions/hashes
και corresponding licenses, compiler version και isolated release output.
Δεν εγκαταστάθηκαν dependencies ούτε τροποποιήθηκε το owner environment.

Spec: onedir/windowed EXE, assets/locales + ICO/PE resources. Build: clean
PyInstaller analysis, private `_internal/data` gate, επιτρεπτό μόνο dependency
pyproj `proj.db`, bounded fresh installer-attempt filenames, setup SHA256.
CI installer output είναι σε RUNNER_TEMP ανά run/attempt· bundle στο repo dist.
Το υπάρχον dist είναι ιστορικό. Χρειάζεται νέο isolated output/evidence, χωρίς
να μπερδευτούν παλιά alpha artifacts με v1 και χωρίς destructive cleanup εδώ.
Το current CI verify/upload παραμένει alpha-pinned και δεν ελέγχει notices,
Qt VirtualKeyboard exclusion ή signing. Αυτά πρέπει να μπουν στην τελική
release acceptance ανά την επιλεγμένη route.

Installer: Windows >=10, x64compatible, per-user/lowest privileges,
`%LOCALAPPDATA%/Programs/Mastixa Manager`. User data ξεχωριστά στο
`%LOCALAPPDATA%/MastixaManager`. Same version→repair, different version→update,
stable AppId. Uninstall default KEEP DATA· μόνο explicit Yes ή `/PURGEDATA`
διαγράφει τον user-data root. Install files και app-owned registry καθαρίζονται.
Current theme είναι external appearance.ini, profile preferences/registry και
DB settings είναι data-owned. Settings survival χρειάζεται actual test.
Κάθε different-version installer θεωρείται update, χωρίς ξεχωριστό downgrade
guard· αυτό δεν αποδεικνύει ασφαλές manual downgrade. Δεν εμφανίζεται ως νέο
confirmed v1 data-loss bug.

Η packaging suite ελέγχει privacy/resource contracts και PowerShell smoke-runner
exit/no-marker/error/timeout/success μέσω **synthetic fixture executable**.
Δεν χτίζει Mastixa installer και δεν αποτελεί acceptance του παλιού EXE.
Actual candidate smoke/install/restart/upgrade/KEEP DATA uninstall/reinstall,
profiles/DB/settings/backups/attachments, Task Manager/PE/uninstall branding,
notice membership και final checksum/signature παραμένουν ανοικτά.

## 10. Source-tree cross-check / final classification

Το νέο `CODEX_HANDOFF.md` checkpoint υπερκαλύπτει τα παλιά performance-blocker,
audit-not-started και owner-review-needed claims για ήδη accepted source issues.
Τα historical MASTER_PROGRESS/parity/license/manual-QA docs παραμένουν ως
evidence· Phase16I distribution deferral εξακολουθεί να ισχύει. Δεν άλλαξαν
AGENTS/context, ούτε δηλώθηκε all-platform feature-complete ή public approval.
Current release tests ελέγχουν την alpha.2· PASS δεν σημαίνει έτοιμη v1 metadata.

| Remaining item | Required output class |
| --- | --- |
| Επιλογή exact Windows v1 version/channel και coordinated metadata/CI/test/release-notes update | OWNER DECISION REQUIRED, έπειτα RELEASE BLOCKER μέχρι configuration closure |
| Qt exclusion ή compatible distribution route | OWNER DECISION REQUIRED· PUBLIC-DISTRIBUTION REQUIREMENT, unresolved final-candidate packaging gate |
| App license, contributor/asset rights, platform redistribution entitlement | OWNER DECISION REQUIRED / PUBLIC-DISTRIBUTION REQUIREMENT, με EXTERNAL/LEGAL CONFIRMATION REQUIRED όπου λείπει evidence |
| Complete exact-version notices/source access + package inclusion/visible Qt notice | PUBLIC-DISTRIBUTION REQUIREMENT· τελικό distributable candidate δεν γίνεται accepted πριν closure |
| Signed ή unsigned identity/workflow και publisher | OWNER DECISION REQUIRED· δεν είναι τεχνικά υποχρεωτική υπογραφή για private direct EXE build |
| Production feed/channel/content/URLs/hashes | OWNER DECISION REQUIRED / PUBLIC-DISTRIBUTION REQUIREMENT· το live E2E είναι ARTIFACT VALIDATION REQUIRED |
| Locked build inputs, fresh broad Desktop verification που ζητά το Batch8, final EXE/setup/SHA/privacy/notice membership | ARTIFACT VALIDATION REQUIRED όταν επιτραπεί το candidate build· δεν μεταφέρεται παλιό CI PASS στη dirty πηγή |
| Actual install/upgrade/restart/KEEP DATA/reinstall, targeted rebuilt owner UI acceptance και updater E2E | ARTIFACT VALIDATION REQUIRED |
| Owner-accepted performance one final pre-public-release recheck | ARTIFACT VALIDATION REQUIRED· καμία νέα optimization παρτίδα χωρίς blocker |
| Tall Annual KPI cards, combo popup font warning, Income Sort absence, icon-background/resolution polish | UI/POLISH FOLLOW-UP, report-only |
| Legacy constructor title/deferred docs cleanup, explicit manual-downgrade policy | POST-V1 / NON-BLOCKING, εκτός αν βρεθεί πραγματικό runtime/correctness regression |

## Validation / files / preservation

**52 distinct unittest methods PASS, 0 FAIL / ERROR / SKIP.**
`release-final`: 36 (updater + 2 new methods, branding, installer/build/smoke
contracts, runtime paths), `updates-staged-final`: 1 existing lazy Updates-tab
regression, `privacy-final`: 15 explicit final release source gates για profile
ZIP limits/rejection, redacted diagnostics και disabled PROJ networking.
Επιπλέον uninstall-purge function: PASS, δεν προστίθεται ως unittest count.
Όλα τα τελικά runs: 0 Qt messages, 0 ResourceWarnings, native Windows Qt plugin,
isolated synthetic data. Δεν έγινε full discovery/99-scenario rerun ή νέο
performance/native visual acceptance run. Initial harness Git trust/import
setup failures διορθώθηκαν πριν τα valid evidence runs· δεν είναι app defects.
9 Windows metadata checks PASS. PowerShell scripts parse / smoke failure-path
checks PASS. License/notices gate ACTION REQUIRED, όχι υποθετικό PASS.

Changed in this batch only:

- `app/update_integration.py`: μία recovery γραμμή· το προϋπάρχον staged-tab diff διατηρείται.
- `tests/test_batch10_update_retry.py`: 2 focused mock-I/O/native-Qt regressions.
- `docs/WINDOWS_V1_RELEASE_GATE_BATCH10.md`: αυτό το πλήρες assessment.
- `docs/CODEX_HANDOFF.md`: νέο authoritative checkpoint, ολόκληρο prior ιστορικό διατηρείται.

Evidence εκτός production checkout: `<WORKSPACE>/Batch10ReleaseEvidence`.
Περιέχει before/after preservation, prior handoff/diff, inventory με 41 resource
hashes + 419 old-bundle membership paths, red/green logs/JSONs και read-only ICO
render. Whole worktree final: **38 tracked modified / 18 untracked / 0 staged**,
ίδιο branch/HEAD. Protected MastixaManager: ίδια 64 dirty/untracked hashes και
status/branch/HEAD. Approved worktree 8 και protected checkout 36 private
data/backup files: byte-identical. Όλα τα προϋπάρχοντα worktree files εκτός
handoff και της μίας updater γραμμής παραμένουν byte-identical.
`git -c core.safecrlf=false diff --check` και separate new-file whitespace checks:
PASS. Καμία commit/push/reset/clean/revert/discard/stash πράξη.

**Exact next Windows v1 action:** owner καθορίζει exact version/channel,
license/Qt distribution route, resource rights και signing identity/unsigned
decision. Με αυτές τις συγκεκριμένες αποφάσεις, επόμενη scoped RELEASE-INFRA
εργασία ενημερώνει metadata/CI/tests, συλλέγει authoritative notices/source-access
materials και υλοποιεί την επιλεγμένη Qt packaging/feed configuration.
Επανέλεγχος αυτού του source gate πριν από candidate build· κατόπιν μόνο νέο
Windows EXE/setup/SHA και τα παραπάνω actual artifact/owner checks.
**STOP. Δεν ξεκινά άλλη παρτίδα ή packaging αυτόματα.**
