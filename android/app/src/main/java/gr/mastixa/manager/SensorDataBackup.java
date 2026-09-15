package gr.mastixa.manager;

import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import org.json.JSONObject;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

/** Logical-backup metadata and semantic validation for Phase 15 sensor data. */
final class SensorDataBackup {
    static final String[] TABLES = {"sensor_devices", "sensor_channels", "sensor_observations"};
    static final String[][] COLUMNS = {
        SensorDataStore.DEVICE_COLUMNS,
        SensorDataStore.CHANNEL_COLUMNS,
        SensorDataStore.OBSERVATION_COLUMNS
    };

    private SensorDataBackup() {}

    static boolean isDecimalColumn(String key) {
        return key.equals("numeric_value");
    }

    static boolean allowsNegativeNumeric(String key) {
        return key.equals("numeric_value");
    }

    private static String required(JSONObject row, String key) throws Exception {
        String value = row.getString(key).trim();
        if (value.isEmpty()) throw new IOException("Missing sensor identity: " + key);
        return value;
    }

    static void validateRow(int tableIndex, JSONObject row) throws Exception {
        try {
            switch (tableIndex) {
                case 0 -> SensorData.project(new SensorData.Device(
                    required(row, "id"), required(row, "name"), required(row, "provider"),
                    row.getString("field_id"), row.getString("external_id"),
                    required(row, "status"), row.getString("notes")
                ), List.of(), List.of());
                case 1 -> {
                    SensorData.Channel channel = new SensorData.Channel(
                        required(row, "id"), required(row, "device_id"), required(row, "metric"),
                        required(row, "unit"), row.getString("label")
                    );
                    SensorData.project(new SensorData.Device(
                        channel.deviceId(), "backup", "backup", "", "", "active", ""
                    ), List.of(channel), List.of());
                }
                case 2 -> {
                    SensorData.Observation observation = new SensorData.Observation(
                        required(row, "id"), required(row, "channel_id"), required(row, "observed_at"),
                        row.getDouble("numeric_value"), required(row, "quality"), row.getString("source_ref")
                    );
                    SensorData.Channel channel = new SensorData.Channel(
                        observation.channelId(), "__backup_device__", "custom.backup", "raw", ""
                    );
                    SensorData.project(new SensorData.Device(
                        "__backup_device__", "backup", "backup", "", "", "active", ""
                    ), List.of(channel), List.of(observation));
                }
                default -> throw new IOException("Unknown sensor backup table");
            }
        } catch (RuntimeException error) {
            throw new IOException("Invalid sensor backup row", error);
        }
    }

    static void validateRelations(SQLiteDatabase db) throws IOException {
        try (Cursor c = db.rawQuery(
            "SELECT 1 FROM sensor_devices d LEFT JOIN fields f ON f.id=d.field_id " +
            "WHERE d.field_id<>'' AND f.id IS NULL LIMIT 1", null
        )) {
            if (c.moveToFirst()) throw new IOException("Sensor references missing field");
        }
        try (Cursor c = db.rawQuery(
            "SELECT 1 FROM sensor_channels c LEFT JOIN sensor_devices d ON d.id=c.device_id " +
            "WHERE d.id IS NULL LIMIT 1", null
        )) {
            if (c.moveToFirst()) throw new IOException("Sensor channel references missing device");
        }
        try (Cursor c = db.rawQuery(
            "SELECT 1 FROM sensor_observations o LEFT JOIN sensor_channels c ON c.id=o.channel_id " +
            "WHERE c.id IS NULL LIMIT 1", null
        )) {
            if (c.moveToFirst()) throw new IOException("Sensor observation references missing channel");
        }

        try (Cursor devices = db.rawQuery(
            "SELECT id,name,provider,field_id,external_id,status,notes FROM sensor_devices", null
        )) {
            while (devices.moveToNext()) {
                SensorData.Device device = new SensorData.Device(
                    devices.getString(0), devices.getString(1), devices.getString(2), devices.getString(3),
                    devices.getString(4), devices.getString(5), devices.getString(6)
                );
                List<SensorData.Channel> channels = new ArrayList<>();
                List<SensorData.Observation> observations = new ArrayList<>();
                try (Cursor c = db.rawQuery(
                    "SELECT id,device_id,metric,unit,label FROM sensor_channels WHERE device_id=? ORDER BY id",
                    new String[]{device.id()}
                )) {
                    while (c.moveToNext()) channels.add(new SensorData.Channel(
                        c.getString(0), c.getString(1), c.getString(2), c.getString(3), c.getString(4)
                    ));
                }
                for (SensorData.Channel channel : channels) {
                    try (Cursor c = db.rawQuery(
                        "SELECT id,channel_id,observed_at,numeric_value,quality,source_ref " +
                        "FROM sensor_observations WHERE channel_id=? ORDER BY observed_at,id",
                        new String[]{channel.id()}
                    )) {
                        while (c.moveToNext()) observations.add(new SensorData.Observation(
                            c.getString(0), c.getString(1), c.getString(2), c.getDouble(3), c.getString(4), c.getString(5)
                        ));
                    }
                }
                try {
                    SensorData.project(device, channels, observations);
                } catch (RuntimeException error) {
                    throw new IOException("Invalid sensor history", error);
                }
            }
        }
    }
}
