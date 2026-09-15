package gr.mastixa.manager;

import java.time.LocalDate;
import java.util.*;

/** Pure deterministic crop-program rule engine. No database or Android runtime dependency. */
public final class CropProgram {
    public static final Set<String> CATEGORIES = Set.of(
        "irrigation", "fertilization", "cultivation", "plant_protection",
        "inspection", "pruning", "other"
    );
    public static final Set<String> SCHEDULES = Set.of("fixed_date", "interval_window");

    private CropProgram() {}

    public record Rule(
        String id,
        String title,
        String category,
        String scheduleKind,
        String notes,
        Integer month,
        Integer day,
        Integer startMonth,
        Integer startDay,
        Integer endMonth,
        Integer endDay,
        Integer everyDays
    ) {}

    public record Task(
        String generationKey,
        String programId,
        String ruleId,
        String fieldId,
        int seasonYear,
        String dueDate,
        String category,
        String title,
        String notes,
        String status
    ) {}

    private static String required(String value, String label) {
        String text = value == null ? "" : value.trim();
        if (text.isEmpty()) throw new IllegalArgumentException(label + " is required");
        return text;
    }

    private static void validateRule(Rule rule, int seasonYear) {
        required(rule.id(), "rule id");
        required(rule.title(), "rule title");
        if (!CATEGORIES.contains(rule.category()))
            throw new IllegalArgumentException("Unsupported crop-program category: " + rule.category());
        if (!SCHEDULES.contains(rule.scheduleKind()))
            throw new IllegalArgumentException("Unsupported crop-program schedule: " + rule.scheduleKind());

        if (rule.scheduleKind().equals("fixed_date")) {
            if (rule.month() == null || rule.day() == null)
                throw new IllegalArgumentException("fixed_date requires month and day");
            LocalDate.of(seasonYear, rule.month(), rule.day());
            return;
        }

        if (rule.startMonth() == null || rule.startDay() == null ||
            rule.endMonth() == null || rule.endDay() == null || rule.everyDays() == null)
            throw new IllegalArgumentException(
                "interval_window requires start/end month/day and every_days"
            );
        if (rule.everyDays() <= 0)
            throw new IllegalArgumentException("every_days must be positive");

        LocalDate start = LocalDate.of(seasonYear, rule.startMonth(), rule.startDay());
        LocalDate end = LocalDate.of(seasonYear, rule.endMonth(), rule.endDay());
        if (end.isBefore(start)) LocalDate.of(seasonYear + 1, rule.endMonth(), rule.endDay());
    }

    public static List<Task> generate(
        String programId,
        String fieldId,
        int seasonYear,
        List<Rule> rules
    ) {
        String program = required(programId, "program id");
        String field = required(fieldId, "field id");
        if (seasonYear < 1900 || seasonYear > 9998)
            throw new IllegalArgumentException("season_year is outside the supported range");
        Objects.requireNonNull(rules, "rules");

        Set<String> seen = new HashSet<>();
        List<Task> tasks = new ArrayList<>();

        for (Rule rule : rules) {
            Objects.requireNonNull(rule, "rule");
            validateRule(rule, seasonYear);
            if (!seen.add(rule.id()))
                throw new IllegalArgumentException("Duplicate crop-program rule id: " + rule.id());

            List<LocalDate> dates = new ArrayList<>();
            if (rule.scheduleKind().equals("fixed_date")) {
                dates.add(LocalDate.of(seasonYear, rule.month(), rule.day()));
            } else {
                LocalDate start = LocalDate.of(seasonYear, rule.startMonth(), rule.startDay());
                LocalDate end = LocalDate.of(seasonYear, rule.endMonth(), rule.endDay());
                if (end.isBefore(start))
                    end = LocalDate.of(seasonYear + 1, rule.endMonth(), rule.endDay());
                for (LocalDate current = start; !current.isAfter(end); current = current.plusDays(rule.everyDays()))
                    dates.add(current);
            }

            String notes = rule.notes() == null ? "" : rule.notes();
            for (LocalDate due : dates) {
                String dueDate = due.toString();
                tasks.add(new Task(
                    program + ":" + field + ":" + rule.id() + ":" + dueDate,
                    program,
                    rule.id(),
                    field,
                    seasonYear,
                    dueDate,
                    rule.category(),
                    rule.title(),
                    notes,
                    "pending"
                ));
            }
        }

        tasks.sort(Comparator.comparing(Task::dueDate).thenComparing(Task::ruleId));
        return List.copyOf(tasks);
    }
}
