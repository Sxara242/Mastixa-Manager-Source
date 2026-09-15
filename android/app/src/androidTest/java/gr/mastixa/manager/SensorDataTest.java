package gr.mastixa.manager;

import androidx.test.platform.app.InstrumentationRegistry;
import org.json.JSONArray;
import org.json.JSONObject;
import org.junit.Test;
import java.nio.charset.StandardCharsets;
import java.util.*;
import static org.junit.Assert.*;

public class SensorDataTest {
    private JSONObject fixture() throws Exception {
        try (var input = InstrumentationRegistry.getInstrumentation().getContext()
            .getAssets().open("phase15_sensor_data.json")) {
            return new JSONObject(new String(input.readAllBytes(), StandardCharsets.UTF_8));
        }
    }

    private SensorData.Device device(JSONObject row) throws Exception {
        return new SensorData.Device(
            row.getString("id"),
            row.getString("name"),
            row.getString("provider"),
            row.optString("field_id", ""),
            row.optString("external_id", ""),
            row.optString("status", "active"),
            row.optString("notes", "")
        );
    }

    private SensorData.Channel channel(JSONObject row) throws Exception {
        return new SensorData.Channel(
            row.getString("id"),
            row.getString("device_id"),
            row.getString("metric"),
            row.getString("unit"),
            row.optString("label", "")
        );
    }

    private SensorData.Observation observation(JSONObject row) throws Exception {
        return new SensorData.Observation(
            row.getString("id"),
            row.getString("channel_id"),
            row.getString("observed_at"),
            row.getDouble("value"),
            row.optString("quality", "good"),
            row.optString("source_ref", "")
        );
    }

    @Test public void sharedFixtureMatchesCrossClientSensorContract() throws Exception {
        JSONObject fixture = fixture();
        SensorData.Device device = device(fixture.getJSONObject("device"));
        List<SensorData.Channel> channels = new ArrayList<>();
        JSONArray channelsJson = fixture.getJSONArray("channels");
        for (int n = 0; n < channelsJson.length(); n++) {
            channels.add(channel(channelsJson.getJSONObject(n)));
        }
        List<SensorData.Observation> observations = new ArrayList<>();
        JSONArray observationsJson = fixture.getJSONArray("observations");
        for (int n = 0; n < observationsJson.length(); n++) {
            observations.add(observation(observationsJson.getJSONObject(n)));
        }

        SensorData.Snapshot snapshot = SensorData.project(device, channels, observations);
        JSONObject expected = fixture.getJSONObject("expected");
        assertEquals(expected.getString("device_id"), snapshot.deviceId());
        assertEquals(expected.getString("field_id"), snapshot.fieldId());
        assertEquals(expected.getString("name"), snapshot.name());
        assertEquals(expected.getString("provider"), snapshot.provider());
        assertEquals(expected.getString("external_id"), snapshot.externalId());
        assertEquals(expected.getString("status"), snapshot.status());
        assertEquals(expected.getString("notes"), snapshot.notes());

        JSONArray expectedChannels = expected.getJSONArray("channels");
        assertEquals(expectedChannels.length(), snapshot.channels().size());
        for (int n = 0; n < expectedChannels.length(); n++) {
            JSONObject row = expectedChannels.getJSONObject(n);
            SensorData.ChannelSnapshot actual = snapshot.channels().get(n);
            assertEquals(row.getString("channel_id"), actual.channelId());
            assertEquals(row.getString("metric"), actual.metric());
            assertEquals(row.getString("unit"), actual.unit());
            assertEquals(row.getString("label"), actual.label());
            assertEquals(row.getDouble("latest_value"), actual.latestValue(), 0.0000001);
            assertEquals(row.getString("latest_quality"), actual.latestQuality());
            assertEquals(row.getString("latest_observed_at"), actual.latestObservedAt());
            assertEquals(row.getString("latest_source_ref"), actual.latestSourceRef());
            assertEquals(row.getInt("observation_count"), actual.observationCount());
        }
    }

    @Test public void validationAndExtensionNamespaceMatchWindowsSemantics() {
        SensorData.Device device = new SensorData.Device(
            "device-1", "Station", "generic", "", "", "active", ""
        );
        SensorData.Channel good = new SensorData.Channel(
            "air", "device-1", "air_temperature", "celsius", ""
        );

        SensorData.Snapshot custom = SensorData.project(
            device,
            List.of(new SensorData.Channel(
                "leaf", "device-1", "custom.leaf_wetness", "percent", "Leaf"
            )),
            List.of()
        );
        assertEquals("", custom.fieldId());
        assertNull(custom.channels().get(0).latestValue());

        try {
            SensorData.project(device, List.of(new SensorData.Channel(
                "air", "device-1", "air_temperature", "fahrenheit", ""
            )), List.of());
            fail("Canonical unit mismatch must fail");
        } catch (IllegalArgumentException expected) {
            assertTrue(expected.getMessage().contains("canonical unit"));
        }
        try {
            SensorData.project(device, List.of(new SensorData.Channel(
                "mystery", "device-1", "leaf_wetness", "percent", ""
            )), List.of());
            fail("Unknown metrics must use custom namespace");
        } catch (IllegalArgumentException expected) {
            assertTrue(expected.getMessage().contains("custom"));
        }
        try {
            SensorData.project(device, List.of(good), List.of(new SensorData.Observation(
                "o1", "air", "2026-09-12T01:00:00+03:00", 20.0, "good", ""
            )));
            fail("Non-UTC timestamps must fail");
        } catch (IllegalArgumentException expected) {
            assertTrue(expected.getMessage().contains("UTC"));
        }
        try {
            SensorData.project(device, List.of(good), List.of(new SensorData.Observation(
                "o1", "air", "2026-09-12T01:00:00Z", Double.NaN, "good", ""
            )));
            fail("Non-finite values must fail");
        } catch (IllegalArgumentException expected) {
            assertTrue(expected.getMessage().contains("finite"));
        }
        try {
            SensorData.project(device, List.of(good), List.of(new SensorData.Observation(
                "o1", "missing", "2026-09-12T01:00:00Z", 20.0, "good", ""
            )));
            fail("Unknown channel must fail");
        } catch (IllegalArgumentException expected) {
            assertTrue(expected.getMessage().contains("unknown channel"));
        }
    }
}
