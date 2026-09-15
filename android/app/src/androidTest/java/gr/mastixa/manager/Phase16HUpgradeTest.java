package gr.mastixa.manager;

import android.content.Context;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import androidx.test.platform.app.InstrumentationRegistry;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;
import org.junit.Test;
import static org.junit.Assert.*;

/** Phase 16H: preserve app data across a real APK replacement and migrate an older DB. */
public class Phase16HUpgradeTest {
    private static final String DB = "phase16h-upgrade.db";
    private static final String PREFS = "phase16h-upgrade";
    private static final String SENTINEL = "phase16h-preserved";
    private static final String FIELD = "Phase 16H upgrade sentinel";

    @Test public void seedLegacyState() throws Exception {
        Context c = context();
        assertTrue("Upgrade fixture must stay isolated from the main app", c.getPackageName().endsWith(".checks"));
        c.deleteDatabase(DB);
        assertTrue(c.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().clear().putString("sentinel", SENTINEL).commit());

        try (FarmStore farm = new FarmStore(c, DB)) {
            farm.saveField(null, FIELD, 12.5, "012345678901", "upgrade-fixture", 17, "must survive package replacement");
            assertEquals(1, farm.fields().size());
        }

        try (SQLiteDatabase db = SQLiteDatabase.openDatabase(c.getDatabasePath(DB).getPath(), null, SQLiteDatabase.OPEN_READWRITE)) {
            LegacySchema.dropStage12(db);
            db.execSQL("PRAGMA user_version=11");
            assertEquals(11, userVersion(db));
        }
    }

    @Test public void verifyPreservedAndMigrated() throws Exception {
        Context c = context();
        assertEquals(SENTINEL, c.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getString("sentinel", null));

        try (FarmStore farm = new FarmStore(c, DB)) {
            var fields = farm.fields();
            assertEquals("APK replacement must preserve the seeded field", 1, fields.size());
            var field = fields.get(0);
            assertEquals(FIELD, field.name());
            assertEquals(12.5, field.area(), 0.000001);
            assertEquals("012345678901", field.kaek());
            assertEquals("upgrade-fixture", field.location());
            assertEquals(17, field.trees());
            assertEquals("must survive package replacement", field.notes());

            SQLiteDatabase db = farm.getReadableDatabase();
            assertEquals(14, userVersion(db));
            assertTrue(tableExists(db, "invoice_documents"));
            assertTrue(tableExists(db, "year_locks"));
            assertTrue(tableExists(db, "gis_records"));
            for (String table : GisSyncRepository.TABLES) assertTrue("Missing migrated table: " + table, tableExists(db, table));
        }
    }

    @Test public void storageAccessUsesSafWithoutBroadStoragePermissions() throws Exception {
        Context c = context();
        PackageInfo info = c.getPackageManager().getPackageInfo(c.getPackageName(), PackageManager.GET_PERMISSIONS);
        Set<String> requested = new HashSet<>();
        if (info.requestedPermissions != null) requested.addAll(Arrays.asList(info.requestedPermissions));
        assertFalse(requested.contains("android.permission.READ_EXTERNAL_STORAGE"));
        assertFalse(requested.contains("android.permission.WRITE_EXTERNAL_STORAGE"));
        assertFalse(requested.contains("android.permission.MANAGE_EXTERNAL_STORAGE"));

        // Do not require DocumentsUI to be installed in this isolated headless AVD.
        // ExportFailureUiTest exercises the application's actual ACTION_CREATE_DOCUMENT
        // launch path and verifies the unavailable-picker fallback separately.
    }

    private static Context context() {
        return InstrumentationRegistry.getInstrumentation().getTargetContext();
    }

    private static int userVersion(SQLiteDatabase db) {
        try (Cursor c = db.rawQuery("PRAGMA user_version", null)) {
            assertTrue(c.moveToFirst());
            return c.getInt(0);
        }
    }

    private static boolean tableExists(SQLiteDatabase db, String table) {
        try (Cursor c = db.rawQuery("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", new String[]{table})) {
            return c.moveToFirst();
        }
    }
}
