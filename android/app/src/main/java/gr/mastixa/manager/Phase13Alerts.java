package gr.mastixa.manager;

import java.time.LocalDate;
import java.util.*;

/** Adds crop-program task reminders to the existing derived in-app alert stream without persisting a second queue. */
public final class Phase13Alerts {
    private Phase13Alerts() {}

    public static List<DashboardStore.Alert> alerts(FarmStore store, boolean english, LocalDate today) {
        Objects.requireNonNull(store, "store");
        Objects.requireNonNull(today, "today");
        var result = new ArrayList<>(new DashboardStore(store, english).alerts(today));
        var fields = new HashMap<String,String>();
        for (var field : store.fields()) fields.put(field.id(), field.name());
        String historical = english ? "Historical field" : "Αγροτεμάχιο ιστορικού";

        for (var task : new CropProgramStore(store).tasks(null, null, null)) {
            Integer severity = TaskCalendar.reminderSeverity(task.status(), task.dueDate(), today);
            if (severity == null) continue;
            String prefix = switch (severity) {
                case 0 -> english ? "Overdue crop task: " : "Εκπρόθεσμη εργασία προγράμματος: ";
                case 1 -> english ? "Crop task due today: " : "Εργασία προγράμματος για σήμερα: ";
                default -> english ? "Crop task within 7 days: " : "Εργασία προγράμματος εντός 7 ημερών: ";
            };
            result.add(new DashboardStore.Alert(
                "crop_task:" + task.generationKey(),
                "crop_task",
                task.generationKey(),
                severity,
                task.dueDate(),
                fields.getOrDefault(task.fieldId(), historical),
                prefix + task.title() + (task.notes().isBlank() ? "" : " · " + task.notes())
            ));
        }

        result.sort(Comparator.comparingInt(DashboardStore.Alert::severity)
            .thenComparing(a -> a.date().isEmpty() ? "9999-12-31" : a.date())
            .thenComparing(DashboardStore.Alert::subject)
            .thenComparing(DashboardStore.Alert::id));
        return List.copyOf(result);
    }
}
