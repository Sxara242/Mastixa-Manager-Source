package gr.mastixa.manager;

import android.app.Activity;
import android.content.Intent;
import android.os.SystemClock;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.TextView;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;
import static org.junit.Assert.*;

public class SensorDataUiTest {
    private List<View> views(View v){var result=new ArrayList<View>();result.add(v);if(v instanceof ViewGroup g)for(int i=0;i<g.getChildCount();i++)result.addAll(views(g.getChildAt(i)));return result;}
    private boolean hasText(String value){for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())for(var v:views(root))if(v instanceof TextView t&&t.getText().toString().equals(value))return true;return false;}
    private boolean hasTextContaining(String value){for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())for(var v:views(root))if(v instanceof TextView t&&t.getText().toString().contains(value))return true;return false;}
    private boolean hasButtonContaining(String value){for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())for(var v:views(root))if(v instanceof Button b&&b.getText().toString().contains(value))return true;return false;}
    private void clickContaining(String value){for(var roots=android.view.inspector.WindowInspector.getGlobalWindowViews();!roots.isEmpty();){for(int i=roots.size()-1;i>=0;i--)for(var v:views(roots.get(i)))if(v instanceof Button b&&b.getText().toString().contains(value)){b.performClick();return;}break;}fail("Missing button containing: "+value);}
    private void waitFor(android.app.Instrumentation i, java.util.function.BooleanSupplier condition, String label) throws Exception {
        long deadline=SystemClock.uptimeMillis()+5000;
        while(SystemClock.uptimeMillis()<deadline){boolean[] found={false};i.runOnMainSync(()->found[0]=condition.getAsBoolean());if(found[0])return;i.waitForIdleSync();Thread.sleep(50);}fail("Missing UI: "+label);
    }
    private void cleanup(android.app.Instrumentation i, Activity screen){i.runOnMainSync(()->{for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())if(root.getContext() instanceof Activity a&&!a.isFinishing())a.finish();if(screen!=null&&!screen.isFinishing())screen.finish();UserSession.clear();});i.waitForIdleSync();}

    @Test public void greekUiShowsLatestStaleSuspectAndHistory() throws Exception {
        var i=InstrumentationRegistry.getInstrumentation();var context=i.getTargetContext();var profile=new ProfileStore.Profile("phase15e-sensor-ui","Sensor UI","ui","el");Activity activity=null;
        try {
            context.deleteDatabase(profile.database());
            try(var db=new FarmStore(context,profile.database())){
                db.addField("Αγρός Sensor",2.0);String field=db.fields().get(0).id();var registry=new SensorDataStore(db);
                registry.saveDevice(new SensorData.Device("station","Field station","generic-http",field,"","active",""));
                registry.saveChannel(new SensorData.Channel("air","station","air_temperature","celsius","Air"));
                registry.saveChannel(new SensorData.Channel("soil","station","soil_moisture","percent","Soil"));
                String fresh=Instant.now().minusSeconds(60).truncatedTo(ChronoUnit.SECONDS).toString();
                String stale=Instant.now().minusSeconds(90000).truncatedTo(ChronoUnit.SECONDS).toString();
                registry.appendObservation(new SensorData.Observation("fresh","air",fresh,24.5,"suspect","packet-fresh"));
                registry.appendObservation(new SensorData.Observation("old","soil",stale,31.0,"good","packet-old"));
            }
            i.runOnMainSync(()->{UserSession.clear();UserSession.signIn(profile);});
            activity=i.startActivitySync(new Intent(context,SensorDataActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));
            waitFor(i,()->hasText("Αισθητήρες / API"),"page title");
            waitFor(i,()->hasTextContaining("Ύποπτη"),"suspect indicator");
            waitFor(i,()->hasTextContaining("Παρωχημένη"),"stale indicator");
            assertTrue(hasButtonContaining("Ιστορικό · Soil"));
            i.runOnMainSync(()->clickContaining("Ιστορικό · Soil"));
            waitFor(i,()->hasTextContaining("Ιστορικό · Soil"),"history dialog");
            waitFor(i,()->hasTextContaining("packet-old"),"history source reference");
        } finally {cleanup(i,activity);context.deleteDatabase(profile.database());}
    }

    @Test public void sensorShortcutIntentRequiresSignedInProfile() throws Exception {
        var i=InstrumentationRegistry.getInstrumentation();var context=i.getTargetContext();var profile=new ProfileStore.Profile("phase15e-shortcut","Sensor shortcut","ui","el");Activity activity=null;
        try {
            context.deleteDatabase(profile.database());try(var db=new FarmStore(context,profile.database())){new SensorDataStore(db);}
            i.runOnMainSync(()->{UserSession.clear();UserSession.signIn(profile);});
            var intent=new Intent("gr.mastixa.manager.SENSOR_DATA").setPackage(context.getPackageName()).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK);
            activity=i.startActivitySync(intent);
            waitFor(i,()->hasText("Αισθητήρες / API"),"shortcut destination");
        } finally {cleanup(i,activity);context.deleteDatabase(profile.database());}
    }
}
