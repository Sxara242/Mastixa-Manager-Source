package gr.mastixa.manager;

import android.app.Activity;
import android.content.Intent;
import android.view.*;
import android.widget.*;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import static org.junit.Assert.*;
import java.util.*;

public class ProductionUiTest {
    private List<View> views(View v){var result=new ArrayList<View>();result.add(v);if(v instanceof ViewGroup g)for(int i=0;i<g.getChildCount();i++)result.addAll(views(g.getChildAt(i)));return result;}
    private void click(String label){var roots=android.view.inspector.WindowInspector.getGlobalWindowViews();for(int i=roots.size()-1;i>=0;i--)for(var v:views(roots.get(i)))if(v instanceof Button b&&b.getText().toString().equals(label)){b.performClick();return;}fail("Missing button: "+label);}
    private void fill(String label,String text){for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())for(var v:views(root))if(v instanceof EditText e&&label.contentEquals(e.getContentDescription())){e.setText(text);return;}fail("Missing input: "+label);}
    private void choose(String label,int index){for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())for(var v:views(root))if(v instanceof Spinner s&&label.contentEquals(s.getContentDescription())){s.setSelection(index);return;}fail("Missing choice: "+label);}
    @Test public void createProductionSellAndFollowIncome() throws Exception {
        var i=InstrumentationRegistry.getInstrumentation();var context=i.getTargetContext();var profile=new ProfileStore.Profile("production-ui","Δοκιμή παραγωγής","ui","el");context.deleteDatabase(profile.database());Activity activity=null;
        try {
            try(var store=new FarmStore(context,profile.database())){store.addField("Δοκιμαστικό αγροτεμάχιο",2);new CatalogStore(store).saveProduct(null,"Μαστίχα","kg",true);}
            i.runOnMainSync(()->{UserSession.clear();UserSession.signIn(profile);});activity=i.startActivitySync(new Intent(context,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));
            i.runOnMainSync(()->{click("Ενότητες");click("Παραγωγή  ›");click("+ Νέα παραγωγή");});i.waitForIdleSync();i.runOnMainSync(()->{fill("Ποσότητα *","20");fill("Σημειώσεις","Δοκιμαστική συγκομιδή");click("Αποθήκευση");});i.waitForIdleSync();
            i.runOnMainSync(()->{click("Ενότητες");click("Πωλήσεις Παραγωγής  ›");click("+ Νέα πώληση");});i.waitForIdleSync();i.runOnMainSync(()->{fill("Όνομα αγοραστή χωρίς σύνδεση","Δοκιμαστικός αγοραστής");fill("Ποσότητα *","6");fill("Τιμή ανά μονάδα € *","8,5");fill("Τρόπος πληρωμής","Τράπεζα");click("Αποθήκευση");});i.waitForIdleSync();
            try(var store=new FarmStore(context,profile.database())){var sale=new ProductionStore(store).sales().get(0);assertEquals(14,new ProductionStore(store).available(sale.productId()),0);assertEquals(51,new MoneyStore(store).entries("income").get(0).amount(),0);}
            Thread.sleep(500);try(var out=new java.io.FileOutputStream(new java.io.File(context.getExternalFilesDir(null),"production-sales-ui.png"))){i.getUiAutomation().takeScreenshot().compress(android.graphics.Bitmap.CompressFormat.PNG,100,out);}
            i.runOnMainSync(()->{click("Ενότητες");click("Έσοδα  ›");click("Στοιχεία εγγραφής");});i.waitForIdleSync();i.runOnMainSync(()->click("Πώληση παραγωγής"));i.waitForIdleSync();i.runOnMainSync(()->click("Επεξεργασία"));i.waitForIdleSync();i.runOnMainSync(()->{fill("Ποσότητα *","5");fill("Τιμή ανά μονάδα € *","9");click("Αποθήκευση");});i.waitForIdleSync();
            try(var store=new FarmStore(context,profile.database())){assertEquals(1,new MoneyStore(store).entries("income").size());assertEquals(45,new MoneyStore(store).entries("income").get(0).amount(),0);}
        }finally{var screen=activity;i.runOnMainSync(()->{if(screen!=null)screen.finish();UserSession.clear();});}
    }
}
