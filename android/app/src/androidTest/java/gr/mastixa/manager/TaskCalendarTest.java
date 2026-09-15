package gr.mastixa.manager;

import androidx.test.platform.app.InstrumentationRegistry;
import org.json.JSONObject;
import org.junit.Test;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import static org.junit.Assert.*;

public class TaskCalendarTest {
    private JSONObject fixture() throws Exception {
        try (var input = InstrumentationRegistry.getInstrumentation().getContext()
            .getAssets().open("phase13_task_calendar.json")) {
            return new JSONObject(new String(input.readAllBytes(), StandardCharsets.UTF_8));
        }
    }

    @Test public void sharedFixtureMatchesPhase13Contract() throws Exception {
        JSONObject fixture = fixture();
        LocalDate today = LocalDate.parse(fixture.getString("today"));
        int horizon = fixture.getInt("horizon_days");
        var tasks = fixture.getJSONArray("tasks");
        for (int n = 0; n < tasks.length(); n++) {
            JSONObject row = tasks.getJSONObject(n);
            assertEquals(
                row.getString("state"),
                TaskCalendar.state(row.getString("status"), row.getString("due_date"), today, horizon)
            );
            Integer severity = TaskCalendar.reminderSeverity(
                row.getString("status"), row.getString("due_date"), today, horizon
            );
            if (row.isNull("severity")) assertNull(severity);
            else assertEquals(Integer.valueOf(row.getInt("severity")), severity);
        }
    }

    @Test public void invalidValuesAreRejected() {
        try {
            TaskCalendar.state("pending", "11/09/2026", LocalDate.of(2026, 9, 11));
            fail("Non-ISO due date must fail");
        } catch (IllegalArgumentException expected) {
            assertTrue(expected.getMessage().contains("YYYY-MM-DD"));
        }
        try {
            TaskCalendar.state("done", "2026-09-11", LocalDate.of(2026, 9, 11));
            fail("Unknown status must fail");
        } catch (IllegalArgumentException expected) {
            assertTrue(expected.getMessage().contains("Unsupported"));
        }
    }
}
