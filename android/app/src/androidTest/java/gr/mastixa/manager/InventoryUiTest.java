package gr.mastixa.manager;

import android.app.Activity;
import android.content.Intent;
import android.view.*;
import android.widget.*;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import static org.junit.Assert.*;
import java.util.*;

public class InventoryUiTest {
    private List<View> views(View v){var result=new ArrayList<View>();result.add(v);if(v instanceof ViewGroup g)for(int i=0;i<g.getChildCount();i++)result.addAll(views(g.getChildAt(i)));return result;}
    private void click(String label){var roots=android.view.inspector.WindowInspector.getGlobalWindowViews();for(int i=roots.size()-1;i>=0;i--)for(var v:views(roots.get(i)))if(v instanceof Button b&&b.getText().toString().equals(label)){b.performClick();return;}fail("Missing button: "+label);}
    private void fill(String label,String text){for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())for(var v:views(root))if(v instanceof EditText e&&label.contentEquals(e.getContentDescription())){e.setText(text);return;}fail("Missing input: "+label);}
    private void choose(String label,int index){for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())for(var v:views(root))if(v instanceof Spinner s&&label.contentEquals(s.getContentDescription())){s.setSelection(index);return;}fail("Missing choice: "+label);}
    @Test public void initialStockReceiptConsumptionAndScreens() throws Exception {
        var i=InstrumentationRegistry.getInstrumentation();var context=i.getTargetContext();assertTrue(context.getPackageName().endsWith(".checks"));var profile=new ProfileStore.Profile("inventory-ui","Δοκιμή αποθήκης","ui","el");context.deleteDatabase(profile.database());Activity activity=null;
        try {
            UserSession.profile=profile;activity=i.startActivitySync(new Intent(context,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));
            i.runOnMainSync(()->{click("Ενότητες");click("Αποθήκη & Εφόδια  ›");click("+ Νέο είδος");});i.waitForIdleSync();
            i.runOnMainSync(()->{fill("Όνομα είδους *","Λίπασμα δοκιμής");fill("Κατηγορία","Λίπασμα");fill("Ελάχιστο απόθεμα","5");fill("Αρχικό απόθεμα","10");click("Αποθήκευση");});i.waitForIdleSync();
            try(var store=new FarmStore(context,profile.database())){var inv=new InventoryStore(store);assertEquals(10,inv.stock(inv.items().get(0).id()),0);}
            i.runOnMainSync(()->{click("Στοιχεία και κινήσεις");click("+ Νέα κίνηση");});i.waitForIdleSync();
            i.runOnMainSync(()->{fill("Ποσότητα *","2");fill("Τιμή μονάδας € (μόνο παραλαβή)","2,5");click("Αποθήκευση");});i.waitForIdleSync();
            i.runOnMainSync(()->click("+ Νέα κίνηση"));i.waitForIdleSync();i.runOnMainSync(()->{choose("Τύπος κίνησης",1);fill("Ποσότητα *","8");click("Αποθήκευση");});i.waitForIdleSync();
            try(var store=new FarmStore(context,profile.database())){var inv=new InventoryStore(store);assertEquals(4,inv.stock(inv.items().get(0).id()),0);assertEquals(5,inv.movements(null).stream().filter(m->m.type().equals("Παραλαβή")).findFirst().orElseThrow().cost(),0);}
            Thread.sleep(500);try(var out=new java.io.FileOutputStream(new java.io.File(context.getExternalFilesDir(null),"inventory-movements-ui.png"))){i.getUiAutomation().takeScreenshot().compress(android.graphics.Bitmap.CompressFormat.PNG,100,out);}
            i.runOnMainSync(()->click("Πίσω στα είδη"));i.waitForIdleSync();Thread.sleep(500);try(var out=new java.io.FileOutputStream(new java.io.File(context.getExternalFilesDir(null),"inventory-ui.png"))){i.getUiAutomation().takeScreenshot().compress(android.graphics.Bitmap.CompressFormat.PNG,100,out);}
        } finally{var screen=activity;if(screen!=null)i.runOnMainSync(screen::finish);i.waitForIdleSync();UserSession.profile=null;}
    }
}
