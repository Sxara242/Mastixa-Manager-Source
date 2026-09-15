package gr.mastixa.manager;

import android.app.Activity;
import android.content.Intent;
import android.view.*;
import android.widget.*;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import static org.junit.Assert.*;
import java.util.*;

public class MoneyUiTest {
    private List<View> views(View v){var result=new ArrayList<View>();result.add(v);if(v instanceof ViewGroup g)for(int i=0;i<g.getChildCount();i++)result.addAll(views(g.getChildAt(i)));return result;}
    private void click(String label){var roots=android.view.inspector.WindowInspector.getGlobalWindowViews();for(int i=roots.size()-1;i>=0;i--)for(var v:views(roots.get(i)))if(v instanceof Button b&&b.getText().toString().equals(label)){b.performClick();return;}fail("Missing button: "+label);}
    private void fill(String label,String text){for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())for(var v:views(root))if(v instanceof EditText e&&label.contentEquals(e.getContentDescription())){e.setText(text);return;}fail("Missing input: "+label);}
    private void choose(String label,int index){for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())for(var v:views(root))if(v instanceof Spinner s&&label.contentEquals(s.getContentDescription())){s.setSelection(index);return;}fail("Missing choice: "+label);}
    @Test public void manualEntryAndImportedReceiptNavigation() throws Exception {
        var i=InstrumentationRegistry.getInstrumentation();var context=i.getTargetContext();assertTrue(context.getPackageName().endsWith(".checks"));var profile=new ProfileStore.Profile("money-ui","Δοκιμή οικονομικών","ui","el");context.deleteDatabase(profile.database());Activity activity=null;
        try {
            try(var store=new FarmStore(context,profile.database());var in=i.getContext().getAssets().open("windows-money.zip")){CatalogImport.apply(store,CatalogImport.read(in),new java.io.File(context.getCacheDir(),"money-ui-before.json"));}
            UserSession.profile=profile;activity=i.startActivitySync(new Intent(context,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));
            i.runOnMainSync(()->{click("Ενότητες");click("Έσοδα  ›");click("+ Νέο έσοδο");});i.waitForIdleSync();
            i.runOnMainSync(()->{fill("Περιγραφή *","Νέο έσοδο δοκιμής");fill("Ποσό € *","25,50");fill("Τρόπος πληρωμής","Μετρητά");click("Αποθήκευση");});i.waitForIdleSync();
            try(var store=new FarmStore(context,profile.database())){assertEquals(2,new MoneyStore(store).entries("income").size());}
            i.runOnMainSync(()->click("Στοιχεία εγγραφής"));i.waitForIdleSync();i.runOnMainSync(()->click("Επεξεργασία"));i.waitForIdleSync();i.runOnMainSync(()->{fill("Ποσό € *","30");click("Αποθήκευση");});i.waitForIdleSync();
            try(var store=new FarmStore(context,profile.database())){assertTrue(new MoneyStore(store).entries("income").stream().anyMatch(e->e.description().equals("Νέο έσοδο δοκιμής")&&e.amount()==30));}
            Thread.sleep(500);try(var out=new java.io.FileOutputStream(new java.io.File(context.getExternalFilesDir(null),"money-income-ui.png"))){i.getUiAutomation().takeScreenshot().compress(android.graphics.Bitmap.CompressFormat.PNG,100,out);}
            i.runOnMainSync(()->{click("Ενότητες");click("Έξοδα  ›");});i.waitForIdleSync();Thread.sleep(500);try(var out=new java.io.FileOutputStream(new java.io.File(context.getExternalFilesDir(null),"money-expenses-ui.png"))){i.getUiAutomation().takeScreenshot().compress(android.graphics.Bitmap.CompressFormat.PNG,100,out);}
            // Filter to the receipt so the detail action targets the linked automatic expense.
            i.runOnMainSync(()->click("Αναζήτηση: "));i.waitForIdleSync();
            i.runOnMainSync(()->{for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())for(var v:views(root))if(v instanceof EditText e)e.setText("Παραλαβή");click("Εντάξει");});i.waitForIdleSync();
            i.runOnMainSync(()->click("Στοιχεία εγγραφής"));i.waitForIdleSync();i.runOnMainSync(()->click("Παραλαβή αποθήκης"));i.waitForIdleSync();
            i.runOnMainSync(()->click("Πίσω στα είδη"));i.waitForIdleSync();
            i.runOnMainSync(()->{click("Ενότητες");click("Προμηθευτές & Αγοραστές  ›");click("Οικονομικό ιστορικό");});i.waitForIdleSync();Thread.sleep(500);try(var out=new java.io.FileOutputStream(new java.io.File(context.getExternalFilesDir(null),"money-partner-ui.png"))){i.getUiAutomation().takeScreenshot().compress(android.graphics.Bitmap.CompressFormat.PNG,100,out);}
            i.runOnMainSync(()->click("Κλείσιμο"));
        }finally{var screen=activity;if(screen!=null)i.runOnMainSync(screen::finish);i.waitForIdleSync();UserSession.profile=null;}
    }
}
