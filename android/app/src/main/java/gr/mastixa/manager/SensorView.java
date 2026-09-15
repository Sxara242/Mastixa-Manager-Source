package gr.mastixa.manager;

import java.time.Instant;
import java.time.format.DateTimeParseException;
import java.time.temporal.ChronoUnit;
import java.util.Set;
import java.util.regex.Pattern;

/** Shared Phase 15E presentation-only stale/suspect classification. */
public final class SensorView {
    public static final long DEFAULT_STALE_AFTER_SECONDS = 24L * 60L * 60L;
    private static final Pattern UTC_SECOND = Pattern.compile("^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$");
    private static final Set<String> QUALITIES = Set.of("good", "suspect");

    private SensorView() {}

    public record ReadingState(boolean hasReading, boolean stale, boolean suspect) {}

    private static Instant parseUtc(String value, String label) {
        String text = value == null ? "" : value.trim();
        if (!UTC_SECOND.matcher(text).matches())
            throw new IllegalArgumentException(label + " must be UTC YYYY-MM-DDTHH:MM:SSZ");
        try {
            Instant parsed = Instant.parse(text);
            if (!parsed.toString().equals(text))
                throw new IllegalArgumentException(label + " must be UTC YYYY-MM-DDTHH:MM:SSZ");
            return parsed;
        } catch (DateTimeParseException error) {
            throw new IllegalArgumentException(label + " must be UTC YYYY-MM-DDTHH:MM:SSZ", error);
        }
    }

    public static String nowUtc() {
        return Instant.now().truncatedTo(ChronoUnit.SECONDS).toString();
    }

    public static ReadingState classify(String observedAt, String quality, String nowUtc) {
        return classify(observedAt, quality, nowUtc, DEFAULT_STALE_AFTER_SECONDS);
    }

    public static ReadingState classify(String observedAt, String quality, String nowUtc, long staleAfterSeconds) {
        if (staleAfterSeconds <= 0) throw new IllegalArgumentException("stale_after_seconds must be positive");
        String observed = observedAt == null ? "" : observedAt.trim();
        String normalizedQuality = quality == null ? "" : quality.trim();
        if (observed.isEmpty()) return new ReadingState(false, false, false);
        if (!QUALITIES.contains(normalizedQuality))
            throw new IllegalArgumentException("latest quality must be good or suspect");
        Instant observedInstant = parseUtc(observed, "latest_observed_at");
        Instant now = parseUtc(nowUtc, "now_utc");
        long age = now.getEpochSecond() - observedInstant.getEpochSecond();
        return new ReadingState(true, age > staleAfterSeconds, normalizedQuality.equals("suspect"));
    }
}
