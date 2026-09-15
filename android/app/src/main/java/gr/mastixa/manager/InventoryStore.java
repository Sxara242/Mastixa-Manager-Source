package gr.mastixa.manager;

import android.content.ContentValues;
import android.database.sqlite.SQLiteDatabase;
import java.util.*;

public final class InventoryStore {
    public static final String[] TYPES={"Παραλαβή","Κατανάλωση","Διόρθωση +","Διόρθωση -"};
    public record Item(String id,String name,String category,String unit,double minimum,String notes) {}
    public record Movement(String id,String itemId,String date,String type,double quantity,String fieldId,String partnerId,String supplier,double price,double cost,String notes,String sourceType,String sourceId,String expenseId,String windowsId) {}
    static final String[] ITEM_COLUMNS={"id","name","category","unit","minimum_stock","notes","revision","updated_at","deleted_at"};
    static final String[] MOVEMENT_COLUMNS={"id","item_id","movement_date","movement_type","quantity","field_id","partner_id","supplier_name","unit_price","total_cost","notes","source_type","source_id","expense_id","windows_id","revision","updated_at","deleted_at"};
    private final FarmStore store;
    public InventoryStore(FarmStore store) {this.store=store;}
    static void createTables(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE inventory_items(id TEXT PRIMARY KEY,name TEXT NOT NULL,category TEXT NOT NULL,unit TEXT NOT NULL,minimum_stock REAL NOT NULL CHECK(minimum_stock>=0),notes TEXT NOT NULL,revision INTEGER NOT NULL,updated_at INTEGER NOT NULL,deleted_at INTEGER)");
        db.execSQL("CREATE TABLE inventory_movements(id TEXT PRIMARY KEY,item_id TEXT NOT NULL,movement_date TEXT NOT NULL,movement_type TEXT NOT NULL,quantity REAL NOT NULL CHECK(quantity>0),field_id TEXT NOT NULL,partner_id TEXT NOT NULL,supplier_name TEXT NOT NULL,unit_price REAL NOT NULL CHECK(unit_price>=0),total_cost REAL NOT NULL CHECK(total_cost>=0),notes TEXT NOT NULL,source_type TEXT NOT NULL,source_id TEXT NOT NULL,expense_id TEXT NOT NULL,windows_id TEXT NOT NULL,revision INTEGER NOT NULL,updated_at INTEGER NOT NULL,deleted_at INTEGER)");
        db.execSQL("CREATE INDEX inventory_by_item ON inventory_movements(item_id)");
    }
    public List<Item> items() {
        var result=new ArrayList<Item>();try(var c=store.getReadableDatabase().rawQuery("SELECT id,name,category,unit,minimum_stock,notes FROM inventory_items WHERE deleted_at IS NULL ORDER BY name,id",null)) {while(c.moveToNext())result.add(new Item(c.getString(0),c.getString(1),c.getString(2),c.getString(3),c.getDouble(4),c.getString(5)));}return result;
    }
    public List<Movement> movements(String itemId) {
        var result=new ArrayList<Movement>();try(var c=store.getReadableDatabase().rawQuery("SELECT id,item_id,movement_date,movement_type,quantity,field_id,partner_id,supplier_name,unit_price,total_cost,notes,source_type,source_id,expense_id,windows_id FROM inventory_movements WHERE deleted_at IS NULL"+(itemId==null?"":" AND item_id=?")+" ORDER BY movement_date DESC,updated_at DESC,id",itemId==null?null:new String[]{itemId})) {while(c.moveToNext())result.add(new Movement(c.getString(0),c.getString(1),c.getString(2),c.getString(3),c.getDouble(4),c.getString(5),c.getString(6),c.getString(7),c.getDouble(8),c.getDouble(9),c.getString(10),c.getString(11),c.getString(12),c.getString(13),c.getString(14)));}return result;
    }
    public static double signed(String type,double quantity){return type.equals(TYPES[0])||type.equals(TYPES[2])?quantity:-quantity;}
    public double stock(String itemId){return movements(itemId).stream().mapToDouble(m->signed(m.type(),m.quantity())).sum();}
    public static void validateItem(Item i) {if(i.name().isBlank()||i.unit().isBlank()||!Double.isFinite(i.minimum())||i.minimum()<0)throw new IllegalArgumentException("Συμπλήρωσε όνομα, μονάδα και μη αρνητικό ελάχιστο απόθεμα.");}
    public static void validateMovement(Movement m) {
        if(!Arrays.asList(TYPES).contains(m.type())||!Double.isFinite(m.quantity())||m.quantity()<=0||!Double.isFinite(m.price())||m.price()<0||!Double.isFinite(m.cost())||m.cost()<0)throw new IllegalArgumentException("Μη έγκυρος τύπος, ποσότητα ή κόστος.");
        if(m.date().isBlank())throw new IllegalArgumentException("Χρειάζεται ημερομηνία YYYY-MM-DD.");CatalogStore.validateCultivation(m.date(),"active");
    }
    private int revision(SQLiteDatabase db,String table,String id){try(var c=db.rawQuery("SELECT revision FROM "+table+" WHERE id=? AND deleted_at IS NULL",new String[]{id})){if(!c.moveToFirst())throw new IllegalArgumentException("Η εγγραφή δεν υπάρχει.");return c.getInt(0);}}
    private void queue(SQLiteDatabase db,String table,String id,String operation,int revision,long now){var v=new ContentValues();v.put("operation_id",UUID.randomUUID().toString());v.put("entity",table);v.put("entity_id",id);v.put("operation",operation);v.put("revision",revision);v.put("created_at",now);db.insertOrThrow("pending_changes",null,v);}
    private String save(SQLiteDatabase db,String table,String id,ContentValues v){int revision=id==null?1:revision(db,table,id)+1;String key=id==null?UUID.randomUUID().toString():id;long now=System.currentTimeMillis();v.put("id",key);v.put("revision",revision);v.put("updated_at",now);if(id==null)db.insertOrThrow(table,null,v);else db.update(table,v,"id=?",new String[]{id});queue(db,table,key,id==null?"create":"update",revision,now);return key;}
    public String saveItem(Item i){validateItem(i);var db=store.getWritableDatabase();db.beginTransaction();try {
        for(var other:items())if(!other.id().equals(i.id())&&other.name().equalsIgnoreCase(i.name().trim()))throw new IllegalArgumentException("Υπάρχει ήδη είδος με αυτό το όνομα.");
        if(i.id()!=null){try(var c=db.rawQuery("SELECT 1 FROM farm_activities WHERE inventory_item_id=? AND inventory_quantity>0 AND deleted_at IS NULL UNION ALL SELECT 1 FROM plant_protection_records WHERE inventory_item_id=? AND inventory_quantity>0 AND deleted_at IS NULL LIMIT 1",new String[]{i.id(),i.id()})){if(c.moveToFirst()&&items().stream().anyMatch(old->old.id().equals(i.id())&&!old.unit().equals(i.unit().trim())))throw new IllegalArgumentException("Η μονάδα δεν αλλάζει όταν υπάρχουν συνδεδεμένες εργασίες.");}}
        if(i.id()!=null&&!movements(i.id()).isEmpty()){var old=items().stream().filter(x->x.id().equals(i.id())).findFirst().orElseThrow();if(!old.unit().equals(i.unit().trim()))throw new IllegalArgumentException("Η μονάδα δεν αλλάζει όταν υπάρχουν κινήσεις.");}
        var v=new ContentValues();v.put("name",i.name().trim());v.put("category",i.category().trim());v.put("unit",i.unit().trim());v.put("minimum_stock",i.minimum());v.put("notes",i.notes().trim());String id=save(db,"inventory_items",i.id(),v);db.setTransactionSuccessful();return id;
    }finally{db.endTransaction();}}
    public String saveMovement(Movement m){return saveMovement(m,false);}
    String saveMovement(Movement m,boolean importing){validateMovement(m);var db=store.getWritableDatabase();db.beginTransaction();try {
        if(items().stream().noneMatch(i->i.id().equals(m.itemId())))throw new IllegalArgumentException("Λείπει είδος αποθήκης.");
        if(!m.fieldId().isEmpty()&&store.fields().stream().noneMatch(f->f.id().equals(m.fieldId())))throw new IllegalArgumentException("Λείπει αγροτεμάχιο.");
        if(!m.partnerId().isEmpty()&&new PartnerStore(store).partners().stream().noneMatch(p->p.id().equals(m.partnerId())))throw new IllegalArgumentException("Λείπει συνεργάτης.");
        Movement old=m.id()==null?null:movements(null).stream().filter(x->x.id().equals(m.id())).findFirst().orElseThrow();
        if(!importing&&((old!=null&&(!old.sourceType().isEmpty()||!old.windowsId().isEmpty()))||!m.sourceType().isEmpty()||!m.windowsId().isEmpty()))throw new IllegalArgumentException("Οι εισαγόμενες και αυτόματες κινήσεις διατηρούνται ως ιστορικό. Πρόσθεσε διορθωτική κίνηση.");
        if(old!=null&&!old.itemId().equals(m.itemId()))throw new IllegalArgumentException("Το είδος μιας κίνησης δεν αλλάζει.");
        double balance=stock(m.itemId())-(old==null?0:signed(old.type(),old.quantity()))+signed(m.type(),m.quantity());if(!Double.isFinite(balance)||balance < -0.000001)throw new IllegalArgumentException("Η κίνηση θα έκανε το απόθεμα αρνητικό.");
        var v=new ContentValues();v.put("item_id",m.itemId());v.put("movement_date",m.date());v.put("movement_type",m.type());v.put("quantity",m.quantity());v.put("field_id",m.fieldId());v.put("partner_id",m.partnerId());v.put("supplier_name",m.supplier().trim());v.put("unit_price",m.price());v.put("total_cost",m.cost());v.put("notes",m.notes().trim());v.put("source_type",m.sourceType());v.put("source_id",m.sourceId());v.put("expense_id",m.expenseId());v.put("windows_id",m.windowsId());String id=save(db,"inventory_movements",m.id(),v);if(!importing)MoneyStore.syncReceipt(db,id,false);db.setTransactionSuccessful();return id;
    }finally{db.endTransaction();}}
    private void remove(String table,String id){var db=store.getWritableDatabase();int rev=revision(db,table,id)+1;long now=System.currentTimeMillis();var v=new ContentValues();v.put("deleted_at",now);v.put("updated_at",now);v.put("revision",rev);db.update(table,v,"id=?",new String[]{id});queue(db,table,id,"delete",rev,now);}
    public void deleteItem(String id){var db=store.getWritableDatabase();db.beginTransaction();try{if(!movements(id).isEmpty())throw new IllegalArgumentException("Διατηρούνται είδη που έχουν κινήσεις.");remove("inventory_items",id);db.setTransactionSuccessful();}finally{db.endTransaction();}}
    public void deleteMovement(String id){var db=store.getWritableDatabase();db.beginTransaction();try{var m=movements(null).stream().filter(x->x.id().equals(id)).findFirst().orElseThrow();if(!m.windowsId().isEmpty()||!m.sourceType().isEmpty())throw new IllegalArgumentException("Η εισαγόμενη κίνηση διατηρείται ως ιστορικό.");if(stock(m.itemId())-signed(m.type(),m.quantity()) < -0.000001)throw new IllegalArgumentException("Η διαγραφή θα έκανε το απόθεμα αρνητικό.");MoneyStore.syncReceipt(db,id,true);remove("inventory_movements",id);db.setTransactionSuccessful();}finally{db.endTransaction();}}
    // Called only inside the owning activity transaction. Imported Windows sources keep their original IDs.
    void removeActivityConsumption(String activityId,String movementId){
        if(movementId.isEmpty())return;
        var m=movements(null).stream().filter(x->x.id().equals(movementId)).findFirst().orElseThrow();
        if(!m.sourceType().equals("android_farm_activity")||!m.sourceId().equals(activityId)||!m.windowsId().isEmpty()||!m.type().equals("Κατανάλωση"))throw new IllegalArgumentException("Ασυνεπής σύνδεση εργασίας με αποθήκη.");
        remove("inventory_movements",movementId);
    }
    String syncActivityConsumption(String id,ActivityStore.Activity a,String oldMovement){
        removeActivityConsumption(id,oldMovement);
        double amount=ActivityStore.consumption(a);if(amount<=0)return "";
        return saveMovement(new Movement(null,a.itemId(),a.date(),"Κατανάλωση",amount,a.fieldId(),"","",0,0,"Άρδευση & Λίπανση — "+a.product(),"android_farm_activity",id,"",""),true);
    }
    void removeProtectionConsumption(String id){for(var m:movements(null))if(m.sourceType().equals("android_plant_protection")&&m.sourceId().equals(id)){if(!m.windowsId().isEmpty()||!m.type().equals("Κατανάλωση"))throw new IllegalArgumentException("Ασυνεπής κατανάλωση φυτοπροστασίας.");remove("inventory_movements",m.id());}}
    String syncProtectionConsumption(String id,WorkStore.Protection a){removeProtectionConsumption(id);if(a.inventory_quantity()<=0)return "";return saveMovement(new Movement(null,a.inventory_item_id(),a.application_date(),"Κατανάλωση",a.inventory_quantity(),a.field_id(),"","",0,0,"Φυτοπροστασία — "+a.product_name(),"android_plant_protection",id,"",""),true);}
}
