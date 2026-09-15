package gr.mastixa.manager;

import android.app.Activity;
import android.content.Intent;
import android.view.*;
import android.widget.*;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import static org.junit.Assert.*;
import java.util.*;

public class PlantingUiTest {
    private List<View> views(View v){var result=new ArrayList<View>();result.add(v);if(v instanceof ViewGroup g)for(int i=0;i<g.getChildCount();i++)result.addAll(views(g.getChildAt(i)));return result;}
    private void click(String label){var roots=android.view.inspector.WindowInspector.getGlobalWindowViews();for(int i=roots.size()-1;i>=0;i--)for(var v:views(roots.get(i)))if(v instanceof Button b&&b.getText().toString().equals(label)){b.performClick();return;}fail("Missing button: "+label);}
    private void fill(String label,String text){for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())for(var v:views(root))if(v instanceof EditText e&&label.contentEquals(e.getContentDescription())){e.setText(text);return;}fail("Missing input: "+label);}
    private void choose(String label,int index){for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())for(var v:views(root))if(v instanceof Spinner s&&label.contentEquals(s.getContentDescription())){s.setSelection(index);return;}fail("Missing choice: "+label);}
    @Test public void createEditAndReturn() throws Exception {
        var i=InstrumentationRegistry.getInstrumentation();var context=i.getTargetContext();var profile=new ProfileStore.Profile("planting-ui","Δοκιμή φυτεύσεων","ui","el");context.deleteDatabase(profile.database());Activity activity=null;
        try{try(var store=new FarmStore(context,profile.database())){store.addField("Δοκιμαστικό αγροτεμάχιο",2);}
            i.runOnMainSync(()->{UserSession.clear();UserSession.signIn(profile);});activity=i.startActivitySync(new Intent(context,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));
            i.runOnMainSync(()->{click("Ενότητες");click("Φυτεύσεις & Δέντρα  ›");click("+ Νέα φύτευση");});i.waitForIdleSync();i.runOnMainSync(()->{fill("Φυτεμένα δέντρα","30");fill("Ζωντανά δέντρα","27");fill("Υλικό φύτευσης","Μοσχεύματα");fill("Προέλευση","Δοκιμαστικό φυτώριο");fill("Ποικιλία","Ποικιλία Α");fill("Αποστάσεις φύτευσης","4 x 4 m");fill("Κόστος €","120,5");click("Αποθήκευση");});i.waitForIdleSync();
            Thread.sleep(500);try(var out=new java.io.FileOutputStream(new java.io.File(context.getExternalFilesDir(null),"planting-ui.png"))){i.getUiAutomation().takeScreenshot().compress(android.graphics.Bitmap.CompressFormat.PNG,100,out);}
            i.runOnMainSync(()->click("Στοιχεία φύτευσης"));i.waitForIdleSync();i.runOnMainSync(()->click("Επεξεργασία"));i.waitForIdleSync();i.runOnMainSync(()->{fill("Ζωντανά δέντρα","25");click("Αποθήκευση");});i.waitForIdleSync();try(var store=new FarmStore(context,profile.database())){assertEquals(25,new WorkStore(store).plantings().get(0).trees_alive());assertEquals(0,store.fields().get(0).trees());}i.runOnMainSync(()->click("‹ Πίσω"));i.waitForIdleSync();
        }finally{var screen=activity;i.runOnMainSync(()->{if(screen!=null)screen.finish();UserSession.clear();});}
    }
    @Test public void importOnlyNewPlantingInEnglish() throws Exception {
        var i=InstrumentationRegistry.getInstrumentation();var context=i.getTargetContext();var profile=new ProfileStore.Profile("planting-import-ui","Planting import","ui","en");context.deleteDatabase(profile.database());Activity activity=null;CatalogImport.Package d;try(var in=i.getContext().getAssets().open("windows-plantings.zip")){d=CatalogImport.read(in);}
        try{try(var store=new FarmStore(context,profile.database())){CatalogImport.apply(store,new CatalogImport.Package(d.fields(),d.producer(),d.products(),d.links(),d.partners(),d.inventory(),d.money(),d.production(),d.activities(),WorkImport.Data.empty(),d.ignored()),new java.io.File(context.getCacheDir(),"planting-ui-import.json"));}
            i.runOnMainSync(()->{UserSession.clear();UserSession.signIn(profile);});activity=i.startActivitySync(new Intent(context,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));var screen=activity;i.runOnMainSync(()->{try{var m=MainActivity.class.getDeclaredMethod("confirmCatalogImport",CatalogImport.Package.class);m.setAccessible(true);m.invoke(screen,d);}catch(Exception e){throw new RuntimeException(e);}});i.waitForIdleSync();i.runOnMainSync(()->click("Import"));i.waitForIdleSync();try(var store=new FarmStore(context,profile.database())){assertEquals(1,new WorkStore(store).plantings().size());}i.runOnMainSync(()->click("OK"));i.waitForIdleSync();i.runOnMainSync(()->{click("Sections");click("Plantings & Trees  ›");click("Planting details");});i.waitForIdleSync();
        }finally{var screen=activity;i.runOnMainSync(()->{if(screen!=null)screen.finish();UserSession.clear();});}
    }
}
