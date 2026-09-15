package gr.mastixa.manager;

import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import static org.junit.Assert.*;

public class SensorDataStoreTest {
    private static String fieldId(FarmStore store, String name) {
        return store.fields().stream().filter(field -> field.name().equals(name)).findFirst().orElseThrow().id();
    }

    @Test public void persistenceProjectionIdentityFreezeAndProfileIsolation() {
        var context=InstrumentationRegistry.getInstrumentation().getTargetContext();
        context.deleteDatabase("sensor-a.db");context.deleteDatabase("sensor-b.db");
        try(FarmStore first=new FarmStore(context,"sensor-a.db");FarmStore second=new FarmStore(context,"sensor-b.db")){
            first.saveField(null,"North",2,"","",0,"");second.saveField(null,"South",2,"","",0,"");
            String north=fieldId(first,"North"),south=fieldId(second,"South");
            SensorDataStore sensors=new SensorDataStore(first);
            sensors.saveDevice(new SensorData.Device("station","Weather","manual",north,"","active",""));
            sensors.saveChannel(new SensorData.Channel("air","station","air_temperature","celsius","Air"));
            sensors.appendObservation(new SensorData.Observation("obs-2","air","2026-06-01T10:00:00Z",28.5,"good","p2"));
            sensors.appendObservation(new SensorData.Observation("obs-1","air","2026-06-01T09:00:00Z",27.0,"good","p1"));
            assertEquals(28.5,sensors.snapshot("station").channels().get(0).latestValue(),0.0001);
            assertEquals("obs-1",sensors.observations("air").get(0).id());

            sensors.saveChannel(new SensorData.Channel("air","station","air_temperature","celsius","Renamed"));
            assertEquals("Renamed",sensors.channel("air").label());
            try{
                sensors.saveChannel(new SensorData.Channel("air","station","air_humidity","percent","bad"));
                fail("Observed channel identity must be frozen");
            }catch(IllegalArgumentException expected){assertTrue(expected.getMessage().contains("identity"));}

            try{
                sensors.appendObservation(new SensorData.Observation("obs-2","air","2026-06-01T11:00:00Z",29,"good",""));
                fail("Observation ids are immutable");
            }catch(IllegalArgumentException expected){assertTrue(expected.getMessage().contains("already exists"));}

            sensors.deleteDevice("station");assertTrue(sensors.devices(false).isEmpty());assertEquals(2,sensors.observations("air").size());
            sensors.restoreDevice("station");assertEquals(1,sensors.devices(false).size());

            SensorDataStore other=new SensorDataStore(second);
            try{
                other.saveDevice(new SensorData.Device("wrong","Wrong","manual",north,"","active",""));
                fail("Cross-profile field references must fail");
            }catch(IllegalArgumentException expected){assertTrue(expected.getMessage().contains("Field"));}
            other.saveDevice(new SensorData.Device("other","Other","manual",south,"","active",""));
            assertEquals(1,other.devices(false).size());assertEquals(1,sensors.devices(false).size());
        }finally{context.deleteDatabase("sensor-a.db");context.deleteDatabase("sensor-b.db");}
    }

    @Test public void disabledDeviceRejectsNewObservationsAndCustomMetricWorks() {
        var context=InstrumentationRegistry.getInstrumentation().getTargetContext();context.deleteDatabase("sensor-rules.db");
        try(FarmStore store=new FarmStore(context,"sensor-rules.db")){
            SensorDataStore sensors=new SensorDataStore(store);
            sensors.saveDevice(new SensorData.Device("station","Station","provider","","","active",""));
            try{
                sensors.saveChannel(new SensorData.Channel("bad","station","leaf_wetness","percent",""));
                fail("Unknown metric must use custom namespace");
            }catch(IllegalArgumentException expected){assertTrue(expected.getMessage().contains("custom"));}
            sensors.saveChannel(new SensorData.Channel("leaf","station","custom.leaf_wetness","percent",""));
            sensors.saveDevice(new SensorData.Device("station","Station","provider","","","disabled",""));
            try{
                sensors.appendObservation(new SensorData.Observation("obs","leaf","2026-06-01T10:00:00Z",20,"good",""));
                fail("Disabled devices must not ingest");
            }catch(IllegalArgumentException expected){assertTrue(expected.getMessage().contains("Disabled"));}
        }finally{context.deleteDatabase("sensor-rules.db");}
    }
}
