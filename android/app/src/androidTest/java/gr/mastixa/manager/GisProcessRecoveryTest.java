package gr.mastixa.manager;

import android.app.Activity;
import android.content.Intent;
import android.location.Location;
import androidx.test.platform.app.InstrumentationRegistry;
import org.json.*;
import org.junit.*;
import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import static org.junit.Assert.*;

/** Host runs prepare, force-stops ONLY .checks, then runs verify in a new process. */
public class GisProcessRecoveryTest {
    @Test public void durableGeometryPendingSyncAndRecordingSurviveProcessLoss()throws Exception{
        var i=InstrumentationRegistry.getInstrumentation();var context=i.getTargetContext();String stage=InstrumentationRegistry.getArguments().getString("process_stage","");
        Assume.assumeTrue("Requires explicit host prepare/force-stop/verify sequence",stage.equals("prepare")||stage.equals("verify"));
        assertEquals("gr.mastixa.manager.checks",context.getPackageName());
        var profile=new ProfileStore.Profile("gis-process-recovery-test","Process recovery","test","en");File evidence=new File(context.getFilesDir(),"qa-process-recovery.json");String dataset="00000000-0000-0000-0000-000000000010";
        if(stage.equals("prepare")){
            context.deleteDatabase(profile.database());
            try(var farm=new FarmStore(context,profile.database())){
                farm.addField("Durable synthetic field",1);String id=farm.fields().get(0).id();var geo=new GeoStore(farm);
                geo.saveGeometry(id,ParcelGeometry.manual("500000.12345678 4200000.12345678\n500010.12345678 4200000.12345678\n500010.12345678 4200010.12345678\n500000.12345678 4200010.12345678","EPSG:2100"),"fixture","",0);
                String point=geo.savePoint(null,id,"note","Pending GPS point","Must survive process loss",24.001,37.95,5,0);
                var track=new GpsTrack(geo,id);track.start("Interrupted recording",100000,1000);var fix=new Location("gps");fix.setLongitude(24.001);fix.setLatitude(37.95);fix.setAccuracy(5);fix.setTime(105000);fix.setElapsedRealtimeNanos(6000000000L);track.append(fix,6000000000L);
                var repo=new GisSyncRepository(farm,dataset);repo.acknowledge(id,GisSyncContract.fingerprint(repo.document(id)),1);repo.setCursor(1);
                JSONObject out=new JSONObject().put("pid",android.os.Process.myPid()).put("field",id).put("point",point).put("track",track.current().id()).put("documents",GisSyncContract.canonical(new JSONArray(repo.documents())));
                Files.write(evidence.toPath(),out.toString().getBytes(StandardCharsets.UTF_8));assertEquals("recording",track.current().payload().getString("state"));assertNull(repo.state(point));assertEquals(3,repo.documents().size());
            }
            return;
        }
        JSONObject expected=new JSONObject(new String(Files.readAllBytes(evidence.toPath()),StandardCharsets.UTF_8));String id=expected.getString("field");assertNotEquals("Verification must run in a different process",expected.getInt("pid"),android.os.Process.myPid());
        try(var farm=new FarmStore(context,profile.database())){
            var repo=new GisSyncRepository(farm,dataset);assertEquals(expected.getString("documents"),GisSyncContract.canonical(new JSONArray(repo.documents())));assertEquals(1,repo.cursor());assertNull(repo.state(expected.getString("point")));
        }
        Activity screen=null;
        try{
            i.runOnMainSync(()->{UserSession.clear();UserSession.signIn(profile);});screen=i.startActivitySync(new Intent(context,ParcelMapActivity.class).putExtra("field_id",id).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));i.waitForIdleSync();assertFalse(screen.isFinishing());
            try(var farm=new FarmStore(context,profile.database())){
                var geo=new GeoStore(farm);var tracks=geo.records(id,"track");assertEquals(1,tracks.size());assertEquals(expected.getString("track"),tracks.get(0).id());var payload=tracks.get(0).payload();assertEquals("paused",payload.getString("state"));assertEquals(5000,payload.getLong("duration_ms"));assertEquals(1,payload.getJSONArray("positions").length());assertEquals(1,geo.records(id,"point").size());assertEquals("EPSG:2100",GeoStore.geometry(geo.parcel(id)).sourceCrs);assertEquals(1,LocalBackup.inspect(farm,LocalBackup.snapshot(farm)));
                try(var cursor=farm.getReadableDatabase().rawQuery("SELECT 1 FROM pending_changes WHERE entity='gis_records' AND entity_id=?",new String[]{expected.getString("point")})){assertTrue(cursor.moveToFirst());}
            }
        }finally{var last=screen;i.runOnMainSync(()->{if(last!=null)last.finish();UserSession.clear();});}
    }
}
