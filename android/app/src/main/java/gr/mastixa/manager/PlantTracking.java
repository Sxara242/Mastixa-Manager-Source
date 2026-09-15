package gr.mastixa.manager;

import java.time.LocalDate;
import java.time.format.DateTimeParseException;
import java.util.*;

/** Pure optional per-plant state projection. No database or Android runtime dependency. */
public final class PlantTracking {
    public static final Set<String> STATUSES = Set.of("active", "dead", "removed");
    public static final Set<String> HEALTH = Set.of("unknown", "good", "watch", "poor");
    public static final Set<String> EVENT_KINDS = Set.of("note", "health", "status");

    private PlantTracking() {}

    public record Plant(
        String id,
        String fieldId,
        String plantingBatchId,
        String label,
        String plantedDate,
        String variety,
        Double latitude,
        Double longitude,
        String status,
        String health,
        String notes
    ) {}

    public record Event(
        String id,
        String plantId,
        String eventDate,
        String kind,
        String value,
        String notes
    ) {}

    public record Snapshot(
        String plantId,
        String fieldId,
        String plantingBatchId,
        String label,
        String plantedDate,
        String variety,
        Double latitude,
        Double longitude,
        String status,
        String health,
        String notes,
        String lastEventDate,
        int eventCount
    ) {}

    private static String required(String value, String label) {
        String text = value == null ? "" : value.trim();
        if (text.isEmpty()) throw new IllegalArgumentException(label + " is required");
        return text;
    }

    private static String text(String value) { return value == null ? "" : value.trim(); }

    private static LocalDate isoDate(String value, String label, boolean optional) {
        String text = text(value);
        if (optional && text.isEmpty()) return null;
        try {
            LocalDate parsed = LocalDate.parse(text);
            if (!parsed.toString().equals(text)) throw new DateTimeParseException("non-canonical", text, 0);
            return parsed;
        } catch (DateTimeParseException error) {
            throw new IllegalArgumentException(label + " must be YYYY-MM-DD", error);
        }
    }

    private static void validatePlant(Plant plant) {
        Objects.requireNonNull(plant, "plant");
        required(plant.id(), "plant id");
        required(plant.fieldId(), "field id");
        if (!STATUSES.contains(plant.status()))
            throw new IllegalArgumentException("Unsupported plant status: " + plant.status());
        if (!HEALTH.contains(plant.health()))
            throw new IllegalArgumentException("Unsupported plant health: " + plant.health());
        isoDate(plant.plantedDate(), "planted_date", true);
        if ((plant.latitude() == null) != (plant.longitude() == null))
            throw new IllegalArgumentException("latitude and longitude must be supplied together");
        if (plant.latitude() != null) {
            if (!Double.isFinite(plant.latitude()) || plant.latitude() < -90 || plant.latitude() > 90)
                throw new IllegalArgumentException("latitude is outside the supported range");
            if (!Double.isFinite(plant.longitude()) || plant.longitude() < -180 || plant.longitude() > 180)
                throw new IllegalArgumentException("longitude is outside the supported range");
        }
    }

    private static void validateEvent(Event event) {
        Objects.requireNonNull(event, "event");
        required(event.id(), "event id");
        required(event.plantId(), "plant id");
        isoDate(event.eventDate(), "event_date", false);
        if (!EVENT_KINDS.contains(event.kind()))
            throw new IllegalArgumentException("Unsupported plant event kind: " + event.kind());
        String value = text(event.value());
        if (event.kind().equals("health") && !HEALTH.contains(value))
            throw new IllegalArgumentException("Unsupported plant health: " + value);
        if (event.kind().equals("status") && !STATUSES.contains(value))
            throw new IllegalArgumentException("Unsupported plant status: " + value);
        if (event.kind().equals("note") && value.isEmpty() && text(event.notes()).isEmpty())
            throw new IllegalArgumentException("note event requires value or notes");
    }

    public static Snapshot project(Plant plant, List<Event> events) {
        validatePlant(plant);
        Objects.requireNonNull(events, "events");
        LocalDate planted = isoDate(plant.plantedDate(), "planted_date", true);
        Set<String> seen = new HashSet<>();
        List<Event> ordered = new ArrayList<>();
        for (Event event : events) {
            validateEvent(event);
            if (!event.plantId().equals(plant.id()))
                throw new IllegalArgumentException("plant event belongs to another plant");
            if (!seen.add(event.id()))
                throw new IllegalArgumentException("Duplicate plant event id: " + event.id());
            LocalDate eventDate = isoDate(event.eventDate(), "event_date", false);
            if (planted != null && eventDate.isBefore(planted))
                throw new IllegalArgumentException("plant event cannot predate planted_date");
            ordered.add(event);
        }
        ordered.sort(Comparator.comparing(Event::eventDate).thenComparing(Event::id));

        String status = plant.status();
        String health = plant.health();
        for (Event event : ordered) {
            if (event.kind().equals("status")) status = text(event.value());
            else if (event.kind().equals("health")) health = text(event.value());
        }

        return new Snapshot(
            plant.id(),
            plant.fieldId(),
            text(plant.plantingBatchId()),
            text(plant.label()),
            text(plant.plantedDate()),
            text(plant.variety()),
            plant.latitude(),
            plant.longitude(),
            status,
            health,
            text(plant.notes()),
            ordered.isEmpty() ? "" : ordered.get(ordered.size() - 1).eventDate(),
            ordered.size()
        );
    }
}
