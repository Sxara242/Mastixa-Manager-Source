package gr.mastixa.manager;

import android.content.ContentValues;
import android.database.sqlite.SQLiteDatabase;
import java.util.*;

/** Profile-owned producer, products and field cultivation details. */
public final class CatalogStore {
    public record Producer(String name,String taxId,String phone,String email,String notes) {
        public boolean empty() { return (name+taxId+phone+email+notes).isBlank(); }
    }
    public record Product(String id,String name,String unit,boolean active) {
        @Override public String toString() { return name+" ("+unit+")"; }
    }
    public record Link(String id,String productId,String fieldId,String variety,String plantingDate,String status) {}
    private final FarmStore store;
    public CatalogStore(FarmStore store) { this.store=store; }
    static void createTables(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE producer(id TEXT PRIMARY KEY CHECK(id='producer'), name TEXT NOT NULL, tax_id TEXT NOT NULL,phone TEXT NOT NULL,email TEXT NOT NULL,notes TEXT NOT NULL,revision INTEGER NOT NULL,updated_at INTEGER NOT NULL)");
        db.execSQL("CREATE TABLE products(id TEXT PRIMARY KEY,name TEXT NOT NULL,unit TEXT NOT NULL,is_active INTEGER NOT NULL CHECK(is_active IN (0,1)),revision INTEGER NOT NULL,updated_at INTEGER NOT NULL)");
        db.execSQL("CREATE TABLE product_fields(id TEXT PRIMARY KEY,product_id TEXT NOT NULL,field_id TEXT NOT NULL,variety TEXT NOT NULL,planting_date TEXT NOT NULL,cultivation_status TEXT NOT NULL CHECK(cultivation_status IN ('active','inactive')),revision INTEGER NOT NULL,updated_at INTEGER NOT NULL,UNIQUE(product_id,field_id))");
    }
    public Producer producer() {
        try(var c=store.getReadableDatabase().rawQuery("SELECT name,tax_id,phone,email,notes FROM producer",null)) {
            return c.moveToFirst()?new Producer(c.getString(0),c.getString(1),c.getString(2),c.getString(3),c.getString(4)):new Producer("","","","","");
        }
    }
    private void save(String table,String id,ContentValues row) {
        var db=store.getWritableDatabase(); db.beginTransaction();
        try {
            int revision=0;
            try(var c=db.rawQuery("SELECT revision FROM "+table+" WHERE id=?",new String[]{id})) { if(c.moveToFirst()) revision=c.getInt(0); }
            long now=System.currentTimeMillis(); row.put("id",id); row.put("revision",revision+1); row.put("updated_at",now);
            if(revision==0) db.insertOrThrow(table,null,row); else db.update(table,row,"id=?",new String[]{id});
            ContentValues change=new ContentValues(); change.put("operation_id",UUID.randomUUID().toString()); change.put("entity_id",id); change.put("entity",table); change.put("operation",revision==0?"create":"update"); change.put("revision",revision+1); change.put("created_at",now);
            db.insertOrThrow("pending_changes",null,change); db.setTransactionSuccessful();
        } finally { db.endTransaction(); }
    }
    public void saveProducer(Producer p) {
        ContentValues row=new ContentValues(); row.put("name",p.name().trim()); row.put("tax_id",p.taxId().trim()); row.put("phone",p.phone().trim()); row.put("email",p.email().trim()); row.put("notes",p.notes().trim()); save("producer","producer",row);
    }
    public List<Product> products() {
        List<Product> result=new ArrayList<>();
        try(var c=store.getReadableDatabase().rawQuery("SELECT id,name,unit,is_active FROM products ORDER BY name,id",null)) {
            while(c.moveToNext()) result.add(new Product(c.getString(0),c.getString(1),c.getString(2),c.getInt(3)==1));
        } return result;
    }
    public String saveProduct(String id,String name,String unit,boolean active) {
        name=name.trim(); unit=unit.trim(); if(name.isEmpty() || unit.isEmpty()) throw new IllegalArgumentException("Συμπλήρωσε όνομα και μονάδα.");
        var db=store.getWritableDatabase(); db.beginTransaction();
        try {
            for(var existing:products()) if(!existing.id().equals(id) && existing.name().equalsIgnoreCase(name)) throw new IllegalArgumentException("Υπάρχει ήδη προϊόν με αυτό το όνομα.");
            if(id!=null && products().stream().noneMatch(p->p.id().equals(id))) throw new IllegalArgumentException("Το προϊόν δεν υπάρχει.");
            if(id!=null){var old=products().stream().filter(p->p.id().equals(id)).findFirst().orElseThrow();if(!old.unit().equals(unit)){try(var c=db.rawQuery("SELECT 1 FROM production WHERE product_id=? UNION ALL SELECT 1 FROM production_sales WHERE product_id=? LIMIT 1",new String[]{id,id})){if(c.moveToFirst())throw new IllegalArgumentException("Η μονάδα δεν αλλάζει όταν υπάρχει παραγωγή ή πώληση.");}}}
            String result=id==null?UUID.randomUUID().toString():id;
            ContentValues row=new ContentValues(); row.put("name",name); row.put("unit",unit); row.put("is_active",active?1:0); save("products",result,row);
            db.setTransactionSuccessful(); return result;
        } finally { db.endTransaction(); }
    }
    public List<Link> links() {
        List<Link> result=new ArrayList<>();
        try(var c=store.getReadableDatabase().rawQuery("SELECT id,product_id,field_id,variety,planting_date,cultivation_status FROM product_fields ORDER BY id",null)) {
            while(c.moveToNext()) result.add(new Link(c.getString(0),c.getString(1),c.getString(2),c.getString(3),c.getString(4),c.getString(5)));
        } return result;
    }
    public void saveLink(String productId,String fieldId,String variety,String date,String status) {
        validateCultivation(date,status);
        if(products().stream().noneMatch(p->p.id().equals(productId)) || store.fields().stream().noneMatch(f->f.id().equals(fieldId))) throw new IllegalArgumentException("Λείπει προϊόν ή αγροτεμάχιο.");
        ContentValues row=new ContentValues(); row.put("product_id",productId); row.put("field_id",fieldId); row.put("variety",variety.trim()); row.put("planting_date",date); row.put("cultivation_status",status);
        save("product_fields",productId+":"+fieldId,row);
    }
    public static void validateCultivation(String date,String status) {
        if(!Set.of("active","inactive").contains(status)) throw new IllegalArgumentException("Μη έγκυρη κατάσταση.");
        if(!date.isEmpty()) {
            try { if(!date.matches("[0-9]{4}-[0-9]{2}-[0-9]{2}") || java.time.LocalDate.parse(date).getYear()<1) throw new IllegalArgumentException(); }
            catch(Exception error) { throw new IllegalArgumentException("Η ημερομηνία πρέπει να είναι YYYY-MM-DD."); }
        }
    }
    public void removeLink(String id) {
        var db=store.getWritableDatabase(); db.beginTransaction();
        try {
            // This local queue is not yet a sync protocol; keep a terminal deletion event.
            int revision=1; try(var c=db.rawQuery("SELECT revision FROM product_fields WHERE id=?",new String[]{id})) { if(!c.moveToFirst()) return; revision=c.getInt(0)+1; }
            db.delete("product_fields","id=?",new String[]{id}); db.delete("pending_changes","entity='product_fields' AND entity_id=?",new String[]{id});
            ContentValues row=new ContentValues(); row.put("operation_id",UUID.randomUUID().toString()); row.put("entity_id",id); row.put("entity","product_fields"); row.put("operation","delete"); row.put("revision",revision); row.put("created_at",System.currentTimeMillis()); db.insertOrThrow("pending_changes",null,row);
            db.setTransactionSuccessful();
        } finally { db.endTransaction(); }
    }
}
