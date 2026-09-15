package gr.mastixa.manager;

import android.app.Activity;
import android.content.Intent;
import android.view.*;
import android.widget.*;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import static org.junit.Assert.*;
import java.util.*;

public class PartnerUiTest {
    private List<View> views(View v) {
        var result=new ArrayList<View>();result.add(v);if(v instanceof ViewGroup g)for(int i=0;i<g.getChildCount();i++)result.addAll(views(g.getChildAt(i)));return result;
    }
    private void click(String label) {
        var roots=android.view.inspector.WindowInspector.getGlobalWindowViews();
        for(int i=roots.size()-1;i>=0;i--)for(var v:views(roots.get(i)))if(v instanceof Button b && b.getText().toString().equals(label)){b.performClick();return;}
        fail("Missing button: "+label);
    }
    private void fill(String label,String value) {
        for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())for(var v:views(root))if(v instanceof EditText edit && label.contentEquals(edit.getContentDescription())){edit.setText(value);return;}
        fail("Missing input: "+label);
    }
    @Test public void createEditDetailsDeleteAndScreenshot() throws Exception {
        var i=InstrumentationRegistry.getInstrumentation();var context=i.getTargetContext();assertTrue(context.getPackageName().endsWith(".checks"));
        var profile=new ProfileStore.Profile("partners-ui","Δοκιμή συνεργατών","ui","el");context.deleteDatabase(profile.database());Activity activity=null;
        try {
            UserSession.profile=profile;activity=i.startActivitySync(new Intent(context,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK));
            i.runOnMainSync(()->{click("Ενότητες");click("Προμηθευτές & Αγοραστές  ›");click("+ Νέος συνεργάτης");});i.waitForIdleSync();
            i.runOnMainSync(()->{fill("Επωνυμία *","Δοκιμαστικός συνεργάτης");fill("ΑΦΜ","001234567");fill("Τηλέφωνο","00302100000000");fill("Όροι πληρωμής","30 ημέρες");fill("Σημειώσεις","Πρώτη γραμμή\nΔεύτερη γραμμή");click("Αποθήκευση");});i.waitForIdleSync();
            try(var store=new FarmStore(context,profile.database())){assertEquals("001234567",new PartnerStore(store).partners().get(0).taxId());}
            Thread.sleep(500);
            try(var out=new java.io.FileOutputStream(new java.io.File(context.getExternalFilesDir(null),"partners-ui.png"))){i.getUiAutomation().takeScreenshot().compress(android.graphics.Bitmap.CompressFormat.PNG,100,out);}
            i.runOnMainSync(()->click("Επεξεργασία"));i.waitForIdleSync();
            i.runOnMainSync(()->{fill("Υπεύθυνος επικοινωνίας","Μαρία");click("Αποθήκευση");});i.waitForIdleSync();
            try(var store=new FarmStore(context,profile.database())){assertEquals("Μαρία",new PartnerStore(store).partners().get(0).contact());}
            i.runOnMainSync(()->click("Στοιχεία συνεργάτη"));i.waitForIdleSync();
            i.runOnMainSync(()->click("Διαγραφή"));i.waitForIdleSync();i.runOnMainSync(()->click("Ακύρωση"));i.waitForIdleSync();
            try(var store=new FarmStore(context,profile.database())){assertEquals(1,new PartnerStore(store).partners().size());}
            i.runOnMainSync(()->click("Στοιχεία συνεργάτη"));i.waitForIdleSync();i.runOnMainSync(()->click("Διαγραφή"));i.waitForIdleSync();i.runOnMainSync(()->click("Διαγραφή"));i.waitForIdleSync();
            try(var store=new FarmStore(context,profile.database())){assertTrue(new PartnerStore(store).partners().isEmpty());}
        } finally {var screen=activity;if(screen!=null)i.runOnMainSync(screen::finish);i.waitForIdleSync();UserSession.profile=null;}
    }
}
