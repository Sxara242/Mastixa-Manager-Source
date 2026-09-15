package gr.mastixa.manager;

import android.app.Activity;
import android.content.Intent;
import android.os.SystemClock;
import android.view.*;
import android.widget.*;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import static org.junit.Assert.*;
import java.util.*;

public class CropProgramUiTest {
    private List<View> views(View v){var result=new ArrayList<View>();result.add(v);if(v instanceof ViewGroup g)for(int i=0;i<g.getChildCount();i++)result.addAll(views(g.getChildAt(i)));return result;}
    private void click(String label){var roots=android.view.inspector.WindowInspector.getGlobalWindowViews();for(int i=roots.size()-1;i>=0;i--)for(var v:views(roots.get(i)))if(v instanceof Button b&&b.getText().toString().equals(label)){b.performClick();return;}fail("Missing button: "+label);}
    private void fill(String label,String value){for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())for(var v:views(root))if(v instanceof EditText e&&label.contentEquals(e.getContentDescription())){e.setText(value);return;}fail("Missing input: "+label);}
    private boolean hasButton(String value){for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())for(var v:views(root))if(v instanceof Button b&&b.getText().toString().equals(value))return true;return false;}
    private boolean hasText(String value){for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())for(var v:views(root))if(v instanceof TextView t&&t.getText().toString().equals(value))return true;return false;}
    private boolean hasTextContaining(String value){for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())for(var v:views(root))if(v instanceof TextView t&&t.getText().toString().contains(value))return true;return false;}
    private void waitForButton(android.app.Instrumentation i,String value) throws Exception {
        long deadline=SystemClock.uptimeMillis()+5000;
        while(SystemClock.uptimeMillis()<deadline){
            boolean[] found={false};i.runOnMainSync(()->found[0]=hasButton(value));if(found[0])return;
            i.waitForIdleSync();Thread.sleep(50);
        }
        fail("Missing button after activity transition: "+value);
    }
    private void waitForText(android.app.Instrumentation i,String value) throws Exception {
        long deadline=SystemClock.uptimeMillis()+5000;
        while(SystemClock.uptimeMillis()<deadline){
            boolean[] found={false};i.runOnMainSync(()->found[0]=hasText(value));if(found[0])return;
            i.waitForIdleSync();Thread.sleep(50);
        }
        fail("Missing text after activity transition: "+value);
    }
    private void cleanup(android.app.Instrumentation i, Activity screen){
        i.runOnMainSync(()->{for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())if(root.getContext() instanceof Activity a&&!a.isFinishing())a.finish();if(screen!=null&&!screen.isFinishing())screen.finish();UserSession.clear();});
        i.waitForIdleSync();
    }

    @Test public void greekUiCreatesProgramRuleAndGeneratedTask() throws Exception {
        var i=InstrumentationRegistry.getInstrumentation();var context=i.getTargetContext();var profile=new ProfileStore.Profile("crop-program-ui","Πρόγραμμα δοκιμής","ui","el");context.deleteDatabase(profile.database());Activity activity=null;
        try {
            try(var store=new FarmStore(context,profile.database())){store.addField("Αγρός Α",2.0);}
            i.runOnMainSync(()->{UserSession.clear();UserSession.signIn(profile);});
            activity=i.startActivitySync(new Intent(context,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));
            i.runOnMainSync(()->{click("Ενότητες");click("Πρόγραμμα Καλλιέργειας  ›");});
            waitForButton(i,"+ Νέο πρόγραμμα");
            i.runOnMainSync(()->click("+ Νέο πρόγραμμα"));i.waitForIdleSync();
            i.runOnMainSync(()->{fill("Όνομα προγράμματος *","Πρόγραμμα Α");fill("Καλλιέργεια","Μαστίχα");fill("Περιγραφή","Δοκιμαστικό πρόγραμμα");click("Αποθήκευση");});i.waitForIdleSync();
            i.runOnMainSync(()->click("Κανόνες: 0"));i.waitForIdleSync();i.runOnMainSync(()->click("+ Νέος κανόνας"));i.waitForIdleSync();
            i.runOnMainSync(()->{fill("Τίτλος εργασίας *","Πότισμα δοκιμής");fill("Ημερομηνία (DD/MM) *","15/05");click("Αποθήκευση");});i.waitForIdleSync();
            i.runOnMainSync(()->click("Ανάθεση / Δημιουργία εργασιών"));i.waitForIdleSync();
            i.runOnMainSync(()->{fill("Έτος καλλιεργητικής περιόδου *","2026");click("Αποθήκευση");});i.waitForIdleSync();
            try(var store=new FarmStore(context,profile.database())){
                try(var programs=store.getReadableDatabase().rawQuery("SELECT COUNT(*) FROM crop_programs WHERE active=1",null)){assertTrue(programs.moveToFirst());assertEquals(1,programs.getInt(0));}
                try(var rules=store.getReadableDatabase().rawQuery("SELECT COUNT(*) FROM crop_program_rules",null)){assertTrue(rules.moveToFirst());assertEquals(1,rules.getInt(0));}
                var tasks=new CropProgramStore(store).tasks(null,null,null);assertEquals(1,tasks.size());assertEquals("2026-05-15",tasks.get(0).dueDate());assertEquals("pending",tasks.get(0).status());
            }
        } finally {cleanup(i,activity);}
    }

    @Test public void englishNavigationExposesCropProgramPage() throws Exception {
        var i=InstrumentationRegistry.getInstrumentation();var context=i.getTargetContext();var profile=new ProfileStore.Profile("crop-program-en-ui","Crop program","ui","en");context.deleteDatabase(profile.database());Activity activity=null;
        try {
            i.runOnMainSync(()->{UserSession.clear();UserSession.signIn(profile);});
            activity=i.startActivitySync(new Intent(context,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));
            i.runOnMainSync(()->{click("Sections");click("Crop Program  ›");});
            waitForText(i,"Crop Program");
        } finally {cleanup(i,activity);}
    }

    @Test public void invalidProgramUsesCanonicalLocalizedValidationMessage() throws Exception {
        assertInvalidProgramMessage("el","+ Νέο πρόγραμμα","Αποθήκευση","Έλεγξε τα υποχρεωτικά πεδία και τις ημερομηνίες.");
        assertInvalidProgramMessage("en","+ New program","Save","Check the required fields and dates.");
    }

    private void assertInvalidProgramMessage(String language,String createLabel,String saveLabel,String expected) throws Exception {
        var i=InstrumentationRegistry.getInstrumentation();var context=i.getTargetContext();var profile=new ProfileStore.Profile("crop-program-invalid-"+language,"Validation "+language,"ui",language);context.deleteDatabase(profile.database());Activity activity=null;
        try {
            i.runOnMainSync(()->{UserSession.clear();UserSession.signIn(profile);});
            activity=i.startActivitySync(new Intent(context,CropProgramActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));
            waitForButton(i,createLabel);
            i.runOnMainSync(()->click(createLabel));i.waitForIdleSync();
            waitForButton(i,saveLabel);
            i.runOnMainSync(()->click(saveLabel));
            waitForText(i,expected);
            i.runOnMainSync(()->assertFalse("Raw backend validation leaked into UI",hasTextContaining("program name is required")));
        } finally {cleanup(i,activity);context.deleteDatabase(profile.database());}
    }
}
