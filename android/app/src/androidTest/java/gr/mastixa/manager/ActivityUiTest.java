package gr.mastixa.manager;

import android.app.Activity;
import android.content.Intent;
import android.view.*;
import android.widget.*;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import static org.junit.Assert.*;
import java.util.*;

public class ActivityUiTest {
    @Test public void englishActivityOnlyImportAndIrrigation() throws Exception {
        var i=InstrumentationRegistry.getInstrumentation();var context=i.getTargetContext();var profile=new ProfileStore.Profile("activity-en-ui","Activity English","ui","en");context.deleteDatabase(profile.database());Activity activity=null;
        CatalogImport.Package data;try(var in=i.getContext().getAssets().open("windows-activities.zip")){data=CatalogImport.read(in);}
        try{
            try(var store=new FarmStore(context,profile.database())){CatalogImport.apply(store,new CatalogImport.Package(data.fields(),data.producer(),data.products(),data.links(),data.partners(),data.inventory(),data.money(),data.production(),List.of(),data.work(),data.ignored()),new java.io.File(context.getCacheDir(),"activity-ui-import.json"));assertEquals(2,CatalogImport.preview(store,data).activities());}
            i.runOnMainSync(()->{UserSession.clear();UserSession.signIn(profile);});activity=i.startActivitySync(new Intent(context,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));var screen=activity;
            i.runOnMainSync(()->{try{var method=MainActivity.class.getDeclaredMethod("confirmCatalogImport",CatalogImport.Package.class);method.setAccessible(true);method.invoke(screen,data);}catch(Exception e){throw new RuntimeException(e);}});i.waitForIdleSync();i.runOnMainSync(()->click("Import"));i.waitForIdleSync();
            try(var store=new FarmStore(context,profile.database())){assertEquals(2,new ActivityStore(store).activities().size());assertEquals(3,new InventoryStore(store).movements(null).size());}
            i.runOnMainSync(()->click("OK"));i.waitForIdleSync();i.runOnMainSync(()->{click("Sections");click("Irrigation & Fertilization  ›");click("+ New activity");});i.waitForIdleSync();i.runOnMainSync(()->{fill("Duration (minutes)","30");fill("Water quantity (m³)","2.5");click("Save");});i.waitForIdleSync();
            try(var store=new FarmStore(context,profile.database())){assertEquals(3,new ActivityStore(store).activities().size());assertTrue(new ActivityStore(store).activities().stream().anyMatch(a->a.windowsId().isEmpty()&&a.duration()==30&&a.water()==2.5&&a.movementId().isEmpty()));}
        }finally{var screen=activity;i.runOnMainSync(()->{if(screen!=null)screen.finish();UserSession.clear();});}
    }
    private List<View> views(View v){var result=new ArrayList<View>();result.add(v);if(v instanceof ViewGroup g)for(int i=0;i<g.getChildCount();i++)result.addAll(views(g.getChildAt(i)));return result;}
    private void click(String label){var roots=android.view.inspector.WindowInspector.getGlobalWindowViews();for(int i=roots.size()-1;i>=0;i--)for(var v:views(roots.get(i)))if(v instanceof Button b&&b.getText().toString().equals(label)){b.performClick();return;}fail("Missing button: "+label);}
    private void fill(String label,String text){for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())for(var v:views(root))if(v instanceof EditText e&&label.contentEquals(e.getContentDescription())){e.setText(text);return;}fail("Missing input: "+label);}
    private void choose(String label,int index){for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())for(var v:views(root))if(v instanceof Spinner s&&label.contentEquals(s.getContentDescription())){s.setSelection(index);return;}fail("Missing choice: "+label);}
    @Test public void createFertilizationEditAndReturnFromInventory() throws Exception {
        var i=InstrumentationRegistry.getInstrumentation();var context=i.getTargetContext();var profile=new ProfileStore.Profile("activity-ui","Δοκιμή εργασιών","ui","el");context.deleteDatabase(profile.database());Activity activity=null;
        try{
            try(var store=new FarmStore(context,profile.database())){store.addField("Δοκιμαστικό αγροτεμάχιο",2);var stock=new InventoryStore(store);String item=stock.saveItem(new InventoryStore.Item(null,"Λίπασμα","Λίπασμα","kg",0,""));stock.saveMovement(new InventoryStore.Movement(null,item,"2026-09-01","Παραλαβή",20,"","","",0,0,"","","","",""));}
            i.runOnMainSync(()->{UserSession.clear();UserSession.signIn(profile);});activity=i.startActivitySync(new Intent(context,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));
            i.runOnMainSync(()->{click("Ενότητες");click("Άρδευση & Λίπανση  ›");click("+ Νέα εργασία");});i.waitForIdleSync();i.runOnMainSync(()->{choose("Είδος εργασίας",1);choose("Αγροτεμάχιο",1);choose("Είδος αποθήκης",1);});i.waitForIdleSync();
            i.runOnMainSync(()->{fill("Προϊόν λίπανσης","Λίπασμα");fill("Δόση","2");fill("Ποσότητα αποθήκης (μονάδα είδους)","4");fill("Κόστος €","12,5");fill("Υπεύθυνος","Δημήτρης");click("Αποθήκευση");});i.waitForIdleSync();
            try(var store=new FarmStore(context,profile.database())){var a=new ActivityStore(store).activities().get(0);assertEquals(16,new InventoryStore(store).stock(a.itemId()),0);assertEquals(12.5,a.cost(),0);}
            Thread.sleep(500);try(var out=new java.io.FileOutputStream(new java.io.File(context.getExternalFilesDir(null),"activities-ui.png"))){i.getUiAutomation().takeScreenshot().compress(android.graphics.Bitmap.CompressFormat.PNG,100,out);}
            i.runOnMainSync(()->click("Στοιχεία εργασίας"));i.waitForIdleSync();i.runOnMainSync(()->click("Επεξεργασία"));i.waitForIdleSync();i.runOnMainSync(()->{choose("Κατάσταση",2);click("Αποθήκευση");});i.waitForIdleSync();
            try(var store=new FarmStore(context,profile.database())){var a=new ActivityStore(store).activities().get(0);assertEquals("Ακυρώθηκε",a.status());assertEquals(20,new InventoryStore(store).stock(a.itemId()),0);}
            i.runOnMainSync(()->click("Στοιχεία εργασίας"));i.waitForIdleSync();i.runOnMainSync(()->click("Επεξεργασία"));i.waitForIdleSync();i.runOnMainSync(()->{choose("Κατάσταση",1);click("Αποθήκευση");});i.waitForIdleSync();
            i.runOnMainSync(()->{click("Ενότητες");click("Αποθήκη & Εφόδια  ›");});i.waitForIdleSync();
            // Follow the actual item button label used by the inventory list.
            i.runOnMainSync(()->click("Στοιχεία και κινήσεις"));i.waitForIdleSync();i.runOnMainSync(()->click("Συνδεδεμένη εργασία"));i.waitForIdleSync();i.runOnMainSync(()->click("Κλείσιμο"));i.waitForIdleSync();i.runOnMainSync(()->click("‹ Πίσω"));i.waitForIdleSync();
        }finally{var screen=activity;i.runOnMainSync(()->{if(screen!=null)screen.finish();UserSession.clear();});}
    }
}
