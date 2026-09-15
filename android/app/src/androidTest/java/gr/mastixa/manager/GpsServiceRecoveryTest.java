package gr.mastixa.manager;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.location.LocationManager;
import android.location.Location;
import android.os.SystemClock;
import android.widget.TextView;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.*;
import static org.junit.Assert.*;

/** Opt-in host test: grant checks-only permissions, disable location, then enable at the marker. */
public class GpsServiceRecoveryTest {
    private Object field(Object target,String name)throws Exception{var f=target.getClass().getDeclaredField(name);f.setAccessible(true);return f.get(target);}
    private void invoke(Object target,String name)throws Exception{var m=target.getClass().getDeclaredMethod(name);m.setAccessible(true);m.invoke(target);}
    private Location fix(long elapsed,long wall){var value=new Location("gps");value.setLongitude(26);value.setLatitude(38);value.setAccuracy(5);value.setElapsedRealtimeNanos(elapsed);value.setTime(wall);return value;}
    @Test public void disabledGpsKeepsStatusAndRecoversWithoutReopening()throws Exception{
        Assume.assumeTrue("Requires host location-service transition",InstrumentationRegistry.getArguments().getString("gps_recovery","").equals("true"));
        var i=InstrumentationRegistry.getInstrumentation();var c=i.getTargetContext();assertEquals("gr.mastixa.manager.checks",c.getPackageName());assertEquals(PackageManager.PERMISSION_GRANTED,c.checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION));
        var locations=(LocationManager)c.getSystemService(android.content.Context.LOCATION_SERVICE);assertFalse("Host must actually disable location",locations.isProviderEnabled(LocationManager.GPS_PROVIDER));
        var profile=new ProfileStore.Profile("gps-service-recovery-test","GPS recovery","test","en");c.deleteDatabase(profile.database());String id;byte[] before;
        try(var farm=new FarmStore(c,profile.database())){farm.addField("GPS service fixture",1);id=farm.fields().get(0).id();before=LocalBackup.snapshot(farm);}
        i.runOnMainSync(()->{UserSession.clear();UserSession.signIn(profile);});var screen=(ParcelMapActivity)i.startActivitySync(new Intent(c,ParcelMapActivity.class).putExtra("field_id",id).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));
        try{
            Location oldSessionFix=fix(SystemClock.elapsedRealtimeNanos(),System.currentTimeMillis());
            i.runOnMainSync(()->{try{invoke(screen,"enableGps");assertTrue(((TextView)field(screen,"gpsStatus")).getText().toString().contains("disabled"));invoke(screen,"showFix");assertTrue("Freshness refresh must retain actionable disabled-service status",((TextView)field(screen,"gpsStatus")).getText().toString().contains("disabled"));assertTrue("Listen for provider return even while it is disabled",(boolean)field(screen,"listening"));}catch(Exception e){throw new RuntimeException(e);}});
            android.os.Bundle marker=new android.os.Bundle();marker.putString("stream","GPS_QA_READY_ENABLE\n");i.sendStatus(0,marker);
            boolean[] recovered={false};long deadline=SystemClock.elapsedRealtime()+30000;
            while(!recovered[0]&&SystemClock.elapsedRealtime()<deadline){SystemClock.sleep(100);i.runOnMainSync(()->{try{recovered[0]=locations.isProviderEnabled(LocationManager.GPS_PROVIDER)&&(boolean)field(screen,"listening")&&!((TextView)field(screen,"gpsStatus")).getText().toString().contains("disabled");}catch(Exception e){throw new RuntimeException(e);}});}
            assertTrue("Same map must recover when location service returns",recovered[0]);assertFalse(screen.isFinishing());
            i.runOnMainSync(()->{try{
                invoke(screen,"stopGps"); // Isolate deterministic fix injection after real service/callback recovery.
                Object previousFix=field(screen,"fix"),previousMapFix=field(field(screen,"map"),"location");
                assertTrue("The old-session sample is still fresh by the 30-second rule",GpsFix.usable(oldSessionFix,SystemClock.elapsedRealtimeNanos()));
                screen.onLocationChanged(oldSessionFix);
                assertSame("A fix from before provider activation must not return",previousFix,field(screen,"fix"));assertSame(previousMapFix,field(field(screen,"map"),"location"));
                assertEquals(profile.id(),((ProfileStore.Profile)field(screen,"profile")).id());
            }catch(Exception e){throw new RuntimeException(e);}});
            try(var farm=new FarmStore(c,profile.database())){assertArrayEquals("Recovery alone must not write GPS data",before,LocalBackup.snapshot(farm));}
            i.runOnMainSync(()->{try{
                var track=(GpsTrack)field(screen,"track");track.start("Recovery track",System.currentTimeMillis(),SystemClock.elapsedRealtime());
                Location fresh=fix(SystemClock.elapsedRealtimeNanos(),System.currentTimeMillis()+1);
                screen.onLocationChanged(fresh);screen.onLocationChanged(new Location(fresh));screen.onLocationChanged(oldSessionFix);
                assertEquals("Duplicate and old callbacks must not append records",1,track.current().payload().getJSONArray("positions").length());
                assertEquals(fresh.getElapsedRealtimeNanos(),((Location)field(screen,"fix")).getElapsedRealtimeNanos());
                track.change("paused",System.currentTimeMillis(),SystemClock.elapsedRealtime());
                // A queued callback from this screen must not write into either profile after a session switch.
                UserSession.clear();UserSession.signIn(new ProfileStore.Profile("gps-service-other-test","Other context","test","en"));
                screen.onLocationChanged(fix(SystemClock.elapsedRealtimeNanos(),System.currentTimeMillis()+2));
                assertEquals(1,track.current().payload().getJSONArray("positions").length());
            }catch(Exception e){throw new RuntimeException(e);}});
            try(var farm=new FarmStore(c,profile.database())){var geo=new GeoStore(farm);assertEquals(1,geo.records(id,"track").size());assertEquals(1,geo.records(id,"track").get(0).payload().getJSONArray("positions").length());assertTrue(geo.records(id,"point").isEmpty());}
        }finally{i.runOnMainSync(()->{screen.finish();UserSession.clear();});}
    }
}
