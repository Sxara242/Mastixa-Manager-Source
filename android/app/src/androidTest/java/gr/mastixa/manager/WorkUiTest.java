package gr.mastixa.manager;

import android.app.Activity;
import android.content.Intent;
import android.view.*;
import android.widget.*;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import static org.junit.Assert.*;
import java.util.*;

public class WorkUiTest {
    private List<View> views(View v){var result=new ArrayList<View>();result.add(v);if(v instanceof ViewGroup g)for(int i=0;i<g.getChildCount();i++)result.addAll(views(g.getChildAt(i)));return result;}
    private void click(String label){var roots=android.view.inspector.WindowInspector.getGlobalWindowViews();for(int i=roots.size()-1;i>=0;i--)for(var v:views(roots.get(i)))if(v instanceof Button b&&b.getText().toString().equals(label)){b.performClick();return;}fail("Missing button: "+label);}
    private void fill(String label,String text){for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())for(var v:views(root))if(v instanceof EditText e&&label.contentEquals(e.getContentDescription())){e.setText(text);return;}fail("Missing input: "+label);}
    private void choose(String label,int index){for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())for(var v:views(root))if(v instanceof Spinner s&&label.contentEquals(s.getContentDescription())){s.setSelection(index);return;}fail("Missing choice: "+label);}
    @Test public void greekProtectionCreateEditInventoryAndBack() throws Exception {
        var i=InstrumentationRegistry.getInstrumentation();var context=i.getTargetContext();var profile=new ProfileStore.Profile("protection-ui","Δοκιμή φυτοπροστασίας","ui","el");context.deleteDatabase(profile.database());Activity activity=null;
        try{
            try(var store=new FarmStore(context,profile.database())){store.addField("Δοκιμαστικό αγροτεμάχιο",2);var stock=new InventoryStore(store);String item=stock.saveItem(new InventoryStore.Item(null,"Δοκιμαστικό προϊόν","Εφόδια","L",0,""));stock.saveMovement(new InventoryStore.Movement(null,item,"2026-01-01","Παραλαβή",20,"","","",0,0,"","","","",""));}
            i.runOnMainSync(()->{UserSession.clear();UserSession.signIn(profile);});activity=i.startActivitySync(new Intent(context,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));
            i.runOnMainSync(()->{click("Ενότητες");click("Φυτοπροστασία  ›");click("+ Νέα επέμβαση");});i.waitForIdleSync();i.runOnMainSync(()->{choose("Είδος αποθήκης",1);fill("Στόχος *","Δοκιμαστικός στόχος");fill("Σκεύασμα / προϊόν *","Δοκιμαστικό προϊόν");fill("Δραστική ουσία","Δοκιμαστική ουσία");fill("Αριθμός έγκρισης","00123");fill("Δόση","0,5");fill("Μονάδα δόσης","L/στρ.");fill("Ψεκαστικό υγρό (L)","40");fill("Έκταση (στρ.)","2");fill("Εφαρμοστής","Δημήτρης");fill("Καιρός","Ήπιος");fill("Αναμονή συγκομιδής (ημέρες)","14");fill("Κόστος €","15");fill("Ποσότητα αποθήκης (μονάδα είδους)","2");click("Αποθήκευση");});i.waitForIdleSync();
            try(var store=new FarmStore(context,profile.database())){var p=new WorkStore(store).protections().get(0);assertEquals("00123",p.authorization_number());assertEquals(18,new InventoryStore(store).stock(p.inventory_item_id()),0);}
            Thread.sleep(500);try(var out=new java.io.FileOutputStream(new java.io.File(context.getExternalFilesDir(null),"protection-ui.png"))){i.getUiAutomation().takeScreenshot().compress(android.graphics.Bitmap.CompressFormat.PNG,100,out);}
            i.runOnMainSync(()->{click("Ενότητες");click("Αποθήκη & Εφόδια  ›");click("Στοιχεία και κινήσεις");click("Συνδεδεμένη φυτοπροστασία");});i.waitForIdleSync();i.runOnMainSync(()->click("Επεξεργασία"));i.waitForIdleSync();i.runOnMainSync(()->{fill("Ποσότητα αποθήκης (μονάδα είδους)","3");click("Αποθήκευση");});i.waitForIdleSync();i.runOnMainSync(()->click("‹ Πίσω"));i.waitForIdleSync();
            try(var store=new FarmStore(context,profile.database())){var p=new WorkStore(store).protections().get(0);assertEquals(17,new InventoryStore(store).stock(p.inventory_item_id()),0);}
        }finally{var screen=activity;i.runOnMainSync(()->{if(screen!=null)screen.finish();UserSession.clear();});}
    }
    @Test public void englishWorkersLaborCalculatedCostHistoryAndInactive() throws Exception {
        var i=InstrumentationRegistry.getInstrumentation();var context=i.getTargetContext();var profile=new ProfileStore.Profile("labor-ui","Labor test","ui","en");context.deleteDatabase(profile.database());Activity activity=null;
        try{
            try(var store=new FarmStore(context,profile.database())){store.addField("Test field",2);}
            i.runOnMainSync(()->{UserSession.clear();UserSession.signIn(profile);});activity=i.startActivitySync(new Intent(context,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));
            i.runOnMainSync(()->{click("Sections");click("Labor & Personnel  ›");click("Staff");click("+ New worker");});i.waitForIdleSync();i.runOnMainSync(()->{fill("Full name *","Test worker");fill("Role","Harvesting");fill("Phone","00123");fill("Default hourly rate €","8.5");click("Save");});i.waitForIdleSync();i.runOnMainSync(()->{click("‹ Back");click("+ New labor entry");});i.waitForIdleSync();i.runOnMainSync(()->{choose("Field",1);fill("Work type *","Harvesting");fill("Hours *","6");click("Save");});i.waitForIdleSync();
            try(var store=new FarmStore(context,profile.database())){var work=new WorkStore(store);assertEquals(51,work.labor().get(0).cost(),0);assertEquals("00123",work.workers().get(0).phone());assertTrue(new MoneyStore(store).entries(null).isEmpty());}
            Thread.sleep(500);try(var out=new java.io.FileOutputStream(new java.io.File(context.getExternalFilesDir(null),"labor-ui.png"))){i.getUiAutomation().takeScreenshot().compress(android.graphics.Bitmap.CompressFormat.PNG,100,out);}
            i.runOnMainSync(()->click("Labor details"));i.waitForIdleSync();i.runOnMainSync(()->click("Edit"));i.waitForIdleSync();i.runOnMainSync(()->{fill("Hours *","5");fill("Hourly rate €","9");click("Save");});i.waitForIdleSync();i.runOnMainSync(()->{click("Staff");click("Worker details");});i.waitForIdleSync();i.runOnMainSync(()->click("Edit"));i.waitForIdleSync();i.runOnMainSync(()->{choose("Status",0);click("Save");});i.waitForIdleSync();i.runOnMainSync(()->click("Worker details"));i.waitForIdleSync();i.runOnMainSync(()->click("Labor history"));i.waitForIdleSync();
            try(var store=new FarmStore(context,profile.database())){assertEquals(45,new WorkStore(store).labor().get(0).cost(),0);assertEquals(0,new WorkStore(store).workers().get(0).active());}
            i.runOnMainSync(()->click("‹ Back"));i.waitForIdleSync();
        }finally{var screen=activity;i.runOnMainSync(()->{if(screen!=null)screen.finish();UserSession.clear();});}
    }
}
