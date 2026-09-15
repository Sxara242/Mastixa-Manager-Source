package gr.mastixa.manager;

import android.database.Cursor;
import java.time.LocalDate;
import java.util.*;

/** Read-only Android projection that mirrors the Windows unified farm calendar and adds Phase 12 tasks. */
public final class UnifiedCalendarStore {
    public static final List<String> SOURCES = List.of("production","activity","protection","labor","planting","crop_task");

    public record Entry(
        String date,
        String source,
        String section,
        String fieldId,
        String fieldName,
        String title,
        String detail,
        String recordId,
        String state
    ) {}

    private final FarmStore store;
    private final boolean english;

    public UnifiedCalendarStore(FarmStore store, boolean english) {
        this.store = Objects.requireNonNull(store, "store");
        this.english = english;
        CropProgramStore.create(store.getWritableDatabase());
    }

    private String w(String greek, String en) { return english ? en : greek; }
    private String fieldName(Map<String,String> fields, String id) {
        return fields.getOrDefault(id, w("Αγροτεμάχιο ιστορικού", "Historical field"));
    }
    private String stateLabel(String state) {
        return switch (state) {
            case "overdue" -> w("Εκπρόθεσμη", "Overdue");
            case "due_today" -> w("Σήμερα", "Due today");
            case "upcoming" -> w("Εντός 7 ημερών", "Within 7 days");
            case "completed" -> w("Ολοκληρωμένη", "Completed");
            case "skipped" -> w("Παραλείφθηκε", "Skipped");
            default -> w("Εκκρεμής", "Pending");
        };
    }

    public List<Entry> entries(LocalDate today) {
        Objects.requireNonNull(today, "today");
        var rows = new ArrayList<Entry>();
        var fields = new HashMap<String,String>();
        for (var field : store.fields()) fields.put(field.id(), field.name());
        var db = store.getReadableDatabase();

        try (Cursor c = db.rawQuery("SELECT id,entry_date,field_id,product,quantity_kg,notes FROM production WHERE deleted_at IS NULL", null)) {
            while (c.moveToNext()) {
                String detail = ReportStore.n(c.getDouble(4)) + " kg" + (c.getString(5).isBlank() ? "" : " · " + c.getString(5));
                rows.add(new Entry(c.getString(1),"production",w("Παραγωγή","Production"),c.getString(2),fieldName(fields,c.getString(2)),c.getString(3),detail,c.getString(0),""));
            }
        }
        try (Cursor c = db.rawQuery("SELECT id,activity_date,field_id,category,status,description,product,water_quantity_m3,dose,dose_unit,cost,notes FROM farm_activities WHERE deleted_at IS NULL", null)) {
            while (c.moveToNext()) {
                var parts = new ArrayList<String>();
                parts.add(c.getString(4));
                if (!c.getString(5).isBlank()) parts.add(c.getString(5));
                if (!c.getString(6).isBlank()) parts.add(c.getString(6));
                if (c.getDouble(7) > 0) parts.add(ReportStore.n(c.getDouble(7)) + " m³");
                if (c.getDouble(8) > 0) parts.add(ReportStore.n(c.getDouble(8)) + " " + c.getString(9));
                if (c.getDouble(10) > 0) parts.add(ReportStore.n(c.getDouble(10)) + " €");
                if (!c.getString(11).isBlank()) parts.add(c.getString(11));
                rows.add(new Entry(c.getString(1),"activity",w("Άρδευση & Λίπανση","Irrigation & Fertilization"),c.getString(2),fieldName(fields,c.getString(2)),c.getString(3),String.join(" · ",parts),c.getString(0),""));
            }
        }
        try (Cursor c = db.rawQuery("SELECT id,application_date,field_id,product_name,purpose,dose,dose_unit,cost,notes FROM plant_protection_records WHERE deleted_at IS NULL", null)) {
            while (c.moveToNext()) {
                var parts = new ArrayList<String>();
                if (!c.getString(4).isBlank()) parts.add(c.getString(4));
                if (c.getDouble(5) > 0) parts.add(ReportStore.n(c.getDouble(5)) + " " + c.getString(6));
                if (c.getDouble(7) > 0) parts.add(ReportStore.n(c.getDouble(7)) + " €");
                if (!c.getString(8).isBlank()) parts.add(c.getString(8));
                rows.add(new Entry(c.getString(1),"protection",w("Φυτοπροστασία","Plant protection"),c.getString(2),fieldName(fields,c.getString(2)),c.getString(3),String.join(" · ",parts),c.getString(0),""));
            }
        }
        try (Cursor c = db.rawQuery("SELECT id,work_date,field_id,work_type,hours,cost,notes FROM labor_entries WHERE deleted_at IS NULL", null)) {
            while (c.moveToNext()) {
                String detail = ReportStore.n(c.getDouble(4)) + w(" ώρες"," hours") + " · " + ReportStore.n(c.getDouble(5)) + " €" + (c.getString(6).isBlank() ? "" : " · " + c.getString(6));
                rows.add(new Entry(c.getString(1),"labor",w("Εργατικά","Labor"),c.getString(2),fieldName(fields,c.getString(2)),c.getString(3),detail,c.getString(0),""));
            }
        }
        try (Cursor c = db.rawQuery("SELECT id,planting_date,field_id,trees_planted,trees_alive,material_type,source,cost,notes FROM planting_batches WHERE deleted_at IS NULL", null)) {
            while (c.moveToNext()) {
                var parts = new ArrayList<String>();
                parts.add(c.getInt(3) + w(" φυτεμένα"," planted"));
                parts.add(c.getInt(4) + w(" ζωντανά"," alive"));
                if (!c.getString(6).isBlank()) parts.add(c.getString(6));
                if (c.getDouble(7) > 0) parts.add(ReportStore.n(c.getDouble(7)) + " €");
                if (!c.getString(8).isBlank()) parts.add(c.getString(8));
                rows.add(new Entry(c.getString(1),"planting",w("Φυτεύσεις & Δέντρα","Plantings & Trees"),c.getString(2),fieldName(fields,c.getString(2)),c.getString(5),String.join(" · ",parts),c.getString(0),""));
            }
        }
        try (Cursor c = db.rawQuery("SELECT generation_key,due_date,field_id,title,notes,status FROM crop_tasks", null)) {
            while (c.moveToNext()) {
                String state = TaskCalendar.state(c.getString(5), c.getString(1), today);
                String detail = stateLabel(state) + (c.getString(4).isBlank() ? "" : " · " + c.getString(4));
                rows.add(new Entry(c.getString(1),"crop_task",w("Πρόγραμμα Καλλιέργειας","Crop Program"),c.getString(2),fieldName(fields,c.getString(2)),c.getString(3),detail,c.getString(0),state));
            }
        }

        rows.sort(Comparator.comparing(Entry::date).reversed().thenComparing(Entry::section).thenComparing(Entry::recordId));
        return List.copyOf(rows);
    }

    public static List<Entry> filter(List<Entry> entries, Integer year, Integer month, String fieldId, String source, String query) {
        String field = fieldId == null ? "" : fieldId;
        String src = source == null ? "" : source;
        String q = query == null ? "" : query.trim().toLowerCase(Locale.ROOT);
        return entries.stream().filter(row -> {
            LocalDate date = LocalDate.parse(row.date());
            if (year != null && date.getYear() != year) return false;
            if (month != null && date.getMonthValue() != month) return false;
            if (!field.isEmpty() && !row.fieldId().equals(field)) return false;
            if (!src.isEmpty() && !row.source().equals(src)) return false;
            if (!q.isEmpty() && !(row.title()+" "+row.detail()+" "+row.fieldName()+" "+row.section()).toLowerCase(Locale.ROOT).contains(q)) return false;
            return true;
        }).toList();
    }
}
