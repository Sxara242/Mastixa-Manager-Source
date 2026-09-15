package gr.mastixa.manager;

import android.app.*;
import android.content.Intent;
import android.view.*;
import android.widget.*;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import static org.junit.Assert.*;
import java.util.*;

public class ProfileFlowTest {
    private <T> List<T> views(View root,Class<T> type) {
        var result=new ArrayList<T>(); if(type.isInstance(root)) result.add(type.cast(root));
        if(root instanceof ViewGroup group) for(int i=0;i<group.getChildCount();i++) result.addAll(views(group.getChildAt(i),type));
        return result;
    }
    private void click(Activity activity,String text) {
        for(var button:views(activity.getWindow().getDecorView(),Button.class)) if(button.getText().toString().equals(text)) { button.performClick(); return; }
        fail("Missing button: "+text);
    }
    @Test public void firstSetupKeepsExistingDataThenLogoutAndSignIn() throws Exception {
        var instrumentation=InstrumentationRegistry.getInstrumentation(); var context=instrumentation.getTargetContext();
        assertTrue(context.getPackageName().endsWith(".checks"));
        context.deleteDatabase("profiles.db"); context.deleteDatabase("mastixa.db"); UserSession.profile=null;
        Activity welcome=null,main=null;
        try {
            try(var farm=new FarmStore(context)) { farm.addField("Existing field",2); }
            welcome=instrumentation.startActivitySync(new Intent(context,WelcomeActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK));
            var first=welcome;
            instrumentation.runOnMainSync(()->views(first.getWindow().getDecorView(),Spinner.class).get(0).setSelection(1));
            instrumentation.waitForIdleSync();
            var mainMonitor=instrumentation.addMonitor(MainActivity.class.getName(),null,false);
            instrumentation.runOnMainSync(()-> {
                var inputs=views(first.getWindow().getDecorView(),EditText.class); assertEquals(4,inputs.size());
                inputs.get(0).setText("Test owner"); inputs.get(1).setText("owner"); inputs.get(2).setText("TestOnly123!"); inputs.get(3).setText("TestOnly123!");
                click(first,"Create and sign in");
            });
            main=instrumentation.waitForMonitorWithTimeout(mainMonitor,20000); instrumentation.removeMonitor(mainMonitor); assertNotNull(main);
            assertEquals("en",UserSession.profile.language()); assertEquals("legacy",UserSession.profile.id());
            try(var farm=new FarmStore(context,UserSession.profile.database())) { assertEquals("Existing field",farm.fields().get(0).name()); }
            var screen=main;
            var loginMonitor=instrumentation.addMonitor(WelcomeActivity.class.getName(),null,false);
            instrumentation.runOnMainSync(()-> { click(screen,"Profile and language"); click(screen,"Sign out"); });
            welcome=instrumentation.waitForMonitorWithTimeout(loginMonitor,10000); instrumentation.removeMonitor(loginMonitor); assertNotNull(welcome); assertNull(UserSession.profile);
            var login=welcome;
            instrumentation.runOnMainSync(()-> {
                click(login,"New profile");
                assertEquals(4,views(login.getWindow().getDecorView(),EditText.class).size());
            });
            instrumentation.waitForIdleSync();
            // Invoke the Activity back path directly. A shell KEYCODE_BACK can be
            // consumed by focused/IME state on hosted emulators and leave the
            // create-profile form visible even though the app back behavior is sound.
            instrumentation.runOnMainSync(login::onBackPressed);
            instrumentation.waitForIdleSync();
            instrumentation.runOnMainSync(()-> {
                assertFalse(login.isFinishing());
                assertEquals(2,views(login.getWindow().getDecorView(),EditText.class).size());
            });
            mainMonitor=instrumentation.addMonitor(MainActivity.class.getName(),null,false);
            instrumentation.runOnMainSync(()-> {
                var inputs=views(login.getWindow().getDecorView(),EditText.class); assertEquals(2,inputs.size());
                inputs.get(0).setText("owner"); inputs.get(1).setText("TestOnly123!"); click(login,"Sign in");
            });
            main=instrumentation.waitForMonitorWithTimeout(mainMonitor,20000); instrumentation.removeMonitor(mainMonitor); assertNotNull(main);
            assertEquals("Test owner",UserSession.profile.name());
        } finally {
            Activity endMain=main,endWelcome=welcome;
            instrumentation.runOnMainSync(()-> { if(endMain!=null) endMain.finish(); if(endWelcome!=null) endWelcome.finish(); });
            instrumentation.waitForIdleSync(); UserSession.profile=null;
            context.deleteDatabase("profiles.db"); context.deleteDatabase("mastixa.db");
        }
    }
}
