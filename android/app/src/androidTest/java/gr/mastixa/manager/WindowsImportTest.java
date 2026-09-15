package gr.mastixa.manager;

import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import static org.junit.Assert.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.zip.*;

public class WindowsImportTest {
    private byte[] archive(String csv, int count) throws Exception {
        var bytes=new ByteArrayOutputStream();
        try(var zip=new ZipOutputStream(bytes)) {
            zip.putNextEntry(new ZipEntry("manifest.json"));
            zip.write(("{\"schema\":\"mastixa-manager-portable-export-v1\",\"tables\":[{\"table\":\"fields\",\"status\":\"exported\",\"file\":\"tables/fields.csv\",\"rows\":"+count+"}]}").getBytes(StandardCharsets.UTF_8));
            zip.closeEntry(); zip.putNextEntry(new ZipEntry("tables/fields.csv"));
            zip.write(csv.getBytes(StandardCharsets.UTF_8)); zip.closeEntry();
        }
        return bytes.toByteArray();
    }
    private List<FarmStore.Field> read(String csv, int count) throws Exception { return WindowsImport.read(new ByteArrayInputStream(archive(csv,count))); }
    private final String header="\uFEFFid;name;kaek;location;area_stremma;productive_trees;notes\r\n";

    @Test public void importRoundTripDuplicatesConflictsAndBackup() throws Exception {
        var context=InstrumentationRegistry.getInstrumentation().getTargetContext();
        context.deleteDatabase("windows-test.db"); var recovery=new File(context.getCacheDir(),"windows-recovery.json");
        try(var store=new FarmStore(context,"windows-test.db")) {
            var incoming=read(header+"1;Χίος;001;Πυργί;2.5;20;\"Γραμμή; με \"\"εισαγωγικά\"\"\r\nΔεύτερη\"\r\n",1);
            assertEquals("Γραμμή; με \"εισαγωγικά\"\r\nΔεύτερη",incoming.get(0).notes());
            assertEquals(1,WindowsImport.preview(store,incoming).additions().size());
            assertTrue(store.fields().isEmpty()); // preview does not mutate
            WindowsImport.apply(store,incoming,recovery);
            assertEquals(1,store.fields().size()); assertEquals("001",store.fields().get(0).kaek());
            assertNotEquals("1",store.fields().get(0).id());
            try(var in=new FileInputStream(recovery)) { assertEquals(0,LocalBackup.inspect(store,LocalBackup.read(in))); }
            assertEquals(1,WindowsImport.preview(store,incoming).identical());
            assertEquals(0,WindowsImport.apply(store,incoming,recovery).additions().size());
            var changed=read(header+"1;Χίος;001;Πυργί;9;20;Διαφορετικό\r\n",1);
            assertEquals(1,WindowsImport.preview(store,changed).conflicts());
            WindowsImport.apply(store,changed,recovery); assertEquals(2.5,store.fields().get(0).area(),0);
            var repeated=new ArrayList<>(incoming); repeated.addAll(incoming);
            assertEquals(2,WindowsImport.preview(store,repeated).identical());
        } finally { context.deleteDatabase("windows-test.db"); recovery.delete(); }
    }
    @Test public void invalidArchiveRejected() throws Exception {
        for(String row:List.of("1;;001;Πυργί;2;20;", "1;Χίος;001;Πυργί;NaN;20;", "1;Χίος;001;Πυργί;2;-1;", "1;Χίος;001;Πυργί;2;2.5;", "1;Χίος;001;Πυργί;2;20;\"broken")) {
            try { read(header+row+"\r\n",1); fail(row); } catch(IOException expected) {}
        }
        try { read(header+"1;Χίος;001;Πυργί;2;20;\r\n",2); fail(); } catch(IOException expected) {}
        try { WindowsImport.read(new ByteArrayInputStream("not a zip".getBytes(StandardCharsets.UTF_8))); fail(); } catch(IOException expected) {}
        assertTrue(read(header,0).isEmpty());
    }
    @Test public void failureRollsBackEntireBatchAndQueue() throws Exception {
        var context=InstrumentationRegistry.getInstrumentation().getTargetContext();
        context.deleteDatabase("windows-rollback.db"); var recovery=new File(context.getCacheDir(),"windows-rollback.json");
        try(var store=new FarmStore(context,"windows-rollback.db")) {
            store.addField("Υπάρχον",1);
            store.getWritableDatabase().execSQL("CREATE TRIGGER fail_second BEFORE INSERT ON fields WHEN NEW.name='Δεύτερο' BEGIN SELECT RAISE(ABORT,'test'); END");
            var incoming=read(header+"1;Πρώτο;;;2;0;\r\n2;Δεύτερο;;;3;0;\r\n",2);
            try { WindowsImport.apply(store,incoming,recovery); fail(); } catch(android.database.SQLException expected) {}
            assertEquals(1,store.fields().size()); assertEquals("Υπάρχον",store.fields().get(0).name());
            try(var cursor=store.getReadableDatabase().rawQuery("SELECT count(*) FROM pending_changes",null)) { cursor.moveToFirst(); assertEquals(1,cursor.getInt(0)); }
        } finally { context.deleteDatabase("windows-rollback.db"); recovery.delete(); }
    }
}
