package gr.mastixa.manager;

import androidx.test.platform.app.InstrumentationRegistry;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import org.json.JSONObject;
import org.junit.Test;
import static org.junit.Assert.*;

public class InventoryProvenanceContractTest {
    private final android.content.Context context = InstrumentationRegistry.getInstrumentation().getTargetContext();

    private JSONObject fixture() throws Exception {
        try (InputStream in = InstrumentationRegistry.getInstrumentation().getContext().getAssets().open("phase10_inventory_provenance.json")) {
            return new JSONObject(new String(in.readAllBytes(), StandardCharsets.UTF_8));
        }
    }

    private InventoryImport.Data packageData(JSONObject f, boolean corrected) throws Exception {
        JSONObject state = f.getJSONObject(corrected ? "corrected" : "initial");
        var items = List.of(
            new InventoryStore.Item("item-a", "Item A", "Λίπασμα", "kg", 0, ""),
            new InventoryStore.Item("item-b", "Item B", "Λίπασμα", "kg", 0, "")
        );
        var movement = new InventoryStore.Movement(
            null,
            state.getString("item_key"),
            corrected ? "2026-09-12" : "2026-09-11",
            "Κατανάλωση",
            state.getDouble("quantity"),
            "",
            "",
            "",
            0,
            0,
            corrected ? "corrected owner projection" : "initial owner projection",
            f.getString("source_type"),
            String.valueOf(f.getInt("source_id")),
            "",
            f.getString("windows_movement_id")
        );
        return new InventoryImport.Data(items, List.of(movement));
    }

    @Test public void importedProvenanceIsStableAndCorrectedReimportConflicts() throws Exception {
        JSONObject f = fixture();
        String windowsMovementId = f.getString("windows_movement_id");
        String sourceType = f.getString("source_type");
        String sourceId = String.valueOf(f.getInt("source_id"));
        assertEquals(
            "explicit_conflict_not_duplicate_or_silent_skip",
            f.getJSONObject("expected").getString("corrected_reimport_policy")
        );

        String name = "phase10d-inventory-provenance.db";
        context.deleteDatabase(name);
        try (var store = new FarmStore(context, name)) {
            var inventory = new InventoryStore(store);
            String itemA = inventory.saveItem(new InventoryStore.Item(null, "Item A", "Λίπασμα", "kg", 0, ""));
            String itemB = inventory.saveItem(new InventoryStore.Item(null, "Item B", "Λίπασμα", "kg", 0, ""));
            inventory.saveMovement(new InventoryStore.Movement(null,itemA,"2026-09-10","Παραλαβή",10,"","","",0,0,"opening A","","","",""));
            inventory.saveMovement(new InventoryStore.Movement(null,itemB,"2026-09-10","Παραλαβή",10,"","","",0,0,"opening B","","","",""));

            var first = InventoryImport.process(store, packageData(f, false), Map.of(), List.of(), true);
            assertEquals(1, first.movements());

            var imported = inventory.movements(null).stream()
                .filter(m -> m.windowsId().equals(windowsMovementId))
                .findFirst().orElseThrow();
            assertEquals(sourceType, imported.sourceType());
            assertEquals(sourceId, imported.sourceId());
            assertEquals(windowsMovementId, imported.windowsId());
            assertEquals(itemA, imported.itemId());

            var repeat = InventoryImport.process(store, packageData(f, false), Map.of(), List.of(), true);
            assertEquals(0, repeat.movements());
            assertTrue(repeat.skipped() >= 1);
            assertEquals(1, inventory.movements(null).stream().filter(m -> m.windowsId().equals(windowsMovementId)).count());

            try {
                InventoryImport.process(store, packageData(f, true), Map.of(), List.of(), true);
                fail("Expected changed Windows movement to be rejected as an explicit import conflict");
            } catch (IllegalArgumentException expected) {
                assertTrue(expected.getMessage().contains("κίνηση Windows"));
            }
            assertEquals(1, inventory.movements(null).stream().filter(m -> m.windowsId().equals(windowsMovementId)).count());

            try {
                inventory.saveMovement(new InventoryStore.Movement(imported.id(),imported.itemId(),imported.date(),imported.type(),1,imported.fieldId(),imported.partnerId(),imported.supplier(),imported.price(),imported.cost(),imported.notes(),imported.sourceType(),imported.sourceId(),imported.expenseId(),imported.windowsId()));
                fail("Expected imported/source-owned movement to remain immutable from manual editing");
            } catch (IllegalArgumentException expected) {
                assertTrue(expected.getMessage().contains("ιστορικό"));
            }
        } finally {
            context.deleteDatabase(name);
        }
    }
}
