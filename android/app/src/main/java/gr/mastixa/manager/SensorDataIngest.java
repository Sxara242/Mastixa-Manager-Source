package gr.mastixa.manager;

import android.content.ContentValues;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/** Phase 15D provider-neutral, atomic and idempotent normalized ingestion boundary. */
public final class SensorDataIngest {
    public record Result(
        boolean deviceCreated,
        int channelsCreated,
        int observationsInserted,
        int observationsUnchanged
    ) {}

    private SensorDataIngest() {}

    private static String text(String value) { return value == null ? "" : value.trim(); }

    private static SensorData.Device device(SensorData.Device value) {
        Objects.requireNonNull(value, "device");
        return new SensorData.Device(
            text(value.id()), text(value.name()), text(value.provider()), text(value.fieldId()),
            text(value.externalId()), text(value.status()), text(value.notes())
        );
    }

    private static SensorData.Channel channel(SensorData.Channel value) {
        Objects.requireNonNull(value, "channel");
        return new SensorData.Channel(
            text(value.id()), text(value.deviceId()), text(value.metric()), text(value.unit()),
            text(value.label())
        );
    }

    private static SensorData.Observation observation(SensorData.Observation value) {
        Objects.requireNonNull(value, "observation");
        return new SensorData.Observation(
            text(value.id()), text(value.channelId()), text(value.observedAt()), value.value(),
            text(value.quality()), text(value.sourceRef())
        );
    }

    public static Result ingest(
        FarmStore store,
        SensorData.Device inputDevice,
        List<SensorData.Channel> inputChannels,
        List<SensorData.Observation> inputObservations
    ) {
        Objects.requireNonNull(store, "store");
        Objects.requireNonNull(inputChannels, "channels");
        Objects.requireNonNull(inputObservations, "observations");

        SensorData.Device device = device(inputDevice);
        List<SensorData.Channel> channels = new ArrayList<>();
        for (SensorData.Channel value : inputChannels) channels.add(channel(value));
        List<SensorData.Observation> observations = new ArrayList<>();
        for (SensorData.Observation value : inputObservations) observations.add(observation(value));
        SensorData.project(device, channels, observations);

        SQLiteDatabase db = store.getWritableDatabase();
        SensorDataStore.create(db);
        boolean deviceCreated = false;
        int channelsCreated = 0;
        int observationsInserted = 0;
        int observationsUnchanged = 0;
        long now = System.currentTimeMillis();

        db.beginTransaction();
        try {
            String effectiveStatus;
            try (Cursor c = db.rawQuery(
                "SELECT provider,external_id,status,deleted_at FROM sensor_devices WHERE id=?",
                new String[]{device.id()}
            )) {
                if (!c.moveToFirst()) {
                    if (!device.fieldId().isEmpty()) {
                        try (Cursor field = db.rawQuery(
                            "SELECT 1 FROM fields WHERE id=? AND deleted_at IS NULL",
                            new String[]{device.fieldId()}
                        )) {
                            if (!field.moveToFirst()) throw new IllegalArgumentException("Field does not exist");
                        }
                    }
                    ContentValues row = new ContentValues();
                    row.put("id", device.id());
                    row.put("name", device.name());
                    row.put("provider", device.provider());
                    row.put("field_id", device.fieldId());
                    row.put("external_id", device.externalId());
                    row.put("status", device.status());
                    row.put("notes", device.notes());
                    row.put("created_at", now);
                    row.put("updated_at", now);
                    row.putNull("deleted_at");
                    db.insertOrThrow("sensor_devices", null, row);
                    effectiveStatus = device.status();
                    deviceCreated = true;
                } else {
                    if (!c.isNull(3)) throw new IllegalArgumentException("Deleted sensor device cannot accept ingestion");
                    if (!c.getString(0).equals(device.provider()))
                        throw new IllegalArgumentException("Sensor device provider identity conflict");
                    String external = c.getString(1) == null ? "" : c.getString(1);
                    if (!external.isEmpty() && !device.externalId().isEmpty() && !external.equals(device.externalId()))
                        throw new IllegalArgumentException("Sensor device external identity conflict");
                    if (external.isEmpty() && !device.externalId().isEmpty()) {
                        ContentValues update = new ContentValues();
                        update.put("external_id", device.externalId());
                        update.put("updated_at", now);
                        db.update("sensor_devices", update, "id=?", new String[]{device.id()});
                    }
                    effectiveStatus = c.getString(2);
                }
            }

            if (!observations.isEmpty() && !"active".equals(effectiveStatus))
                throw new IllegalArgumentException("Disabled sensor device cannot accept observations");

            for (SensorData.Channel channel : channels) {
                boolean exists = false;
                try (Cursor c = db.rawQuery(
                    "SELECT device_id,metric,unit FROM sensor_channels WHERE id=?",
                    new String[]{channel.id()}
                )) {
                    if (c.moveToFirst()) {
                        exists = true;
                        if (!c.getString(0).equals(channel.deviceId())
                            || !c.getString(1).equals(channel.metric())
                            || !c.getString(2).equals(channel.unit()))
                            throw new IllegalArgumentException("Sensor channel identity conflict");
                    }
                }
                if (exists) continue;
                ContentValues row = new ContentValues();
                row.put("id", channel.id());
                row.put("device_id", channel.deviceId());
                row.put("metric", channel.metric());
                row.put("unit", channel.unit());
                row.put("label", channel.label());
                row.put("created_at", now);
                row.put("updated_at", now);
                db.insertOrThrow("sensor_channels", null, row);
                channelsCreated++;
            }

            for (SensorData.Observation observation : observations) {
                boolean exists = false;
                try (Cursor c = db.rawQuery(
                    "SELECT channel_id,observed_at,numeric_value,quality,source_ref " +
                        "FROM sensor_observations WHERE id=?",
                    new String[]{observation.id()}
                )) {
                    if (c.moveToFirst()) {
                        exists = true;
                        boolean identical = c.getString(0).equals(observation.channelId())
                            && c.getString(1).equals(observation.observedAt())
                            && Double.compare(c.getDouble(2), observation.value()) == 0
                            && c.getString(3).equals(observation.quality())
                            && (c.getString(4) == null ? "" : c.getString(4)).equals(observation.sourceRef());
                        if (!identical)
                            throw new IllegalArgumentException("Sensor observation identity conflict");
                    }
                }
                if (exists) {
                    observationsUnchanged++;
                    continue;
                }
                ContentValues row = new ContentValues();
                row.put("id", observation.id());
                row.put("channel_id", observation.channelId());
                row.put("observed_at", observation.observedAt());
                row.put("numeric_value", observation.value());
                row.put("quality", observation.quality());
                row.put("source_ref", observation.sourceRef());
                row.put("created_at", now);
                db.insertOrThrow("sensor_observations", null, row);
                observationsInserted++;
            }

            db.setTransactionSuccessful();
        } finally {
            db.endTransaction();
        }

        return new Result(deviceCreated, channelsCreated, observationsInserted, observationsUnchanged);
    }
}
