package gr.mastixa.manager;

import androidx.test.platform.app.InstrumentationRegistry;
import org.json.JSONArray;
import org.json.JSONObject;
import org.junit.Test;
import java.nio.charset.StandardCharsets;
import java.util.*;
import static org.junit.Assert.*;

public class CropProgramTest {
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
            row.optString("id"),
            row.optString("title"),
            row.optString("category"),
            row.optString("schedule_kind"),
            row.optString("notes", ""),
            optionalInt(row, "month"),
            optionalInt(row, "day"),
            optionalInt(row, "start_month"),
            optionalInt(row, "start_day"),
            optionalInt(row, "end_month"),
            optionalInt(row, "end_day"),
            optionalInt(row, "every_days")
        );
    }

    @Test public void sharedFixtureGeneratesSameContract() throws Exception {
        JSONObject fixture = fixture();
        List<CropProgram.Rule> rules = new ArrayList<>();
        JSONArray ruleRows = fixture.getJSONArray("rules");
        for (int n = 0; n < ruleRows.length(); n++) rules.add(rule(ruleRows.getJSONObject(n)));

        List<CropProgram.Task> tasks = CropProgram.generate(
            fixture.getString("program_id"),
            fixture.getString("field_id"),
            fixture.getInt("season_year"),
            rules
        );
        JSONArray expected = fixture.getJSONArray("expected");
        assertEquals(expected.length(), tasks.size());
        for (int n = 0; n < expected.length(); n++) {
            JSONObject row = expected.getJSONObject(n);
            CropProgram.Task task = tasks.get(n);
            assertEquals(row.getString("rule_id"), task.ruleId());
            assertEquals(row.getString("due_date"), task.dueDate());
            assertEquals(row.getString("generation_key"), task.generationKey());
            assertEquals("pending", task.status());
        }
    }

    @Test public void invalidAndDuplicateRulesAreRejected() {
        var duplicate = new CropProgram.Rule(
            "same", "Check", "inspection", "fixed_date", "",
            3, 1, null, null, null, null, null
        );
        try {
            CropProgram.generate("program", "field", 2026, List.of(duplicate, duplicate));
            fail("Duplicate rule id must fail");
        } catch (IllegalArgumentException expected) {
            assertTrue(expected.getMessage().contains("Duplicate"));
        }

        var invalid = new CropProgram.Rule(
            "bad-step", "Bad", "irrigation", "interval_window", "",
            null, null, 5, 1, 5, 31, 0
        );
        try {
            CropProgram.generate("program", "field", 2026, List.of(invalid));
            fail("Non-positive interval must fail");
        } catch (IllegalArgumentException expected) {
            assertTrue(expected.getMessage().contains("positive"));
        }
    }
}
