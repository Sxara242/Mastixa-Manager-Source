package gr.mastixa.manager;

import android.app.Activity;
import android.content.Intent;
import android.location.Location;
import android.os.*;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import java.io.*;
import java.util.*;
import static org.junit.Assert.*;

public class GisLifecycleUiTest {
    private Object field(Object target,String name){try{var f=target.getClass().getDeclaredField(name);f.setAccessible(true);return f.get(target);}catch(Exception error){throw new RuntimeException(error);}}
    private void set(Object target,String name,Object value){try{var f=target.getClass().getDeclaredField(name);f.setAccessible(true);f.set(target,value);}catch(Exception error){throw new RuntimeException(error);}}
    private void invoke(Object target,String name,Class<?>[] types,Object... values){try{var method=target.getClass().getDeclaredMethod(name,types);method.setAccessible(true);method.invoke(target,values);}catch(Exception error){throw new RuntimeException(error);}}
    private String seed(ProfileStore.Profile profile){var context=InstrumentationRegistry.getInstrumentation().getTargetContext();assertTrue(context.getPackageName().endsWith(".checks"));context.deleteDatabase(profile.database());try(var farm=new FarmStore(context,profile.database())){farm.addField("Lifecycle fixture",1);String id=farm.fields().get(0).id();new GeoStore(farm).saveGeometry(id,ParcelGeometry.manual("26 38\n26.001 38\n26.001 38.001\n26 38.001","EPSG:4326"),"fixture","",0);return id;}}
    private Activity recreate(Activity screen){var i=InstrumentationRegistry.getInstrumentation();var monitor=i.addMonitor(screen.getClass().getName(),null,false);i.runOnMainSync(screen::recreate);Activity replacement=i.waitForMonitorWithTimeout(monitor,5000);i.removeMonitor(monitor);assertNotNull("Recreated activity must start",replacement);i.waitForIdleSync();return replacement;}
    private Location fix(double lon,long wall){var fix=new Location("gps");fix.setLongitude(lon);fix.setLatitude(38.0005);fix.setAccuracy(500);fix.setTime(wall);fix.setElapsedRealtimeNanos(SystemClock.elapsedRealtimeNanos());return fix;}

    @Test public void recreationPreservesViewportAndDurableTrackWhilePausingRecording()throws Exception{
        var i=InstrumentationRegistry.getInstrumentation();var context=i.getTargetContext();var profile=new ProfileStore.Profile("gis-lifecycle-ui","GIS lifecycle","test","en");String id=seed(profile);Activity screen=null;
        try{
            i.runOnMainSync(()->{UserSession.clear();UserSession.signIn(profile);});screen=i.startActivitySync(new Intent(context,ParcelMapActivity.class).putExtra("field_id",id).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));var a=(ParcelMapActivity)screen;i.waitForIdleSync();
            i.runOnMainSync(()->{
                var map=(ParcelMapView)field(a,"map");map.restoreViewport(new double[]{123,456,.5});map.vertices=false;map.boundary=false;
                var track=(GpsTrack)field(a,"track");track.start("Lifecycle track",System.currentTimeMillis(),SystemClock.elapsedRealtime());
                long wall=System.currentTimeMillis();a.onLocationChanged(fix(26.0004,wall));a.onLocationChanged(fix(26.0005,wall+1));
                assertFalse("Current track must be visible without reopening saved tracks",((List<?>)field(map,"trackSegments")).isEmpty());
                assertNotNull("Low accuracy is shown, not silently treated as precise",field(map,"location"));
            });
            screen=recreate(screen);var b=(ParcelMapActivity)screen;
            i.runOnMainSync(()->{var map=(ParcelMapView)field(b,"map");assertArrayEquals(new double[]{123,456,.5},map.viewport(),0);assertFalse(map.vertices);assertFalse(map.boundary);assertNull("Do not resurrect an old GPS fix",field(map,"location"));assertFalse(((GpsTrack)field(b,"track")).recording());assertFalse(((List<?>)field(map,"trackSegments")).isEmpty());});
            try(var farm=new FarmStore(context,profile.database())){var rows=new GeoStore(farm).records(id,"track");assertEquals(1,rows.size());assertEquals("paused",rows.get(0).payload().getString("state"));assertEquals(2,rows.get(0).payload().getJSONArray("positions").length());assertEquals(1,LocalBackup.inspect(farm,LocalBackup.snapshot(farm)));}
        }finally{var last=screen;i.runOnMainSync(()->{if(last!=null)last.finish();UserSession.clear();});}
    }
    @Test public void recreatedExportRetainsPreparedFileAndCancellationCleansOnlyTemporaryFile()throws Exception{
        var i=InstrumentationRegistry.getInstrumentation();var context=i.getTargetContext();var profile=new ProfileStore.Profile("gis-export-lifecycle-ui","Export lifecycle","test","en");String id=seed(profile);Activity screen=null;File temporary=new File(context.getCacheDir(),"coordinates-00000000-0000-0000-0000-000000000004.tmp");byte[] before;
        try(var farm=new FarmStore(context,profile.database())){before=LocalBackup.snapshot(farm);}
        try{
            i.runOnMainSync(()->{UserSession.clear();UserSession.signIn(profile);});screen=i.startActivitySync(new Intent(context,CoordinateExportActivity.class).putExtra("field_id",id).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));i.waitForIdleSync();
            try(FileOutputStream out=new FileOutputStream(temporary)){out.write("synthetic prepared export".getBytes(java.nio.charset.StandardCharsets.UTF_8));}
            var a=screen;i.runOnMainSync(()->set(a,"pending",temporary));screen=recreate(screen);var b=screen;
            i.runOnMainSync(()->{assertEquals(temporary,field(b,"pending"));assertTrue(temporary.isFile());invoke(b,"onActivityResult",new Class[]{int.class,int.class,Intent.class},203,Activity.RESULT_CANCELED,null);assertNull(field(b,"pending"));assertFalse(temporary.exists());});
            try(var farm=new FarmStore(context,profile.database())){assertArrayEquals(before,LocalBackup.snapshot(farm));}
        }finally{var last=screen;i.runOnMainSync(()->{if(last!=null)last.finish();UserSession.clear();});temporary.delete();}
    }
}
