package gr.mastixa.manager;

import android.app.Activity;
import android.app.Application;
import android.os.Bundle;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.Set;

/** Track started app Activities so internal navigation and rotation do not start the background timer. */
public final class MastixaApplication extends Application implements Application.ActivityLifecycleCallbacks {
    private final Set<Activity> started=Collections.newSetFromMap(new IdentityHashMap<>());
    @Override public void onCreate(){
        super.onCreate();
        registerActivityLifecycleCallbacks(this);
        CropTaskNotifications.initialize(this);
    }
    @Override public void onActivityStarted(Activity activity){
        boolean wasEmpty=started.isEmpty();
        started.add(activity);
        if(wasEmpty)UserSession.enteredForeground(this);
        if(UserSession.profile!=null){
            CropTaskNotifications.createChannel(this,UserSession.profile);
            CropTaskNotifications.schedule(this,UserSession.profile);
            CropTaskNotifications.requestPermissionIfNeeded(activity,UserSession.profile);
        }
    }
    @Override public void onActivityStopped(Activity activity){
        boolean removed=started.remove(activity);
        if(removed&&started.isEmpty()&&!activity.isChangingConfigurations())UserSession.enteredBackground();
    }
    @Override public void onActivityCreated(Activity activity,Bundle state){}
    @Override public void onActivityResumed(Activity activity){}
    @Override public void onActivityPaused(Activity activity){}
    @Override public void onActivitySaveInstanceState(Activity activity,Bundle state){}
    @Override public void onActivityDestroyed(Activity activity){
        boolean removed=started.remove(activity);
        if(removed&&started.isEmpty()&&!activity.isChangingConfigurations())UserSession.enteredBackground();
    }
}
