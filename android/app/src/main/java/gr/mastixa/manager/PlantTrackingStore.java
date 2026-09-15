package gr.mastixa.manager;

import android.content.ContentValues;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import java.util.*;

/** Additive optional per-plant persistence. Plant events are append-only projection inputs. */
public final class PlantTrackingStore {
    public static final String[] PLANT_COLUMNS = {
        "id","field_id","planting_batch_id","label","planted_date","variety",
        "latitude","longitude","status","health","notes","created_at","updated_at","deleted_at"
    };
    public static final String[] EVENT_COLUMNS = {
        "id","plant_id","event_date","kind","value","notes","created_at"
    };

    private final FarmStore store;

    public PlantTrackingStore(FarmStore store) {
        this.store = Objects.requireNonNull(store, "store");
        create(store.getWritableDatabase());
    }

    public static void create(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE IF NOT EXISTS individual_plants(" +
            "id TEXT PRIMARY KEY,field_id TEXT NOT NULL,planting_batch_id TEXT NOT NULL DEFAULT ''," +
            "label TEXT NOT NULL DEFAULT '',planted_date TEXT NOT NULL DEFAULT '',variety TEXT NOT NULL DEFAULT ''," +
            "latitude REAL,longitude REAL,status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','dead','removed'))," +
            "health TEXT NOT NULL DEFAULT 'unknown' CHECK(health IN ('unknown','good','watch','poor'))," +
            "notes TEXT NOT NULL DEFAULT '',created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL,deleted_at INTEGER)");
        db.execSQL("CREATE TABLE IF NOT EXISTS plant_events(" +
            "id TEXT PRIMARY KEY,plant_id TEXT NOT NULL,event_date TEXT NOT NULL," +
            "kind TEXT NOT NULL CHECK(kind IN ('note','health','status')),value TEXT NOT NULL DEFAULT ''," +
            "notes TEXT NOT NULL DEFAULT '',created_at INTEGER NOT NULL)");
        db.execSQL("CREATE INDEX IF NOT EXISTS idx_individual_plants_field ON individual_plants(field_id,deleted_at)");
        db.execSQL("CREATE INDEX IF NOT EXISTS idx_individual_plants_batch ON individual_plants(planting_batch_id)");
        db.execSQL("CREATE INDEX IF NOT EXISTS idx_plant_events_plant_date ON plant_events(plant_id,event_date,id)");
    }

    private static String text(String value) { return value == null ? "" : value.trim(); }

    private void requireField(String fieldId) {
        try (Cursor cursor = store.getReadableDatabase().rawQuery(
            "SELECT 1 FROM fields WHERE id=? AND deleted_at IS NULL", new String[]{fieldId}
        )) {
            if (!cursor.moveToFirst()) throw new IllegalArgumentException("Field does not exist");
        }
    }

    private void requireBatch(String batchId, String fieldId) {
        if (batchId.isEmpty()) return;
        try (Cursor cursor = store.getReadableDatabase().rawQuery(
            "SELECT field_id FROM planting_batches WHERE id=? AND deleted_at IS NULL", new String[]{batchId}
        )) {
            if (!cursor.moveToFirst()) throw new IllegalArgumentException("Planting batch does not exist");
            if (!fieldId.equals(cursor.getString(0)))
                throw new IllegalArgumentException("Planting batch belongs to another field");
        }
    }

    private static PlantTracking.Plant plant(Cursor c) {
        return new PlantTracking.Plant(
            c.getString(0), c.getString(1), c.getString(2), c.getString(3), c.getString(4), c.getString(5),
            c.isNull(6) ? null : c.getDouble(6), c.isNull(7) ? null : c.getDouble(7),
            c.getString(8), c.getString(9), c.getString(10)
        );
    }

    private static PlantTracking.Event event(Cursor c) {
        return new PlantTracking.Event(
            c.getString(0), c.getString(1), c.getString(2), c.getString(3), c.getString(4), c.getString(5)
        );
    }

    private static PlantTracking.Plant normalized(PlantTracking.Plant plant) {
        return new PlantTracking.Plant(
            text(plant.id()), text(plant.fieldId()), text(plant.plantingBatchId()), text(plant.label()),
            text(plant.plantedDate()), text(plant.variety()), plant.latitude(), plant.longitude(),
            text(plant.status()), text(plant.health()), text(plant.notes())
        );
    }

    private static PlantTracking.Event normalized(PlantTracking.Event event) {
        return new PlantTracking.Event(
            text(event.id()), text(event.plantId()), text(event.eventDate()), text(event.kind()),
            text(event.value()), text(event.notes())
        );
    }

    public void savePlant(PlantTracking.Plant input) {
        PlantTracking.Plant value = normalized(Objects.requireNonNull(input, "plant"));
        PlantTracking.project(value, List.of());
        requireField(value.fieldId());
        requireBatch(value.plantingBatchId(), value.fieldId());

        Long created = null;
        try (Cursor cursor = store.getReadableDatabase().rawQuery(
            "SELECT created_at,deleted_at FROM individual_plants WHERE id=?", new String[]{value.id()}
        )) {
            if (cursor.moveToFirst()) {
                if (!cursor.isNull(1)) throw new IllegalArgumentException("Deleted plant must be restored before editing");
                created = cursor.getLong(0);
            }
        }
        PlantTracking.project(value, events(value.id()));
        long now = System.currentTimeMillis();
        ContentValues row = new ContentValues();
        row.put("id", value.id()); row.put("field_id", value.fieldId()); row.put("planting_batch_id", value.plantingBatchId());
        row.put("label", value.label()); row.put("planted_date", value.plantedDate()); row.put("variety", value.variety());
        if (value.latitude() == null) row.putNull("latitude"); else row.put("latitude", value.latitude());
        if (value.longitude() == null) row.putNull("longitude"); else row.put("longitude", value.longitude());
        row.put("status", value.status()); row.put("health", value.health()); row.put("notes", value.notes());
        row.put("created_at", created == null ? now : created); row.put("updated_at", now); row.putNull("deleted_at");
        SQLiteDatabase db = store.getWritableDatabase();
        if (created == null) db.insertOrThrow("individual_plants", null, row);
        else if (db.update("individual_plants", row, "id=?", new String[]{value.id()}) != 1)
            throw new IllegalArgumentException("Plant does not exist");
    }

    public PlantTracking.Plant plant(String plantId) { return plant(plantId, false); }

    public PlantTracking.Plant plant(String plantId, boolean includeDeleted) {
        String key = text(plantId);
        String sql = "SELECT id,field_id,planting_batch_id,label,planted_date,variety,latitude,longitude,status,health,notes " +
            "FROM individual_plants WHERE id=?" + (includeDeleted ? "" : " AND deleted_at IS NULL");
        try (Cursor cursor = store.getReadableDatabase().rawQuery(sql, new String[]{key})) {
            if (!cursor.moveToFirst()) throw new IllegalArgumentException("Plant does not exist");
            return plant(cursor);
        }
    }

    public List<PlantTracking.Plant> plants(String fieldId, boolean includeDeleted) {
        List<PlantTracking.Plant> rows = new ArrayList<>();
        StringBuilder where = new StringBuilder();
        List<String> args = new ArrayList<>();
        if (!includeDeleted) where.append("deleted_at IS NULL");
        if (fieldId != null) {
            if (where.length() > 0) where.append(" AND ");
            where.append("field_id=?"); args.add(text(fieldId));
        }
        String sql = "SELECT id,field_id,planting_batch_id,label,planted_date,variety,latitude,longitude,status,health,notes " +
            "FROM individual_plants" + (where.length() == 0 ? "" : " WHERE " + where) +
            " ORDER BY field_id,label COLLATE NOCASE,id";
        try (Cursor cursor = store.getReadableDatabase().rawQuery(sql, args.toArray(new String[0]))) {
            while (cursor.moveToNext()) rows.add(plant(cursor));
        }
        return List.copyOf(rows);
    }

    public List<PlantTracking.Event> events(String plantId) {
        List<PlantTracking.Event> rows = new ArrayList<>();
        try (Cursor cursor = store.getReadableDatabase().rawQuery(
            "SELECT id,plant_id,event_date,kind,value,notes FROM plant_events WHERE plant_id=? ORDER BY event_date,id",
            new String[]{text(plantId)}
        )) {
            while (cursor.moveToNext()) rows.add(event(cursor));
        }
        return List.copyOf(rows);
    }

    public void appendEvent(PlantTracking.Event input) {
        PlantTracking.Event value = normalized(Objects.requireNonNull(input, "event"));
        PlantTracking.Plant owner = plant(value.plantId());
        if (eventExists(value.id())) throw new IllegalArgumentException("Plant event id already exists");
        List<PlantTracking.Event> next = new ArrayList<>(events(value.plantId())); next.add(value);
        PlantTracking.project(owner, next);
        ContentValues row = new ContentValues();
        row.put("id", value.id()); row.put("plant_id", value.plantId()); row.put("event_date", value.eventDate());
        row.put("kind", value.kind()); row.put("value", value.value()); row.put("notes", value.notes());
        row.put("created_at", System.currentTimeMillis());
        store.getWritableDatabase().insertOrThrow("plant_events", null, row);
    }

    private boolean eventExists(String eventId) {
        try (Cursor cursor = store.getReadableDatabase().rawQuery(
            "SELECT 1 FROM plant_events WHERE id=?", new String[]{eventId}
        )) { return cursor.moveToFirst(); }
    }

    public PlantTracking.Snapshot snapshot(String plantId) {
        PlantTracking.Plant value = plant(plantId);
        return PlantTracking.project(value, events(value.id()));
    }

    public void deletePlant(String plantId) {
        String key = text(plantId); long now = System.currentTimeMillis();
        ContentValues row = new ContentValues(); row.put("deleted_at", now); row.put("updated_at", now);
        if (store.getWritableDatabase().update("individual_plants", row, "id=? AND deleted_at IS NULL", new String[]{key}) != 1)
            throw new IllegalArgumentException("Plant does not exist");
    }

    public void restorePlant(String plantId) {
        PlantTracking.Plant value = plant(plantId, true);
        requireField(value.fieldId());
        requireBatch(value.plantingBatchId(), value.fieldId());
        String key = text(plantId); ContentValues row = new ContentValues(); row.putNull("deleted_at"); row.put("updated_at", System.currentTimeMillis());
        if (store.getWritableDatabase().update("individual_plants", row, "id=? AND deleted_at IS NOT NULL", new String[]{key}) != 1)
            throw new IllegalArgumentException("Deleted plant does not exist");
    }
}
