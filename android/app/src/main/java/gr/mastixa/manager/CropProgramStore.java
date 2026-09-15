package gr.mastixa.manager;

import android.content.ContentValues;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import java.util.*;

/** Additive local persistence for Phase 12 crop programs and generated planned work. */
public final class CropProgramStore {
    public static final Set<String> STATUSES = Set.of("pending", "completed", "skipped");

    public record TaskRecord(
        String generationKey,
        String programId,
        String ruleId,
        String fieldId,
        int seasonYear,
        String dueDate,
        String category,
        String title,
        String notes,
        String status,
        long createdAt,
        long updatedAt
    ) {}

    private final FarmStore store;

    public CropProgramStore(FarmStore store) {
        this.store = Objects.requireNonNull(store, "store");
        create(store.getWritableDatabase());
    }

    public static void create(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE IF NOT EXISTS crop_programs(" +
            "id TEXT PRIMARY KEY,name TEXT NOT NULL,crop TEXT NOT NULL DEFAULT ''," +
            "description TEXT NOT NULL DEFAULT '',active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1))," +
            "updated_at INTEGER NOT NULL)");
        db.execSQL("CREATE TABLE IF NOT EXISTS crop_program_rules(" +
            "program_id TEXT NOT NULL,rule_id TEXT NOT NULL,title TEXT NOT NULL,category TEXT NOT NULL," +
            "schedule_kind TEXT NOT NULL,notes TEXT NOT NULL DEFAULT '',month INTEGER,day INTEGER," +
            "start_month INTEGER,start_day INTEGER,end_month INTEGER,end_day INTEGER,every_days INTEGER," +
            "position INTEGER NOT NULL,PRIMARY KEY(program_id,rule_id))");
        db.execSQL("CREATE TABLE IF NOT EXISTS crop_program_assignments(" +
            "program_id TEXT NOT NULL,field_id TEXT NOT NULL,season_year INTEGER NOT NULL " +
            "CHECK(season_year BETWEEN 1900 AND 9998),generated_at INTEGER NOT NULL," +
            "PRIMARY KEY(program_id,field_id,season_year))");
        db.execSQL("CREATE TABLE IF NOT EXISTS crop_tasks(" +
            "generation_key TEXT PRIMARY KEY,program_id TEXT NOT NULL,rule_id TEXT NOT NULL,field_id TEXT NOT NULL," +
            "season_year INTEGER NOT NULL CHECK(season_year BETWEEN 1900 AND 9998),due_date TEXT NOT NULL," +
            "category TEXT NOT NULL,title TEXT NOT NULL,notes TEXT NOT NULL DEFAULT ''," +
            "status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','completed','skipped'))," +
            "created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL)");
        db.execSQL("CREATE INDEX IF NOT EXISTS idx_crop_tasks_field_due ON crop_tasks(field_id,due_date)");
        db.execSQL("CREATE INDEX IF NOT EXISTS idx_crop_tasks_status_due ON crop_tasks(status,due_date)");
        db.execSQL("CREATE INDEX IF NOT EXISTS idx_crop_tasks_assignment ON crop_tasks(program_id,field_id,season_year)");
    }

    private static String required(String value, String label) {
        String text = value == null ? "" : value.trim();
        if (text.isEmpty()) throw new IllegalArgumentException(label + " is required");
        return text;
    }

    private static void putNullableInt(ContentValues values, String key, Integer value) {
        if (value == null) values.putNull(key); else values.put(key, value);
    }

    private static Integer nullableInt(Cursor cursor, int index) {
        return cursor.isNull(index) ? null : cursor.getInt(index);
    }

    public void saveProgram(
        String programId,
        String name,
        String crop,
        String description,
        List<CropProgram.Rule> rules
    ) {
        String id = required(programId, "program id");
        String displayName = required(name, "program name");
        Objects.requireNonNull(rules, "rules");
        List<CropProgram.Rule> ruleList = List.copyOf(rules);
        CropProgram.generate(id, "__template_validation__", 2000, ruleList);

        SQLiteDatabase db = store.getWritableDatabase();
        long now = System.currentTimeMillis();
        db.beginTransaction();
        try {
            ContentValues program = new ContentValues();
            program.put("id", id);
            program.put("name", displayName);
            program.put("crop", crop == null ? "" : crop.trim());
            program.put("description", description == null ? "" : description.trim());
            program.put("active", 1);
            program.put("updated_at", now);
            if (db.update("crop_programs", program, "id=?", new String[]{id}) == 0)
                db.insertOrThrow("crop_programs", null, program);

            db.delete("crop_program_rules", "program_id=?", new String[]{id});
            int position = 0;
            for (CropProgram.Rule rule : ruleList) {
                ContentValues row = new ContentValues();
                row.put("program_id", id);
                row.put("rule_id", rule.id());
                row.put("title", rule.title());
                row.put("category", rule.category());
                row.put("schedule_kind", rule.scheduleKind());
                row.put("notes", rule.notes() == null ? "" : rule.notes());
                putNullableInt(row, "month", rule.month());
                putNullableInt(row, "day", rule.day());
                putNullableInt(row, "start_month", rule.startMonth());
                putNullableInt(row, "start_day", rule.startDay());
                putNullableInt(row, "end_month", rule.endMonth());
                putNullableInt(row, "end_day", rule.endDay());
                putNullableInt(row, "every_days", rule.everyDays());
                row.put("position", position++);
                db.insertOrThrow("crop_program_rules", null, row);
            }
            db.setTransactionSuccessful();
        } finally {
            db.endTransaction();
        }
    }

    private List<CropProgram.Rule> rules(String programId) {
        List<CropProgram.Rule> rows = new ArrayList<>();
        try (Cursor cursor = store.getReadableDatabase().query(
            "crop_program_rules",
            new String[]{"rule_id","title","category","schedule_kind","notes","month","day",
                "start_month","start_day","end_month","end_day","every_days"},
            "program_id=?", new String[]{programId}, null, null, "position,rule_id"
        )) {
            while (cursor.moveToNext()) {
                rows.add(new CropProgram.Rule(
                    cursor.getString(0), cursor.getString(1), cursor.getString(2), cursor.getString(3),
                    cursor.getString(4), nullableInt(cursor,5), nullableInt(cursor,6),
                    nullableInt(cursor,7), nullableInt(cursor,8), nullableInt(cursor,9),
                    nullableInt(cursor,10), nullableInt(cursor,11)
                ));
            }
        }
        return rows;
    }

    private void requireActiveProgram(String programId) {
        try (Cursor cursor = store.getReadableDatabase().rawQuery(
            "SELECT active FROM crop_programs WHERE id=?", new String[]{programId}
        )) {
            if (!cursor.moveToFirst()) throw new IllegalArgumentException("Crop program does not exist");
            if (cursor.getInt(0) != 1) throw new IllegalArgumentException("Crop program is archived");
        }
    }

    private void requireField(String fieldId) {
        try (Cursor cursor = store.getReadableDatabase().rawQuery(
            "SELECT 1 FROM fields WHERE id=? AND deleted_at IS NULL", new String[]{fieldId}
        )) {
            if (!cursor.moveToFirst()) throw new IllegalArgumentException("Field does not exist");
        }
    }

    public List<TaskRecord> generateForField(String programId, String fieldId, int seasonYear) {
        String program = required(programId, "program id");
        String field = required(fieldId, "field id");
        requireActiveProgram(program);
        requireField(field);
        List<CropProgram.Task> generated = CropProgram.generate(program, field, seasonYear, rules(program));

        SQLiteDatabase db = store.getWritableDatabase();
        long now = System.currentTimeMillis();
        db.beginTransaction();
        try {
            db.delete(
                "crop_tasks",
                "program_id=? AND field_id=? AND season_year=? AND status='pending'",
                new String[]{program, field, String.valueOf(seasonYear)}
            );
            for (CropProgram.Task task : generated) {
                ContentValues row = new ContentValues();
                row.put("generation_key", task.generationKey());
                row.put("program_id", program);
                row.put("rule_id", task.ruleId());
                row.put("field_id", field);
                row.put("season_year", seasonYear);
                row.put("due_date", task.dueDate());
                row.put("category", task.category());
                row.put("title", task.title());
                row.put("notes", task.notes());
                row.put("status", "pending");
                row.put("created_at", now);
                row.put("updated_at", now);
                db.insertWithOnConflict("crop_tasks", null, row, SQLiteDatabase.CONFLICT_IGNORE);
            }

            ContentValues assignment = new ContentValues();
            assignment.put("program_id", program);
            assignment.put("field_id", field);
            assignment.put("season_year", seasonYear);
            assignment.put("generated_at", now);
            String[] key = new String[]{program, field, String.valueOf(seasonYear)};
            if (db.update(
                "crop_program_assignments", assignment,
                "program_id=? AND field_id=? AND season_year=?", key
            ) == 0) {
                db.insertOrThrow("crop_program_assignments", null, assignment);
            }
            db.setTransactionSuccessful();
        } finally {
            db.endTransaction();
        }
        return tasks(program, field, seasonYear);
    }

    public void setTaskStatus(String generationKey, String status) {
        String key = required(generationKey, "generation key");
        String value = status == null ? "" : status.trim();
        if (!STATUSES.contains(value))
            throw new IllegalArgumentException("Unsupported crop task status: " + value);
        ContentValues row = new ContentValues();
        row.put("status", value);
        row.put("updated_at", System.currentTimeMillis());
        if (store.getWritableDatabase().update(
            "crop_tasks", row, "generation_key=?", new String[]{key}
        ) != 1) throw new IllegalArgumentException("Crop task does not exist");
    }

    public List<TaskRecord> tasks(String programId, String fieldId, Integer seasonYear) {
        StringBuilder selection = new StringBuilder();
        List<String> args = new ArrayList<>();
        if (programId != null) addFilter(selection, args, "program_id=?", programId);
        if (fieldId != null) addFilter(selection, args, "field_id=?", fieldId);
        if (seasonYear != null) addFilter(selection, args, "season_year=?", String.valueOf(seasonYear));

        List<TaskRecord> rows = new ArrayList<>();
        try (Cursor cursor = store.getReadableDatabase().query(
            "crop_tasks",
            new String[]{"generation_key","program_id","rule_id","field_id","season_year","due_date",
                "category","title","notes","status","created_at","updated_at"},
            selection.length() == 0 ? null : selection.toString(),
            args.isEmpty() ? null : args.toArray(new String[0]),
            null, null, "due_date,rule_id,generation_key"
        )) {
            while (cursor.moveToNext()) {
                rows.add(new TaskRecord(
                    cursor.getString(0), cursor.getString(1), cursor.getString(2), cursor.getString(3),
                    cursor.getInt(4), cursor.getString(5), cursor.getString(6), cursor.getString(7),
                    cursor.getString(8), cursor.getString(9), cursor.getLong(10), cursor.getLong(11)
                ));
            }
        }
        return List.copyOf(rows);
    }

    private static void addFilter(StringBuilder selection, List<String> args, String clause, String value) {
        if (selection.length() > 0) selection.append(" AND ");
        selection.append(clause);
        args.add(value);
    }

    public void archiveProgram(String programId) {
        String program = required(programId, "program id");
        SQLiteDatabase db = store.getWritableDatabase();
        db.beginTransaction();
        try {
            ContentValues row = new ContentValues();
            row.put("active", 0);
            row.put("updated_at", System.currentTimeMillis());
            if (db.update("crop_programs", row, "id=?", new String[]{program}) != 1)
                throw new IllegalArgumentException("Crop program does not exist");
            db.delete("crop_program_assignments", "program_id=?", new String[]{program});
            db.delete("crop_tasks", "program_id=? AND status='pending'", new String[]{program});
            db.setTransactionSuccessful();
        } finally {
            db.endTransaction();
        }
    }
}
