package gr.mastixa.manager;

import android.app.Activity;
import android.content.Intent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import java.time.LocalDate;
import java.util.List;
import static org.junit.Assert.*;

/** Display-only localization; every fixture belongs to the isolated checks app. */
public class CalendarActivityLocalizationTest {
    private final android.app.Instrumentation instrumentation = InstrumentationRegistry.getInstrumentation();
    private final android.content.Context context = instrumentation.getTargetContext();
    private static final LocalDate DAY = LocalDate.of(2026, 9, 26);
    private static final String USER_TEXT = "Πότισμα / Προγραμματισμένη — user text";

    private ProfileStore.Profile profile(String suffix, String language) {
        assertTrue(context.getPackageName().endsWith(".checks"));
        return new ProfileStore.Profile("calendar-localization-" + suffix, "QA", "qa", language);
    }

    private String seed(FarmStore store, String category, String status) {
        if (store.fields().isEmpty()) store.addField(USER_TEXT, 1);
        return new ActivityStore(store).save(new ActivityStore.Activity(
            null, DAY.toString(), store.fields().get(0).id(), category, status,
            30, 5, USER_TEXT, 2, "kg", 0, USER_TEXT, USER_TEXT,
            "", 0, 0, "", USER_TEXT, "", ""
        ));
    }

    @Test public void allCanonicalLabelsSwitchWithoutChangingSnapshot() throws Exception {
        var base = profile("values", "el");
        context.deleteDatabase(base.database());
        try (var store = new FarmStore(context, base.database())) {
            String[] categories = {"Πότισμα", "Λίπανση"};
            String[] statuses = {"Προγραμματισμένη", "Ολοκληρώθηκε", "Ακυρώθηκε"};
            String[] englishCategories = {"Irrigation", "Fertilization"};
            String[] englishStatuses = {"Planned", "Completed", "Cancelled"};
            for (String category : categories) for (String status : statuses) seed(store, category, status);
            var originals = new ActivityStore(store).activities();
            byte[] before = LocalBackup.snapshot(store);
            for (String language : List.of("el", "en", "el", "en")) {
                var active = profile("values", language);
                var entries = new UnifiedCalendarStore(store, active.language().equals("en")).entries(DAY);
                assertEquals(6, entries.size());
                for (var original : originals) {
                    var row = entries.stream().filter(e -> e.recordId().equals(original.id())).findFirst().orElseThrow();
                    int category = List.of(categories).indexOf(original.category());
                    int status = List.of(statuses).indexOf(original.status());
                    assertEquals(language.equals("en") ? englishCategories[category] : categories[category], row.title());
                    assertTrue(row.detail(), row.detail().startsWith((language.equals("en") ? englishStatuses[status] : statuses[status]) + " · "));
                    assertTrue(row.detail().contains(USER_TEXT));
                    assertEquals(USER_TEXT, row.fieldName());
                    assertEquals(original.fieldId(), row.fieldId());
                    assertEquals(original.date(), row.date());
                    assertEquals("activity", row.source());
                    assertEquals("", row.state());
                }
                assertEquals(originals, new ActivityStore(store).activities());
                assertArrayEquals(before, LocalBackup.snapshot(store));
            }
        } finally { context.deleteDatabase(base.database()); }
    }

    @Test public void unknownLegacyValuesRemainVerbatimInBothLanguages() throws Exception {
        var base = profile("legacy", "el");
        context.deleteDatabase(base.database());
        try (var store = new FarmStore(context, base.database())) {
            String id = seed(store, "Πότισμα", "Προγραμματισμένη");
            // Simulate historical values without changing the current validation contract.
            for (String unknown : List.of("Legacy / παλιά τιμή", "Πότισμα legacy", "", "  custom  ")) {
                store.getWritableDatabase().execSQL("UPDATE farm_activities SET category=?,status=? WHERE id=?", new Object[]{unknown, unknown, id});
                var originals = new ActivityStore(store).activities();
                byte[] before = LocalBackup.snapshot(store);
                for (boolean english : List.of(false, true, false)) {
                    var row = new UnifiedCalendarStore(store, english).entries(DAY).get(0);
                    assertEquals(unknown, row.title());
                    assertTrue(row.detail().startsWith(unknown + " · "));
                    assertEquals(id, row.recordId());
                    assertEquals(originals, new ActivityStore(store).activities());
                    assertArrayEquals(before, LocalBackup.snapshot(store));
                }
            }
        } finally { context.deleteDatabase(base.database()); }
    }

    private boolean hasText(View view, String text) {
        if (view instanceof TextView label && label.getText().toString().equals(text)) return true;
        if (view instanceof ViewGroup group) for (int n = 0; n < group.getChildCount(); n++)
            if (hasText(group.getChildAt(n), text)) return true;
        return false;
    }

    @Test public void calendarCardsFollowProfileLanguageAcrossReopen() throws Exception {
        var base = profile("cards", "el");
        context.deleteDatabase(base.database());
        try (var store = new FarmStore(context, base.database())) {
            seed(store, "Πότισμα", "Προγραμματισμένη");
            byte[] before = LocalBackup.snapshot(store);
            for (String language : List.of("el", "en", "el")) {
                var active = profile("cards", language);
                instrumentation.runOnMainSync(() -> { UserSession.clear(); UserSession.signIn(active); });
                Activity screen = instrumentation.startActivitySync(new Intent(context, UnifiedCalendarActivity.class)
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK));
                try {
                    instrumentation.waitForIdleSync();
                    var expected = new UnifiedCalendarStore(store, language.equals("en")).entries(DAY).get(0);
                    instrumentation.runOnMainSync(() -> {
                        View root = screen.getWindow().getDecorView();
                        assertTrue(hasText(root, language.equals("en") ? "Irrigation" : "Πότισμα"));
                        assertTrue(hasText(root, expected.detail()));
                        assertTrue(hasText(root, USER_TEXT));
                    });
                    assertArrayEquals(before, LocalBackup.snapshot(store));
                } finally {
                    instrumentation.runOnMainSync(screen::finish);
                    instrumentation.waitForIdleSync();
                    instrumentation.runOnMainSync(UserSession::clear);
                }
            }
        } finally { context.deleteDatabase(base.database()); }
    }
}
