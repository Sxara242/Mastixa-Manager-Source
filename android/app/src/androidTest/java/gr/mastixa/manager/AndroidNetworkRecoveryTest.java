package gr.mastixa.manager;

import android.app.Activity;
import android.content.Intent;
import android.net.ConnectivityManager;
import android.net.NetworkCapabilities;
import android.os.*;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import org.junit.Assume;
import java.io.*;
import java.util.*;
import java.util.function.BooleanSupplier;
import static org.junit.Assert.*;

/** Opt-in live emulator QA. Host toggles networking at the two explicit stage markers. */
public class AndroidNetworkRecoveryTest {
    @Test public void lateRecoveryCallbacksCannotRestorePreviousProfileContext()throws Exception{
        var i=InstrumentationRegistry.getInstrumentation();var context=i.getTargetContext();assertEquals("gr.mastixa.manager.checks",context.getPackageName());
        var profiles=List.of(new ProfileStore.Profile("network-context-a-test","Context A","test","en"),new ProfileStore.Profile("network-context-b-test","Context B","test","en"));
        String sharedId=UUID.randomUUID().toString();var snapshots=new ArrayList<byte[]>();
        for(int index=0;index<profiles.size();index++){
            var profile=profiles.get(index);context.deleteDatabase(profile.database());
            try(var farm=new FarmStore(context,profile.database())){
                farm.addField("Context "+index,1);farm.getWritableDatabase().execSQL("UPDATE fields SET id=?",new Object[]{sharedId});
                var geo=new GeoStore(farm);double lon=26+index;
                geo.saveGeometry(sharedId,ParcelGeometry.manual(lon+" 38\n"+(lon+.001)+" 38\n"+(lon+.001)+" 38.001\n"+lon+" 38.001","EPSG:4326"),"context fixture","",0);
                geo.savePoint(null,sharedId,"note","Profile "+index,"Private point",lon,38,5,0);snapshots.add(LocalBackup.snapshot(farm));
            }
        }
        Activity screen=null;var redraws=new java.util.concurrent.atomic.AtomicInteger();
        var oldProvider=new AndroidBasemap(context,AndroidBasemap.OSM,redraws::incrementAndGet);
        try{
            i.runOnMainSync(()->{UserSession.clear();UserSession.signIn(profiles.get(0));});
            screen=i.startActivitySync(new Intent(context,ParcelMapActivity.class).putExtra("field_id",sharedId).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));var oldScreen=screen;
            i.runOnMainSync(()->{
                var oldMap=(ParcelMapView)field(oldScreen,"map");oldMap.setBasemap(oldProvider);
                // Exercise the same close path used by onPause without issuing tile requests.
                oldMap.setBasemap(null);oldScreen.finish();
            });
            waitFor("Old profile must finish pausing",()->!(boolean)field(oldScreen,"resumed"),5000);
            i.runOnMainSync(()->{UserSession.clear();UserSession.signIn(profiles.get(1));});
            screen=i.startActivitySync(new Intent(context,ParcelMapActivity.class).putExtra("field_id",sharedId).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));var current=screen;i.waitForIdleSync();
            var oldCallbacks=(ConnectivityManager.NetworkCallback)field(oldScreen,"networkCallback");var callbacks=(ConnectivityManager.NetworkCallback)field(current,"networkCallback");
            i.runOnMainSync(()->{
                oldProvider.networkAvailable();oldCallbacks.onAvailable(null);oldCallbacks.onCapabilitiesChanged(null,new NetworkCapabilities());callbacks.onAvailable(null);
            });i.waitForIdleSync();
            i.runOnMainSync(()->{
                assertEquals("Closed provider must not request a stale redraw",0,redraws.get());assertTrue((boolean)field(oldProvider,"closed"));
                assertEquals(profiles.get(1).id(),((ProfileStore.Profile)field(current,"profile")).id());
                var map=(ParcelMapView)field(current,"map");var rings=(List<List<double[]>>)field(map,"rings");var points=(List<double[]>)field(map,"savedPoints");
                assertArrayEquals(ParcelMapView.project(27,38),rings.get(0).get(0),0);assertEquals(1,points.size());assertArrayEquals(ParcelMapView.project(27,38),points.get(0),0);
                assertNull("Old GPS fix must not transfer",field(map,"location"));assertTrue("Old track must not transfer",((List<?>)field(map,"trackSegments")).isEmpty());assertFalse(current.isFinishing());
            });
            for(int index=0;index<profiles.size();index++)try(var farm=new FarmStore(context,profiles.get(index).database())){assertArrayEquals(snapshots.get(index),LocalBackup.snapshot(farm));}
        }finally{var last=screen;i.runOnMainSync(()->{oldProvider.close();if(last!=null)last.finish();UserSession.clear();});}
    }
    private Object field(Object target,String name){try{var f=target.getClass().getDeclaredField(name);f.setAccessible(true);return f.get(target);}catch(Exception error){throw new RuntimeException(error);}}
    private void stage(String name)throws Exception{var i=InstrumentationRegistry.getInstrumentation();try(var out=new FileOutputStream(new File(i.getTargetContext().getExternalFilesDir(null),"network-recovery-stage.txt"))){out.write(name.getBytes(java.nio.charset.StandardCharsets.UTF_8));}var status=new Bundle();status.putString("stream","\nNETWORK_QA_"+name+"\n");i.sendStatus(0,status);}
    private void waitFor(String description,BooleanSupplier condition,long timeout)throws Exception{var i=InstrumentationRegistry.getInstrumentation();long deadline=SystemClock.elapsedRealtime()+timeout;boolean[] done={false};while(!done[0]&&SystemClock.elapsedRealtime()<deadline){i.runOnMainSync(()->done[0]=condition.getAsBoolean());if(!done[0])Thread.sleep(100);}assertTrue(description,done[0]);}
    private boolean online(ConnectivityManager manager){var caps=manager.getNetworkCapabilities(manager.getActiveNetwork());return caps!=null&&caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED);}
    private int loaded(ParcelMapView map){var provider=field(map,"basemap");return provider==null?0:((android.util.LruCache<?,?>)field(provider,"images")).size();}
    @Test public void cachedTilesOfflineAndUncachedTilesRecoverWithoutReopening()throws Exception{
        Assume.assumeTrue("Requires explicit host-controlled live network cycle",InstrumentationRegistry.getArguments().getString("live_network","").equals("true"));
        var i=InstrumentationRegistry.getInstrumentation();var context=i.getTargetContext();assertTrue(context.getPackageName().endsWith(".checks"));var profile=new ProfileStore.Profile("network-recovery-ui","Network QA","test","en");context.deleteDatabase(profile.database());String id;byte[] before;
        try(var farm=new FarmStore(context,profile.database())){farm.addField("Synthetic network parcel",1);id=farm.fields().get(0).id();new GeoStore(farm).saveGeometry(id,ParcelGeometry.manual("26 38\n26.001 38\n26.001 38.001\n26 38.001","EPSG:4326"),"fixture","",0);before=LocalBackup.snapshot(farm);}
        var manager=(ConnectivityManager)context.getSystemService(android.content.Context.CONNECTIVITY_SERVICE);Activity screen=null;
        try{
            waitFor("Internet available before live test",()->online(manager),30000);
            i.runOnMainSync(()->{UserSession.clear();UserSession.signIn(profile);});screen=i.startActivitySync(new Intent(context,ParcelMapActivity.class).putExtra("field_id",id).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));var a=screen;var map=(ParcelMapView)field(a,"map");
            i.runOnMainSync(()->map.setBasemap(new AndroidBasemap(context,AndroidBasemap.OSM,map::invalidate)));
            waitFor("Official visible OSM tiles loaded",()->loaded(map)>0,30000);stage("READY_OFFLINE");
            waitFor("Host disabled internet",()->!online(manager),90000);
            long cacheHits=android.net.http.HttpResponseCache.getInstalled().getHitCount();
            i.runOnMainSync(()->map.setBasemap(new AndroidBasemap(context,AndroidBasemap.OSM,map::invalidate)));
            waitFor("Fresh provider reads cached tiles while offline",()->loaded(map)>0,15000);
            assertTrue("Offline tiles must come from the HTTP disk cache",android.net.http.HttpResponseCache.getInstalled().getHitCount()>cacheHits);
            i.runOnMainSync(()->{double[] viewport=map.viewport();viewport[0]+=200000+(SystemClock.elapsedRealtime()%1000000);map.restoreViewport(viewport);map.setBasemap(new AndroidBasemap(context,AndroidBasemap.OSM,map::invalidate));});
            waitFor("Uncached offline tile failure must finish",()->{var provider=field(map,"basemap");return !((Map<?,?>)field(provider,"failed")).isEmpty();},15000);
            assertFalse(online(manager));stage("READY_RESTORE");waitFor("Host restored internet",()->online(manager),90000);
            waitFor("Uncached tiles recover in the same map without pan/reopen",()->loaded(map)>0,15000);
            try(var farm=new FarmStore(context,profile.database())){assertArrayEquals(before,LocalBackup.snapshot(farm));}
            stage("PASSED");
        }finally{var last=screen;i.runOnMainSync(()->{if(last!=null)last.finish();UserSession.clear();});}
    }
}
