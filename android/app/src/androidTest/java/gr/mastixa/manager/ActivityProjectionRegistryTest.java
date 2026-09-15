package gr.mastixa.manager;

import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import static org.junit.Assert.*;

public class ActivityProjectionRegistryTest {
    private final android.content.Context context = InstrumentationRegistry.getInstrumentation().getTargetContext();

    @Test public void businessActivityGetsPortableIdentityOnlyFromVerifiedRegistry() throws Exception {
        String name="phase9f-android-projection-registry.db";
        context.deleteDatabase(name);
        String dataset="11111111-1111-4111-8111-111111111111";
        String fieldLocal="field-local";
        String fieldUuid="22222222-2222-4222-8222-222222222222";
        String sourceLocal="production-local";
        String sourceUuid="33333333-3333-4333-8333-333333333333";

        try(var store=new FarmStore(context,name)) {
            var db=store.getWritableDatabase();
            db.execSQL(
                "INSERT INTO fields(id,name,area,revision,updated_at,kaek,location,trees,notes,deleted_at) VALUES(?, 'Field',1,1,1,'','',0,'',NULL)",
                new Object[]{fieldLocal}
            );
            db.execSQL(
                "INSERT INTO production(id,entry_date,product_id,product,field_id,quantity_kg,notes,windows_id,revision,updated_at,deleted_at) VALUES(?,'2026-09-10','p','Μαστίχα',?,1,'','legacy-win-id',1,1,NULL)",
                new Object[]{sourceLocal,fieldLocal}
            );

            var before=ActivityProjection.project(store,"profile-a",fieldLocal,dataset);
            var harvestBefore=before.stream().filter(x->x.sourceRef().id().equals(sourceLocal)).findFirst().orElseThrow();
            assertNull(harvestBefore.syncRef());

            ActivityIdentityRegistry.registerField(db,"profile-a",dataset,fieldLocal,fieldUuid,10);
            ActivityIdentityRegistry.registerSource(db,"profile-a",dataset,"production",sourceLocal,fieldLocal,sourceUuid,11);

            var mapped=ActivityProjection.project(store,"profile-a",fieldLocal,dataset);
            var harvest=mapped.stream().filter(x->x.sourceRef().id().equals(sourceLocal)).findFirst().orElseThrow();
            assertNotNull(harvest.syncRef());
            assertEquals(dataset,harvest.syncRef().datasetId());
            assertEquals(sourceUuid,harvest.syncRef().sourceUuid());
            assertEquals(fieldUuid,harvest.syncRef().fieldUuid());

            var wrongScope=ActivityProjection.project(store,"profile-b",fieldLocal,dataset);
            assertNull(wrongScope.stream().filter(x->x.sourceRef().id().equals(sourceLocal)).findFirst().orElseThrow().syncRef());

            assertNull(ActivityProjection.project(store,"profile-a",fieldLocal)
                .stream().filter(x->x.sourceRef().id().equals(sourceLocal)).findFirst().orElseThrow().syncRef());
        } finally {
            context.deleteDatabase(name);
        }
    }
}
