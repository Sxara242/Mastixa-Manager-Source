package gr.mastixa.manager;

import android.app.Activity;
import android.content.Intent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.Spinner;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import static org.junit.Assert.*;
import java.util.*;

public class WelcomeResponsiveUiTest {
    private <T> List<T> views(View root,Class<T> type){
        var result=new ArrayList<T>();
        if(type.isInstance(root))result.add(type.cast(root));
        if(root instanceof ViewGroup group)for(int i=0;i<group.getChildCount();i++)result.addAll(views(group.getChildAt(i),type));
        return result;
    }
    private int dp(Activity activity,int value){return (int)(value*activity.getResources().getDisplayMetrics().density);}

    @Test public void signInInputsAndSelectorsUseMinimumHeightInsteadOfFixedHeight() throws Exception {
        var instrumentation=InstrumentationRegistry.getInstrumentation();
        var context=instrumentation.getTargetContext();
        Activity activity=null;
        try {
            instrumentation.runOnMainSync(UserSession::clear);
            activity=instrumentation.startActivitySync(new Intent(context,WelcomeActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));
            instrumentation.waitForIdleSync();
            var screen=activity;
            instrumentation.runOnMainSync(()->{
                var edits=views(screen.getWindow().getDecorView(),EditText.class);
                assertTrue("Welcome screen must expose sign-in inputs",edits.size()>=2);
                for(var edit:edits){
                    assertEquals("EditText height must grow with scaled text",ViewGroup.LayoutParams.WRAP_CONTENT,edit.getLayoutParams().height);
                    assertTrue("EditText must retain at least a 54dp touch target",edit.getMinimumHeight()>=dp(screen,54));
                }
                var spinners=views(screen.getWindow().getDecorView(),Spinner.class);
                assertFalse("Welcome screen must expose a language selector",spinners.isEmpty());
                for(var spinner:spinners){
                    assertEquals("Spinner height must grow with scaled text",ViewGroup.LayoutParams.WRAP_CONTENT,spinner.getLayoutParams().height);
                    assertTrue("Spinner must retain at least a 52dp touch target",spinner.getMinimumHeight()>=dp(screen,52));
                }
            });
        } finally {
            var screen=activity;
            instrumentation.runOnMainSync(()->{if(screen!=null)screen.finish();UserSession.clear();});
            instrumentation.waitForIdleSync();
        }
    }
}
