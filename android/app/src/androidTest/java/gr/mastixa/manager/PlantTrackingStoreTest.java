package gr.mastixa.manager;

import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import java.util.List;
import static org.junit.Assert.*;

public class PlantTrackingStoreTest {
    private PlantTracking.Plant plant(String id, String fieldId, String batchId) {
        return new PlantTracking.Plant(
            id, fieldId, batchId, "A-001", "2026-03-01", "Mastic",
            38.25, 26.02, "active", "good", "baseline"
        );
    }

    private static String fieldId(FarmStore store, String name) {
        return store.fields().stream().filter(field -> field.name().equals(name)).findFirst().orElseThrow().id();
    }

    @Test public void persistenceHistorySoftDeleteAndProfileIsolation() {
        var context = InstrumentationRegistry.getInstrumentation().getTargetContext();
        context.deleteDatabase("plant-store-a.db");
        context.deleteDatabase("plant-store-b.db");
        try (FarmStore first = new FarmStore(context, "plant-store-a.db");
             FarmStore second = new FarmStore(context, "plant-store-b.db")) {
            first.saveField(null, "Α", 2, "", "", 70, "");
            second.saveField(null, "Β", 3, "", "", 20, "");
            String firstField = fieldId(first, "Α");
            String secondField = fieldId(second, "Β");

            WorkStore work = new WorkStore(first);
            String batch = work.savePlanting(new WorkStore.Planting(
                null, "2026-03-01", firstField, 70, 68, "Δενδρύλλια", "", "Mastic", "2 x 6", 0, "", ""
            ));
            PlantTrackingStore plants = new PlantTrackingStore(first);
            plants.savePlant(plant("plant-1", firstField, batch));
            plants.appendEvent(new PlantTracking.Event(
                "event-2", "plant-1", "2026-04-10", "status", "dead", ""
            ));
            plants.appendEvent(new PlantTracking.Event(
                "event-1", "plant-1", "2026-04-01", "health", "watch", ""
            ));

            PlantTracking.Snapshot snapshot = plants.snapshot("plant-1");
            assertEquals("dead", snapshot.status());
            assertEquals("watch", snapshot.health());
            assertEquals("2026-04-10", snapshot.lastEventDate());
            assertEquals(List.of("event-1", "event-2"), plants.events("plant-1").stream().map(PlantTracking.Event::id).toList());
            assertEquals(70, work.plantings().get(0).trees_planted());
            assertEquals(68, work.plantings().get(0).trees_alive());

            plants.deletePlant("plant-1");
            assertTrue(plants.plants(null, false).isEmpty());
            assertEquals(2, plants.events("plant-1").size());
            plants.restorePlant("plant-1");
            assertEquals("dead", plants.snapshot("plant-1").status());

            PlantTrackingStore otherProfile = new PlantTrackingStore(second);
            assertTrue(otherProfile.plants(null, false).isEmpty());
            try {
                otherProfile.savePlant(new PlantTracking.Plant(
                    "wrong-profile", firstField, "", "", "", "", null, null, "active", "unknown", ""
                ));
                fail("A plant cannot reference a field from another profile database");
            } catch (IllegalArgumentException expected) {
                assertTrue(expected.getMessage().contains("Field"));
            }
            otherProfile.savePlant(new PlantTracking.Plant(
                "plant-b", secondField, "", "", "", "", null, null, "active", "unknown", ""
            ));
            assertEquals(1, otherProfile.plants(null, false).size());
            assertEquals(1, plants.plants(null, false).size());
        } finally {
            context.deleteDatabase("plant-store-a.db");
            context.deleteDatabase("plant-store-b.db");
        }
    }

    @Test public void batchRelationshipAndImmutableEventsAreEnforced() {
        var context = InstrumentationRegistry.getInstrumentation().getTargetContext();
        context.deleteDatabase("plant-store-rel.db");
        try (FarmStore store = new FarmStore(context, "plant-store-rel.db")) {
            store.saveField(null, "Α", 2, "", "", 10, "");
            store.saveField(null, "Β", 2, "", "", 10, "");
            String fieldA = fieldId(store, "Α");
            String fieldB = fieldId(store, "Β");
            WorkStore work = new WorkStore(store);
            String batchB = work.savePlanting(new WorkStore.Planting(
                null, "2026-03-01", fieldB, 10, 10, "Δενδρύλλια", "", "", "", 0, "", ""
            ));
            PlantTrackingStore plants = new PlantTrackingStore(store);
            try {
                plants.savePlant(plant("bad", fieldA, batchB));
                fail("Cross-field batch link must fail");
            } catch (IllegalArgumentException expected) {
                assertTrue(expected.getMessage().contains("another field"));
            }

            plants.savePlant(new PlantTracking.Plant(
                "plant-1", fieldA, "", "", "2026-03-01", "", null, null, "active", "unknown", ""
            ));
            var event = new PlantTracking.Event("event-1", "plant-1", "2026-03-10", "note", "checked", "");
            plants.appendEvent(event);
            try {
                plants.appendEvent(event);
                fail("Event ids are immutable identities");
            } catch (IllegalArgumentException expected) {
                assertTrue(expected.getMessage().contains("already exists"));
            }
            try {
                plants.savePlant(new PlantTracking.Plant(
                    "plant-1", fieldA, "", "", "2026-03-20", "", null, null, "active", "unknown", ""
                ));
                fail("Metadata edit cannot invalidate immutable history");
            } catch (IllegalArgumentException expected) {
                assertTrue(expected.getMessage().contains("predate"));
            }
        } finally {
            context.deleteDatabase("plant-store-rel.db");
        }
    }
}
