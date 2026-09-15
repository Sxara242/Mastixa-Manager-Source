package gr.mastixa.manager;

import android.app.Activity;
import android.content.Intent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import java.util.ArrayList;
import java.util.List;
import static org.junit.Assert.*;

public class MainResponsiveUiTest {
    @Test public void mainShellButtonsUseMinimumHeightInsteadOfFixedHeight() throws Exception {
        var instrumentation=InstrumentationRegistry.getInstrumentation();
        var context=instrumentation.getTargetContext();
        var profile=new ProfileStore.Profile("main-responsive-ui","Responsive UI","ui","el");
        context.deleteDatabase(profile.database());
        Activity activity=null;
        try {
            instrumentation.runOnMainSync(()->{UserSession.clear();UserSession.signIn(profile);});
            activity=instrumentation.startActivitySync(new Intent(context,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));
            instrumentation.waitForIdleSync();
            var screen=activity;
            instrumentation.runOnMainSync(()->{
                var root=screen.getWindow().getDecorView();
                var language=new AppLanguage(screen,profile.language());
                for(String sourceLabel:new String[]{"Αρχική","Αγροτεμάχια","Ενότητες","Backup"}) {
                    String label=language.t(sourceLabel);
                    var tab=button(root,label);
                    assertEquals("Bottom navigation should grow with scaled text: "+label,ViewGroup.LayoutParams.WRAP_CONTENT,tab.getLayoutParams().height);
                    assertTrue("Bottom navigation minimum touch height: "+label,tab.getMinHeight()>=dp(screen,52));
                }
                button(root,language.t("Αγροτεμάχια")).performClick();
            });
            instrumentation.waitForIdleSync();
            instrumentation.runOnMainSync(()->{
                var back=button(screen.getWindow().getDecorView(),"‹ Πίσω");
                assertEquals("Back button should grow with scaled text",ViewGroup.LayoutParams.WRAP_CONTENT,back.getLayoutParams().height);
                assertTrue("Back button minimum touch height",back.getMinHeight()>=dp(screen,48));
            });
        } finally {
            var screen=activity;
            instrumentation.runOnMainSync(()->{if(screen!=null)screen.finish();UserSession.clear();});
            instrumentation.waitForIdleSync();
        }
    }

    private int dp(Activity activity,int value){return (int)(activity.getResources().getDisplayMetrics().density*value);}
    private Button button(View root,String label){
        for(var view:views(root))if(view instanceof Button button&&label.contentEquals(button.getText()))return button;
        fail("Missing button: "+label);return null;
    }
    private List<View> views(View root){
        var result=new ArrayList<View>();result.add(root);
        if(root instanceof ViewGroup group)for(int i=0;i<group.getChildCount();i++)result.addAll(views(group.getChildAt(i)));
        return result;
    }
}
