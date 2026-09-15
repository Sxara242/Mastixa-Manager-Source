package gr.mastixa.manager;

import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import org.json.JSONObject;
import java.io.IOException;
import java.util.*;

/** Backup metadata and validation for Phase 14 optional per-plant history. */
final class PlantTrackingBackup {
    static final String[] TABLES = {"individual_plants", "plant_events"};
    static final String[][] COLUMNS = {
        PlantTrackingStore.PLANT_COLUMNS,
        PlantTrackingStore.EVENT_COLUMNS
    };

    private PlantTrackingBackup() {}

    static boolean isDecimalColumn(String key) {
        return key.equals("latitude") || key.equals("longitude");
    }

    static boolean isNullableNumericColumn(String key) {
        return key.equals("latitude") || key.equals("longitude") || key.equals("deleted_at");
    }

    private static String required(JSONObject row, String key) throws Exception {
        String value = row.getString(key).trim();
        if (value.isEmpty()) throw new IOException("Missing plant-tracking identity: " + key);
        return value;
    }

    private static Double nullableDouble(JSONObject row, String key) throws Exception {
        return row.isNull(key) ? null : row.getDouble(key);
    }

    static void validateRow(int tableIndex, JSONObject row) throws Exception {
        try {
            switch (tableIndex) {
                case 0 -> PlantTracking.project(new PlantTracking.Plant(
                    required(row, "id"), required(row, "field_id"), row.getString("planting_batch_id"),
                    row.getString("label"), row.getString("planted_date"), row.getString("variety"),
                    nullableDouble(row, "latitude"), nullableDouble(row, "longitude"),
                    required(row, "status"), required(row, "health"), row.getString("notes")
                ), List.of());
                case 1 -> {
                    PlantTracking.Event event = new PlantTracking.Event(
                        required(row, "id"), required(row, "plant_id"), required(row, "event_date"),
                        required(row, "kind"), row.getString("value"), row.getString("notes")
                    );
                    PlantTracking.project(new PlantTracking.Plant(
                        event.plantId(), "__backup_field__", "", "", "", "", null, null,
                        "active", "unknown", ""
                    ), List.of(event));
                }
                default -> throw new IOException("Unknown plant-tracking backup table");
            }
        } catch (RuntimeException error) {
            throw new IOException("Invalid plant-tracking backup row", error);
        }
    }

    static void validateRelations(SQLiteDatabase db) throws IOException {
        try (Cursor c = db.rawQuery(
            "SELECT 1 FROM individual_plants p LEFT JOIN fields f ON f.id=p.field_id " +
            "WHERE f.id IS NULL OR f.deleted_at IS NOT NULL LIMIT 1", null
        )) {
            if (c.moveToFirst()) throw new IOException("Plant references missing field");
        }
        try (Cursor c = db.rawQuery(
            "SELECT 1 FROM individual_plants p LEFT JOIN planting_batches b ON b.id=p.planting_batch_id " +
            "WHERE p.planting_batch_id<>'' AND (b.id IS NULL OR b.deleted_at IS NOT NULL OR b.field_id<>p.field_id) LIMIT 1",
            null
        )) {
            if (c.moveToFirst()) throw new IOException("Planting-batch relationship mismatch");
        }
        try (Cursor c = db.rawQuery(
            "SELECT 1 FROM plant_events e LEFT JOIN individual_plants p ON p.id=e.plant_id " +
            "WHERE p.id IS NULL LIMIT 1", null
        )) {
            if (c.moveToFirst()) throw new IOException("Plant event references missing plant");
        }

        try (Cursor plants = db.rawQuery(
            "SELECT id,field_id,planting_batch_id,label,planted_date,variety,latitude,longitude,status,health,notes " +
            "FROM individual_plants", null
        )) {
            while (plants.moveToNext()) {
                PlantTracking.Plant plant = new PlantTracking.Plant(
                    plants.getString(0), plants.getString(1), plants.getString(2), plants.getString(3),
                    plants.getString(4), plants.getString(5), plants.isNull(6) ? null : plants.getDouble(6),
                    plants.isNull(7) ? null : plants.getDouble(7), plants.getString(8), plants.getString(9), plants.getString(10)
                );
                List<PlantTracking.Event> events = new ArrayList<>();
                try (Cursor c = db.rawQuery(
                    "SELECT id,plant_id,event_date,kind,value,notes FROM plant_events WHERE plant_id=? ORDER BY event_date,id",
                    new String[]{plant.id()}
                )) {
                    while (c.moveToNext()) events.add(new PlantTracking.Event(
                        c.getString(0), c.getString(1), c.getString(2), c.getString(3), c.getString(4), c.getString(5)
                    ));
                }
                try {
                    PlantTracking.project(plant, events);
                } catch (RuntimeException error) {
                    throw new IOException("Invalid plant event history", error);
                }
            }
        }
    }
}
