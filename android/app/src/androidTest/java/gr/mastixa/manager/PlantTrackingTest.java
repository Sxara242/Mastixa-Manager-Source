package gr.mastixa.manager;

import androidx.test.platform.app.InstrumentationRegistry;
import org.json.JSONObject;
import org.junit.Test;
import java.nio.charset.StandardCharsets;
import java.util.*;
import static org.junit.Assert.*;

public class PlantTrackingTest {
    private JSONObject fixture() throws Exception {
        try (var input = InstrumentationRegistry.getInstrumentation().getContext()
            .getAssets().open("phase14_plant_tracking.json")) {
            return new JSONObject(new String(input.readAllBytes(), StandardCharsets.UTF_8));
        }
    }

    private PlantTracking.Plant plant(JSONObject row) throws Exception {
        return new PlantTracking.Plant(
            row.getString("id"), row.getString("field_id"), row.optString("planting_batch_id", ""),
            row.optString("label", ""), row.optString("planted_date", ""), row.optString("variety", ""),
            row.isNull("latitude") ? null : row.getDouble("latitude"),
            row.isNull("longitude") ? null : row.getDouble("longitude"),
            row.optString("status", "active"), row.optString("health", "unknown"), row.optString("notes", "")
        );
    }

    @Test public void sharedFixtureMatchesPhase14Contract() throws Exception {
        JSONObject fixture = fixture();
        var plant = plant(fixture.getJSONObject("plant"));
        var eventsJson = fixture.getJSONArray("events");
        var events = new ArrayList<PlantTracking.Event>();
        for (int n = 0; n < eventsJson.length(); n++) {
            var row = eventsJson.getJSONObject(n);
            events.add(new PlantTracking.Event(
                row.getString("id"), row.getString("plant_id"), row.getString("event_date"),
                row.getString("kind"), row.optString("value", ""), row.optString("notes", "")
            ));
        }
        var snapshot = PlantTracking.project(plant, events);
        JSONObject expected = fixture.getJSONObject("expected");
        assertEquals(expected.getString("plant_id"), snapshot.plantId());
        assertEquals(expected.getString("field_id"), snapshot.fieldId());
        assertEquals(expected.getString("planting_batch_id"), snapshot.plantingBatchId());
        assertEquals(expected.getString("label"), snapshot.label());
        assertEquals(expected.getString("planted_date"), snapshot.plantedDate());
        assertEquals(expected.getString("variety"), snapshot.variety());
        assertEquals(expected.getDouble("latitude"), snapshot.latitude(), 0.0000001);
        assertEquals(expected.getDouble("longitude"), snapshot.longitude(), 0.0000001);
        assertEquals(expected.getString("status"), snapshot.status());
        assertEquals(expected.getString("health"), snapshot.health());
        assertEquals(expected.getString("notes"), snapshot.notes());
        assertEquals(expected.getString("last_event_date"), snapshot.lastEventDate());
        assertEquals(expected.getInt("event_count"), snapshot.eventCount());
    }

    @Test public void optionalRegistryAndValidationMatchWindowsSemantics() {
        var optional = PlantTracking.project(new PlantTracking.Plant(
            "p2", "field-a", "", "", "", "", null, null, "active", "unknown", ""
        ), List.of());
        assertEquals("active", optional.status());
        assertEquals("unknown", optional.health());
        assertEquals(0, optional.eventCount());

        try {
            PlantTracking.project(new PlantTracking.Plant(
                "p", "f", "", "", "", "", 38.0, null, "active", "unknown", ""
            ), List.of());
            fail("Partial coordinates must fail");
        } catch (IllegalArgumentException expected) {
            assertTrue(expected.getMessage().contains("together"));
        }

        var planted = new PlantTracking.Plant(
            "p", "f", "", "", "2026-03-01", "", null, null, "active", "unknown", ""
        );
        try {
            PlantTracking.project(planted, List.of(
                new PlantTracking.Event("e", "p", "2026-02-28", "note", "before planting", "")
            ));
            fail("Event before planted date must fail");
        } catch (IllegalArgumentException expected) {
            assertTrue(expected.getMessage().contains("predate"));
        }
        try {
            PlantTracking.project(planted, List.of(
                new PlantTracking.Event("e", "p", "2026-03-02", "health", "excellent", "")
            ));
            fail("Unknown health must fail");
        } catch (IllegalArgumentException expected) {
            assertTrue(expected.getMessage().contains("health"));
        }
    }
}
