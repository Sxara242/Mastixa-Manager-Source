package gr.mastixa.manager;

import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import static org.junit.Assert.*;
import android.database.Cursor;

public class FarmStoreTest {
    @Test public void migrationEditDelete() {
        String dbName = "migration-test.db"; getContext().deleteDatabase(dbName);
        try {
            android.database.sqlite.SQLiteDatabase old = getContext().openOrCreateDatabase(dbName,0,null);
            old.execSQL("CREATE TABLE fields(id TEXT PRIMARY KEY,name TEXT NOT NULL,area REAL NOT NULL,revision INTEGER NOT NULL,updated_at INTEGER NOT NULL)");
            old.execSQL("CREATE TABLE pending_changes(operation_id TEXT PRIMARY KEY,entity_id TEXT NOT NULL,entity TEXT NOT NULL,operation TEXT NOT NULL,revision INTEGER NOT NULL,created_at INTEGER NOT NULL)");
            old.execSQL("INSERT INTO fields VALUES('old','Existing',2,1,1)"); old.setVersion(1); old.close();
            try(FarmStore store = new FarmStore(getContext(),dbName)) {
                assertEquals("Existing",store.fields().get(0).name()); assertEquals(0,store.fields().get(0).trees());
                store.saveField("old","Updated",3.5,"0012","Χίος",20,"Σημείωση");
                assertEquals("0012",store.fields().get(0).kaek()); assertEquals(20,store.fields().get(0).trees());
                store.getWritableDatabase().execSQL("CREATE TRIGGER reject_change BEFORE INSERT ON pending_changes BEGIN SELECT RAISE(ABORT,'test'); END");
                try { store.deleteField("old"); fail(); } catch(android.database.SQLException expected) {}
                assertEquals(1,store.fields().size());
                try { store.saveField("old","Lost",1,"","",0,""); fail(); } catch(android.database.SQLException expected) {}
                assertEquals("Updated",store.fields().get(0).name());
                store.getWritableDatabase().execSQL("DROP TRIGGER reject_change");
                store.deleteField("old"); assertTrue(store.fields().isEmpty());
                try(Cursor c = store.getReadableDatabase().rawQuery("SELECT revision,deleted_at FROM fields WHERE id='old'",null)) { assertTrue(c.moveToFirst()); assertEquals(3,c.getInt(0)); assertFalse(c.isNull(1)); }
                try { store.saveField("old","Resurrect",1,"","",0,""); fail(); } catch(IllegalArgumentException expected) {}
            }
        } finally { getContext().deleteDatabase(dbName); }
    }
    private android.content.Context getContext() { return InstrumentationRegistry.getInstrumentation().getTargetContext(); }
    @Test
    public void testPersistenceAndAtomicQueue() {
        String dbName = "test-farm.db"; getContext().deleteDatabase(dbName);
        try {
            FarmStore store = new FarmStore(getContext(),dbName);
            store.addField("Δοκιμή",2.5); store.close();
            store = new FarmStore(getContext(),dbName);
            assertEquals(1,store.fields().size()); assertEquals(2.5,store.fields().get(0).area(),0.0001);
            try { store.addField("",1); fail("Blank name accepted"); } catch (IllegalArgumentException expected) {}
            store.getWritableDatabase().execSQL("CREATE TRIGGER reject_change BEFORE INSERT ON pending_changes BEGIN SELECT RAISE(ABORT,'test'); END");
            try { store.addField("Rollback",1); fail("Should fail"); } catch (android.database.SQLException expected) {}
            assertEquals(1,store.fields().size());
            try(Cursor cursor = store.getReadableDatabase().rawQuery("SELECT count(*) FROM pending_changes",null)) { cursor.moveToFirst(); assertEquals(1,cursor.getInt(0)); }
            store.close();
        } finally { getContext().deleteDatabase(dbName); }
    }
}
