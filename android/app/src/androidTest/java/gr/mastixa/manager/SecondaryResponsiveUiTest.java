package gr.mastixa.manager;

import android.app.Activity;
import android.content.Intent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import java.util.ArrayList;
import java.util.List;
import static org.junit.Assert.*;

public class SecondaryResponsiveUiTest {
    @Test public void secondaryBackButtonsGrowWithScaledText() throws Exception {
        var instrumentation = InstrumentationRegistry.getInstrumentation();
        var context = instrumentation.getTargetContext();
        var profile = new ProfileStore.Profile("secondary-responsive-ui","Responsive UI","ui","el");
        context.deleteDatabase(profile.database());
        try {
            instrumentation.runOnMainSync(() -> { UserSession.clear(); UserSession.signIn(profile); });
            assertResponsiveBackButton(CropProgramActivity.class);
            assertResponsiveBackButton(UnifiedCalendarActivity.class);
            assertResponsiveBackButton(PlantTrackingActivity.class);
            assertResponsiveBackButton(SensorDataActivity.class);
        } finally {
            instrumentation.runOnMainSync(UserSession::clear);
            instrumentation.waitForIdleSync();
        }
    }

    private void assertResponsiveBackButton(Class<? extends Activity> type) {
        var instrumentation = InstrumentationRegistry.getInstrumentation();
        var context = instrumentation.getTargetContext();
        Activity activity = instrumentation.startActivitySync(new Intent(context,type)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK));
        instrumentation.waitForIdleSync();
        try {
            instrumentation.runOnMainSync(() -> {
                var back = button(activity.getWindow().getDecorView(),"‹ Πίσω");
                assertEquals("Back button should grow with scaled text in " + type.getSimpleName(),
                    ViewGroup.LayoutParams.WRAP_CONTENT, back.getLayoutParams().height);
                assertTrue("Back button minimum touch height in " + type.getSimpleName(),
                    back.getMinHeight() >= dp(activity,48));
            });
        } finally {
            instrumentation.runOnMainSync(activity::finish);
            instrumentation.waitForIdleSync();
        }
    }

    private int dp(Activity activity,int value) {
        return (int)(activity.getResources().getDisplayMetrics().density * value);
    }

    private Button button(View root,String label) {
        for (var view : views(root))
            if (view instanceof Button button && label.contentEquals(button.getText())) return button;
        fail("Missing button: " + label);
        return null;
    }

    private List<View> views(View root) {
        var result = new ArrayList<View>();
        result.add(root);
        if (root instanceof ViewGroup group)
            for (int i=0;i<group.getChildCount();i++) result.addAll(views(group.getChildAt(i)));
        return result;
    }
}
