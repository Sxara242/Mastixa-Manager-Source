package gr.mastixa.manager;

import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import org.json.JSONObject;
import java.io.IOException;
import java.time.LocalDate;
import java.util.List;
import java.util.Set;

/** Backup-format metadata and validation for the additive Phase 12 crop-program tables. */
final class CropProgramBackup {
    static final String[] TABLES = {
        "crop_programs", "crop_program_rules", "crop_program_assignments", "crop_tasks"
    };
    static final String[][] COLUMNS = {
        {"id","name","crop","description","active","updated_at"},
        {"program_id","rule_id","title","category","schedule_kind","notes","month","day",
            "start_month","start_day","end_month","end_day","every_days","position"},
        {"program_id","field_id","season_year","generated_at"},
        {"generation_key","program_id","rule_id","field_id","season_year","due_date","category",
            "title","notes","status","created_at","updated_at"}
    };

    private static final Set<String> INTEGER_COLUMNS = Set.of(
        "month", "day", "start_month", "start_day", "end_month", "end_day", "every_days",
        "season_year", "generated_at"
    );
    private static final Set<String> NULLABLE_INTEGER_COLUMNS = Set.of(
        "month", "day", "start_month", "start_day", "end_month", "end_day", "every_days"
    );

    private CropProgramBackup() {}

    static boolean isIntegerColumn(String key) {
        return INTEGER_COLUMNS.contains(key);
    }

    static boolean isNullableIntegerColumn(String key) {
        return NULLABLE_INTEGER_COLUMNS.contains(key);
    }

    private static String required(JSONObject row, String key) throws Exception {
        String value = row.getString(key).trim();
        if (value.isEmpty()) throw new IOException("Missing crop-program backup identity: " + key);
        return value;
    }

    private static Integer nullableInt(JSONObject row, String key) throws Exception {
        return row.isNull(key) ? null : row.getInt(key);
    }

    static void validateRow(int tableIndex, JSONObject row) throws Exception {
        switch (tableIndex) {
            case 0 -> {
                required(row, "id");
                required(row, "name");
                int active = row.getInt("active");
                if (active != 0 && active != 1) throw new IOException("Invalid crop-program active flag");
            }
            case 1 -> {
                String programId = required(row, "program_id");
                CropProgram.Rule rule = new CropProgram.Rule(
                    required(row, "rule_id"),
                    required(row, "title"),
                    required(row, "category"),
                    required(row, "schedule_kind"),
                    row.getString("notes"),
                    nullableInt(row, "month"), nullableInt(row, "day"),
                    nullableInt(row, "start_month"), nullableInt(row, "start_day"),
                    nullableInt(row, "end_month"), nullableInt(row, "end_day"),
                    nullableInt(row, "every_days")
                );
                if (row.getInt("position") < 0) throw new IOException("Invalid crop-program rule position");
                try {
                    CropProgram.generate(programId, "__backup_validation__", 2000, List.of(rule));
                } catch (RuntimeException error) {
                    throw new IOException("Invalid crop-program rule", error);
                }
            }
            case 2 -> {
                required(row, "program_id");
                required(row, "field_id");
                int season = row.getInt("season_year");
                if (season < 1900 || season > 9998) throw new IOException("Invalid crop-program season");
            }
            case 3 -> {
                String generationKey = required(row, "generation_key");
                String programId = required(row, "program_id");
                String ruleId = required(row, "rule_id");
                String fieldId = required(row, "field_id");
                required(row, "title");
                String category = required(row, "category");
                String status = required(row, "status");
                if (!CropProgram.CATEGORIES.contains(category)) throw new IOException("Invalid crop-task category");
                if (!CropProgramStore.STATUSES.contains(status)) throw new IOException("Invalid crop-task status");
                int season = row.getInt("season_year");
                if (season < 1900 || season > 9998) throw new IOException("Invalid crop-task season");
                LocalDate due;
                try {
                    due = LocalDate.parse(required(row, "due_date"));
                } catch (RuntimeException error) {
                    throw new IOException("Invalid crop-task due date", error);
                }
                if (due.getYear() != season && due.getYear() != season + 1)
                    throw new IOException("Crop-task date is outside its season");
                String expected = programId + ":" + fieldId + ":" + ruleId + ":" + due;
                if (!generationKey.equals(expected)) throw new IOException("Invalid crop-task generation key");
            }
            default -> throw new IOException("Unknown crop-program backup table");
        }
    }

    static void validateRelations(SQLiteDatabase db) throws IOException {
        try (Cursor c = db.rawQuery(
            "SELECT 1 FROM crop_program_rules r LEFT JOIN crop_programs p ON p.id=r.program_id " +
            "WHERE p.id IS NULL LIMIT 1", null
        )) {
            if (c.moveToFirst()) throw new IOException("Crop-program rule references missing program");
        }
        try (Cursor c = db.rawQuery(
            "SELECT 1 FROM crop_program_assignments a " +
            "LEFT JOIN crop_programs p ON p.id=a.program_id " +
            "LEFT JOIN fields f ON f.id=a.field_id " +
            "WHERE p.id IS NULL OR f.id IS NULL LIMIT 1", null
        )) {
            if (c.moveToFirst()) throw new IOException("Crop-program assignment relationship mismatch");
        }
        try (Cursor c = db.rawQuery(
            "SELECT 1 FROM crop_tasks t " +
            "LEFT JOIN crop_programs p ON p.id=t.program_id " +
            "LEFT JOIN fields f ON f.id=t.field_id " +
            "WHERE p.id IS NULL OR f.id IS NULL LIMIT 1", null
        )) {
            if (c.moveToFirst()) throw new IOException("Crop-task relationship mismatch");
        }
        try (Cursor c = db.rawQuery(
            "SELECT 1 FROM crop_tasks t LEFT JOIN crop_program_rules r " +
            "ON r.program_id=t.program_id AND r.rule_id=t.rule_id " +
            "WHERE t.status='pending' AND r.rule_id IS NULL LIMIT 1", null
        )) {
            if (c.moveToFirst()) throw new IOException("Pending crop task references missing rule");
        }
    }
}
