package gr.mastixa.manager;

import android.content.ContentValues;
import android.database.sqlite.SQLiteDatabase;
import java.util.*;

/** Per-profile partners. Tombstones preserve identity for future transaction links. */
public final class PartnerStore {
    static final String[] DETAILS={"name","partner_type","tax_id","contact_person","phone","email","address","products","payment_terms","notes"};
    public record Partner(String id,String name,String type,String taxId,String contact,String phone,String email,String address,String products,String paymentTerms,String notes) {
        String[] values() { return new String[]{name,type,taxId,contact,phone,email,address,products,paymentTerms,notes}; }
    }
    private final FarmStore store;
    public PartnerStore(FarmStore store) { this.store=store; }
    static void createTables(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE business_partners(id TEXT PRIMARY KEY,name TEXT NOT NULL,partner_type TEXT NOT NULL CHECK(partner_type IN ('supplier','buyer','both')),tax_id TEXT NOT NULL,contact_person TEXT NOT NULL,phone TEXT NOT NULL,email TEXT NOT NULL,address TEXT NOT NULL,products TEXT NOT NULL,payment_terms TEXT NOT NULL,notes TEXT NOT NULL,revision INTEGER NOT NULL,updated_at INTEGER NOT NULL,deleted_at INTEGER)");
    }
    public List<Partner> partners() {
        var result=new ArrayList<Partner>();
        try(var c=store.getReadableDatabase().rawQuery("SELECT id,name,partner_type,tax_id,contact_person,phone,email,address,products,payment_terms,notes FROM business_partners WHERE deleted_at IS NULL ORDER BY name,id",null)) {
            while(c.moveToNext()) result.add(new Partner(c.getString(0),c.getString(1),c.getString(2),c.getString(3),c.getString(4),c.getString(5),c.getString(6),c.getString(7),c.getString(8),c.getString(9),c.getString(10)));
        } return result;
    }
    public static boolean matches(Partner p,String query,String type) {
        String haystack=String.join(" ",p.name(),p.taxId(),p.phone(),p.products()).toLowerCase(Locale.ROOT);
        return haystack.contains(query.trim().toLowerCase(Locale.ROOT)) && (type.equals("all") || p.type().equals(type) || (!type.equals("both") && p.type().equals("both")));
    }
    public String save(Partner p) {
        if(p.name().isBlank() || !Set.of("supplier","buyer","both").contains(p.type())) throw new IllegalArgumentException("Συμπλήρωσε επωνυμία και έγκυρο τύπο συνεργάτη.");
        var db=store.getWritableDatabase(); db.beginTransaction();
        try {
            for(var existing:partners()) if(!existing.id().equals(p.id()) && existing.name().equalsIgnoreCase(p.name().trim())) throw new IllegalArgumentException("Υπάρχει ήδη συνεργάτης με αυτή την επωνυμία.");
            int revision=p.id()==null?1:revision(db,p.id())+1;
            String id=p.id()==null?UUID.randomUUID().toString():p.id(); long now=System.currentTimeMillis();
            var row=new ContentValues(); String[] values=p.values(); for(int i=0;i<DETAILS.length;i++) row.put(DETAILS[i],values[i].trim());
            row.put("id",id); row.put("revision",revision); row.put("updated_at",now);
            if(p.id()==null) db.insertOrThrow("business_partners",null,row); else db.update("business_partners",row,"id=? AND deleted_at IS NULL",new String[]{id});
            enqueue(db,id,p.id()==null?"create":"update",revision,now); db.setTransactionSuccessful(); return id;
        } finally { db.endTransaction(); }
    }
    private int revision(SQLiteDatabase db,String id) {
        try(var c=db.rawQuery("SELECT revision FROM business_partners WHERE id=? AND deleted_at IS NULL",new String[]{id})) {
            if(!c.moveToFirst()) throw new IllegalArgumentException("Ο συνεργάτης δεν υπάρχει."); return c.getInt(0);
        }
    }
    private void enqueue(SQLiteDatabase db,String id,String operation,int revision,long now) {
        var row=new ContentValues(); row.put("operation_id",UUID.randomUUID().toString()); row.put("entity_id",id); row.put("entity","business_partners"); row.put("operation",operation); row.put("revision",revision); row.put("created_at",now); db.insertOrThrow("pending_changes",null,row);
    }
    public void delete(String id) {
        var db=store.getWritableDatabase(); db.beginTransaction();
        try {
            int revision=revision(db,id)+1; long now=System.currentTimeMillis(); var row=new ContentValues(); row.put("revision",revision); row.put("updated_at",now); row.put("deleted_at",now);
            db.update("business_partners",row,"id=?",new String[]{id}); enqueue(db,id,"delete",revision,now); db.setTransactionSuccessful();
        } finally { db.endTransaction(); }
    }
}
