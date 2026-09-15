package gr.mastixa.manager;

import android.app.Activity;
import android.content.Intent;
import android.view.*;
import android.widget.*;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import static org.junit.Assert.*;
import java.util.*;

public class MainActivityLocalizationErrorUiTest {
    private List<View> views(View view){var rows=new ArrayList<View>();rows.add(view);if(view instanceof ViewGroup group)for(int i=0;i<group.getChildCount();i++)rows.addAll(views(group.getChildAt(i)));return rows;}
    private boolean hasGlobal(String text){for(var root:android.view.inspector.WindowInspector.getGlobalWindowViews())for(var view:views(root))if(view instanceof TextView label&&label.getText().toString().contains(text))return true;return false;}
    private void click(String text){var roots=android.view.inspector.WindowInspector.getGlobalWindowViews();for(int n=roots.size()-1;n>=0;n--)for(var view:views(roots.get(n)))if(view instanceof Button button&&button.getText().toString().equals(text)){button.performClick();return;}fail("Missing button "+text);}
    private void invoke(Activity activity,String name,Class<?>[] types,Object...values){try{var method=MainActivity.class.getDeclaredMethod(name,types);method.setAccessible(true);method.invoke(activity,values);}catch(Exception e){throw new RuntimeException(e);}}
    private void ui(Runnable action){var instrumentation=InstrumentationRegistry.getInstrumentation();instrumentation.runOnMainSync(action);instrumentation.waitForIdleSync();}
    private void assertVisible(String stage,String text){assertTrue(stage+" — missing visible text: "+text,hasGlobal(text));}
    private void assertHidden(String stage,String text){assertFalse(stage+" — leaked text: "+text,hasGlobal(text));}
    private String ok(String language){return language.equals("el")?"Εντάξει":"OK";}
    private String cancel(String language){return language.equals("el")?"Ακύρωση":"Cancel";}
    private String save(String language){return language.equals("el")?"Αποθήκευση":"Save";}
    private void closeMessage(String language){ui(()->click(ok(language)));}
    private void cancelForm(String language){ui(()->click(cancel(language)));}
    private void assertGeneric(Activity activity,String language,String method,String greek,String english){
        ui(()->invoke(activity,method,new Class[]{Runnable.class},(Runnable)()->{throw new IllegalArgumentException("RAW_MAIN_SENTINEL");}));
        String expected=language.equals("el")?greek:english;
        assertVisible(method,expected);
        assertHidden(method,"RAW_MAIN_SENTINEL");
        closeMessage(language);
    }
    @Test public void backendErrorsAreLocalizedAndUiValidationRemainsSpecific()throws Exception{
        var instrumentation=InstrumentationRegistry.getInstrumentation();var context=instrumentation.getTargetContext();
        for(var language:List.of("el","en")){
            var profile=new ProfileStore.Profile("main-errors-"+language,"RAW_PROFILE_DATA_"+language,"ui",language);context.deleteDatabase(profile.database());Activity screen=null;
            try{
                ui(()->{UserSession.clear();UserSession.signIn(profile);});screen=instrumentation.startActivitySync(new Intent(context,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));var activity=screen;instrumentation.waitForIdleSync();
                assertGeneric(activity,language,"inventoryAction","Έλεγξε το διαθέσιμο απόθεμα και τις συνδεδεμένες εγγραφές. Το εισαγόμενο ιστορικό δεν αλλάζει.","Check available stock and linked records. Imported history cannot be changed.");
                assertGeneric(activity,language,"productionAction","Έλεγξε τη διαθέσιμη παραγωγή και τις συνδεδεμένες εγγραφές. Το εισαγόμενο ιστορικό δεν αλλάζει.","Check available production and linked records. Imported history cannot be changed.");
                assertGeneric(activity,language,"documentAction","Η ενέργεια απέτυχε.","Action failed.");

                String safe=language.equals("el")?"ΑΣΦΑΛΕΣ ΜΗΝΥΜΑ ΕΛΕΓΧΟΥ":"SAFE UI VALIDATION";
                ui(()->{
                    var form=new LinearLayout(activity);
                    invoke(activity,"saveForm",new Class[]{String.class,LinearLayout.class,Runnable.class},language.equals("el")?"Δοκιμή":"Test",form,(Runnable)()->{throw new UiValidationException(safe);});
                });
                ui(()->click(save(language)));
                assertVisible("saveForm UiValidationException",safe);
                assertHidden("saveForm UiValidationException","RAW_MAIN_SENTINEL");
                closeMessage(language);
                cancelForm(language);

                ui(()->{
                    var form=new LinearLayout(activity);
                    invoke(activity,"saveForm",new Class[]{String.class,LinearLayout.class,Runnable.class},language.equals("el")?"Δοκιμή":"Test",form,(Runnable)()->{throw new IllegalArgumentException("RAW_MAIN_SENTINEL");});
                });
                ui(()->click(save(language)));
                String expected=language.equals("el")?"Έλεγξε τα υποχρεωτικά πεδία, τα μοναδικά ονόματα, τις επιλογές και τις ημερομηνίες (YYYY-MM-DD).":"Check required fields, unique names, selections and dates (YYYY-MM-DD).";
                assertVisible("saveForm backend IllegalArgumentException",expected);
                assertHidden("saveForm backend IllegalArgumentException","RAW_MAIN_SENTINEL");
                closeMessage(language);
                cancelForm(language);

                assertVisible("profile data remains verbatim","RAW_PROFILE_DATA_"+language);
            }finally{var activity=screen;ui(()->{if(activity!=null)activity.finish();UserSession.clear();});context.deleteDatabase(profile.database());}
        }
    }
}
