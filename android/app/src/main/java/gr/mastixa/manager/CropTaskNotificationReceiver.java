package gr.mastixa.manager;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import java.time.LocalDate;

/** Receives the daily crop-task reminder alarm and reboot/time-change rescheduling broadcasts. */
public final class CropTaskNotificationReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context context, Intent intent) {
        String action = intent == null ? "" : String.valueOf(intent.getAction());
        if (!CropTaskNotifications.ACTION_CHECK.equals(action)) {
            CropTaskNotifications.scheduleAll(context);
            return;
        }

        String profileId = intent.getStringExtra(CropTaskNotifications.EXTRA_PROFILE_ID);
        if (profileId == null || profileId.isBlank()) return;
        var pending = goAsync();
        new Thread(() -> {
            ProfileStore.Profile profile = null;
            try (var profiles = new ProfileStore(context)) {
                profile = profiles.profiles().stream().filter(p -> p.id().equals(profileId)).findFirst().orElse(null);
                if (profile != null) CropTaskNotifications.deliver(context, profile, LocalDate.now());
            } catch (RuntimeException ignored) {
                // Background reminders must never crash the app process.
            } finally {
                if (profile != null) CropTaskNotifications.schedule(context, profile);
                pending.finish();
            }
        }, "crop-task-reminders").start();
    }
}
