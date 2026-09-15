package gr.mastixa.manager;

import java.time.LocalDate;
import java.time.format.DateTimeParseException;
import java.util.Set;

/** Phase 13 derived calendar/reminder semantics. Stored task status is never rewritten to overdue. */
public final class TaskCalendar {
    public static final Set<String> STATUSES = Set.of("pending", "completed", "skipped");
    public static final Set<String> REMINDER_STATES = Set.of("overdue", "due_today", "upcoming");

    private TaskCalendar() {}

    private static LocalDate isoDate(String value, String label) {
        String text = value == null ? "" : value.trim();
        try {
            LocalDate parsed = LocalDate.parse(text);
            if (!parsed.toString().equals(text)) throw new DateTimeParseException("non-canonical", text, 0);
            return parsed;
        } catch (DateTimeParseException error) {
            throw new IllegalArgumentException(label + " must be YYYY-MM-DD", error);
        }
    }

    public static String state(String status, String dueDate, LocalDate today, int horizonDays) {
        String value = status == null ? "" : status.trim();
        if (!STATUSES.contains(value))
            throw new IllegalArgumentException("Unsupported crop task status: " + value);
        if (today == null) throw new IllegalArgumentException("today is required");
        if (horizonDays < 0) throw new IllegalArgumentException("horizon_days must be nonnegative");

        LocalDate due = isoDate(dueDate, "due_date");
        if (value.equals("completed") || value.equals("skipped")) return value;
        if (due.isBefore(today)) return "overdue";
        if (due.equals(today)) return "due_today";
        if (!due.isAfter(today.plusDays(horizonDays))) return "upcoming";
        return "pending";
    }

    public static String state(String status, String dueDate, LocalDate today) {
        return state(status, dueDate, today, 7);
    }

    public static Integer reminderSeverity(String status, String dueDate, LocalDate today, int horizonDays) {
        return switch (state(status, dueDate, today, horizonDays)) {
            case "overdue" -> 0;
            case "due_today" -> 1;
            case "upcoming" -> 2;
            default -> null;
        };
    }

    public static Integer reminderSeverity(String status, String dueDate, LocalDate today) {
        return reminderSeverity(status, dueDate, today, 7);
    }
}
