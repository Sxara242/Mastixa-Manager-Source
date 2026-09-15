package gr.mastixa.manager;

import android.app.Activity;
import android.content.Intent;
import android.view.*;
import android.widget.*;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import static org.junit.Assert.*;
import java.util.*;

public class EquipmentUiTest {
    private List<View> views(View v){var result=new ArrayList<View>();result.add(v);if(v instanceof ViewGroup g)for(int i=0;i<g.getChildCount();i++)result.addAll(views(g.getChildAt(i)));return result;}
    private void click(String label){var roots=android.view.inspector.WindowInspector.getGlobalWindowViews();for(int i=roots.size()-1;i>=0;i--)for(var v:views(roots.get(i)))if(v instanceof Button b&&b.getText().toString().equals(label)){b.performClick();return;}fail("Missing button: "+label);}
    private void fill(String label,String text){for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())for(var v:views(root))if(v instanceof EditText e&&label.contentEquals(e.getContentDescription())){e.setText(text);return;}fail("Missing input: "+label);}
    private void choose(String label,int index){for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())for(var v:views(root))if(v instanceof Spinner s&&label.contentEquals(s.getContentDescription())){s.setSelection(index);return;}fail("Missing choice: "+label);}
    @Test public void equipmentServiceExpenseEditAndBack() throws Exception {
        var i=InstrumentationRegistry.getInstrumentation();var context=i.getTargetContext();var profile=new ProfileStore.Profile("equipment-ui","Δοκιμή μηχανημάτων","ui","el");context.deleteDatabase(profile.database());Activity activity=null;
        try{i.runOnMainSync(()->{UserSession.clear();UserSession.signIn(profile);});activity=i.startActivitySync(new Intent(context,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));i.runOnMainSync(()->{click("Ενότητες");click("Μηχανήματα & Συντήρηση  ›");click("+ Νέο μηχάνημα");});i.waitForIdleSync();i.runOnMainSync(()->{fill("Όνομα μηχανήματος *","Δοκιμαστικό τρακτέρ");fill("Μάρκα / μοντέλο","Μοντέλο Α");fill("Κωδικός μηχανήματος","00123");fill("Τρέχουσα ένδειξη","100");click("Αποθήκευση");});i.waitForIdleSync();i.runOnMainSync(()->{click("Ιστορικό συντήρησης");click("+ Νέα συντήρηση");});i.waitForIdleSync();i.runOnMainSync(()->{fill("Είδος συντήρησης *","Αλλαγή λαδιών");fill("Κόστος €","85,5");fill("Ένδειξη μετρητή","120");fill("Τεχνικός","Δοκιμαστικός τεχνικός");fill("Επόμενη συντήρηση (YYYY-MM-DD, προαιρετική)","2027-01-01");fill("Επόμενη ένδειξη (προαιρετική)","150");click("Αποθήκευση");});i.waitForIdleSync();
            try(var store=new FarmStore(context,profile.database())){assertEquals(85.5,new MoneyStore(store).entries("expense").get(0).amount(),0);assertEquals(120,new WorkStore(store).equipment().get(0).current_meter(),0);}
            i.runOnMainSync(()->click("‹ Πίσω"));i.waitForIdleSync();Thread.sleep(500);try(var out=new java.io.FileOutputStream(new java.io.File(context.getExternalFilesDir(null),"equipment-ui.png"))){i.getUiAutomation().takeScreenshot().compress(android.graphics.Bitmap.CompressFormat.PNG,100,out);}
            i.runOnMainSync(()->{click("Ενότητες");click("Έξοδα  ›");click("Στοιχεία εγγραφής");});i.waitForIdleSync();i.runOnMainSync(()->click("Συντήρηση μηχανήματος"));i.waitForIdleSync();i.runOnMainSync(()->click("Επεξεργασία"));i.waitForIdleSync();i.runOnMainSync(()->{fill("Κόστος €","90");click("Αποθήκευση");});i.waitForIdleSync();try(var store=new FarmStore(context,profile.database())){assertEquals(1,new MoneyStore(store).entries("expense").size());assertEquals(90,new MoneyStore(store).entries("expense").get(0).amount(),0);}i.runOnMainSync(()->click("‹ Πίσω"));i.waitForIdleSync();
        }finally{var screen=activity;i.runOnMainSync(()->{if(screen!=null)screen.finish();UserSession.clear();});}
    }
    @Test public void englishImportOnlyEquipmentAndServices() throws Exception {
        var i=InstrumentationRegistry.getInstrumentation();var context=i.getTargetContext();var profile=new ProfileStore.Profile("equipment-en-ui","Equipment import","ui","en");context.deleteDatabase(profile.database());Activity activity=null;CatalogImport.Package d;try(var in=i.getContext().getAssets().open("windows-equipment.zip")){d=CatalogImport.read(in);}
        try{try(var store=new FarmStore(context,profile.database())){CatalogImport.apply(store,new CatalogImport.Package(d.fields(),d.producer(),d.products(),d.links(),d.partners(),d.inventory(),d.money(),d.production(),d.activities(),WorkImport.Data.empty(),d.ignored()),new java.io.File(context.getCacheDir(),"equipment-ui-before.json"));}
            i.runOnMainSync(()->{UserSession.clear();UserSession.signIn(profile);});activity=i.startActivitySync(new Intent(context,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));var screen=activity;i.runOnMainSync(()->{try{var method=MainActivity.class.getDeclaredMethod("confirmCatalogImport",CatalogImport.Package.class);method.setAccessible(true);method.invoke(screen,d);}catch(Exception e){throw new RuntimeException(e);}});i.waitForIdleSync();i.runOnMainSync(()->click("Import"));i.waitForIdleSync();try(var store=new FarmStore(context,profile.database())){assertEquals(1,new WorkStore(store).equipment().size());assertEquals(2,new WorkStore(store).services().size());assertEquals(3,new MoneyStore(store).entries("expense").size());}i.runOnMainSync(()->click("OK"));i.waitForIdleSync();i.runOnMainSync(()->{click("Sections");click("Machinery & Maintenance  ›");click("Maintenance history");click("Service details");});i.waitForIdleSync();
        }finally{var screen=activity;i.runOnMainSync(()->{if(screen!=null)screen.finish();UserSession.clear();});}
    }
}
