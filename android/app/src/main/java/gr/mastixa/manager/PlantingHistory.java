package gr.mastixa.manager;

import android.content.ContentValues;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import java.time.LocalDate;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import org.json.JSONObject;

/** Append-only aggregate replacement/replanting history for planting batches. */
public final class PlantingHistory {
    static final String TABLE = "planting_replantings";
    static final String[] COLUMNS = {
        "id", "planting_batch_id", "replanting_date", "tree_count", "notes", "created_at"
    };

    public record Replanting(
        String id,
        String plantingBatchId,
        String replantingDate,
        int treeCount,
        String notes,
        long createdAt
    ) {}

    public record Totals(
        long positions,
        long replantings,
        long historicalPlantings,
        long living,
        long historicalLosses,
        long vacantPositions
    ) {}

    private final FarmStore store;

    public PlantingHistory(FarmStore store) {
        this.store = store;
        create(store.getWritableDatabase());
    }

    static void create(SQLiteDatabase db) {
        db.execSQL(
            "CREATE TABLE IF NOT EXISTS planting_replantings(" +
            "id TEXT PRIMARY KEY," +
            "planting_batch_id TEXT NOT NULL," +
            "replanting_date TEXT NOT NULL," +
            "tree_count INTEGER NOT NULL CHECK(tree_count>0)," +
            "notes TEXT NOT NULL," +
            "created_at INTEGER NOT NULL)"
        );
        db.execSQL(
            "CREATE INDEX IF NOT EXISTS planting_replantings_batch_date " +
            "ON planting_replantings(planting_batch_id,replanting_date,id)"
        );
    }

    static void validate(Replanting row) {
        if (row.id() == null || row.id().isBlank() || row.plantingBatchId() == null || row.plantingBatchId().isBlank()) {
            throw new IllegalArgumentException("Χρειάζεται ταυτότητα επαναφύτευσης και παρτίδας.");
        }
        try {
            LocalDate.parse(row.replantingDate());
        } catch (DateTimeParseException | NullPointerException error) {
            throw new IllegalArgumentException("Η ημερομηνία επαναφύτευσης πρέπει να είναι YYYY-MM-DD.");
        }
        if (row.treeCount() <= 0 || row.createdAt() < 0) {
            throw new IllegalArgumentException("Η επαναφύτευση χρειάζεται θετικό αριθμό δέντρων.");
        }
    }

    static void validateBackupRow(JSONObject row) throws Exception {
        if (row.getString("id").isBlank() || row.getString("planting_batch_id").isBlank()) {
            throw new IllegalArgumentException("Μη έγκυρη επαναφύτευση.");
        }
        long count = row.getLong("tree_count");
        long created = row.getLong("created_at");
        if (count <= 0 || count > Integer.MAX_VALUE || created < 0) {
            throw new IllegalArgumentException("Μη έγκυρη επαναφύτευση.");
        }
        validate(new Replanting(
            row.getString("id"),
            row.getString("planting_batch_id"),
            row.getString("replanting_date"),
            (int) count,
            row.getString("notes"),
            created
        ));
    }

    static void validateRelations(SQLiteDatabase db) throws Exception {
        try (Cursor c = db.rawQuery(
            "SELECT 1 FROM planting_replantings r " +
            "LEFT JOIN planting_batches p ON p.id=r.planting_batch_id " +
            "WHERE p.id IS NULL OR r.replanting_date<p.planting_date LIMIT 1",
            null
        )) {
            if (c.moveToFirst()) throw new IllegalArgumentException("Ασύνδετη ή πρόωρη επαναφύτευση.");
        }
    }

    private String plantingDate(SQLiteDatabase db, String batchId) {
        try (Cursor c = db.rawQuery(
            "SELECT planting_date FROM planting_batches WHERE id=?",
            new String[]{batchId}
        )) {
            if (!c.moveToFirst()) throw new IllegalArgumentException("Η παρτίδα φύτευσης δεν υπάρχει.");
            return c.getString(0);
        }
    }

    public String add(String batchId, String replantingDate, int treeCount, String notes) {
        return add(UUID.randomUUID().toString(), batchId, replantingDate, treeCount, notes);
    }

    public String add(String id, String batchId, String replantingDate, int treeCount, String notes) {
        Replanting event = new Replanting(
            id == null ? "" : id.trim(),
            batchId == null ? "" : batchId.trim(),
            replantingDate == null ? "" : replantingDate.trim(),
            treeCount,
            notes == null ? "" : notes.trim(),
            System.currentTimeMillis()
        );
        validate(event);
        SQLiteDatabase db = store.getWritableDatabase();
        db.beginTransaction();
        try {
            String planted = plantingDate(db, event.plantingBatchId());
            if (event.replantingDate().compareTo(planted) < 0) {
                throw new IllegalArgumentException("Η επαναφύτευση δεν μπορεί να προηγείται της αρχικής φύτευσης.");
            }
            try (Cursor c = db.rawQuery(
                "SELECT 1 FROM planting_replantings WHERE id=?",
                new String[]{event.id()}
            )) {
                if (c.moveToFirst()) throw new IllegalArgumentException("Η επαναφύτευση υπάρχει ήδη.");
            }
            ContentValues values = new ContentValues();
            values.put("id", event.id());
            values.put("planting_batch_id", event.plantingBatchId());
            values.put("replanting_date", event.replantingDate());
            values.put("tree_count", event.treeCount());
            values.put("notes", event.notes());
            values.put("created_at", event.createdAt());
            db.insertOrThrow(TABLE, null, values);
            db.setTransactionSuccessful();
            return event.id();
        } finally {
            db.endTransaction();
        }
    }

    public List<Replanting> events(String batchId) {
        List<Replanting> result = new ArrayList<>();
        try (Cursor c = store.getReadableDatabase().rawQuery(
            "SELECT id,planting_batch_id,replanting_date,tree_count,notes,created_at " +
            "FROM planting_replantings WHERE planting_batch_id=? " +
            "ORDER BY replanting_date,id",
            new String[]{batchId}
        )) {
            while (c.moveToNext()) {
                result.add(new Replanting(
                    c.getString(0), c.getString(1), c.getString(2), c.getInt(3), c.getString(4), c.getLong(5)
                ));
            }
        }
        return result;
    }

    public Totals totals(String batchId) {
        try (Cursor c = store.getReadableDatabase().rawQuery(
            "SELECT p.trees_planted,p.trees_alive,COALESCE(SUM(r.tree_count),0) " +
            "FROM planting_batches p LEFT JOIN planting_replantings r ON r.planting_batch_id=p.id " +
            "WHERE p.id=? GROUP BY p.id,p.trees_planted,p.trees_alive",
            new String[]{batchId}
        )) {
            if (!c.moveToFirst()) throw new IllegalArgumentException("Η παρτίδα φύτευσης δεν υπάρχει.");
            long positions = c.getLong(0);
            long living = c.getLong(1);
            long replacements = c.getLong(2);
            if (positions < 0 || living < 0 || living > positions || replacements < 0) {
                throw new IllegalArgumentException("Μη έγκυροι αριθμοί παρτίδας φύτευσης.");
            }
            long historical;
            try {
                historical = Math.addExact(positions, replacements);
            } catch (ArithmeticException error) {
                throw new IllegalArgumentException("Υπερβολικά μεγάλος αριθμός ιστορικών φυτεύσεων.");
            }
            return new Totals(
                positions,
                replacements,
                historical,
                living,
                Math.max(historical - living, 0),
                Math.max(positions - living, 0)
            );
        }
    }
}
