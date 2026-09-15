package gr.mastixa.manager;

import android.Manifest;
import android.app.Activity;
import android.app.AlarmManager;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import java.time.LocalDate;
import java.time.ZonedDateTime;
import java.util.*;

/** Phase 13 background reminders derived from crop tasks. No second task/status store is introduced. */
public final class CropTaskNotifications {
    static final String ACTION_CHECK = "gr.mastixa.manager.action.CROP_TASK_REMINDER_CHECK";
    static final String EXTRA_PROFILE_ID = "profile_id";
    static final String EXTRA_FOCUS_TASK = "focus_task";
    static final String CHANNEL_ID = "crop_task_reminders_v1";
    static final int PERMISSION_REQUEST = 1303;
    private static final String PREF_ENABLED = "crop_task_notifications_enabled";
    private static final String PREF_PROMPTED = "crop_task_notification_permission_prompted";
    private static final String PREF_TOKENS = "crop_task_notification_tokens";

    public record Reminder(
        String generationKey,
        String title,
        String fieldName,
        String dueDate,
        String state,
        int severity,
        String token
    ) {}

    private CropTaskNotifications() {}

    private static SharedPreferences prefs(Context context, ProfileStore.Profile profile) {
        return context.getSharedPreferences(profile.preferences(), Context.MODE_PRIVATE);
    }

    static boolean enabled(Context context, ProfileStore.Profile profile) {
        return prefs(context, profile).getBoolean(PREF_ENABLED, true);
    }

    static void setEnabled(Context context, ProfileStore.Profile profile, boolean enabled) {
        prefs(context, profile).edit().putBoolean(PREF_ENABLED, enabled).apply();
        if (enabled) { createChannel(context, profile); schedule(context, profile); } else cancel(context, profile);
    }

    public static void initialize(Context context) {
        scheduleAll(context);
    }

    static void createChannel(Context context, ProfileStore.Profile profile) {
        var manager = context.getSystemService(NotificationManager.class);
        if (manager == null) return;
        boolean english = profile.language().equals("en");
        var channel = new NotificationChannel(
            CHANNEL_ID,
            english ? "Crop tasks" : "Εργασίες καλλιέργειας",
            NotificationManager.IMPORTANCE_DEFAULT
        );
        channel.setDescription(english
            ? "Reminders for scheduled crop tasks."
            : "Υπενθυμίσεις για προγραμματισμένες εργασίες καλλιέργειας.");
        manager.createNotificationChannel(channel);
    }

    static long nextCheckMillis(ZonedDateTime now) {
        var next = now.withHour(8).withMinute(0).withSecond(0).withNano(0);
        if (!next.isAfter(now)) next = next.plusDays(1);
        return next.toInstant().toEpochMilli();
    }

    private static Intent alarmIntent(Context context, ProfileStore.Profile profile) {
        return new Intent(context, CropTaskNotificationReceiver.class)
            .setAction(ACTION_CHECK)
            .setData(Uri.parse("mastixa://crop-reminder/" + Uri.encode(profile.id())))
            .putExtra(EXTRA_PROFILE_ID, profile.id());
    }

    private static PendingIntent alarmPendingIntent(Context context, ProfileStore.Profile profile, int extraFlags) {
        return PendingIntent.getBroadcast(
            context,
            0,
            alarmIntent(context, profile),
            PendingIntent.FLAG_IMMUTABLE | extraFlags
        );
    }

    static void schedule(Context context, ProfileStore.Profile profile) {
        if (!enabled(context, profile)) { cancel(context, profile); return; }
        var manager = context.getSystemService(AlarmManager.class);
        if (manager == null) return;
        var pending = alarmPendingIntent(context, profile, PendingIntent.FLAG_UPDATE_CURRENT);
        manager.setAndAllowWhileIdle(
            AlarmManager.RTC_WAKEUP,
            nextCheckMillis(ZonedDateTime.now()),
            pending
        );
    }

    static void cancel(Context context, ProfileStore.Profile profile) {
        var manager = context.getSystemService(AlarmManager.class);
        var pending = alarmPendingIntent(context, profile, PendingIntent.FLAG_NO_CREATE);
        if (manager != null && pending != null) manager.cancel(pending);
        if (pending != null) pending.cancel();
    }

    static boolean hasScheduled(Context context, ProfileStore.Profile profile) {
        return alarmPendingIntent(context, profile, PendingIntent.FLAG_NO_CREATE) != null;
    }

    static void scheduleAll(Context context) {
        try (var profiles = new ProfileStore(context)) {
            for (var profile : profiles.profiles()) if (enabled(context, profile)) schedule(context, profile);
        } catch (RuntimeException ignored) {
            // A damaged profile registry must not prevent the app from starting.
        }
    }

    static List<Reminder> reminders(FarmStore store, boolean english, LocalDate today) {
        Objects.requireNonNull(store, "store");
        Objects.requireNonNull(today, "today");
        var fields = new HashMap<String,String>();
        for (var field : store.fields()) fields.put(field.id(), field.name());
        String historical = english ? "Historical field" : "Αγροτεμάχιο ιστορικού";
        var result = new ArrayList<Reminder>();
        for (var task : new CropProgramStore(store).tasks(null, null, null)) {
            Integer severity = TaskCalendar.reminderSeverity(task.status(), task.dueDate(), today);
            if (severity == null) continue;
            String state = TaskCalendar.state(task.status(), task.dueDate(), today);
            result.add(new Reminder(
                task.generationKey(),
                task.title(),
                fields.getOrDefault(task.fieldId(), historical),
                task.dueDate(),
                state,
                severity,
                task.generationKey() + "|" + state
            ));
        }
        result.sort(Comparator.comparingInt(Reminder::severity)
            .thenComparing(Reminder::dueDate)
            .thenComparing(Reminder::title)
            .thenComparing(Reminder::generationKey));
        return List.copyOf(result);
    }

    static List<Reminder> newlyRelevant(List<Reminder> current, Set<String> previousTokens) {
        Set<String> previous = previousTokens == null ? Set.of() : previousTokens;
        return current.stream().filter(r -> !previous.contains(r.token())).toList();
    }

    private static String stateLabel(String state, boolean english) {
        return switch (state) {
            case "overdue" -> english ? "Overdue" : "Εκπρόθεσμη";
            case "due_today" -> english ? "Due today" : "Σήμερα";
            default -> english ? "Within 7 days" : "Εντός 7 ημερών";
        };
    }

    private static boolean canPost(Context context) {
        return Build.VERSION.SDK_INT < 33 || context.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED;
    }

    static int deliver(Context context, ProfileStore.Profile profile, LocalDate today) {
        if (!enabled(context, profile) || !canPost(context)) return 0;
        createChannel(context, profile);
        List<Reminder> current;
        try (var store = new FarmStore(context, profile.database())) {
            current = reminders(store, profile.language().equals("en"), today);
        }
        var preferences = prefs(context, profile);
        var previous = new HashSet<>(preferences.getStringSet(PREF_TOKENS, Set.of()));
        var fresh = newlyRelevant(current, previous);
        var currentTokens = new HashSet<String>();
        for (var reminder : current) currentTokens.add(reminder.token());
        if (fresh.isEmpty()) {
            preferences.edit().putStringSet(PREF_TOKENS, currentTokens).apply();
            return 0;
        }

        boolean english = profile.language().equals("en");
        String title = profile.name() + " · " + (english ? "Crop task reminders" : "Υπενθυμίσεις εργασιών");
        String body;
        if (fresh.size() == 1) {
            var r = fresh.get(0);
            body = stateLabel(r.state(), english) + ": " + r.title() + " · " + r.fieldName();
        } else {
            body = english ? fresh.size() + " new crop task reminders" : fresh.size() + " νέες υπενθυμίσεις εργασιών";
        }

        Intent open = new Intent(context, NotificationOpenActivity.class)
            .setData(Uri.parse("mastixa://crop-notification/" + Uri.encode(profile.id())))
            .putExtra(EXTRA_PROFILE_ID, profile.id());
        if (fresh.size() == 1) open.putExtra(EXTRA_FOCUS_TASK, fresh.get(0).generationKey());
        var contentIntent = PendingIntent.getActivity(
            context,
            0,
            open,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );

        var builder = new Notification.Builder(context, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle(title)
            .setContentText(body)
            .setContentIntent(contentIntent)
            .setAutoCancel(true)
            .setCategory(Notification.CATEGORY_REMINDER)
            .setVisibility(Notification.VISIBILITY_PRIVATE)
            .setNumber(fresh.size());
        var inbox = new Notification.InboxStyle();
        inbox.setBigContentTitle(title);
        for (int index = 0; index < Math.min(5, fresh.size()); index++) {
            var r = fresh.get(index);
            inbox.addLine(stateLabel(r.state(), english) + " · " + r.title() + " · " + r.fieldName());
        }
        if (fresh.size() > 5) inbox.setSummaryText(english ? "+" + (fresh.size()-5) + " more" : "+" + (fresh.size()-5) + " ακόμη");
        builder.setStyle(inbox);

        var manager = context.getSystemService(NotificationManager.class);
        if (manager == null) return 0;
        try {
            manager.notify("crop-task-" + profile.id(), notificationId(profile), builder.build());
        } catch (SecurityException denied) {
            return 0;
        }
        preferences.edit().putStringSet(PREF_TOKENS, currentTokens).apply();
        return fresh.size();
    }

    static int notificationId(ProfileStore.Profile profile) {
        return 0x13000000 ^ profile.id().hashCode();
    }

    private static boolean hasPendingTasks(Context context, ProfileStore.Profile profile) {
        if (!context.getDatabasePath(profile.database()).exists()) return false;
        try (var store = new FarmStore(context, profile.database())) {
            for (var task : new CropProgramStore(store).tasks(null, null, null))
                if (task.status().equals("pending")) return true;
            return false;
        } catch (RuntimeException error) {
            return false;
        }
    }

    static void requestPermissionIfNeeded(Activity activity, ProfileStore.Profile profile) {
        if (Build.VERSION.SDK_INT < 33 || !enabled(activity, profile)) return;
        if (activity.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED) return;
        // Runtime instrumentation uses the checks application id; tests grant permission explicitly when they exercise delivery.
        if (activity.getPackageName().endsWith(".checks")) return;
        var preferences = prefs(activity, profile);
        if (preferences.getBoolean(PREF_PROMPTED, false) || !hasPendingTasks(activity, profile)) return;
        preferences.edit().putBoolean(PREF_PROMPTED, true).apply();
        activity.requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, PERMISSION_REQUEST);
    }
}
