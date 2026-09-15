package gr.mastixa.manager;

import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import static org.junit.Assert.*;
import java.time.Instant;

public class ActivityProjectionSyncIdentityTest {
    private final android.content.Context context = InstrumentationRegistry.getInstrumentation().getTargetContext();

    @Test public void syncRefRequiresVerifiedDatasetPointAndFieldIdentity() throws Exception {
        String name="phase9f-android-sync-ref.db"; context.deleteDatabase(name);
        String dataset="11111111-1111-4111-8111-111111111111";
        String field="22222222-2222-4222-8222-222222222222";
        String point="33333333-3333-4333-8333-333333333333";
        String production="44444444-4444-4444-8444-444444444444";
        try(var store=new FarmStore(context,name)) {
            var db=store.getWritableDatabase();
            db.execSQL("INSERT INTO fields(id,name,area,revision,updated_at,kaek,location,trees,notes,deleted_at) VALUES(?, 'Field',1,1,1,'','',0,'',NULL)",new Object[]{field});
            db.execSQL("INSERT INTO production(id,entry_date,product_id,product,field_id,quantity_kg,notes,windows_id,revision,updated_at,deleted_at) VALUES(?,'2026-09-10','p','Μαστίχα',?,1,'','',1,1,NULL)",new Object[]{production,field});
            long recorded=Instant.parse("2026-09-10T12:00:00Z").toEpochMilli();
            String payload=new org.json.JSONObject().put("point_type","note").put("title","Observation").put("notes","").put("longitude",26.1).put("latitude",38.3).put("accuracy",2).toString();
            db.execSQL("INSERT INTO gis_records(id,field_id,kind,payload,created_at,updated_at,deleted_at,last_sync_at,revision) VALUES(?,?,'point',?,?,?,NULL,0,1)",new Object[]{point,field,payload,recorded,recorded});

            var withoutDataset=ActivityProjection.project(store,"profile-a",field);
            assertTrue(withoutDataset.stream().allMatch(x->x.syncRef()==null));

            String hash="a".repeat(64);
            db.execSQL("INSERT INTO gis_sync_state(id,dataset,entity_id,local_hash,remote_version,revision) VALUES(?,?,?,?,1,1)",new Object[]{dataset+":"+point,dataset,point,hash});
            var partial=ActivityProjection.project(store,"profile-a",field,dataset);
            assertNull(partial.stream().filter(x->x.sourceRef().id().equals(point)).findFirst().orElseThrow().syncRef());

            db.execSQL("INSERT INTO gis_sync_state(id,dataset,entity_id,local_hash,remote_version,revision) VALUES(?,?,?,?,1,1)",new Object[]{dataset+":"+field,dataset,field,hash});
            var verified=ActivityProjection.project(store,"profile-a",field,dataset);
            var observation=verified.stream().filter(x->x.sourceRef().id().equals(point)).findFirst().orElseThrow();
            assertNotNull(observation.syncRef());
            assertEquals(dataset,observation.syncRef().datasetId());
            assertEquals(point,observation.syncRef().sourceUuid());
            assertEquals(field,observation.syncRef().fieldUuid());
            assertNull(verified.stream().filter(x->x.sourceRef().id().equals(production)).findFirst().orElseThrow().syncRef());

            db.delete("gis_sync_state","dataset=? AND entity_id=?",new String[]{dataset,field});
            assertNull(ActivityProjection.project(store,"profile-a",field,dataset).stream().filter(x->x.sourceRef().id().equals(point)).findFirst().orElseThrow().syncRef());

            try { ActivityProjection.project(store,"profile-a",field,"not-a-dataset"); fail(); }
            catch(IllegalArgumentException expected) { assertTrue(expected.getMessage().contains("dataset_id")); }
        } finally { context.deleteDatabase(name); }
    }
}
