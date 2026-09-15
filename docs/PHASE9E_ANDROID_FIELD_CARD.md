# Phase 9E — Android Καρτέλα Αγροτεμαχίου

Η Android `Καρτέλα Αγροτεμαχίου` χρησιμοποιεί πλέον το κοινό `ActivityProjection` για το activity history του επιλεγμένου αγροτεμαχίου.

## Scope

- Δεν προστέθηκε νέο event table ή migration.
- Το schema παραμένει v14.
- Τα activity rows προέρχονται read-only από `ActivityProjection`.
- Τα οικονομικά totals, operational-cost totals, planting survival, labor hours και inventory movements παραμένουν στις υπάρχουσες report πηγές επειδή δεν αποτελούν activity events του Phase 9 contract.

## Timeline sources

- `production` → `harvest`
- `farm_activities` → `irrigation` / `fertilization`
- `planting_batches` → `planting`
- `plant_protection_records` → `plant_protection`
- `labor_entries` → `cultivation_work`
- `gis_records` point `note/problem` → `observation`

Η σειρά της timeline είναι ακριβώς η deterministic σειρά που επιστρέφει το projection. Δεν γίνεται δεύτερο sorting στη report layer.

## Dates

- Date-only events εμφανίζονται ως `YYYY-MM-DD`.
- GIS recorded timestamps εμφανίζονται ως UTC minute timestamp και σημειώνονται ως recorded time.
- Unknown dates δεν μετατρέπονται σε σημερινή ημερομηνία.
- Unknown-date events εμφανίζονται μόνο όταν δεν έχει οριστεί date range, επειδή δεν μπορούν να τοποθετηθούν αξιόπιστα μέσα σε συγκεκριμένο διάστημα.

## Profile scope

Το report adapter παράγει local `scope_id` από το profile database identity (`legacy` ή το UUID μέσα στο `farm-<profile-id>.db`). Test/non-profile database names παίρνουν μόνο local test scope και δεν αποκτούν cross-device identity.

## QA

Focused instrumentation coverage επιβεβαιώνει ότι:
- το field card εμφανίζει activity projection rows,
- GIS observations συμμετέχουν στο ίδιο timeline,
- η projection ordering διατηρείται,
- δεν εμφανίζονται activity rows άλλου field,
- η παλιά per-table activity παρουσίαση δεν δημιουργεί duplicate timeline rows.

Schema change: **NO**.
