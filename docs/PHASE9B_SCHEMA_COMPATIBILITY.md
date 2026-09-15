# 9B — Schema compatibility: PASS / NO-OP MIGRATION

Βάση: `PHASE9A_ACTIVITY_CONTRACT.md`, commit `75d4c00`.
Το ήδη υπάρχον, μη committed design του 9A διατηρήθηκε αυτούσιο.
**Δεν απαιτείται migration, version bump, event table ή backfill.**

## Επιβεβαιωμένη διαθεσιμότητα πηγών

| Source | Association / identity | Date και kind |
|---|---|---|
| `production` | `field_id`, PK `id` | `entry_date` → `harvest` |
| `farm_activities` | `field_id`, PK `id` | `activity_date`, «Πότισμα» / «Λίπανση» → `irrigation` / `fertilization` |
| `plant_protection_records` | `field_id`, PK `id` | `application_date` → `plant_protection` |
| `labor_entries` | `field_id`, PK `id` | `work_date` → `cultivation_work` |
| `planting_batches` | `field_id`, PK `id` | `planting_date` → `planting` |
| `geo_points` / Android `gis_records(kind=point)` | Windows μέσω `parcel_geometry.field_id`, Android απευθείας `field_id`· PK `id` | `created_at` epoch ms και point type `note/problem` → `observation`, `time_basis=recorded` |

Windows business PKs παραμένουν INTEGER· Android PKs TEXT/UUID. Τα SQL probes
επιβεβαιώνουν ότι update ημερομηνίας/κατηγορίας δεν αλλάζει PK. Το logical source
type και το contract version δεν χρειάζονται DB columns. Το scope προέρχεται
από το επιλεγμένο profile/database handle (`Database.path`, `FarmStore(context,name)`),
όχι από επινόηση profile column σε κάθε row. Ξεχωριστές συνδέσεις fixtures δεν
μοιράζονται rows. Cross-device identity παραμένει αντικείμενο του 9F.

## Fixtures και όρια της απόδειξης

- Windows: τρία αντιπροσωπευτικά schema slices: core με `production` και χωρίς
  optional modules, δηλωμένο βασικό schema ενοτήτων πριν τα additive activity
  columns, current με τα υπάρχοντα activity additions και GIS tables.
  Δεν αποδίδονται πλασματικοί αριθμοί εκδόσεων στις Windows module migrations.
- Android: source-table slices για versions **1–14**, σύμφωνα με τα gates του
  `FarmStore.onUpgrade`: production 7, activities 8, protection/labor 9,
  plantings 10, GIS 13, current 14. Η 14 προσθέτει sync metadata και δεν αλλάζει
  τα απαιτούμενα source fields. Οι πηγές που δεν υπάρχουν ακόμη παραλείπονται.
- Χρησιμοποιήθηκαν τα πραγματικά CREATE declarations των Python/Java πηγών,
  με τα constraints τους, σε `:memory:` SQLite. Τα slices περιλαμβάνουν helper
  worker records για fixtures και **δεν είναι πλήρη ιστορικά backup images**.
  Δεν εκτελέστηκαν Android runtime, `onUpgrade`, migrations σε πραγματική βάση,
  application constructors, UI ή projection implementation.
- Ελέγχθηκαν PK/columns, date-only/κενό/invalid text, απουσία προαιρετικών
  activity columns, planned/cancelled status, hard deletion, Android tombstones
  (ακόμη και `deleted_at=0`), NULL/κενές field links και dangling GIS field link.
  Τα joins αποκλείουν μη διαθέσιμο field και διαγραμμένο GIS parent/source.
- Οι υπάρχουσες business date στήλες είναι NOT NULL: η απόρριψη SQL NULL
  επιβεβαιώθηκε χωρίς χαλάρωση constraint. Το nullable **event_date** του contract
  είναι read-time fallback για άγνωστη/invalid τιμή, όχι απαίτηση nullable SQL.
  Η ίδια η κανονικοποίηση ημερομηνιών και το ordering θα δοκιμαστούν στο 9C.
- Οι read-only association probes εκτελέστηκαν με `PRAGMA query_only=ON` και
  αμετάβλητο logical dump. Δεν παράγουν event objects ούτε γράφουν timeline rows.
  DDL/DML χρησιμοποιήθηκε μόνο για την κατασκευή/μεταβολή συνθετικών fixtures,
  ποτέ ως νέα migration εφαρμογής. Δεν επιθεωρήθηκαν πραγματικά user databases.

## Εκτέλεση

`./.venv/Scripts/python.exe -X utf8 -m unittest tests.test_phase9b_schema_compatibility -v`

**PASS — 2/2 tests, 0,453s:**

- `test_windows_base_legacy_and_current_source_schema_slices`
- `test_android_v1_to_v14_source_schema_slices`

Δεν έτρεξαν full suites, emulator tests, build ή lint. Δεν άλλαξε application
code/schema/behavior. Δεν δημιουργήθηκε κενή migration. Δεν έγινε commit/push.

## Ακριβές επόμενο μικρό βήμα 9C — δεν ξεκίνησε

Πρώτη read-only projection υλοποίηση στα Windows για ένα επιλεγμένο
`scope_id + field_id`, πάνω στις έξι παραπάνω πηγές και στο contract v1 του 9A.
Focused tests για identity/deduplication, nullable date/ordering, missing optional
tables, update/delete/unlinked filtering και αμετάβλητη πηγή. Χωρίς UI, persistent
cache, νέο schema, Android UI, machinery/tasks ή sync· καμία αντιγραφή business data.
