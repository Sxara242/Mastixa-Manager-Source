package gr.mastixa.manager;

import androidx.test.platform.app.InstrumentationRegistry;
import org.json.JSONArray;
import org.json.JSONObject;
import org.junit.Test;
import java.nio.charset.StandardCharsets;
import static org.junit.Assert.*;

public class SensorViewTest {
    private JSONObject fixture() throws Exception {
        try (var input = InstrumentationRegistry.getInstrumentation().getContext()
            .getAssets().open("phase15_sensor_view.json")) {
            return new JSONObject(new String(input.readAllBytes(), StandardCharsets.UTF_8));
        }
    }

    @Test public void sharedFixtureMatchesWindowsStaleAndSuspectSemantics() throws Exception {
        JSONObject fixture = fixture();
        String now = fixture.getString("now_utc");
        long threshold = fixture.getLong("stale_after_seconds");
        JSONArray cases = fixture.getJSONArray("cases");
        for (int n = 0; n < cases.length(); n++) {
            JSONObject row = cases.getJSONObject(n);
            SensorView.ReadingState state = SensorView.classify(
                row.getString("observed_at"), row.getString("quality"), now, threshold
            );
            assertEquals(row.getString("name"), row.getBoolean("has_reading"), state.hasReading());
            assertEquals(row.getString("name"), row.getBoolean("stale"), state.stale());
            assertEquals(row.getString("name"), row.getBoolean("suspect"), state.suspect());
        }
    }

    @Test public void invalidInputsAreRejected() {
        try {
            SensorView.classify("2026-09-12T10:00:00Z", "good", "2026-09-12T12:00:00Z", 0);
            fail("Non-positive stale threshold must fail");
        } catch (IllegalArgumentException expected) {
            assertTrue(expected.getMessage().contains("positive"));
        }
        try {
            SensorView.classify("2026-09-12T10:00:00Z", "unknown", "2026-09-12T12:00:00Z");
            fail("Unknown quality must fail");
        } catch (IllegalArgumentException expected) {
            assertTrue(expected.getMessage().contains("quality"));
        }
        try {
            SensorView.classify("2026-09-12T10:00:00+03:00", "good", "2026-09-12T12:00:00Z");
            fail("Non-UTC timestamp must fail");
        } catch (IllegalArgumentException expected) {
            assertTrue(expected.getMessage().contains("UTC"));
        }
    }
}
