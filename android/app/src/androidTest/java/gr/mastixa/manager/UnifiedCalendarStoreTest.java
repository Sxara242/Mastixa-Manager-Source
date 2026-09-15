package gr.mastixa.manager;

import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import java.time.LocalDate;
import java.util.List;
import static org.junit.Assert.*;

public class UnifiedCalendarStoreTest {
    @Test public void projectionFiltersHistoryAndCropTasksAndAlertsUseSameTaskState() {
        var context = InstrumentationRegistry.getInstrumentation().getTargetContext();
        var profile = new ProfileStore.Profile("phase13b-store","Phase 13B store","test","el");
        context.deleteDatabase(profile.database());
        LocalDate today = LocalDate.of(2026, 9, 12);

        try (var store = new FarmStore(context, profile.database())) {
            store.addField("Αγρός Α", 3.0);
            String fieldId = store.fields().get(0).id();

            new ActivityStore(store).save(new ActivityStore.Activity(
                null, today.minusDays(1).toString(), fieldId,
                "Πότισμα", "Ολοκληρώθηκε", 30, 5,
                "", 0, "", 0, "Tester", "Ιστορικό πότισμα",
                "", 0, 0, "", "", "", ""
            ));

            var programs = new CropProgramStore(store);
            programs.saveProgram(
                "calendar-program", "Πρόγραμμα ημερολογίου", "Μαστίχα", "",
                List.of(new CropProgram.Rule(
                    "today", "Έλεγχος σήμερα", "inspection", "fixed_date", "Σημείωση",
                    today.getMonthValue(), today.getDayOfMonth(),
                    null, null, null, null, null
                ))
            );
            var tasks = programs.generateForField("calendar-program", fieldId, today.getYear());
            assertEquals(1, tasks.size());

            var projection = new UnifiedCalendarStore(store, false);
            var all = projection.entries(today);
            assertEquals(2, all.size());
            assertTrue(all.stream().anyMatch(e -> e.source().equals("activity") && e.title().equals("Πότισμα")));
            assertTrue(all.stream().anyMatch(e -> e.source().equals("crop_task") && e.state().equals("due_today")));

            var filtered = UnifiedCalendarStore.filter(
                all, today.getYear(), today.getMonthValue(), fieldId, "crop_task", "έλεγχος"
            );
            assertEquals(1, filtered.size());
            assertEquals("Έλεγχος σήμερα", filtered.get(0).title());
            assertEquals("Αγρός Α", filtered.get(0).fieldName());

            var alerts = Phase13Alerts.alerts(store, false, today);
            var cropAlerts = alerts.stream().filter(a -> a.kind().equals("crop_task")).toList();
            assertEquals(1, cropAlerts.size());
            assertEquals(1, cropAlerts.get(0).severity());
            assertEquals(tasks.get(0).generationKey(), cropAlerts.get(0).recordId());
            assertTrue(cropAlerts.get(0).message().contains("Έλεγχος σήμερα"));

            programs.setTaskStatus(tasks.get(0).generationKey(), "completed");
            assertTrue(Phase13Alerts.alerts(store, false, today).stream().noneMatch(a -> a.kind().equals("crop_task")));
        } finally {
            context.deleteDatabase(profile.database());
        }
    }

    @Test public void englishProjectionUsesEnglishTaskStateLabels() {
        var context = InstrumentationRegistry.getInstrumentation().getTargetContext();
        var profile = new ProfileStore.Profile("phase13b-en-store","Phase 13B English","test","en");
        context.deleteDatabase(profile.database());
        LocalDate today = LocalDate.of(2026, 9, 12);
        try (var store = new FarmStore(context, profile.database())) {
            store.addField("Field A", 1.0);
            String fieldId = store.fields().get(0).id();
            var programs = new CropProgramStore(store);
            programs.saveProgram("p","Program","Crop","",List.of(new CropProgram.Rule(
                "r","Inspect","inspection","fixed_date","",
                today.getMonthValue(),today.getDayOfMonth(),null,null,null,null,null
            )));
            programs.generateForField("p",fieldId,today.getYear());
            var task = new UnifiedCalendarStore(store,true).entries(today).stream().filter(e->e.source().equals("crop_task")).findFirst().orElseThrow();
            assertTrue(task.detail().startsWith("Due today"));
            assertEquals("Crop Program", task.section());
        } finally {
            context.deleteDatabase(profile.database());
        }
    }
}
