package gr.mastixa.manager;

import android.app.Activity;
import android.content.Intent;
import android.os.SystemClock;
import android.view.*;
import android.widget.*;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import java.time.LocalDate;
import java.util.*;
import static org.junit.Assert.*;

public class Phase13CalendarUiTest {
    private List<View> views(View v){var result=new ArrayList<View>();result.add(v);if(v instanceof ViewGroup g)for(int i=0;i<g.getChildCount();i++)result.addAll(views(g.getChildAt(i)));return result;}
    private void click(String label){var roots=android.view.inspector.WindowInspector.getGlobalWindowViews();for(int i=roots.size()-1;i>=0;i--)for(var v:views(roots.get(i)))if(v instanceof Button b&&b.getText().toString().equals(label)){b.performClick();return;}fail("Missing button: "+label);}
    private void clickContaining(String text){var roots=android.view.inspector.WindowInspector.getGlobalWindowViews();for(int i=roots.size()-1;i>=0;i--)for(var v:views(roots.get(i)))if(v instanceof Button b&&b.getText().toString().contains(text)){b.performClick();return;}fail("Missing button containing: "+text);}
    private boolean hasText(String value){for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())for(var v:views(root))if(v instanceof TextView t&&t.getText().toString().equals(value))return true;return false;}
    private boolean hasButton(String value){for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())for(var v:views(root))if(v instanceof Button b&&b.getText().toString().equals(value))return true;return false;}
    private boolean hasButtonContaining(String value){for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())for(var v:views(root))if(v instanceof Button b&&b.getText().toString().contains(value))return true;return false;}
    private void waitForText(android.app.Instrumentation i,String value) throws Exception {
        long deadline=SystemClock.uptimeMillis()+5000;
        while(SystemClock.uptimeMillis()<deadline){
            boolean[] found={false};i.runOnMainSync(()->found[0]=hasText(value));if(found[0])return;
            i.waitForIdleSync();Thread.sleep(50);
        }
        fail("Missing text after activity transition: "+value);
    }
    private void waitForButton(android.app.Instrumentation i,String value) throws Exception {
        long deadline=SystemClock.uptimeMillis()+5000;
        while(SystemClock.uptimeMillis()<deadline){
            boolean[] found={false};i.runOnMainSync(()->found[0]=hasButton(value));if(found[0])return;
            i.waitForIdleSync();Thread.sleep(50);
        }
        fail("Missing button after activity transition: "+value);
    }
    private void waitForButtonContaining(android.app.Instrumentation i,String value) throws Exception {
        long deadline=SystemClock.uptimeMillis()+5000;
        while(SystemClock.uptimeMillis()<deadline){
            boolean[] found={false};i.runOnMainSync(()->found[0]=hasButtonContaining(value));if(found[0])return;
            i.waitForIdleSync();Thread.sleep(50);
        }
        fail("Missing button after activity transition containing: "+value);
    }
    private String createTodayTask(android.content.Context context, ProfileStore.Profile profile, String title) {
        LocalDate today=LocalDate.now();context.deleteDatabase(profile.database());
        try(var store=new FarmStore(context,profile.database())){
            store.addField("Αγρός Ημερολογίου",2.0);String field=store.fields().get(0).id();var programs=new CropProgramStore(store);
            programs.saveProgram("ui-calendar-program","Πρόγραμμα UI","Μαστίχα","",List.of(new CropProgram.Rule(
                "today",title,"inspection","fixed_date","UI note",today.getMonthValue(),today.getDayOfMonth(),null,null,null,null,null
            )));
            return programs.generateForField("ui-calendar-program",field,today.getYear()).get(0).generationKey();
        }
    }
    private void cleanup(android.app.Instrumentation i, Activity screen){i.runOnMainSync(()->{for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())if(root.getContext() instanceof Activity a&&!a.isFinishing())a.finish();if(screen!=null&&!screen.isFinishing())screen.finish();UserSession.clear();});i.waitForIdleSync();}

    @Test public void greekNavigationOpensUnifiedCalendarWithGreekMonthFilter() throws Exception {
        var i=InstrumentationRegistry.getInstrumentation();var context=i.getTargetContext();var profile=new ProfileStore.Profile("phase13b-calendar-ui","Ημερολόγιο UI","ui","el");Activity activity=null;
        try {
            createTodayTask(context,profile,"Έλεγχος ημερολογίου");
            i.runOnMainSync(()->{UserSession.clear();UserSession.signIn(profile);});
            activity=i.startActivitySync(new Intent(context,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));
            i.runOnMainSync(()->{click("Ενότητες");click("Ενιαίο Ημερολόγιο  ›");});
            waitForText(i,"Ενιαίο Ημερολόγιο");
            waitForText(i,"Έλεγχος ημερολογίου");
            waitForButton(i,"Μήνας: Όλοι οι μήνες");
            assertFalse(hasButton("Month: All months"));
        } finally {cleanup(i,activity);context.deleteDatabase(profile.database());}
    }

    @Test public void cropTaskAlertDeepLinksToFocusedCalendar() throws Exception {
        var i=InstrumentationRegistry.getInstrumentation();var context=i.getTargetContext();var profile=new ProfileStore.Profile("phase13b-alert-ui","Alerts UI","ui","el");Activity activity=null;
        try {
            createTodayTask(context,profile,"Έλεγχος ειδοποίησης");
            i.runOnMainSync(()->{UserSession.clear();UserSession.signIn(profile);});
            activity=i.startActivitySync(new Intent(context,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));
            i.runOnMainSync(()->click("Ειδοποιήσεις & Εκκρεμότητες"));
            waitForButtonContaining(i,"Έλεγχος ειδοποίησης");
            i.runOnMainSync(()->clickContaining("Έλεγχος ειδοποίησης"));
            waitForText(i,"Ενιαίο Ημερολόγιο");
            waitForText(i,"Έλεγχος ειδοποίησης");
            waitForButton(i,"Εμφάνιση όλων");
        } finally {cleanup(i,activity);context.deleteDatabase(profile.database());}
    }
}
