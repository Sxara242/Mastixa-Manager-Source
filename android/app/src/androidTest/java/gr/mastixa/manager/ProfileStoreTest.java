package gr.mastixa.manager;

import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import static org.junit.Assert.*;
import java.util.*;

public class ProfileStoreTest {
    private final android.content.Context context=InstrumentationRegistry.getInstrumentation().getTargetContext();
    @Test public void credentialsPasswordChangeLockoutAndPersistence() throws Exception {
        context.deleteDatabase("profile-test.db");
        try(var store=new ProfileStore(context,"profile-test.db")) {
            var first=store.create("Πρώτο","owner","Original123!".toCharArray(),"el");
            assertEquals("legacy",first.id()); assertEquals("mastixa.db",first.database());
            assertEquals("navigation",first.preferences()); assertEquals("before-restore.json",first.recovery());
            assertNull(store.authenticate(first.id(),"wrong","Original123!".toCharArray(),"el"));
            assertNull(store.authenticate(first.id(),"owner","wrong".toCharArray(),"el"));
            assertNotNull(store.authenticate(first.id(),"OWNER","Original123!".toCharArray(),"en"));
            assertEquals("en",store.profiles().get(0).language());
            store.changePassword(first,"Original123!".toCharArray(),"Updated123!".toCharArray());
            assertNull(store.authenticate(first.id(),"owner","Original123!".toCharArray(),"en"));
            assertNotNull(store.authenticate(first.id(),"owner","Updated123!".toCharArray(),"en"));
            for(int i=0;i<5;i++) assertNull(store.authenticate(first.id(),"owner","wrong".toCharArray(),"en"));
            try { store.authenticate(first.id(),"owner","Updated123!".toCharArray(),"en"); fail(); } catch(IllegalArgumentException expected) {}
            try(var c=store.getReadableDatabase().rawQuery("SELECT hash,salt FROM profiles",null)) {
                c.moveToFirst(); assertFalse(c.getString(0).contains("Updated123!")); assertFalse(c.getString(1).isEmpty());
            }
            try(var reopened=new ProfileStore(context,"profile-test.db")) { assertEquals(first.id(),reopened.profiles().get(0).id()); }
        } finally { context.deleteDatabase("profile-test.db"); }
    }
    @Test public void separateDataAndPreferencesAndRejectedDuplicate() throws Exception {
        context.deleteDatabase("profile-isolation.db"); String secondDatabase=null;
        try(var profiles=new ProfileStore(context,"profile-isolation.db")) {
            var first=profiles.create("First","one","Password123!".toCharArray(),"el");
            var second=profiles.create("Second","two","Password123!".toCharArray(),"en"); secondDatabase=second.database();
            assertNotEquals(first.database(),second.database()); assertNotEquals(first.preferences(),second.preferences()); assertNotEquals(first.recovery(),second.recovery());
            // Separate temporary farm files model the profile-owned stores without touching the default file.
            try(var original=new FarmStore(context,"isolation-original.db");var other=new FarmStore(context,second.database())) {
                original.addField("Μόνο πρώτο",2); assertTrue(other.fields().isEmpty()); other.addField("Only second",4);
                assertEquals("Μόνο πρώτο",original.fields().get(0).name()); assertEquals("Only second",other.fields().get(0).name());
                assertEquals(1,LocalBackup.inspect(other,LocalBackup.snapshot(other)));
            }
            try { profiles.create("Third","ONE","Password123!".toCharArray(),"el"); fail(); } catch(android.database.sqlite.SQLiteConstraintException expected) {}
            assertEquals(2,profiles.profiles().size());
        } finally { context.deleteDatabase("profile-isolation.db"); context.deleteDatabase("isolation-original.db"); if(secondDatabase!=null) context.deleteDatabase(secondDatabase); }
    }
    @Test public void englishNavigationAndPrivateMainActivity() throws Exception {
        var en=new AppLanguage(context,"en");
        assertEquals("My farm",en.t("Η εκμετάλλευσή μου"));
        assertEquals("Local backup  ›",en.t("Τοπικό backup  ›"));
        assertEquals("Η εκμετάλλευσή μου",new AppLanguage(context,"el").t("Η εκμετάλλευσή μου"));
        var info=context.getPackageManager().getActivityInfo(new android.content.ComponentName(context,MainActivity.class),0);
        assertFalse(info.exported);
    }
}
