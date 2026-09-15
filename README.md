# Mastixa Manager

**Privacy-first, offline-first farm management for Windows and Android.**

Mastixa Manager is a farm-management application designed to help farmers keep operational, financial and field data under their own control. It combines day-to-day farm records with parcel management, production tracking, expenses and income, inventory, work logs, equipment, backups, reports, maps, GPS data and coordinate exports.

The project started around mastic cultivation, but its structure is intended to support broader agricultural use. The current project name is not necessarily final.

> **Source-available snapshot — PolyForm Noncommercial 1.0.0**  
> This public repository is a clean source snapshot. It does **not** contain the private development history or private self-hosted CI workflows. Original project material is offered under the terms described in [LICENSE.md](LICENSE.md). Third-party material remains under its own terms; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). This is **not OSI open source**.

## What the application does

Mastixa Manager is intended to replace scattered spreadsheets, notes and disconnected tools with one local application for managing a farm.

### Farm and parcel management

- Producer and farm profile information.
- Agricultural parcels / fields and parcel-related records.
- Products and product-to-field associations.
- Cultivation declarations and yearly records.
- Parcel geometry, coordinates and CRS-aware exports.
- Local map viewing with optional OpenStreetMap tiles.
- GPS points and route recording on Android.

### Production and finances

- Production records by field.
- Sales and income.
- Expenses.
- Inventory / stock records.
- Work and activity records.
- Equipment tracking.
- Year locking and consistency checks.
- Reports and data exports.

### Profiles, backups and portability

- Multiple independent local profiles.
- Separate SQLite database per profile.
- Optional profile PIN.
- Avatar / profile colour support.
- Manual and automatic backups.
- Backup validation before restore.
- Profile import/export and Windows ↔ Android data exchange infrastructure.
- Local-first operation with no mandatory cloud account.

### Interface and accessibility

- Greek and English interface.
- Light and dark themes.
- Per-profile language selection.
- Search, notifications and calendar-style views.
- Keyboard/focus accessibility work included in the verified snapshot.

### Documents and OCR

Document management works without OCR.

On Windows, optional OCR-assisted invoice extraction can use an external Tesseract OCR installation. On Android, the project includes offline OCR support and bundled language data as documented in [android/THIRD_PARTY_NOTICES.md](android/THIRD_PARTY_NOTICES.md).

OCR is designed to operate locally rather than sending document contents to a remote OCR service.

## Privacy model

Mastixa Manager is designed around local ownership of farm data.

- Profile databases are stored locally.
- Backups are local unless the user explicitly moves or synchronises them elsewhere.
- GPS points and recorded routes are stored in the profile database.
- OCR processing is local in the current implementation.
- No advertising or behavioural analytics system is part of this snapshot.
- Online map tiles are optional and requested only when the online map layer is explicitly used.

Typical Windows data locations:

```text
%LOCALAPPDATA%\MastixaManager\
```

Development-tree data locations include:

```text
data/mastixa_manager.db
data/profiles/<profile-id>/
backups/
data/logs/
```

Local databases, backups, SDK paths, signing keys and private user data should never be committed to Git.

## Maps, GPS and coordinate exports

Parcel geometry can be exported in formats including:

- CSV
- XLSX
- PDF
- GeoJSON
- KML

GeoJSON and KML are exported in WGS84. Table-based exports can use WGS84 or the actual stored source CRS where supported.

The application preserves source geometry and CRS information rather than silently rewriting the original parcel data.

The Android application can record GPS points and routes. Route recording stops when the relevant map screen moves to the background.

The project contains infrastructure for cadastral/GIS workflows, but this snapshot does **not** claim a verified live Greek Cadastre KAEK geometry lookup. Google/Sentinel imagery and live Supabase use also require separate external configuration.

See:

- [GIS status](docs/GIS_PHASE3_STATUS.md)
- [CRS verification](docs/CRS_VERIFICATION.md)
- [GIS sync verification](docs/GIS_SYNC_VERIFICATION.md)

## Platforms

| Platform | Technology | Snapshot status |
| --- | --- | --- |
| Windows | Python, PySide6, SQLite | Verified desktop application and installer build path |
| Android | Native Java, SQLite | Working application source with unit/instrumentation coverage; public repo is source-only |

The source snapshot was created from the technical-complete development checkpoint at:

```text
dcf87a9bf9b1bd9b608b9b93833fb4c6b51de4d3
```

Before publication, the private development repository passed its desktop, Android, Android update/migration, Android runtime instrumentation and Windows installer/release gates.

## Repository structure

```text
app/            Windows application code
android/        Android application
packaging/      Windows packaging/build scripts
installer/      Installer-related files
docs/           Technical and verification documentation
tests/          Desktop automated tests
main.py         Windows application entry point
```

The public repository intentionally does **not** include the private self-hosted GitHub Actions workflows.

## Running the Windows application from source

Requirements:

- Windows
- Python 3.12 or newer

Clone the repository and install dependencies:

```powershell
git clone https://github.com/Sxara242/Mastixa-Manager-Source.git
cd Mastixa-Manager-Source
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

The repository also includes `run.bat` for the existing Windows development workflow.

### Windows tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tests use temporary databases and Qt offscreen support where appropriate.

## Building the Windows installer

Build-only dependencies are listed in `requirements-build.txt`.

The verified packaging workflow uses Inno Setup 6.7.3:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\packaging\build_release.ps1
```

Generated installer output is written under:

```text
dist\installer\
```

**Important:** publishing or redistributing compiled binaries has additional third-party licensing obligations beyond publishing this source snapshot. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and [docs/PHASE16I_LICENSE_READINESS.md](docs/PHASE16I_LICENSE_READINESS.md).

## Building Android

Requirements:

- JDK 17 or 21
- Android SDK 36

From the `android/` directory:

```powershell
.\gradlew.bat assembleDebug lintDebug testDebugUnitTest
```

For instrumentation tests on a configured emulator/device, use the project Android test tasks described in [android/README.md](android/README.md).

The public repository does not contain private signing credentials or production secrets.

## Localisation

The Windows application currently includes Greek and English localisation.

Language packs are stored under:

```text
app/locales/
```

The language is stored per profile and can be changed without restarting the application.

## Current external / optional integrations

Some functionality depends on external services or configuration and is intentionally not presented as fully preconfigured in this snapshot:

- Live Supabase backend / RLS configuration.
- Official Greek Cadastre schema/query integration.
- Google or Sentinel imagery services.
- Licensed/bulk offline map packs.
- Production Android signing/distribution setup.

The core application is designed to remain useful without those services.

## Source-available licensing

Original project material covered by the licensor is made available under the **PolyForm Noncommercial License 1.0.0**.

This means the repository is **source available**, but it is **not OSI-approved open source**. Commercial permissions are not granted by the project license unless separately authorised in writing by the licensor.

Third-party components are **not** relicensed under PolyForm. Their own terms continue to apply.

Read:

- [LICENSE.md](LICENSE.md)
- [NOTICE.md](NOTICE.md)
- [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
- [SOURCE_AVAILABLE.md](SOURCE_AVAILABLE.md)
- [Android third-party notices](android/THIRD_PARTY_NOTICES.md)

## Ελληνικά

Το **Mastixa Manager** είναι εφαρμογή διαχείρισης αγροτικής εκμετάλλευσης για **Windows και Android**, με έμφαση στην ιδιωτικότητα, την offline λειτουργία και τον έλεγχο των δεδομένων από τον ίδιο τον χρήστη.

Στόχος του είναι να συγκεντρώνει σε μία εφαρμογή όσα συνήθως βρίσκονται διάσπαρτα σε υπολογιστικά φύλλα, σημειώσεις και διαφορετικά εργαλεία: αγροτεμάχια, παραγωγή, πωλήσεις, έσοδα, έξοδα, αποθήκη, εργασίες, εξοπλισμό, αντίγραφα ασφαλείας, αναφορές, χάρτες, GPS και εξαγωγές συντεταγμένων.

Το project ξεκίνησε με επίκεντρο τη διαχείριση μαστιχοκαλλιέργειας, αλλά η αρχιτεκτονική του εξελίσσεται για γενικότερη αγροτική χρήση.

Τα δεδομένα αποθηκεύονται τοπικά σε SQLite βάσεις ανά προφίλ και η εφαρμογή δεν απαιτεί υποχρεωτικό cloud λογαριασμό για τη βασική λειτουργία της.

Η παρούσα δημόσια έκδοση είναι **source-available snapshot** με άδεια **PolyForm Noncommercial 1.0.0** για το πρωτότυπο υλικό του project. Δεν είναι OSI open-source έκδοση και τα third-party components διατηρούν τις δικές τους άδειες.

## Project status

This repository is a preserved public source snapshot of the verified `0.40.0-alpha.1` technical-complete state while the longer-term project name, licensing model and possible collaboration path are still being evaluated.

Development can continue independently in the private development repository without changing this snapshot.