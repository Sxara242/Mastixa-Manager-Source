package gr.mastixa.manager;

import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import androidx.test.platform.app.InstrumentationRegistry;
import org.json.JSONArray;
import org.json.JSONObject;
import org.junit.Test;
import java.nio.charset.StandardCharsets;
import java.util.*;
import static org.junit.Assert.*;

public class CropProgramStoreTest {
    private Context context() {
        return InstrumentationRegistry.getInstrumentation().getTargetContext();
    }

    private JSONObject fixture() throws Exception {
        try (var input = InstrumentationRegistry.getInstrumentation().getContext()
            .getAssets().open("phase12_crop_program.json")) {
            return new JSONObject(new String(input.readAllBytes(), StandardCharsets.UTF_8));
        }
    }

    private Integer optionalInt(JSONObject row, String key) {
        return row.has(key) ? row.optInt(key) : null;
    }

    private CropProgram.Rule rule(JSONObject row) {
        return new CropProgram.Rule(
            row.optString("id"), row.optString("title"), row.optString("category"),
            row.optString("schedule_kind"), row.optString("notes", ""),
            optionalInt(row, "month"), optionalInt(row, "day"),
            optionalInt(row, "start_month"), optionalInt(row, "start_day"),
            optionalInt(row, "end_month"), optionalInt(row, "end_day"),
            optionalInt(row, "every_days")
        );
    }

    private List<CropProgram.Rule> fixtureRules(JSONObject fixture) throws Exception {
        List<CropProgram.Rule> rules = new ArrayList<>();
        JSONArray rows = fixture.getJSONArray("rules");
        for (int n = 0; n < rows.length(); n++) rules.add(rule(rows.getJSONObject(n)));
        return rules;
    }

    private boolean hasTable(SQLiteDatabase db, String name) {
        try (Cursor cursor = db.rawQuery(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", new String[]{name}
        )) {
            return cursor.moveToFirst();
        }
    }

    @Test public void additiveMigrationRollsBackWithCallerTransaction() {
        SQLiteDatabase db = SQLiteDatabase.create(null);
        try {
            db.beginTransaction();
            try {
                CropProgramStore.create(db);
                assertTrue(hasTable(db, "crop_tasks"));
            } finally {
                db.endTransaction();
            }
            assertFalse(hasTable(db, "crop_tasks"));
        } finally {
            db.close();
        }
    }

    @Test public void regenerationPreservesDecisionsAndArchivePreservesHistory() throws Exception {
        Context c = context();
        String database = "phase12-store-regeneration.db";
        c.deleteDatabase(database);
        try (FarmStore farm = new FarmStore(c, database)) {
            farm.addField("Phase 12 field", 1);
            String fieldId = farm.fields().get(0).id();
            CropProgramStore store = new CropProgramStore(farm);
            JSONObject fixture = fixture();
            String programId = fixture.getString("program_id");
            List<CropProgram.Rule> rules = fixtureRules(fixture);

            store.saveProgram(programId, "Fixture program", "mastic", "", rules);
            List<CropProgramStore.TaskRecord> first = store.generateForField(programId, fieldId, 2026);
            assertEquals(8, first.size());

            String pruneKey = null;
            String irrigationKey = null;
            for (CropProgramStore.TaskRecord task : first) {
                if (pruneKey == null && task.ruleId().equals("prune-winter"))
                    pruneKey = task.generationKey();
                if (irrigationKey == null && task.ruleId().equals("irrigate-window"))
                    irrigationKey = task.generationKey();
            }
            assertNotNull(pruneKey);
            assertNotNull(irrigationKey);
            store.setTaskStatus(pruneKey, "completed");
            store.setTaskStatus(irrigationKey, "skipped");

            List<CropProgram.Rule> edited = new ArrayList<>();
            for (CropProgram.Rule current : rules) {
                if (current.id().equals("winter-inspection")) continue;
                if (current.id().equals("irrigate-window")) {
                    current = new CropProgram.Rule(
                        current.id(), "Irrigation revised", current.category(), current.scheduleKind(),
                        current.notes(), current.month(), current.day(), current.startMonth(),
                        current.startDay(), current.endMonth(), current.endDay(), current.everyDays()
                    );
                }
                edited.add(current);
            }
            store.saveProgram(programId, "Fixture program", "mastic", "", edited);
            List<CropProgramStore.TaskRecord> regenerated =
                store.generateForField(programId, fieldId, 2026);
            assertEquals(5, regenerated.size());

            boolean completed = false;
            boolean skipped = false;
            for (CropProgramStore.TaskRecord task : regenerated) {
                assertNotEquals("winter-inspection", task.ruleId());
                if (task.generationKey().equals(pruneKey)) {
                    assertEquals("completed", task.status());
                    completed = true;
                }
                if (task.generationKey().equals(irrigationKey)) {
                    assertEquals("skipped", task.status());
                    skipped = true;
                }
                if (task.ruleId().equals("irrigate-window") && task.status().equals("pending"))
                    assertEquals("Irrigation revised", task.title());
            }
            assertTrue(completed);
            assertTrue(skipped);

            store.archiveProgram(programId);
            List<CropProgramStore.TaskRecord> history = store.tasks(programId, fieldId, 2026);
            assertEquals(2, history.size());
            for (CropProgramStore.TaskRecord task : history)
                assertTrue(task.status().equals("completed") || task.status().equals("skipped"));

            try {
                store.generateForField(programId, fieldId, 2026);
                fail("Archived program must not generate tasks");
            } catch (IllegalArgumentException expected) {
                assertTrue(expected.getMessage().contains("archived"));
            }
        } finally {
            c.deleteDatabase(database);
        }
    }

    @Test public void failedGenerationIsAtomicAndProfileDatabasesAreIsolated() {
        Context c = context();
        String aName = "phase12-store-a.db";
        String bName = "phase12-store-b.db";
        c.deleteDatabase(aName);
        c.deleteDatabase(bName);
        CropProgram.Rule leap = new CropProgram.Rule(
            "leap-check", "Leap check", "inspection", "fixed_date", "",
            2, 29, null, null, null, null, null
        );
        try (FarmStore a = new FarmStore(c, aName); FarmStore b = new FarmStore(c, bName)) {
            a.addField("A field", 1);
            b.addField("B field", 1);
            String fieldA = a.fields().get(0).id();
            String fieldB = b.fields().get(0).id();
            CropProgramStore storeA = new CropProgramStore(a);
            CropProgramStore storeB = new CropProgramStore(b);

            storeA.saveProgram("leap-program", "Leap", "", "", List.of(leap));
            List<CropProgramStore.TaskRecord> before =
                storeA.generateForField("leap-program", fieldA, 2028);
            assertEquals(1, before.size());
            try {
                storeA.generateForField("leap-program", fieldA, 2027);
                fail("Invalid season date must fail before persistence changes");
            } catch (RuntimeException expected) {
                // java.time.DateTimeException is expected from the shared generator.
            }
            assertEquals(before, storeA.tasks("leap-program", fieldA, 2028));
            assertTrue(storeA.tasks("leap-program", fieldA, 2027).isEmpty());

            assertTrue(storeB.tasks(null, null, null).isEmpty());
            try {
                storeB.generateForField("leap-program", fieldB, 2028);
                fail("Program data must not leak between profile databases");
            } catch (IllegalArgumentException expected) {
                assertTrue(expected.getMessage().contains("does not exist"));
            }
        } finally {
            c.deleteDatabase(aName);
            c.deleteDatabase(bName);
        }
    }
}
