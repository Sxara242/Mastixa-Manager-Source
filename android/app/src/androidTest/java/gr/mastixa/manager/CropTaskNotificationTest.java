package gr.mastixa.manager;

import android.Manifest;
import android.app.NotificationManager;
import android.content.ContentValues;
import android.os.Build;
import android.os.SystemClock;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import java.time.LocalDate;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.util.*;
import static org.junit.Assert.*;

public class CropTaskNotificationTest {
    private static void addTask(FarmStore store, String key, String field, LocalDate due, String status, String title) {
        new CropProgramStore(store);
        var row = new ContentValues();
        row.put("generation_key", key);
        row.put("program_id", "notify-program");
        row.put("rule_id", key + "-rule");
        row.put("field_id", field);
        row.put("season_year", due.getYear());
        row.put("due_date", due.toString());
        row.put("category", "inspection");
        row.put("title", title);
        row.put("notes", "");
        row.put("status", status);
        row.put("created_at", 1L);
        row.put("updated_at", 1L);
        store.getWritableDatabase().insertOrThrow("crop_tasks", null, row);
    }

    @Test public void reminderProjectionAndDeliveryAreDeduplicated() throws Exception {
        var instrumentation = InstrumentationRegistry.getInstrumentation();
        var context = instrumentation.getTargetContext();
        var profile = new ProfileStore.Profile("phase13c-notify", "Υπενθυμίσεις", "ui", "el");
        LocalDate today = LocalDate.now();
        context.deleteDatabase(profile.database());
        context.getSharedPreferences(profile.preferences(), android.content.Context.MODE_PRIVATE).edit().clear().commit();
        try {
            try (var store = new FarmStore(context, profile.database())) {
                store.addField("Αγρός ειδοποιήσεων", 2.0);
                String field = store.fields().get(0).id();
                addTask(store, "overdue", field, today.minusDays(1), "pending", "Εκπρόθεσμος έλεγχος");
                addTask(store, "today", field, today, "pending", "Σημερινός έλεγχος");
                addTask(store, "upcoming", field, today.plusDays(7), "pending", "Επόμενος έλεγχος");
                addTask(store, "far", field, today.plusDays(8), "pending", "Μακρινός έλεγχος");
                addTask(store, "done", field, today, "completed", "Ολοκληρωμένος έλεγχος");

                var reminders = CropTaskNotifications.reminders(store, false, today);
                assertEquals(3, reminders.size());
                assertEquals(List.of("overdue", "due_today", "upcoming"), reminders.stream().map(CropTaskNotifications.Reminder::state).toList());
                assertTrue(reminders.stream().allMatch(r -> r.fieldName().equals("Αγρός ειδοποιήσεων")));
                assertEquals(2, CropTaskNotifications.newlyRelevant(reminders, Set.of(reminders.get(0).token())).size());
            }

            if (Build.VERSION.SDK_INT >= 33)
                instrumentation.getUiAutomation().grantRuntimePermission(context.getPackageName(), Manifest.permission.POST_NOTIFICATIONS);
            var manager = context.getSystemService(NotificationManager.class);
            assertNotNull(manager);
            CropTaskNotifications.createChannel(context, profile);
            var channel = manager.getNotificationChannel(CropTaskNotifications.CHANNEL_ID);
            assertNotNull(channel);
            assertEquals("Εργασίες καλλιέργειας", channel.getName().toString());
            assertEquals("Υπενθυμίσεις για προγραμματισμένες εργασίες καλλιέργειας.", channel.getDescription());
            var englishProfile = new ProfileStore.Profile("phase13c-notify-en", "Reminders", "ui", "en");
            CropTaskNotifications.createChannel(context, englishProfile);
            channel = manager.getNotificationChannel(CropTaskNotifications.CHANNEL_ID);
            assertEquals("Crop tasks", channel.getName().toString());
            assertEquals("Reminders for scheduled crop tasks.", channel.getDescription());
            CropTaskNotifications.createChannel(context, profile);

            assertEquals(3, CropTaskNotifications.deliver(context, profile, today));
            assertEquals(0, CropTaskNotifications.deliver(context, profile, today));

            int expectedId = CropTaskNotifications.notificationId(profile);
            String expectedTag = "crop-task-" + profile.id();
            // NotificationManager publishes asynchronously; wait only for this notification.
            long deadline = SystemClock.elapsedRealtime() + 5_000;
            android.service.notification.StatusBarNotification[] active;
            boolean found;
            while (true) {
                active = manager.getActiveNotifications();
                found = Arrays.stream(active)
                    .anyMatch(n -> n.getId() == expectedId && expectedTag.equals(n.getTag()));
                long remaining = deadline - SystemClock.elapsedRealtime();
                if (found || remaining <= 0) break;
                Thread.sleep(Math.min(50, remaining));
            }
            assertTrue("Notification not active within 5000 ms; expected id=" + expectedId
                + ", tag=" + expectedTag + ", channel=" + CropTaskNotifications.CHANNEL_ID
                + "; actual=" + Arrays.stream(active).map(n -> "{id=" + n.getId()
                    + ", tag=" + n.getTag() + ", channel=" + n.getNotification().getChannelId() + "}").toList(), found);
            manager.cancel("crop-task-" + profile.id(), CropTaskNotifications.notificationId(profile));
        } finally {
            CropTaskNotifications.cancel(context, profile);
            context.deleteDatabase(profile.database());
            context.getSharedPreferences(profile.preferences(), android.content.Context.MODE_PRIVATE).edit().clear().commit();
        }
    }

    @Test public void dailyAlarmUsesNextLocalEightAndCanBeCancelled() {
        var context = InstrumentationRegistry.getInstrumentation().getTargetContext();
        var profile = new ProfileStore.Profile("phase13c-alarm", "Alarm", "ui", "en");
        var zone = ZoneId.of("Europe/Athens");
        var morning = ZonedDateTime.of(2026, 9, 12, 7, 30, 0, 0, zone);
        var eight = ZonedDateTime.of(2026, 9, 12, 8, 0, 0, 0, zone);
        assertEquals(eight.toInstant().toEpochMilli(), CropTaskNotifications.nextCheckMillis(morning));
        assertEquals(eight.plusDays(1).toInstant().toEpochMilli(), CropTaskNotifications.nextCheckMillis(eight));

        CropTaskNotifications.schedule(context, profile);
        assertTrue(CropTaskNotifications.hasScheduled(context, profile));
        CropTaskNotifications.cancel(context, profile);
        assertFalse(CropTaskNotifications.hasScheduled(context, profile));
    }
}
