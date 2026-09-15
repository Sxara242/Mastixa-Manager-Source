package gr.mastixa.manager;

import android.content.Context;
import android.os.SystemClock;
import java.util.function.LongSupplier;

/** In-memory session. Background grace never stores a password or reusable login token. */
final class UserSession {
    static ProfileStore.Profile profile;
    static LongSupplier clock=SystemClock::elapsedRealtime;
    private static long backgroundAt=-1;
    private static boolean foreground;
    private UserSession() {}
    static int timeoutMinutes(Context context){
        if(profile==null)return 5;
        int value=context.getSharedPreferences(profile.preferences(),Context.MODE_PRIVATE).getInt("session_timeout_minutes",5);
        return value==1||value==5||value==15||value==30?value:5;
    }
    static void setTimeoutMinutes(Context context,int minutes){
        if(profile==null||!(minutes==1||minutes==5||minutes==15||minutes==30))throw new IllegalArgumentException("Invalid session timeout");
        context.getSharedPreferences(profile.preferences(),Context.MODE_PRIVATE).edit().putInt("session_timeout_minutes",minutes).apply();
    }
    static boolean valid(Context context){
        if(profile==null)return false;
        long now=clock.getAsLong();
        if(backgroundAt>=0&&(now<backgroundAt||now-backgroundAt>=timeoutMinutes(context)*60_000L)){clear();return false;}
        return true;
    }
    static void signIn(ProfileStore.Profile authenticated){profile=authenticated;backgroundAt=foreground?-1:clock.getAsLong();}
    static void enteredForeground(Context context){valid(context);foreground=true;backgroundAt=-1;}
    static void enteredBackground(){foreground=false;if(profile!=null&&backgroundAt<0)backgroundAt=clock.getAsLong();}
    static void clear(){profile=null;backgroundAt=-1;}
}
