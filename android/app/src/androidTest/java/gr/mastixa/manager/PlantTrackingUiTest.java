package gr.mastixa.manager;

import android.app.Activity;
import android.content.Intent;
import android.os.SystemClock;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import java.util.*;
import static org.junit.Assert.*;

public class PlantTrackingUiTest {
    private List<View> views(View v){var result=new ArrayList<View>();result.add(v);if(v instanceof ViewGroup g)for(int i=0;i<g.getChildCount();i++)result.addAll(views(g.getChildAt(i)));return result;}
    private boolean hasText(String value){for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())for(var v:views(root))if(v instanceof TextView t&&t.getText().toString().equals(value))return true;return false;}
    private boolean hasTextContaining(String value){for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())for(var v:views(root))if(v instanceof TextView t&&t.getText().toString().contains(value))return true;return false;}
    private boolean hasButtonContaining(String value){for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())for(var v:views(root))if(v instanceof Button b&&b.getText().toString().contains(value))return true;return false;}
    private void clickContaining(String value){for(var roots=android.view.inspector.WindowInspector.getGlobalWindowViews();!roots.isEmpty();){for(int i=roots.size()-1;i>=0;i--)for(var v:views(roots.get(i)))if(v instanceof Button b&&b.getText().toString().contains(value)){b.performClick();return;}break;}fail("Missing button containing: "+value);}
    private void fill(String label,String value){for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())for(var v:views(root))if(v instanceof EditText e&&label.contentEquals(e.getContentDescription())){e.setText(value);return;}fail("Missing input: "+label);}
    private void waitFor(android.app.Instrumentation i, java.util.function.BooleanSupplier condition, String label) throws Exception {long deadline=SystemClock.uptimeMillis()+5000;while(SystemClock.uptimeMillis()<deadline){boolean[] found={false};i.runOnMainSync(()->found[0]=condition.getAsBoolean());if(found[0])return;i.waitForIdleSync();Thread.sleep(50);}fail("Missing UI: "+label);}
    private void cleanup(android.app.Instrumentation i, Activity screen){i.runOnMainSync(()->{for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())if(root.getContext() instanceof Activity a&&!a.isFinishing())a.finish();if(screen!=null&&!screen.isFinishing())screen.finish();UserSession.clear();});i.waitForIdleSync();}

    @Test public void greekUiRendersProjectedPlantHistoryAndDetails() throws Exception {
        var i=InstrumentationRegistry.getInstrumentation();var context=i.getTargetContext();var profile=new ProfileStore.Profile("phase14d-plant-ui","Plant UI","ui","el");Activity activity=null;
        try {
            context.deleteDatabase(profile.database());
            try(var db=new FarmStore(context,profile.database())){db.addField("Αγρός UI",2.0);String field=db.fields().get(0).id();var registry=new PlantTrackingStore(db);registry.savePlant(new PlantTracking.Plant("ui-plant",field,"","Δέντρο 17","2026-02-10","Μαστίχα",38.3672,26.1358,"active","good","UI plant"));registry.appendEvent(new PlantTracking.Event("ui-event","ui-plant","2026-09-10","health","watch","Έλεγχος"));}
            i.runOnMainSync(()->{UserSession.clear();UserSession.signIn(profile);});
            activity=i.startActivitySync(new Intent(context,PlantTrackingActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));
            waitFor(i,()->hasText("Μεμονωμένα Φυτά / Δέντρα"),"page title");waitFor(i,()->hasButtonContaining("Δέντρο 17"),"projected plant card");
            i.runOnMainSync(()->clickContaining("Δέντρο 17"));waitFor(i,()->hasText("Δέντρο 17"),"details title");waitFor(i,()->hasTextContaining("Υγεία · Παρακολούθηση"),"localized event value");
            i.runOnMainSync(()->{assertFalse("Internal health value leaked into Greek history",hasTextContaining("Υγεία · watch"));assertTrue("User-entered event note must remain unchanged",hasTextContaining("Έλεγχος"));});
            waitFor(i,()->hasButtonContaining("Συμβάν"),"event action");
        } finally {cleanup(i,activity);context.deleteDatabase(profile.database());}
    }

    @Test public void plantFormAxesAndValidationFollowSelectedLanguage() throws Exception {
        assertPlantFormLocalization("el","+ Νέο φυτό","Γεωγραφικό πλάτος (WGS84)","Γεωγραφικό μήκος (WGS84)","Ημερομηνία φύτευσης (YYYY-MM-DD, προαιρετικό)","Αποθήκευση","Εντάξει","Οι συντεταγμένες πρέπει να είναι αριθμοί.","Έλεγξε τα στοιχεία.");
        assertPlantFormLocalization("en","+ New plant","Latitude (WGS84)","Longitude (WGS84)","Planting date (YYYY-MM-DD, optional)","Save","OK","Coordinates must be numeric.","Check the entered values.");
    }

    private void assertPlantFormLocalization(String language,String create,String latitudeLabel,String longitudeLabel,String dateLabel,String save,String ok,String numericError,String backendError) throws Exception {
        var i=InstrumentationRegistry.getInstrumentation();var context=i.getTargetContext();var profile=new ProfileStore.Profile("phase14d-plant-localization-"+language,"Plant "+language,"ui",language);Activity activity=null;
        try {
            context.deleteDatabase(profile.database());try(var db=new FarmStore(context,profile.database())){db.addField("Watch Field",1.0);}
            i.runOnMainSync(()->{UserSession.clear();UserSession.signIn(profile);});activity=i.startActivitySync(new Intent(context,PlantTrackingActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));
            waitFor(i,()->hasButtonContaining(create),"new plant action");i.runOnMainSync(()->clickContaining(create));i.waitForIdleSync();waitFor(i,()->hasText(latitudeLabel)&&hasText(longitudeLabel),"localized coordinate captions");
            i.runOnMainSync(()->{fill(latitudeLabel,"not-a-number");clickContaining(save);});waitFor(i,()->hasText(numericError),"localized coordinate validation");i.runOnMainSync(()->clickContaining(ok));i.waitForIdleSync();
            i.runOnMainSync(()->{fill(latitudeLabel,"");fill(dateLabel,"2026-99-99");clickContaining(save);});waitFor(i,()->hasText(backendError),"canonical backend validation");
            i.runOnMainSync(()->{assertFalse("Raw backend date validation leaked into UI",hasTextContaining("planted_date must be YYYY-MM-DD"));assertTrue("User field name must remain unchanged",hasTextContaining("Watch Field"));});
        } finally {cleanup(i,activity);context.deleteDatabase(profile.database());}
    }

    @Test public void customShortcutIntentRequiresSignedInProfile() throws Exception {
        var i=InstrumentationRegistry.getInstrumentation();var context=i.getTargetContext();var profile=new ProfileStore.Profile("phase14d-shortcut","Shortcut","ui","el");Activity activity=null;
        try {context.deleteDatabase(profile.database());try(var db=new FarmStore(context,profile.database())){db.addField("Αγρός",1.0);}i.runOnMainSync(()->{UserSession.clear();UserSession.signIn(profile);});var intent=new Intent("gr.mastixa.manager.PLANT_TRACKING").setPackage(context.getPackageName()).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK);activity=i.startActivitySync(intent);waitFor(i,()->hasText("Μεμονωμένα Φυτά / Δέντρα"),"shortcut destination");} finally {cleanup(i,activity);context.deleteDatabase(profile.database());}
    }
}
