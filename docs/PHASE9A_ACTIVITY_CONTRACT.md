# 9A — Ελάχιστο contract Καρτέλας Αγροτεμαχίου

**Κατάσταση: COMPLETE — design μόνο.** Βάση: `75d4c00`, branch `refactor/pages`,
καθαρό working tree πριν τη μελέτη. Δεν εκτελέστηκαν tests/builds ή αλλαγές βάσης.

Master roadmap από εδώ και πέρα: το `Fieltra_Master_Roadmap_16_Phases.txt`
του χρήστη, έκδοση 2026-09-10, στο `C:\Users\elfen\Downloads`.
Η ενσωματωμένη σημείωσή του ότι η Φάση 8 εκκρεμεί είναι παλιά: υπερισχύουν
το επαληθευμένο checkpoint και η τρέχουσα οδηγία. Η νέα Φάση 9 αφορά timeline,
όχι το performance audit της παλαιότερης αρίθμησης. Το 9B δεν έχει ξεκινήσει.

## Απόφαση και υπάρχουσες πηγές

**Read-only projection ανά ενεργό προφίλ/αγροτεμάχιο, χωρίς πίνακα events.**
Οι πηγές παραμένουν αποκλειστικοί ιδιοκτήτες των εγγραφών. Υπάρχει ήδη σχετικό
προηγούμενο στα Windows: `field_profile.py` και `farm_calendar.py` συνθέτουν
ιστορικό από επιμέρους πίνακες. Το ημερολόγιο κρατά και `record_id` για πλοήγηση.

| Activity kind | Υπάρχουσα πηγή | Ημερομηνία / σύνδεση |
|---|---|---|
| `planting` | `planting_batches` και στα δύο συστήματα | `planting_date`, `field_id` |
| `irrigation` / `fertilization` | `farm_activities` | `activity_date`, `field_id`, αποθηκευμένη κατηγορία «Πότισμα» / «Λίπανση» |
| `plant_protection` | `plant_protection_records` | `application_date`, `field_id` |
| `cultivation_work` | `labor_entries` | `work_date`, `field_id`, περιγραφή από `work_type`· πρόκειται για καταχώρηση εργασίας/εργατικών |
| `harvest` | `production` | `entry_date`, `field_id` |
| `observation` | Windows `geo_points`, Android `gis_records` με `kind=point`, τύπο `note` ή `problem` | `created_at` ως χρόνος **καταγραφής**, όχι τεκμαιρόμενος χρόνος παρατήρησης· Windows μέσω `parcel_geometry.field_id`, Android `field_id` |

Το `farm_activities` σήμερα υποστηρίζει μόνο πότισμα/λίπανση· δεν το επεκτείνουμε
σιωπηρά σε γενικό activity store. Τα `fields.notes` και τα notes των άλλων records
δεν είναι ανεξάρτητα χρονολογικά γεγονότα: εμφανίζονται μόνο ως τρέχουσα περιγραφή
της πηγής. Δεν κατασκευάζουμε ιστορικό από μεταβαλλόμενο ελεύθερο κείμενο.
Το `product_fields.planting_date` είναι metadata σχέσης καλλιέργειας και δεν
δημιουργεί δεύτερο planting event δίπλα σε `planting_batches`.

## Minimal event contract v1 — παράγεται κατά την ανάγνωση

| Πεδίο | Κανόνας |
|---|---|
| `version` | Υποχρεωτικό, `1`· έκδοση contract, όχι έκδοση SQLite. |
| `scope_id` | Υποχρεωτικό, το τοπικό προφίλ/χώρος δεδομένων που εξουσιοδοτεί την ανάγνωση. Δεν είναι διαδρομή αρχείου ή αυτόματα κοινό dataset ID. |
| `field_id` | Υποχρεωτικό string του πραγματικού τοπικού field ID, εντός scope. |
| `source_ref` | Υποχρεωτικό `{type, id}`. Σταθερός λογικός τύπος και το πραγματικό τοπικό ID ως string. |
| `kind` | Υποχρεωτικός κωδικός του παραπάνω πίνακα, ανεξάρτητος από μεταφρασμένο UI. |
| `event_date` | Υποχρεωτικό κλειδί, ISO `YYYY-MM-DD` ή `null` για άγνωστη/μη έγκυρη ημερομηνία. |
| `time_basis` | Υποχρεωτικό `occurred`, `recorded` ή `unknown`, ώστε να μη βαφτίζεται η καταγραφή πραγματική ημερομηνία εργασίας. |
| `event_at` | Προαιρετικό UTC epoch milliseconds, μόνο όταν η πηγή δίνει πραγματικό, μη αμφίσημο instant. |
| `status` | Προαιρετικό `planned/completed/cancelled/unknown` από ρητό source status. Απουσία status δεν σημαίνει αυτομάτως completed. |
| `label`, `summary` | Προαιρετικό παράγωγο κείμενο για εμφάνιση, χωρίς ανεξάρτητη αποθήκευση ή sync. |
| `sync_ref` | Προαιρετικό `{dataset_id, source_uuid, field_uuid}`, μόνο μετά από επαληθευμένο κοινό identity mapping. Αλλιώς απουσιάζει. |

Λογικοί source types: `planting_batch`, `farm_activity`, `plant_protection`,
`labor_entry`, `production`, `geo_point`. Το τελευταίο αντιστοιχεί σε διαφορετικό
φυσικό πίνακα ανά πλατφόρμα. Οι τύποι αντιστοιχίζονται σε σταθερούς, επιτρεπόμενους
adapters· δεν μετατρέπεται εξωτερικό `type` σε αυθαίρετο SQL table name.
Δεν προστίθενται payload αντιγράφων, event revision, outbox ή generic plugin registry.

## References, σειρά και κύκλος ζωής

- Τοπικό event key: tuple `(scope_id, source_ref.type, source_ref.id, field_id)`.
  Δεν χρειάζεται ξεχωριστό αποθηκευμένο `event_id`. Δεν εξαρτάται από τίτλο,
  ημερομηνία, kind ή θέση στη λίστα. Επεξεργασία/άνοιγμα γίνεται στην πηγή,
  με νέο έλεγχο προφίλ, ύπαρξης και σύνδεσης με το αγροτεμάχιο.
- Date-only τιμές παραμένουν ημερομηνίες, χωρίς επινόηση μεσονυκτίου/timezone.
  Για epoch-based σημειώσεις το `event_date` παράγεται σε UTC για σταθερή σειρά,
  με εμφανή ένδειξη χρόνου καταγραφής· το UI μπορεί να μορφοποιεί το instant τοπικά.
  Δεν χρησιμοποιούνται `updated_at` ή χρόνος sync/import ως χρόνος συμβάντος.
- Σειρά: γνωστή `event_date` φθίνουσα, έπειτα γνωστά `event_at` φθίνοντα και
  μετά date-only στοιχεία της ίδιας ημέρας, τέλος `(source type, source id)`
  λεξικογραφικά. Άγνωστες ημερομηνίες τελευταίες. Η σειρά date-only στοιχείων
  δεν ισχυρίζεται ότι γνωρίζει την πραγματική ώρα. Invalid/κενές τιμές γίνονται
  `null` μόνο στο projection, όχι «σήμερα» ούτε σιωπηλή διόρθωση της πηγής.
- Κάθε ανάγνωση χρησιμοποιεί συνεπή DB snapshot και join με υπαρκτό ενεργό field.
  Windows hard delete ⇒ το event εξαφανίζεται. Android `deleted_at IS NOT NULL`
  σε source ή field ⇒ αποκλείεται. Ελέγχεται και ο γονέας των GIS points.
  `NULL`, Android κενό string ή dangling `field_id` δεν παράγουν event άλλου field.
- Update ⇒ νέα προβολή με ίδιο key. Μεταφορά source σε άλλο field αφαιρεί την
  παλιά συσχέτιση και εμφανίζει τη νέα. Καμία διαγραφή source από το timeline.
  Cancelled/planned παραμένουν διακριτές καταστάσεις, όχι tombstones ή τετελεσμένες εργασίες.
- Ένα event ανά source/field. JOIN fan-out αφαιρείται με το key· διαφορετικές
  πραγματικές εργασίες ίδιας ημέρας δεν συγχωνεύονται. Συνδεδεμένο expense ή
  inventory movement δεν ξαναπροβάλλεται ως η ίδια λίπανση/φυτοπροστασία.
  Re-read/retry δεν εισάγει rows. Αρχικά δεν προβλέπεται persistent timeline cache.

## Συμβατότητα IDs και μελλοντική επέκταση

Windows business IDs είναι profile-local integers, Android UUIDs. Τα εισαγόμενα
Android business records κρατούν `windows_id`, αλλά τα σημερινά portable exports
δεν δίνουν κοινό dataset/source namespace. Άρα ούτε σκέτο `windows_id`, ούτε KAEK,
όνομα ή ημερομηνία αποδεικνύουν cross-device ταυτότητα. Δεν εξάγουμε UUID από αυτά.
Τα επαληθευμένα GIS UUIDs επαναχρησιμοποιούνται όπου υπάρχουν· ένα Windows field
χωρίς γεωμετρία δεν αποκτά αυθαίρετα GIS identity για να εμφανιστεί στο timeline.

Το 9F θα ορίσει/μεταφέρει το αναγκαίο κοινό source/field mapping μαζί με το source
sync και τότε θα συμπληρώνεται το `sync_ref`. Δεν αλλάζει το ήδη επαληθευμένο GIS
wire schema ούτε αποστέλλονται local integer references ως διεθνώς μοναδικά IDs.
Remote reference χωρίς διαθέσιμη πηγή δεν εμφανίζεται ως stale/φανταστικό event.
Η συμβατότητα είναι σχεδιαστική: δεν ισχυριζόμαστε ότι υπάρχει ήδη business sync.

Αργότερα προστίθενται συγκεκριμένα `machinery_use` / `task` sources με την ίδια
μορφή reference. Το σημερινό `equipment_maintenance` έχει `equipment_id`, όχι
`field_id`: δεν αποδίδεται σε field κατ' εικασία. Οι φάσεις 11–13 θα ορίσουν την
πραγματική σύνδεση και τη διάκριση προγραμματισμένης/εκτελεσμένης εργασίας.
Δεν προστίθενται τώρα task table ή γενικό many-to-many/event framework.

## Ακριβές μικρό βήμα 9B

**Δεν απαιτείται schema change για το πρώτο read-only timeline.** Τα ήδη
υπάρχοντα IDs, field links και ημερομηνίες αρκούν για local projection.
Το schema-only 9B προτείνεται ως τεκμηριωμένο **no-op migration checkpoint**:
επιβεβαίωση των απαιτούμενων columns/optional-table απουσιών σε συνθετικά
legacy/current schema fixtures, με έναν στενό έλεγχο ανά πλατφόρμα, χωρίς DDL,
version bump, backfill, νέο event table ή UI. Δεν χρειάζεται full suite.
Οι Windows module tables μπορεί να μην έχουν δημιουργηθεί ακόμη· το μελλοντικό
projection παραλείπει ανύπαρκτη πηγή και δεν εκτελεί migrations κατά την ανάγνωση.
Αν φανεί πραγματικό schema κενό, καταγράφεται πριν προταθεί ξεχωριστή μικρή αλλαγή.
Projection code ανήκει στο 9C, κοινό identity/sync mapping στο 9F. Κανένα από αυτά
δεν υλοποιήθηκε στο 9A.

### Κώδικας που μελετήθηκε

- Windows: `app/database.py`, `app/activities.py`, `app/plantings.py`,
  `app/plant_protection.py`, `app/labor.py`, `app/equipment.py`,
  `app/field_profile.py`, `app/farm_calendar.py`, `app/data_export.py`,
  `app/gis/store.py`, `app/database_infrastructure/{schema,migrations}.py`.
  Οι πραγματικές migrations είναι στο `Database.initialize` και στα modules·
  το `database_infrastructure/migrations.py` παραμένει placeholder.
- Android (`android/app/src/main/java/gr/mastixa/manager/`): `FarmStore.java`
  (schema 14 / `onUpgrade`), `ActivityStore.java`, `WorkStore.java`,
  `ProductionStore.java`, `GeoStore.java`, `GisSyncRepository.java`,
  `WindowsImport.java`, `ActivityImport.java`, `ProductionImport.java`,
  και σημεία των `CatalogImport.java` / `WorkImport.java` για source references.
