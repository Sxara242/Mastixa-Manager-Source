package gr.mastixa.manager;

import android.content.ContentValues;
import android.database.sqlite.SQLiteDatabase;
import java.util.*;
import java.math.BigDecimal;

public final class MoneyStore {
    public record Entry(String id,String kind,String date,String fieldId,String category,String description,String partnerId,String partnerName,String payment,double amount,String notes,String sourceType,String sourceId,String windowsId) {}
    static final String[] COLUMNS={"id","kind","entry_date","field_id","category","description","partner_id","partner_name","payment_method","amount","notes","source_type","source_id","windows_id","revision","updated_at","deleted_at"};
    private final FarmStore store;
    public MoneyStore(FarmStore store){this.store=store;}
    static void createTables(SQLiteDatabase db){
        db.execSQL("CREATE TABLE money_entries(id TEXT PRIMARY KEY,kind TEXT NOT NULL CHECK(kind IN ('income','expense')),entry_date TEXT NOT NULL,field_id TEXT NOT NULL,category TEXT NOT NULL,description TEXT NOT NULL,partner_id TEXT NOT NULL,partner_name TEXT NOT NULL,payment_method TEXT NOT NULL,amount REAL NOT NULL CHECK(amount>=0),notes TEXT NOT NULL,source_type TEXT NOT NULL,source_id TEXT NOT NULL,windows_id TEXT NOT NULL,revision INTEGER NOT NULL,updated_at INTEGER NOT NULL,deleted_at INTEGER)");
        db.execSQL("CREATE UNIQUE INDEX money_windows ON money_entries(kind,windows_id) WHERE windows_id<>''");
        db.execSQL("CREATE UNIQUE INDEX money_receipt ON money_entries(source_id) WHERE source_type='inventory_receipt' AND kind='expense'");
        // Upgrade old local receipts once. Imported history waits for the Windows expenses export.
        try(var c=db.rawQuery("SELECT id FROM inventory_movements WHERE deleted_at IS NULL AND windows_id='' AND source_type=''",null)){while(c.moveToNext())syncReceipt(db,c.getString(0),false);}
    }
    public List<Entry> entries(String kind){return entries(store.getReadableDatabase(),kind);}
    static List<Entry> entries(SQLiteDatabase db,String kind){var result=new ArrayList<Entry>();try(var c=db.rawQuery("SELECT id,kind,entry_date,field_id,category,description,partner_id,partner_name,payment_method,amount,notes,source_type,source_id,windows_id FROM money_entries WHERE deleted_at IS NULL"+(kind==null?"":" AND kind=?")+" ORDER BY entry_date DESC,updated_at DESC,id",kind==null?null:new String[]{kind})){while(c.moveToNext())result.add(new Entry(c.getString(0),c.getString(1),c.getString(2),c.getString(3),c.getString(4),c.getString(5),c.getString(6),c.getString(7),c.getString(8),c.getDouble(9),c.getString(10),c.getString(11),c.getString(12),c.getString(13)));}return result;}
    public static BigDecimal total(List<Entry> entries){return entries.stream().map(e->BigDecimal.valueOf(e.amount())).reduce(BigDecimal.ZERO,BigDecimal::add);}
    public static void validate(Entry e){if(!Set.of("income","expense").contains(e.kind())||e.description().isBlank()||e.date().isBlank()||!Double.isFinite(e.amount())||e.amount()<0)throw new IllegalArgumentException("Συμπλήρωσε περιγραφή, ημερομηνία και έγκυρο ποσό.");CatalogStore.validateCultivation(e.date(),"active");if(e.kind().equals("expense")&&e.category().isBlank())throw new IllegalArgumentException("Χρειάζεται κατηγορία εξόδου.");}
    private static boolean exists(SQLiteDatabase db,String table,String id){try(var c=db.rawQuery("SELECT 1 FROM "+table+" WHERE id=?",new String[]{id})){return c.moveToFirst();}}
    private static void queue(SQLiteDatabase db,String id,String operation,int revision,long now){var v=new ContentValues();v.put("operation_id",UUID.randomUUID().toString());v.put("entity","money_entries");v.put("entity_id",id);v.put("operation",operation);v.put("revision",revision);v.put("created_at",now);db.insertOrThrow("pending_changes",null,v);}
    static String put(SQLiteDatabase db,Entry e){validate(e);if(!e.fieldId().isEmpty()&&!exists(db,"fields",e.fieldId()))throw new IllegalArgumentException("Λείπει αγροτεμάχιο.");if(!e.partnerId().isEmpty()&&!exists(db,"business_partners",e.partnerId()))throw new IllegalArgumentException("Λείπει συνεργάτης.");int revision=1;if(e.id()!=null){try(var c=db.rawQuery("SELECT revision FROM money_entries WHERE id=?",new String[]{e.id()})){if(!c.moveToFirst())throw new IllegalArgumentException("Η εγγραφή δεν υπάρχει.");revision=c.getInt(0)+1;}}
        String id=e.id()==null?UUID.randomUUID().toString():e.id();long now=System.currentTimeMillis();var v=new ContentValues();v.put("id",id);v.put("kind",e.kind());v.put("entry_date",e.date());v.put("field_id",e.fieldId());v.put("category",e.category().trim());v.put("description",e.description().trim());v.put("partner_id",e.partnerId());v.put("partner_name",e.partnerName().trim());v.put("payment_method",e.payment().trim());v.put("amount",e.amount());v.put("notes",e.notes().trim());v.put("source_type",e.sourceType());v.put("source_id",e.sourceId());v.put("windows_id",e.windowsId());v.put("revision",revision);v.put("updated_at",now);v.putNull("deleted_at");if(e.id()==null)db.insertOrThrow("money_entries",null,v);else db.update("money_entries",v,"id=?",new String[]{id});queue(db,id,e.id()==null?"create":"update",revision,now);return id;
    }
    public String save(Entry e){if(!e.sourceType().isEmpty()||!e.windowsId().isEmpty()||e.amount()<=0)throw new IllegalArgumentException("Χρειάζεται θετικό ποσό. Οι αυτόματες/εισαγόμενες εγγραφές αλλάζουν από την πηγή τους.");var db=store.getWritableDatabase();db.beginTransaction();try{if(e.id()!=null){var old=entries(null).stream().filter(x->x.id().equals(e.id())).findFirst().orElseThrow(()->new IllegalArgumentException("Η εγγραφή δεν υπάρχει."));if(!old.sourceType().isEmpty()||!old.windowsId().isEmpty()||!old.kind().equals(e.kind()))throw new IllegalArgumentException("Η εγγραφή δεν αλλάζει απευθείας.");}String id=put(db,e);db.setTransactionSuccessful();return id;}finally{db.endTransaction();}}
    static void remove(SQLiteDatabase db,String id){try(var c=db.rawQuery("SELECT revision FROM money_entries WHERE id=? AND deleted_at IS NULL",new String[]{id})){if(!c.moveToFirst())return;int rev=c.getInt(0)+1;long now=System.currentTimeMillis();var v=new ContentValues();v.put("revision",rev);v.put("updated_at",now);v.put("deleted_at",now);db.update("money_entries",v,"id=?",new String[]{id});queue(db,id,"delete",rev,now);}}
    public void delete(String id){var db=store.getWritableDatabase();db.beginTransaction();try{var e=entries(null).stream().filter(x->x.id().equals(id)).findFirst().orElseThrow();if(!e.sourceType().isEmpty()||!e.windowsId().isEmpty())throw new IllegalArgumentException("Διόρθωσε την αρχική καταχώριση.");remove(db,id);db.setTransactionSuccessful();}finally{db.endTransaction();}}
    static void syncReceipt(SQLiteDatabase db,String movementId,boolean deleting){
        String existing=null;try(var c=db.rawQuery("SELECT id FROM money_entries WHERE kind='expense' AND source_type='inventory_receipt' AND source_id=?",new String[]{movementId})){if(c.moveToFirst())existing=c.getString(0);}
        try(var c=db.rawQuery("SELECT m.movement_date,m.movement_type,m.total_cost,m.partner_id,m.supplier_name,m.notes,m.windows_id,m.source_type,i.name FROM inventory_movements m JOIN inventory_items i ON i.id=m.item_id WHERE m.id=?",new String[]{movementId})){
            if(!c.moveToFirst())throw new IllegalArgumentException("Λείπει παραλαβή.");if(!c.getString(6).isEmpty()||!c.getString(7).isEmpty())return;
            if(deleting||!c.getString(1).equals("Παραλαβή")||c.getDouble(2)<=0){if(existing!=null)remove(db,existing);return;}
            put(db,new Entry(existing,"expense",c.getString(0),"","Αποθήκη & Εφόδια","Παραλαβή αποθήκης — "+c.getString(8),c.getString(3),c.getString(4),"",c.getDouble(2),c.getString(5),"inventory_receipt",movementId,""));
        }
    }
}
