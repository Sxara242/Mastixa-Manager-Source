package gr.mastixa.manager;

import android.location.Location;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import org.json.JSONObject;
import static org.junit.Assert.*;

public class GpsTrackTest {
    private Location fix(double lon,long wall,long elapsed){var fix=new Location("gps");fix.setLongitude(lon);fix.setLatitude(38);fix.setAccuracy(6);fix.setTime(wall);fix.setElapsedRealtimeNanos(elapsed*1_000_000);return fix;}
    @Test public void pauseResumeExcludesGapAndPreservesDurationAndBackup()throws Exception{
        var context=InstrumentationRegistry.getInstrumentation().getTargetContext();assertTrue(context.getPackageName().endsWith(".checks"));String db="gps-track-test.db";context.deleteDatabase(db);
        try(var farm=new FarmStore(context,db)){farm.addField("Synthetic",1);String field=farm.fields().get(0).id();var geo=new GeoStore(farm);var track=new GpsTrack(geo,field);
            track.start("Walk",100000,1000);track.append(fix(26,101000,2000),2_000_000_000L);track.append(fix(26.001,106000,7000),7_000_000_000L);
            double first=track.current().payload().getDouble("distance_m");assertEquals(87.83,first,.5);track.change("paused",108000,9000);
            track.append(fix(27,110000,11000),11_000_000_000L);assertEquals(2,track.current().payload().getJSONArray("positions").length());
            track.change("recording",120000,21000);track.append(fix(27,121000,22000),22_000_000_000L);assertEquals(first,track.current().payload().getDouble("distance_m"),0);
            track.append(fix(27.001,126000,27000),27_000_000_000L);track.change("stopped",127000,28000);
            var payload=track.current().payload();assertEquals(15000,payload.getLong("duration_ms"));assertEquals(first*2,payload.getDouble("distance_m"),.001);assertEquals("[0,2]",payload.getJSONArray("segment_starts").toString());assertEquals(127000,payload.getLong("ended_at"));
            assertEquals(1,LocalBackup.inspect(farm,LocalBackup.snapshot(farm)));
            var malformed=new JSONObject(payload.toString()).put("distance_m",0);try{geo.save(track.current().id(),field,"track",malformed,track.current().revision());fail("Corrupt distance accepted");}catch(IllegalArgumentException expected){}
            assertEquals(first*2,geo.records(field,"track").get(0).payload().getDouble("distance_m"),.001);
        }finally{context.deleteDatabase(db);}
    }
    @Test public void interruptedRecordingRestoresPausedWithoutInventingDuration()throws Exception{
        var context=InstrumentationRegistry.getInstrumentation().getTargetContext();String db="gps-recovery-test.db";context.deleteDatabase(db);
        try(var farm=new FarmStore(context,db)){farm.addField("Synthetic",1);String field=farm.fields().get(0).id();var geo=new GeoStore(farm);var recorder=new GpsTrack(geo,field);recorder.start("Recover",100000,1000);recorder.append(fix(26,105000,6000),6_000_000_000L);String id=recorder.current().id();
            var restored=new GpsTrack(geo,field);assertFalse(restored.recording());assertEquals(id,restored.current().id());assertEquals(5000,restored.current().payload().getLong("duration_ms"));assertEquals(1,restored.current().payload().getJSONArray("positions").length());
            try{restored.start("Duplicate",110000,11000);fail();}catch(IllegalArgumentException expected){}assertEquals(1,geo.records(field,"track").size());
        }finally{context.deleteDatabase(db);}
    }
    @Test public void invalidStaleAndFutureFixesAreRejected(){var valid=fix(26,100000,1000);assertTrue(GpsFix.usable(valid,2_000_000_000L));assertFalse(GpsFix.usable(valid,32_000_000_000L));assertFalse(GpsFix.usable(valid,500_000_000L));valid.removeAccuracy();assertFalse(GpsFix.usable(valid,2_000_000_000L));valid.setAccuracy(5);valid.setLongitude(Double.NaN);assertFalse(GpsFix.usable(valid,2_000_000_000L));}
}
