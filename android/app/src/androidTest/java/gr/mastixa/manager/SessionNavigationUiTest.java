package gr.mastixa.manager;

import android.app.*;
import android.content.Intent;
import android.os.Bundle;
import android.view.*;
import android.widget.*;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import static org.junit.Assert.*;
import java.util.*;
import java.util.concurrent.atomic.*;

public class SessionNavigationUiTest {
    private List<View> views(View v){var result=new ArrayList<View>();result.add(v);if(v instanceof ViewGroup g)for(int n=0;n<g.getChildCount();n++)result.addAll(views(g.getChildAt(n)));return result;}
    private void click(Activity a,String label){for(var v:views(a.getWindow().getDecorView()))if(v instanceof Button b&&b.getText().toString().equals(label)){b.performClick();return;}fail("Missing action: "+label);}
    private boolean has(Activity a,String label){return views(a.getWindow().getDecorView()).stream().anyMatch(v->v instanceof TextView t&&t.getText().toString().equals(label));}
    private static final class Tracker implements Application.ActivityLifecycleCallbacks {
        final AtomicReference<Activity> resumed=new AtomicReference<>(),stopped=new AtomicReference<>();
        public void onActivityResumed(Activity a){resumed.set(a);} public void onActivityStopped(Activity a){stopped.set(a);} public void onActivityCreated(Activity a,Bundle b){} public void onActivityStarted(Activity a){} public void onActivityPaused(Activity a){} public void onActivitySaveInstanceState(Activity a,Bundle b){} public void onActivityDestroyed(Activity a){}
    }
    private void await(String message,java.util.function.BooleanSupplier condition) throws Exception {for(int n=0;n<200;n++){if(condition.getAsBoolean())return;Thread.sleep(100);}assertTrue(message,condition.getAsBoolean());}
    @Test public void launcherReturnKeepsFormThenExpires() throws Exception {
        var i=InstrumentationRegistry.getInstrumentation();var context=i.getTargetContext();assertTrue(context.getPackageName().endsWith(".checks"));var app=(Application)context.getApplicationContext();var tracker=new Tracker();app.registerActivityLifecycleCallbacks(tracker);var now=new AtomicLong(1_000_000);var oldClock=UserSession.clock;var profile=new ProfileStore.Profile("session-ui","Session UI","session","el");Activity main=null;
        try{
            i.runOnMainSync(()->{UserSession.clear();UserSession.clock=now::get;UserSession.signIn(profile);UserSession.setTimeoutMinutes(context,1);});
            main=i.startActivitySync(new Intent(context,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));var screen=main;
            i.runOnMainSync(()->{click(screen,"Ενότητες");click(screen,"Παραγωγός  ›");click(screen,"Επεξεργασία");});i.waitForIdleSync();
            var edit=new AtomicReference<EditText>();i.runOnMainSync(()->{for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())for(var v:views(root))if(v instanceof EditText e&&"Ονοματεπώνυμο / Επωνυμία".contentEquals(e.getContentDescription())){e.setText("Unsaved draft");edit.set(e);}});assertNotNull(edit.get());
            // Advance the fake clock only after Android has actually delivered onActivityStopped.
            tracker.stopped.set(null);i.runOnMainSync(()->screen.moveTaskToBack(true));await("MainActivity did not enter the background",()->tracker.stopped.get()==screen);i.waitForIdleSync();now.addAndGet(30_000);tracker.resumed.set(null);
            i.runOnMainSync(()->context.startActivity(new Intent(context,WelcomeActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)));
            await("Valid session did not return to the existing MainActivity",()->tracker.resumed.get()==screen);i.waitForIdleSync();assertSame(profile,UserSession.profile);i.runOnMainSync(()->assertEquals("Unsaved draft",edit.get().getText().toString()));assertFalse(screen.isFinishing());
            // A second confirmed background stay reaches the configured minute and must show sign-in.
            tracker.stopped.set(null);i.runOnMainSync(()->screen.moveTaskToBack(true));await("MainActivity did not enter the background a second time",()->tracker.stopped.get()==screen);i.waitForIdleSync();now.addAndGet(60_000);tracker.resumed.set(null);
            i.runOnMainSync(()->context.startActivity(new Intent(context,WelcomeActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)));
            await("Expired session did not remain on WelcomeActivity",()->tracker.resumed.get() instanceof WelcomeActivity);assertNull(UserSession.profile);
        }finally{var screen=main;i.runOnMainSync(()->{var top=tracker.resumed.get();if(top!=null)top.finish();if(screen!=null)screen.finish();UserSession.clear();UserSession.clock=oldClock;});app.unregisterActivityLifecycleCallbacks(tracker);context.getSharedPreferences(profile.preferences(),0).edit().clear().commit();}
    }
    @Test public void backHistoryScrollRecreationAndLinkedInventory() throws Exception {
        var i=InstrumentationRegistry.getInstrumentation();var context=i.getTargetContext();var profile=new ProfileStore.Profile("navigation-ui","Navigation UI","navigation","el");context.deleteDatabase(profile.database());var app=(Application)context.getApplicationContext();var tracker=new Tracker();app.registerActivityLifecycleCallbacks(tracker);Activity main=null;
        try{
            try(var store=new FarmStore(context,profile.database());var in=i.getContext().getAssets().open("windows-money.zip")){CatalogImport.apply(store,CatalogImport.read(in),new java.io.File(context.getCacheDir(),"navigation-before.json"));}
            context.getSharedPreferences(profile.preferences(),0).edit().putStringSet("shortcuts",Set.of("Παραγωγός")).commit();i.runOnMainSync(()->{UserSession.clear();UserSession.signIn(profile);});
            main=i.startActivitySync(new Intent(context,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));var screen=main;
            i.runOnMainSync(()->{click(screen,"Παραγωγός  ›");assertTrue(has(screen,"‹ Πίσω"));click(screen,"‹ Πίσω");assertTrue(has(screen,"Η εκμετάλλευσή μου"));click(screen,"Ενότητες");});i.waitForIdleSync();
            i.runOnMainSync(()->{for(var v:views(screen.getWindow().getDecorView()))if(v instanceof ScrollView s)s.scrollTo(0,400);});i.waitForIdleSync();
            i.runOnMainSync(()->click(screen,"Έξοδα  ›"));i.waitForIdleSync();
            i.runOnMainSync(()->screen.onBackPressed());i.waitForIdleSync();i.runOnMainSync(()->{assertTrue(has(screen,"Όλες οι ενότητες"));assertTrue(views(screen.getWindow().getDecorView()).stream().anyMatch(v->v instanceof ScrollView s&&s.getScrollY()>0));click(screen,"Γενικές Ρυθμίσεις  ›");click(screen,"Διαχείριση δεδομένων");});i.waitForIdleSync();
            tracker.resumed.set(null);i.runOnMainSync(screen::recreate);await("MainActivity recreation did not resume",()->tracker.resumed.get() instanceof MainActivity&&tracker.resumed.get()!=screen);var recreated=tracker.resumed.get();main=recreated;i.waitForIdleSync();
            i.runOnMainSync(()->{assertTrue(has(recreated,"Διαχείριση δεδομένων"));click(recreated,"‹ Πίσω");assertTrue(has(recreated,"Γενικές Ρυθμίσεις"));click(recreated,"‹ Πίσω");assertTrue(has(recreated,"Όλες οι ενότητες"));click(recreated,"Αποθήκη & Εφόδια  ›");click(recreated,"Στοιχεία και κινήσεις");click(recreated,"‹ Πίσω");assertTrue(has(recreated,"+ Νέο είδος"));click(recreated,"‹ Πίσω");assertTrue(has(recreated,"Όλες οι ενότητες"));click(recreated,"Παραγωγός  ›");});i.waitForIdleSync();Thread.sleep(500);
            try(var out=new java.io.FileOutputStream(new java.io.File(context.getExternalFilesDir(null),"back-navigation-ui.png"))){i.getUiAutomation().takeScreenshot().compress(android.graphics.Bitmap.CompressFormat.PNG,100,out);}
        }finally{var screen=main;i.runOnMainSync(()->{if(screen!=null)screen.finish();UserSession.clear();});app.unregisterActivityLifecycleCallbacks(tracker);}
    }
}
