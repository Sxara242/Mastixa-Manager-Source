package gr.mastixa.manager;

import androidx.test.platform.app.InstrumentationRegistry;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import org.json.JSONArray;
import org.json.JSONObject;
import org.junit.Test;
import static org.junit.Assert.*;

public class SensorDataIngestTest {
    private final android.content.Context context =
        InstrumentationRegistry.getInstrumentation().getTargetContext();

    private JSONObject fixture() throws Exception {
        try (var input = InstrumentationRegistry.getInstrumentation().getContext()
            .getAssets().open("phase15_sensor_ingest.json")) {
            return new JSONObject(new String(input.readAllBytes(), StandardCharsets.UTF_8));
        }
    }

    private SensorData.Device device(JSONObject row) throws Exception {
        return new SensorData.Device(
            row.getString("id"), row.getString("name"), row.getString("provider"),
            row.optString("field_id", ""), row.optString("external_id", ""),
            row.optString("status", "active"), row.optString("notes", "")
        );
    }

    private SensorData.Channel channel(JSONObject row) throws Exception {
        return new SensorData.Channel(
            row.getString("id"), row.getString("device_id"), row.getString("metric"),
            row.getString("unit"), row.optString("label", "")
        );
    }

    private SensorData.Observation observation(JSONObject row) throws Exception {
        return new SensorData.Observation(
            row.getString("id"), row.getString("channel_id"), row.getString("observed_at"),
            row.getDouble("value"), row.optString("quality", "good"),
            row.optString("source_ref", "")
        );
    }

    private List<SensorData.Channel> channels(JSONObject root) throws Exception {
        List<SensorData.Channel> result = new ArrayList<>();
        JSONArray rows = root.getJSONArray("channels");
        for (int n = 0; n < rows.length(); n++) result.add(channel(rows.getJSONObject(n)));
        return result;
    }

    private List<SensorData.Observation> observations(JSONObject root) throws Exception {
        List<SensorData.Observation> result = new ArrayList<>();
        JSONArray rows = root.getJSONArray("observations");
        for (int n = 0; n < rows.length(); n++) result.add(observation(rows.getJSONObject(n)));
        return result;
    }

    @Test public void sharedFixtureIsIdempotentAtomicAndPreservesLocalMetadata() throws Exception {
        String name = "sensor-ingest-test.db";
        context.deleteDatabase(name);
        try (FarmStore farm = new FarmStore(context, name)) {
            JSONObject root = fixture();
            SensorData.Device device = device(root.getJSONObject("device"));
            List<SensorData.Channel> channels = channels(root);
            List<SensorData.Observation> observations = observations(root);
            JSONObject expected = root.getJSONObject("expected");

            SensorDataIngest.Result first = SensorDataIngest.ingest(farm, device, channels, observations);
            assertTrue(first.deviceCreated());
            assertEquals(expected.getInt("channels_created"), first.channelsCreated());
            assertEquals(expected.getInt("observations_inserted"), first.observationsInserted());
            assertEquals(0, first.observationsUnchanged());

            SensorDataStore store = new SensorDataStore(farm);
            SensorData.Snapshot snapshot = store.snapshot(device.id());
            SensorData.ChannelSnapshot air = snapshot.channels().stream()
                .filter(value -> value.channelId().equals("ingest-air")).findFirst().orElseThrow();
            assertEquals(19.25, air.latestValue(), 0.0000001);
            assertEquals("suspect", air.latestQuality());
            assertEquals(2, air.observationCount());

            SensorDataIngest.Result replay = SensorDataIngest.ingest(farm, device, channels, observations);
            assertFalse(replay.deviceCreated());
            assertEquals(0, replay.channelsCreated());
            assertEquals(0, replay.observationsInserted());
            assertEquals(expected.getInt("replay_observations_unchanged"), replay.observationsUnchanged());

            store.saveDevice(new SensorData.Device(
                device.id(), "Local station name", device.provider(), "", device.externalId(),
                "active", "local notes"
            ));
            store.saveChannel(new SensorData.Channel(
                "ingest-air", device.id(), "air_temperature", "celsius", "Local air label"
            ));
            SensorDataIngest.ingest(farm, device, channels, observations);
            assertEquals("Local station name", store.device(device.id()).name());
            assertEquals("local notes", store.device(device.id()).notes());
            assertEquals("Local air label", store.channel("ingest-air").label());

            int before = store.observations("ingest-air").size();
            List<SensorData.Observation> conflict = List.of(
                new SensorData.Observation(
                    "new-before-conflict", "ingest-air", "2026-09-12T08:00:00Z",
                    20.0, "good", "fixture:new"
                ),
                new SensorData.Observation(
                    observations.get(0).id(), observations.get(0).channelId(),
                    observations.get(0).observedAt(), observations.get(0).value() + 1.0,
                    observations.get(0).quality(), observations.get(0).sourceRef()
                )
            );
            try {
                SensorDataIngest.ingest(farm, device, channels, conflict);
                fail("Conflicting immutable observation retry must fail");
            } catch (IllegalArgumentException expectedError) {
                assertTrue(expectedError.getMessage().contains("observation identity conflict"));
            }
            assertEquals(before, store.observations("ingest-air").size());
            try (var c = farm.getReadableDatabase().rawQuery(
                "SELECT id FROM sensor_observations WHERE id='new-before-conflict'", null
            )) { assertFalse(c.moveToFirst()); }

            try {
                SensorDataIngest.ingest(
                    farm,
                    new SensorData.Device(
                        device.id(), device.name(), "other-provider", "", device.externalId(),
                        "active", ""
                    ),
                    channels,
                    List.of()
                );
                fail("Provider identity collision must fail");
            } catch (IllegalArgumentException expectedError) {
                assertTrue(expectedError.getMessage().contains("provider identity conflict"));
            }

            store.saveDevice(new SensorData.Device(
                device.id(), "Local station name", device.provider(), "", device.externalId(),
                "disabled", "local notes"
            ));
            try {
                SensorDataIngest.ingest(
                    farm, device, channels,
                    List.of(new SensorData.Observation(
                        "disabled-reading", "ingest-air", "2026-09-12T09:00:00Z",
                        21.0, "good", "fixture:disabled"
                    ))
                );
                fail("Disabled local device must reject observations");
            } catch (IllegalArgumentException expectedError) {
                assertTrue(expectedError.getMessage().contains("Disabled"));
            }
        } finally {
            context.deleteDatabase(name);
        }
    }

    @Test public void newDeviceFieldMustExist() {
        String name = "sensor-ingest-field-test.db";
        context.deleteDatabase(name);
        try (FarmStore farm = new FarmStore(context, name)) {
            SensorData.Device device = new SensorData.Device(
                "field-device", "Field probe", "fixture", "missing-field", "", "active", ""
            );
            SensorData.Channel channel = new SensorData.Channel(
                "field-soil", device.id(), "soil_moisture", "percent", ""
            );
            try {
                SensorDataIngest.ingest(farm, device, List.of(channel), List.of());
                fail("Missing field must fail");
            } catch (IllegalArgumentException expected) {
                assertTrue(expected.getMessage().contains("Field"));
            }
            try (var c = farm.getReadableDatabase().rawQuery(
                "SELECT id FROM sensor_devices WHERE id='field-device'", null
            )) { assertFalse(c.moveToFirst()); }
        } finally {
            context.deleteDatabase(name);
        }
    }
}
