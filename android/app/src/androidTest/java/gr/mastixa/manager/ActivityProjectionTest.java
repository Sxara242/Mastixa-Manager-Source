package gr.mastixa.manager;

import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import static org.junit.Assert.*;
import java.time.Instant;
import java.util.Set;
import java.util.stream.Collectors;

public class ActivityProjectionTest {
    private final android.content.Context context = InstrumentationRegistry.getInstrumentation().getTargetContext();

    private void field(android.database.sqlite.SQLiteDatabase db, String id, String name) {
        db.execSQL(
            "INSERT INTO fields(id,name,area,revision,updated_at,kaek,location,trees,notes,deleted_at) VALUES(?,?,1,1,1,'','',0,'',NULL)",
            new Object[]{id,name}
        );
    }

    private void seedSources(FarmStore store, String field) throws Exception {
        var db = store.getWritableDatabase();
        db.execSQL("INSERT INTO production(id,entry_date,product_id,product,field_id,quantity_kg,notes,windows_id,revision,updated_at,deleted_at) VALUES('prod','2026-09-10','p','Μαστίχα',?,4,'harvest note','',1,1,NULL)",new Object[]{field});
        db.execSQL("INSERT INTO farm_activities(id,activity_date,field_id,category,status,duration_minutes,water_quantity_m3,product,dose,dose_unit,cost,responsible,notes,inventory_item_id,inventory_quantity,quantity,unit,description,movement_id,windows_id,revision,updated_at,deleted_at) VALUES('irr','2026-09-09',?,'Πότισμα','Προγραμματισμένη',30,0,'',0,'',0,'','irrigation note','',0,0,'','Πότισμα','','',1,1,NULL)",new Object[]{field});
        db.execSQL("INSERT INTO farm_activities(id,activity_date,field_id,category,status,duration_minutes,water_quantity_m3,product,dose,dose_unit,cost,responsible,notes,inventory_item_id,inventory_quantity,quantity,unit,description,movement_id,windows_id,revision,updated_at,deleted_at) VALUES('fert','2026-09-08',?,'Λίπανση','Ολοκληρώθηκε',0,0,'Fertilizer',2,'kg',3,'','fertilization note','',0,0,'','Λίπανση','','',1,1,NULL)",new Object[]{field});
        db.execSQL("INSERT INTO planting_batches(id,planting_date,field_id,trees_planted,trees_alive,material_type,source,variety,spacing,cost,notes,windows_id,revision,updated_at,deleted_at) VALUES('plant','2026-09-07',?,10,9,'Δενδρύλλιο','','','',0,'plant note','',1,1,NULL)",new Object[]{field});
        db.execSQL("INSERT INTO plant_protection_records(id,application_date,field_id,inventory_item_id,purpose,product_name,active_ingredient,authorization_number,dose,dose_unit,spray_volume_l,area_stremma,applicator,weather,harvest_interval_days,cost,notes,inventory_quantity,movement_id,windows_id,revision,updated_at,deleted_at) VALUES('protect','2026-09-06',?,'','Έλεγχος','Product','','',0,'',0,0,'','',0,0,'protection note',0,'','',1,1,NULL)",new Object[]{field});
        db.execSQL("INSERT INTO labor_entries(id,work_date,field_id,worker_id,work_type,hours,hourly_rate,cost,notes,windows_id,revision,updated_at,deleted_at) VALUES('labor','2026-09-05',?,'worker','Κλάδεμα',2,0,0,'labor note','',1,1,NULL)",new Object[]{field});
        long recorded = Instant.parse("2026-09-10T12:00:00Z").toEpochMilli();
        String payload = new org.json.JSONObject().put("point_type","note").put("title","Παρατήρηση").put("notes","GIS note").put("longitude",26.1).put("latitude",38.3).put("accuracy",2).toString();
        db.execSQL("INSERT INTO gis_records(id,field_id,kind,payload,created_at,updated_at,deleted_at,last_sync_at,revision) VALUES('geo',?,'point',?,?,?,NULL,0,1)",new Object[]{field,payload,recorded,recorded});
        String ignored = new org.json.JSONObject().put("point_type","tree").put("title","Tree").put("notes","").put("longitude",26.1).put("latitude",38.3).put("accuracy",2).toString();
        db.execSQL("INSERT INTO gis_records(id,field_id,kind,payload,created_at,updated_at,deleted_at,last_sync_at,revision) VALUES('tree',?,'point',?,?,?,NULL,0,1)",new Object[]{field,ignored,recorded,recorded});
    }

    @Test public void sixSourcesFollowContractOrderingStatusAndFieldIsolation() throws Exception {
        String name="phase9e-activity-projection.db"; context.deleteDatabase(name);
        try(var store=new FarmStore(context,name)) {
            var db=store.getWritableDatabase(); field(db,"f1","Field 1"); field(db,"f2","Field 2"); seedSources(store,"f1");
            db.execSQL("INSERT INTO production(id,entry_date,product_id,product,field_id,quantity_kg,notes,windows_id,revision,updated_at,deleted_at) VALUES('other','2026-12-31','p','Other','f2',1,'','',1,1,NULL)");

            var events=ActivityProjection.project(store,"profile-a","f1");
            assertEquals(7,events.size());
            assertEquals("geo_point",events.get(0).sourceRef().type());
            assertEquals("2026-09-10",events.get(0).eventDate());
            assertEquals("recorded",events.get(0).timeBasis());
            assertNotNull(events.get(0).eventAt());
            assertEquals("production",events.get(1).sourceRef().type());
            assertEquals("occurred",events.get(1).timeBasis());
            assertNull(events.get(1).eventAt());
            Set<String> kinds=events.stream().map(ActivityProjection.Event::kind).collect(Collectors.toSet());
            assertEquals(Set.of("harvest","irrigation","fertilization","planting","plant_protection","cultivation_work","observation"),kinds);
            var irrigation=events.stream().filter(x->x.kind().equals("irrigation")).findFirst().orElseThrow();
            assertEquals("planned",irrigation.status());
            assertEquals("profile-a",irrigation.scopeId());
            assertEquals("f1",irrigation.fieldId());
            assertTrue(events.stream().noneMatch(x->x.sourceRef().id().equals("other")));
            assertTrue(events.stream().noneMatch(x->x.sourceRef().id().equals("tree")));
        } finally { context.deleteDatabase(name); }
    }

    @Test public void invalidDateTombstonesAndDeletedParentsAreHandledWithoutInventedTime() throws Exception {
        String name="phase9e-activity-lifecycle.db"; context.deleteDatabase(name);
        try(var store=new FarmStore(context,name)) {
            var db=store.getWritableDatabase(); field(db,"f1","Field 1"); seedSources(store,"f1");
            db.execSQL("UPDATE production SET entry_date='not-a-date' WHERE id='prod'");
            var events=ActivityProjection.project(store,"profile-a","f1");
            var harvest=events.stream().filter(x->x.sourceRef().id().equals("prod")).findFirst().orElseThrow();
            assertNull(harvest.eventDate()); assertNull(harvest.eventAt()); assertEquals("unknown",harvest.timeBasis());
            assertEquals("prod",events.get(events.size()-1).sourceRef().id());

            db.execSQL("UPDATE farm_activities SET deleted_at=9 WHERE id='irr'");
            assertTrue(ActivityProjection.project(store,"profile-a","f1").stream().noneMatch(x->x.sourceRef().id().equals("irr")));
            db.execSQL("UPDATE fields SET deleted_at=10 WHERE id='f1'");
            assertTrue(ActivityProjection.project(store,"profile-a","f1").isEmpty());
            try { ActivityProjection.project(store,"  ","f1"); fail(); } catch(IllegalArgumentException expected) {}
        } finally { context.deleteDatabase(name); }
    }
}
