package gr.mastixa.manager;

import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import static org.junit.Assert.*;
import java.io.*;
import org.json.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

public class CatalogTest {
    private final android.content.Context context=InstrumentationRegistry.getInstrumentation().getTargetContext();
    private CatalogImport.Package fixture() throws Exception {
        try(var in=InstrumentationRegistry.getInstrumentation().getContext().getAssets().open("windows-catalog.zip")) { return CatalogImport.read(in); }
    }
    @Test public void actualWindowsExportImportRelationshipsAndRepeat() throws Exception {
        context.deleteDatabase("catalog-import.db"); var file=new File(context.getCacheDir(),"catalog-before.json");
        try(var store=new FarmStore(context,"catalog-import.db")) {
            var data=fixture(); var preview=CatalogImport.preview(store,data);
            assertEquals(1,preview.fields());assertEquals(1,preview.producer());assertEquals(1,preview.products());assertEquals(1,preview.links());
            assertTrue(store.fields().isEmpty());
            CatalogImport.apply(store,data,file); var catalog=new CatalogStore(store);
            assertEquals("001234567",catalog.producer().taxId()); assertEquals("Σημειώσεις; με νέα\nγραμμή",catalog.producer().notes());
            assertEquals("Μαστίχα",catalog.products().get(0).name());
            assertEquals(store.fields().get(0).id(),catalog.links().get(0).fieldId()); assertEquals(catalog.products().get(0).id(),catalog.links().get(0).productId());
            assertEquals("2024-03-15",catalog.links().get(0).plantingDate());
            var repeat=CatalogImport.apply(store,data,file);assertEquals(0,repeat.fields()+repeat.producer()+repeat.products()+repeat.links());assertEquals(4,repeat.skipped());
            byte[] backup=LocalBackup.snapshot(store); catalog.saveProducer(new CatalogStore.Producer("Changed","","","",""));
            LocalBackup.restore(store,backup,file); assertEquals("Δοκιμαστικός παραγωγός",catalog.producer().name()); assertEquals(1,catalog.links().size());
            var p=catalog.products().get(0);catalog.saveProduct(p.id(),p.name(),p.unit(),false);
            assertEquals(0,CatalogImport.preview(store,data).products());assertFalse(catalog.products().get(0).active());
        } finally { context.deleteDatabase("catalog-import.db");file.delete(); }
    }
    @Test public void rollbackAllRegistriesAndQueue() throws Exception {
        context.deleteDatabase("catalog-rollback.db");var file=new File(context.getCacheDir(),"catalog-fail.json");
        try(var store=new FarmStore(context,"catalog-rollback.db")) {
            store.getWritableDatabase().execSQL("CREATE TRIGGER fail_product BEFORE INSERT ON products BEGIN SELECT RAISE(ABORT,'test'); END");
            try { CatalogImport.apply(store,fixture(),file);fail(); } catch(android.database.SQLException expected) {}
            assertTrue(store.fields().isEmpty());var c=new CatalogStore(store); assertTrue(c.producer().empty());assertTrue(c.products().isEmpty());assertTrue(c.links().isEmpty());
            try(var cursor=store.getReadableDatabase().rawQuery("SELECT count(*) FROM pending_changes",null)) {cursor.moveToFirst();assertEquals(0,cursor.getInt(0));}
        } finally { context.deleteDatabase("catalog-rollback.db");file.delete(); }
    }
    @Test public void legacyBackupStillRestoresAndCatalogValidation() throws Exception {
        context.deleteDatabase("catalog-legacy.db");var file=new File(context.getCacheDir(),"catalog-legacy.json");
        try(var store=new FarmStore(context,"catalog-legacy.db")) {
            store.addField("Old field",2);var envelope=new JSONObject(new String(LocalBackup.snapshot(store),StandardCharsets.UTF_8));
            var payload=new JSONObject(envelope.getString("payload"));payload.remove("producer");payload.remove("products");payload.remove("product_fields");payload.remove("business_partners");payload.remove("inventory_items");payload.remove("inventory_movements");payload.remove("money_entries");payload.remove("production");payload.remove("production_sales");payload.remove("farm_activities");payload.remove("plant_protection_records");payload.remove("workers");payload.remove("labor_entries");payload.remove("planting_batches");payload.remove("equipment");payload.remove("equipment_maintenance");payload.remove("invoice_documents");payload.remove("year_locks");payload.remove("gis_records");LegacySchema.removeSync(payload);String data=payload.toString();
            var hash=new StringBuilder();for(byte b:MessageDigest.getInstance("SHA-256").digest(data.getBytes(StandardCharsets.UTF_8))) hash.append(String.format("%02x",b&255));
            envelope.put("schema",2).put("payload",data).put("sha256",hash.toString());
            var catalog=new CatalogStore(store);catalog.saveProduct(null,"Product","kg",true);
            LocalBackup.restore(store,envelope.toString().getBytes(StandardCharsets.UTF_8),file);assertTrue(catalog.products().isEmpty());assertEquals("Old field",store.fields().get(0).name());
            String product=catalog.saveProduct(null,"Μαστίχα","kg",true);
            try {catalog.saveProduct(null,"μαστίχα","kg",true);fail();} catch(IllegalArgumentException expected) {}
            try {catalog.saveLink(product,store.fields().get(0).id(),"","2025-02-30","active");fail();} catch(IllegalArgumentException expected) {}
            catalog.saveLink(product,store.fields().get(0).id(),"","","active");
            catalog.removeLink(catalog.links().get(0).id());assertEquals(1,LocalBackup.inspect(store,LocalBackup.snapshot(store)));
        } finally {context.deleteDatabase("catalog-legacy.db");file.delete();}
    }
}
