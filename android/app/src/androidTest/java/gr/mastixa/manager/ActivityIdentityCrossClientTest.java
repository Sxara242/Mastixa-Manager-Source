package gr.mastixa.manager;

import androidx.test.platform.app.InstrumentationRegistry;
import org.json.JSONObject;
import org.junit.Test;
import static org.junit.Assert.*;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

public class ActivityIdentityCrossClientTest {
    private final android.content.Context context = InstrumentationRegistry.getInstrumentation().getTargetContext();

    private JSONObject fixture() throws Exception {
        try (InputStream in = InstrumentationRegistry.getInstrumentation().getContext().getAssets().open("phase9f_activity_identity.json")) {
            return new JSONObject(new String(in.readAllBytes(), StandardCharsets.UTF_8));
        }
    }

    @Test public void sharedFixtureProjectsExpectedPortableIdentity() throws Exception {
        JSONObject f = fixture();
        String name = "phase9f-cross-client.db";
        context.deleteDatabase(name);
        try (var store = new FarmStore(context, name)) {
            var db = store.getWritableDatabase();
            String scope = f.getString("scope_id");
            String dataset = f.getString("dataset_id");
            String sourceType = f.getString("source_type");
            String sourceUuid = f.getString("source_uuid");
            String fieldUuid = f.getString("field_uuid");
            String eventDate = f.getString("event_date");
            JSONObject local = f.getJSONObject("android");
            String field = local.getString("local_field_id");
            String source = local.getString("local_source_id");

            db.execSQL("INSERT INTO fields(id,name,area,revision,updated_at,kaek,location,trees,notes,deleted_at) VALUES(?, 'Field',1,1,1,'','',0,'',NULL)", new Object[]{field});
            db.execSQL("INSERT INTO production(id,entry_date,product_id,product,field_id,quantity_kg,notes,windows_id,revision,updated_at,deleted_at) VALUES(?,?,'p','Μαστίχα',?,1,'','',1,1,NULL)", new Object[]{source,eventDate,field});

            ActivityIdentityRegistry.registerField(db, scope, dataset, field, fieldUuid, 1);
            ActivityIdentityRegistry.registerSource(db, scope, dataset, sourceType, source, field, sourceUuid, 2);

            var events = ActivityProjection.project(store, scope, field, dataset);
            var event = events.stream().filter(x -> x.sourceRef().id().equals(source)).findFirst().orElseThrow();
            assertEquals(eventDate, event.eventDate());
            assertNotNull(event.syncRef());
            JSONObject expected = f.getJSONObject("expected_sync_ref");
            assertEquals(expected.getString("dataset_id"), event.syncRef().datasetId());
            assertEquals(expected.getString("source_uuid"), event.syncRef().sourceUuid());
            assertEquals(expected.getString("field_uuid"), event.syncRef().fieldUuid());

            var unrelated = ActivityProjection.project(store, "profile-b", field, dataset);
            assertNull(unrelated.stream().filter(x -> x.sourceRef().id().equals(source)).findFirst().orElseThrow().syncRef());
        } finally {
            context.deleteDatabase(name);
        }
    }
}
