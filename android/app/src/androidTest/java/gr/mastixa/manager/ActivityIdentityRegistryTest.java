package gr.mastixa.manager;

import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import static org.junit.Assert.*;

public class ActivityIdentityRegistryTest {
    private final android.content.Context context=InstrumentationRegistry.getInstrumentation().getTargetContext();

    @Test public void registryIsDatasetAndScopeIsolatedAndRejectsConflicts(){
        String name="phase9f-android-activity-identity.db";context.deleteDatabase(name);
        String dataset="11111111-1111-4111-8111-111111111111";
        String otherDataset="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";
        String fieldUuid="22222222-2222-4222-8222-222222222222";
        String sourceUuid="33333333-3333-4333-8333-333333333333";
        try(var store=new FarmStore(context,name)){
            var db=store.getWritableDatabase();
            ActivityIdentityRegistry.registerField(db,"profile-a",dataset,"local-field",fieldUuid,1);
            ActivityIdentityRegistry.registerSource(db,"profile-a",dataset,"production","local-production","local-field",sourceUuid,2);
            var ref=ActivityIdentityRegistry.lookup(db,"profile-a",dataset,"production","local-production","local-field");
            assertNotNull(ref);assertEquals(dataset,ref.datasetId());assertEquals(sourceUuid,ref.sourceUuid());assertEquals(fieldUuid,ref.fieldUuid());
            assertNull(ActivityIdentityRegistry.lookup(db,"profile-b",dataset,"production","local-production","local-field"));
            assertNull(ActivityIdentityRegistry.lookup(db,"profile-a",otherDataset,"production","local-production","local-field"));

            try{ActivityIdentityRegistry.registerField(db,"profile-a",dataset,"local-field","44444444-4444-4444-8444-444444444444",3);fail();}catch(IllegalArgumentException expected){}
            try{ActivityIdentityRegistry.registerSource(db,"profile-a",dataset,"production","local-production","missing-field",sourceUuid,3);fail();}catch(IllegalArgumentException expected){}
            try{ActivityIdentityRegistry.registerSource(db,"profile-a",dataset,"production","local-production","local-field","55555555-5555-4555-8555-555555555555",3);fail();}catch(IllegalArgumentException expected){}
            try{ActivityIdentityRegistry.registerField(db,"profile-a","not-a-dataset","x",fieldUuid,1);fail();}catch(IllegalArgumentException expected){}
        }finally{context.deleteDatabase(name);}
    }
}
