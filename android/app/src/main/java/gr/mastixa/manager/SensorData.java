package gr.mastixa.manager;

import java.time.Instant;
import java.time.format.DateTimeParseException;
import java.util.*;
import java.util.regex.Pattern;

/** Pure Phase 15 sensor/API normalization contract. No database or network dependency. */
public final class SensorData {
    public static final Set<String> DEVICE_STATUSES = Set.of("active", "disabled");
    public static final Set<String> OBSERVATION_QUALITIES = Set.of("good", "suspect");
    public static final Map<String, String> CANONICAL_UNITS = Map.ofEntries(
        Map.entry("air_temperature", "celsius"),
        Map.entry("soil_temperature", "celsius"),
        Map.entry("air_humidity", "percent"),
        Map.entry("soil_moisture", "percent"),
        Map.entry("rainfall", "millimeter"),
        Map.entry("battery", "percent"),
        Map.entry("water_level", "millimeter"),
        Map.entry("pressure", "hectopascal"),
        Map.entry("wind_speed", "meter_per_second"),
        Map.entry("soil_ec", "microsiemens_per_cm"),
        Map.entry("soil_ph", "ph")
    );

    private static final Pattern MACHINE_ID = Pattern.compile("^[a-z][a-z0-9_.-]{0,63}$");
    private static final Pattern UNIT_ID = Pattern.compile("^[a-z][a-z0-9_./-]{0,31}$");
    private static final Pattern UTC_SECOND = Pattern.compile(
        "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$"
    );

    private SensorData() {}

    public record Device(
        String id,
        String name,
        String provider,
        String fieldId,
        String externalId,
        String status,
        String notes
    ) {}

    public record Channel(
        String id,
        String deviceId,
        String metric,
        String unit,
        String label
    ) {}

    public record Observation(
        String id,
        String channelId,
        String observedAt,
        double value,
        String quality,
        String sourceRef
    ) {}

    public record ChannelSnapshot(
        String channelId,
        String metric,
        String unit,
        String label,
        Double latestValue,
        String latestQuality,
        String latestObservedAt,
        String latestSourceRef,
        int observationCount
    ) {}

    public record Snapshot(
        String deviceId,
        String fieldId,
        String name,
        String provider,
        String externalId,
        String status,
        String notes,
        List<ChannelSnapshot> channels
    ) {}

    private static String text(String value) { return value == null ? "" : value.trim(); }

    private static String required(String value, String label) {
        String normalized = text(value);
        if (normalized.isEmpty()) throw new IllegalArgumentException(label + " is required");
        return normalized;
    }

    private static String machineId(String value, String label, boolean unit) {
        String normalized = required(value, label);
        Pattern pattern = unit ? UNIT_ID : MACHINE_ID;
        if (!pattern.matcher(normalized).matches())
            throw new IllegalArgumentException(label + " must be a stable lowercase machine identifier");
        return normalized;
    }

    private static String utcTimestamp(String value, String label) {
        String normalized = required(value, label);
        if (!UTC_SECOND.matcher(normalized).matches())
            throw new IllegalArgumentException(label + " must be UTC YYYY-MM-DDTHH:MM:SSZ");
        try {
            Instant parsed = Instant.parse(normalized);
            if (!parsed.toString().equals(normalized))
                throw new IllegalArgumentException(label + " must be UTC YYYY-MM-DDTHH:MM:SSZ");
        } catch (DateTimeParseException error) {
            throw new IllegalArgumentException(label + " must be UTC YYYY-MM-DDTHH:MM:SSZ", error);
        }
        return normalized;
    }

    private static void validateDevice(Device device) {
        Objects.requireNonNull(device, "device");
        required(device.id(), "device id");
        required(device.name(), "device name");
        required(device.provider(), "provider");
        if (!DEVICE_STATUSES.contains(device.status()))
            throw new IllegalArgumentException("Unsupported device status: " + device.status());
    }

    private static void validateChannel(Channel channel) {
        Objects.requireNonNull(channel, "channel");
        required(channel.id(), "channel id");
        required(channel.deviceId(), "device id");
        String metric = machineId(channel.metric(), "metric", false);
        String unit = machineId(channel.unit(), "unit", true);
        String expected = CANONICAL_UNITS.get(metric);
        if (expected != null && !expected.equals(unit))
            throw new IllegalArgumentException(
                "Metric " + metric + " requires canonical unit " + expected
            );
        if (expected == null && !metric.startsWith("custom."))
            throw new IllegalArgumentException("Unknown metric must use the custom. namespace");
    }

    private static void validateObservation(Observation observation) {
        Objects.requireNonNull(observation, "observation");
        required(observation.id(), "observation id");
        required(observation.channelId(), "channel id");
        utcTimestamp(observation.observedAt(), "observed_at");
        if (!Double.isFinite(observation.value()))
            throw new IllegalArgumentException("observation value must be finite");
        if (!OBSERVATION_QUALITIES.contains(observation.quality()))
            throw new IllegalArgumentException(
                "Unsupported observation quality: " + observation.quality()
            );
    }

    public static Snapshot project(
        Device device,
        List<Channel> channels,
        List<Observation> observations
    ) {
        validateDevice(device);
        Objects.requireNonNull(channels, "channels");
        Objects.requireNonNull(observations, "observations");

        Map<String, Channel> channelById = new HashMap<>();
        for (Channel channel : channels) {
            validateChannel(channel);
            if (!channel.deviceId().equals(device.id()))
                throw new IllegalArgumentException("sensor channel belongs to another device");
            if (channelById.putIfAbsent(channel.id(), channel) != null)
                throw new IllegalArgumentException("Duplicate sensor channel id: " + channel.id());
        }

        Set<String> observationIds = new HashSet<>();
        Map<String, List<Observation>> grouped = new HashMap<>();
        for (String channelId : channelById.keySet()) grouped.put(channelId, new ArrayList<>());
        for (Observation observation : observations) {
            validateObservation(observation);
            if (!observationIds.add(observation.id()))
                throw new IllegalArgumentException(
                    "Duplicate sensor observation id: " + observation.id()
                );
            List<Observation> bucket = grouped.get(observation.channelId());
            if (bucket == null)
                throw new IllegalArgumentException("sensor observation references an unknown channel");
            bucket.add(observation);
        }

        List<String> channelIds = new ArrayList<>(channelById.keySet());
        Collections.sort(channelIds);
        List<ChannelSnapshot> projected = new ArrayList<>();
        Comparator<Observation> order = Comparator
            .comparing(Observation::observedAt)
            .thenComparing(Observation::id);
        for (String channelId : channelIds) {
            Channel channel = channelById.get(channelId);
            List<Observation> ordered = new ArrayList<>(grouped.get(channelId));
            ordered.sort(order);
            Observation latest = ordered.isEmpty() ? null : ordered.get(ordered.size() - 1);
            projected.add(new ChannelSnapshot(
                channel.id(),
                channel.metric(),
                channel.unit(),
                text(channel.label()),
                latest == null ? null : latest.value(),
                latest == null ? "" : latest.quality(),
                latest == null ? "" : latest.observedAt(),
                latest == null ? "" : text(latest.sourceRef()),
                ordered.size()
            ));
        }

        return new Snapshot(
            device.id(),
            text(device.fieldId()),
            device.name(),
            device.provider(),
            text(device.externalId()),
            device.status(),
            text(device.notes()),
            List.copyOf(projected)
        );
    }
}
