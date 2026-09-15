package gr.mastixa.manager;

import android.app.Activity;
import android.content.Intent;
import android.view.*;
import android.widget.*;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import static org.junit.Assert.*;
import java.util.*;

public class CatalogUiTest {
    private List<Button> buttons(View view) {
        var result=new ArrayList<Button>();if(view instanceof Button b)result.add(b);
        if(view instanceof ViewGroup group)for(int i=0;i<group.getChildCount();i++)result.addAll(buttons(group.getChildAt(i)));
        return result;
    }
    private void click(Activity activity,String label) {
        for(var b:buttons(activity.getWindow().getDecorView()))if(b.getText().toString().equals(label)){b.performClick();return;}
        fail("Missing action: "+label);
    }
    @Test public void catalogScreensAndImportLocation() throws Exception {
        var instrumentation=InstrumentationRegistry.getInstrumentation();var context=instrumentation.getTargetContext();assertTrue(context.getPackageName().endsWith(".checks"));
        var profile=new ProfileStore.Profile("catalog-ui","Δοκιμή εμφάνισης","ui","el");context.deleteDatabase(profile.database());
        Activity activity=null;
        try {
            try(var store=new FarmStore(context,profile.database());var input=instrumentation.getContext().getAssets().open("windows-catalog.zip")) { CatalogImport.apply(store,CatalogImport.read(input),new java.io.File(context.getCacheDir(),"ui-before.json")); }
            UserSession.profile=profile;
            activity=instrumentation.startActivitySync(new Intent(context,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK));var screen=activity;
            instrumentation.runOnMainSync(()-> {
                click(screen,"Αγροτεμάχια");
                assertTrue(buttons(screen.getWindow().getDecorView()).stream().noneMatch(b->b.getText().toString().equals("Εισαγωγή από Windows")));
                click(screen,"Ενότητες");click(screen,"Γενικές Ρυθμίσεις  ›");click(screen,"Διαχείριση δεδομένων");click(screen,"Εισαγωγή από Windows");
                assertTrue(buttons(screen.getWindow().getDecorView()).stream().anyMatch(b->b.getText().toString().equals("Επιλογή ZIP από Windows")));
                click(screen,"Ενότητες");click(screen,"Παραγωγός  ›");
            });
            instrumentation.waitForIdleSync();
            try(var out=new java.io.FileOutputStream(new java.io.File(context.getExternalFilesDir(null),"producer-ui.png"))) { instrumentation.getUiAutomation().takeScreenshot().compress(android.graphics.Bitmap.CompressFormat.PNG,100,out); }
            instrumentation.runOnMainSync(()->{click(screen,"Ενότητες");click(screen,"Προϊόντα  ›");});instrumentation.waitForIdleSync();
            Thread.sleep(500); // Allow the compositor to display the new frame before visual QA.
            try(var out=new java.io.FileOutputStream(new java.io.File(context.getExternalFilesDir(null),"products-ui.png"))) { instrumentation.getUiAutomation().takeScreenshot().compress(android.graphics.Bitmap.CompressFormat.PNG,100,out); }
        } finally {
            var screen=activity;if(screen!=null)instrumentation.runOnMainSync(screen::finish);instrumentation.waitForIdleSync();UserSession.profile=null;
            // Leave the small isolated UI fixture DB until the checks package is replaced; no user profile is touched.
        }
    }
}
