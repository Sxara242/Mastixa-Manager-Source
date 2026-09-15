# Phase 9D — Windows Καρτέλα Αγροτεμαχίου

## Scope

Το Phase 9D επαναχρησιμοποιεί την υπάρχουσα Windows σελίδα **Καρτέλα Αγροτεμαχίου** και το Phase 9C read-only activity projection. Δεν δημιουργείται δεύτερο event/activity model και δεν προστίθεται persistent activity table.

## Existing navigation and field context

Η `FieldProfilePage` υπάρχει ήδη στο Windows navigation ως «Καρτέλα Αγροτεμαχίου». Η σελίδα επιλέγει ένα συγκεκριμένο αγροτεμάχιο και προβάλλει τα υπάρχοντα στοιχεία ταυτότητας (όνομα, ΚΑΕΚ, τοποθεσία, έκταση, παραγωγικά δέντρα), μαζί με τα ήδη υπάρχοντα KPI/cost sections.

## Timeline source

Η 9D timeline πρέπει να τροφοδοτείται αποκλειστικά από `project_field_activities()` μέσω του presentation adapter `app/field_activity_timeline.py`. Η σειρά που επιστρέφει το projection διατηρείται και δεν εφαρμόζεται δεύτερο ανεξάρτητο sort στο UI.

Υποστηριζόμενα projected kinds:

- `harvest`
- `irrigation`
- `fertilization`
- `planting`
- `plant_protection`
- `cultivation_work`
- `observation`

## Date and timestamp semantics

Date-only activities εμφανίζουν το normalized `event_date`.

GIS observations με `time_basis=recorded` και έγκυρο `event_at` εμφανίζουν το ακριβές recorded timestamp σε UTC. Δεν δημιουργείται current-time fallback.

Activities με άγνωστη/άκυρη ημερομηνία εμφανίζονται ως «Άγνωστη ημερομηνία» στην προβολή «Όλα τα έτη». Όταν έχει επιλεγεί συγκεκριμένο έτος, activities χωρίς normalized `event_date` δεν μπορούν να αντιστοιχιστούν στο έτος και αποκλείονται.

## Refresh and isolation

Κάθε refresh πρέπει να ξαναδιαβάζει το projection για το ενεργό field από το ήδη επιλεγμένο profile database. Η αλλαγή field δεν πρέπει να κρατά stale timeline rows από προηγούμενο field. Η profile isolation παραμένει αυτή του profile-local `Database` connection και του local `scope_id`.

## Read-only guarantee

Η timeline integration δεν γράφει activity data, δεν δημιουργεί schema objects και δεν αλλάζει source records. Το Phase 9C projection παραμένει το μοναδικό activity projection και διατηρεί τις 9C4 transaction/read-only εγγυήσεις του.

## QA

Focused presentation tests καλύπτουν:

- mapping όλων των supported kinds
- preservation της projection ordering
- recorded GIS UTC timestamp
- unknown date presentation
- year filtering
- all-years unknown dates
- row limit χωρίς reordering

Τα υπάρχοντα `tests.test_activity_projection` παραμένουν η authoritative regression suite για filtering, identity, updates/deletes, profile/field isolation, GIS parent filtering και transaction safety.

## Schema / platform impact

- Schema change: **NO**
- Android change: **NO**
- Windows production code: **YES**
