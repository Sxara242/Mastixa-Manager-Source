package gr.mastixa.manager;

import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import org.json.JSONException;
import org.json.JSONObject;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneOffset;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.UUID;

/** Read-only Android projection of field activity sources into the Phase 9 contract. */
public final class ActivityProjection {
    public record SourceRef(String type, String id) {}
    public record SyncRef(String datasetId, String sourceUuid, String fieldUuid) {}
    public record Event(
        int version,
        String scopeId,
        String fieldId,
        SourceRef sourceRef,
        String kind,
        String eventDate,
        Long eventAt,
        String timeBasis,
        String status,
        String label,
        String summary,
        SyncRef syncRef
    ) {}

    private ActivityProjection() {}

    private static final String SQL = """
        SELECT 'production',s.id,s.field_id,'harvest',s.entry_date,NULL,NULL,s.product,s.notes,NULL
        FROM production s JOIN fields f ON f.id=s.field_id
        WHERE f.id=? AND f.deleted_at IS NULL AND s.deleted_at IS NULL
        UNION ALL
        SELECT 'farm_activity',s.id,s.field_id,s.category,s.activity_date,NULL,s.status,s.description,s.notes,NULL
        FROM farm_activities s JOIN fields f ON f.id=s.field_id
        WHERE f.id=? AND f.deleted_at IS NULL AND s.deleted_at IS NULL
        UNION ALL
        SELECT 'planting_batch',s.id,s.field_id,'planting',s.planting_date,NULL,NULL,s.material_type,s.notes,NULL
        FROM planting_batches s JOIN fields f ON f.id=s.field_id
        WHERE f.id=? AND f.deleted_at IS NULL AND s.deleted_at IS NULL
        UNION ALL
        SELECT 'plant_protection',s.id,s.field_id,'plant_protection',s.application_date,NULL,NULL,s.product_name,s.purpose,s.notes
        FROM plant_protection_records s JOIN fields f ON f.id=s.field_id
        WHERE f.id=? AND f.deleted_at IS NULL AND s.deleted_at IS NULL
        UNION ALL
        SELECT 'labor_entry',s.id,s.field_id,'cultivation_work',s.work_date,NULL,NULL,s.work_type,s.notes,NULL
        FROM labor_entries s JOIN fields f ON f.id=s.field_id
        WHERE f.id=? AND f.deleted_at IS NULL AND s.deleted_at IS NULL
        UNION ALL
        SELECT 'geo_point',g.id,g.field_id,'observation',NULL,g.created_at,NULL,NULL,NULL,g.payload
        FROM gis_records g JOIN fields f ON f.id=g.field_id
        WHERE f.id=? AND f.deleted_at IS NULL AND g.deleted_at IS NULL AND g.kind='point'
        """;

    public static List<Event> project(FarmStore store, String scopeId, String fieldId) {
        return project(store, scopeId, fieldId, null);
    }

    public static List<Event> project(FarmStore store, String scopeId, String fieldId, String datasetId) {
        if (scopeId == null || scopeId.trim().isEmpty()) {
            throw new IllegalArgumentException("A non-empty profile scope_id is required");
        }
        if (datasetId != null) canonicalUuid(datasetId, "dataset_id");
        if (fieldId == null || fieldId.isBlank()) return List.of();

        String[] args = {fieldId, fieldId, fieldId, fieldId, fieldId, fieldId};
        ArrayList<Event> result = new ArrayList<>();
        SQLiteDatabase db = store.getReadableDatabase();
        try (Cursor c = db.rawQuery(SQL, args)) {
            while (c.moveToNext()) {
                String sourceType = c.getString(0);
                String sourceId = c.getString(1);
                String sourceField = c.getString(2);
                String rawKind = c.getString(3);
                String dateText = c.isNull(4) ? null : c.getString(4);
                Long eventAt = c.isNull(5) || c.getType(5) != Cursor.FIELD_TYPE_INTEGER
                    ? null : c.getLong(5);
                String statusText = c.isNull(6) ? null : c.getString(6);
                String label = c.isNull(7) ? null : clean(c.getString(7));
                String summary = c.isNull(8) ? null : clean(c.getString(8));
                String payload = c.isNull(9) ? null : c.getString(9);

                String kind = normalizeKind(sourceType, rawKind);
                if (kind == null) continue;

                if (sourceType.equals("geo_point")) {
                    try {
                        JSONObject point = new JSONObject(payload == null ? "{}" : payload);
                        String pointType = point.optString("point_type", "");
                        if (!pointType.equals("note") && !pointType.equals("problem")) continue;
                        label = clean(point.optString("title", ""));
                        summary = clean(point.optString("notes", ""));
                    } catch (JSONException error) {
                        throw new IllegalStateException("Invalid stored GIS data", error);
                    }
                }

                String eventDate;
                String timeBasis;
                if (sourceType.equals("geo_point")) {
                    eventDate = utcDate(eventAt);
                    timeBasis = eventDate == null ? "unknown" : "recorded";
                    if (eventDate == null) eventAt = null;
                } else {
                    eventDate = isoDate(dateText);
                    timeBasis = eventDate == null ? "unknown" : "occurred";
                    eventAt = null;
                }

                result.add(new Event(
                    1,
                    scopeId,
                    sourceField,
                    new SourceRef(sourceType, sourceId),
                    kind,
                    eventDate,
                    eventAt,
                    timeBasis,
                    normalizeStatus(statusText),
                    label,
                    summary,
                    verifiedSyncRef(db, scopeId, datasetId, sourceType, sourceId, sourceField)
                ));
            }
        }

        result.sort(EVENT_ORDER);
        return List.copyOf(result);
    }

    private static SyncRef verifiedSyncRef(
        SQLiteDatabase db, String scopeId, String datasetId,
        String sourceType, String sourceId, String fieldId
    ) {
        if (datasetId == null) return null;

        SyncRef mapped = ActivityIdentityRegistry.lookup(
            db, scopeId, datasetId, sourceType, sourceId, fieldId
        );
        if (mapped != null) return mapped;

        // Existing GIS acknowledgement remains a verified fallback until all GIS
        // synchronization paths explicitly register their portable identities.
        if (!sourceType.equals("geo_point")) return null;
        if (!isCanonicalUuid(sourceId) || !isCanonicalUuid(fieldId)) return null;
        if (!syncedIdentity(db, datasetId, sourceId) || !syncedIdentity(db, datasetId, fieldId)) return null;
        return new SyncRef(datasetId, sourceId, fieldId);
    }

    private static boolean syncedIdentity(SQLiteDatabase db, String datasetId, String entityId) {
        try (Cursor c = db.rawQuery(
            "SELECT 1 FROM gis_sync_state WHERE dataset=? AND entity_id=? LIMIT 1",
            new String[]{datasetId, entityId}
        )) {
            return c.moveToFirst();
        }
    }

    private static String canonicalUuid(String value, String name) {
        try {
            String canonical = UUID.fromString(value).toString();
            if (!canonical.equals(value)) throw new IllegalArgumentException(name + " must be a canonical UUID");
            return canonical;
        } catch (IllegalArgumentException error) {
            throw new IllegalArgumentException(name + " must be a canonical UUID", error);
        }
    }

    private static boolean isCanonicalUuid(String value) {
        if (value == null) return false;
        try {
            return UUID.fromString(value).toString().equals(value);
        } catch (IllegalArgumentException error) {
            return false;
        }
    }

    private static String normalizeKind(String sourceType, String rawKind) {
        if (sourceType.equals("farm_activity")) {
            if ("Πότισμα".equals(rawKind)) return "irrigation";
            if ("Λίπανση".equals(rawKind)) return "fertilization";
            return null;
        }
        return rawKind;
    }

    private static String normalizeStatus(String value) {
        if (value == null || value.isBlank()) return null;
        return switch (value) {
            case "Προγραμματισμένη" -> "planned";
            case "Ολοκληρώθηκε" -> "completed";
            case "Ακυρώθηκε" -> "cancelled";
            default -> "unknown";
        };
    }

    private static String isoDate(String value) {
        if (value == null) return null;
        String text = value.trim();
        if (!text.matches("[0-9]{4}-[0-9]{2}-[0-9]{2}")) return null;
        try {
            return LocalDate.parse(text).toString();
        } catch (DateTimeParseException error) {
            return null;
        }
    }

    private static String utcDate(Long millis) {
        if (millis == null) return null;
        try {
            return Instant.ofEpochMilli(millis).atZone(ZoneOffset.UTC).toLocalDate().toString();
        } catch (RuntimeException error) {
            return null;
        }
    }

    private static String clean(String value) {
        if (value == null) return null;
        String text = value.trim();
        return text.isEmpty() ? null : text;
    }

    static final Comparator<Event> EVENT_ORDER = (left, right) -> {
        if (left.eventDate() == null && right.eventDate() != null) return 1;
        if (left.eventDate() != null && right.eventDate() == null) return -1;
        if (left.eventDate() != null) {
            int dateOrder = right.eventDate().compareTo(left.eventDate());
            if (dateOrder != 0) return dateOrder;
            if (left.eventAt() == null && right.eventAt() != null) return 1;
            if (left.eventAt() != null && right.eventAt() == null) return -1;
            if (left.eventAt() != null) {
                int instantOrder = Long.compare(right.eventAt(), left.eventAt());
                if (instantOrder != 0) return instantOrder;
            }
        }
        int typeOrder = left.sourceRef().type().compareTo(right.sourceRef().type());
        if (typeOrder != 0) return typeOrder;
        return left.sourceRef().id().compareTo(right.sourceRef().id());
    };
}
