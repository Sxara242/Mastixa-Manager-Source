package gr.mastixa.manager;

import androidx.test.platform.app.InstrumentationRegistry;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import org.json.JSONArray;
import org.json.JSONObject;
import org.junit.Test;
import static org.junit.Assert.*;

public class InventoryLedgerContractTest {
    private JSONObject fixture() throws Exception {
        try (InputStream in = InstrumentationRegistry.getInstrumentation().getContext().getAssets().open("phase10_inventory_ledger.json")) {
            return new JSONObject(new String(in.readAllBytes(), StandardCharsets.UTF_8));
        }
    }

    @Test public void sharedFixtureHasCanonicalSignedRunningBalance() throws Exception {
        JSONObject f = fixture();
        JSONArray movements = f.getJSONArray("movements");
        double running = 0.0;
        for (int i = 0; i < movements.length(); i++) {
            JSONObject movement = movements.getJSONObject(i);
            double quantity = movement.getDouble("quantity");
            running += InventoryStore.signed(movement.getString("type"), quantity);
            assertEquals(movement.getDouble("running_stock"), running, 0.000001);
        }
        assertEquals(f.getDouble("expected_final_stock"), running, 0.000001);
    }

    @Test public void allCanonicalTypesMatchExpectedSigns() {
        assertEquals(2.0, InventoryStore.signed("Παραλαβή", 2.0), 0.0);
        assertEquals(-2.0, InventoryStore.signed("Κατανάλωση", 2.0), 0.0);
        assertEquals(2.0, InventoryStore.signed("Διόρθωση +", 2.0), 0.0);
        assertEquals(-2.0, InventoryStore.signed("Διόρθωση -", 2.0), 0.0);
    }
}
