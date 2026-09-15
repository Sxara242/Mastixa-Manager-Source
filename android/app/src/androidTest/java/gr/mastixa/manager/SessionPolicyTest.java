package gr.mastixa.manager;

import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import static org.junit.Assert.*;
import java.util.concurrent.atomic.AtomicLong;

public class SessionPolicyTest {
    @Test public void backgroundBoundaryForegroundAndExplicitLogout(){
        var context=InstrumentationRegistry.getInstrumentation().getTargetContext();var now=new AtomicLong(1000);var oldClock=UserSession.clock;var p=new ProfileStore.Profile("timer-policy","Timer","timer","el");
        try{
            UserSession.clear();UserSession.clock=now::get;UserSession.enteredForeground(context);UserSession.signIn(p);UserSession.setTimeoutMinutes(context,1);
            now.addAndGet(3_600_000);assertTrue(UserSession.valid(context));UserSession.enteredBackground();now.addAndGet(59_999);assertTrue(UserSession.valid(context));now.incrementAndGet();assertFalse(UserSession.valid(context));assertNull(UserSession.profile);
            UserSession.signIn(p);UserSession.enteredForeground(context);UserSession.enteredBackground();now.addAndGet(30_000);UserSession.enteredForeground(context);now.addAndGet(600_000);assertTrue(UserSession.valid(context));UserSession.clear();assertFalse(UserSession.valid(context));
        }finally{UserSession.clear();UserSession.clock=oldClock;context.getSharedPreferences(p.preferences(),0).edit().clear().commit();}
    }
    @Test public void timeoutPreferencesArePerProfileAndDoNotRestoreLogin(){
        var context=InstrumentationRegistry.getInstrumentation().getTargetContext();ProfileStore.Profile first=new ProfileStore.Profile("timer-first","First","first","el"),second=new ProfileStore.Profile("timer-second","Second","second","en");
        try{
            UserSession.signIn(first);assertEquals(5,UserSession.timeoutMinutes(context));UserSession.setTimeoutMinutes(context,15);UserSession.signIn(second);assertEquals(5,UserSession.timeoutMinutes(context));UserSession.setTimeoutMinutes(context,30);UserSession.signIn(first);assertEquals(15,UserSession.timeoutMinutes(context));UserSession.clear();assertFalse(UserSession.valid(context));
        }finally{UserSession.clear();for(var p:new ProfileStore.Profile[]{first,second})context.getSharedPreferences(p.preferences(),0).edit().clear().commit();}
    }
}
