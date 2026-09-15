package gr.mastixa.manager;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;

/** Security-aware notification router: deep-link only while the matching local session is still valid. */
public final class NotificationOpenActivity extends Activity {
    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        String expectedProfile = getIntent().getStringExtra(CropTaskNotifications.EXTRA_PROFILE_ID);
        String focusTask = getIntent().getStringExtra(CropTaskNotifications.EXTRA_FOCUS_TASK);
        boolean valid = expectedProfile != null
            && UserSession.valid(this)
            && UserSession.profile != null
            && expectedProfile.equals(UserSession.profile.id());

        Intent target;
        if (valid) {
            target = new Intent(this, UnifiedCalendarActivity.class);
            if (focusTask != null && !focusTask.isBlank()) target.putExtra("focus_task", focusTask);
        } else {
            target = new Intent(this, WelcomeActivity.class);
        }
        target.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        startActivity(target);
        finish();
    }
}
