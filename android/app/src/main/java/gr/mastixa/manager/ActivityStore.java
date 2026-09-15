package gr.mastixa.manager;

import android.content.ContentValues;
import android.database.sqlite.SQLiteDatabase;
import java.util.*;

/** Activities and their inventory consumption commit as one unit. Cost is descriptive, as on Windows. */
public final class ActivityStore {
    public static final List<String> CATEGORIES=List.of("Πότισμα","Λίπανση");
    public static final List<String> STATUSES=List.of("Προγραμματισμένη","Ολοκληρώθηκε","Ακυρώθηκε");
    public record Activity(String id,String date,String fieldId,String category,String status,double duration,double water,String product,double dose,String doseUnit,double cost,String responsible,String notes,String itemId,double inventoryQuantity,double quantity,String unit,String description,String movementId,String windowsId) {}
    static final String[] COLUMNS={"id","activity_date","field_id","category","status","duration_minutes","water_quantity_m3","product","dose","dose_unit","cost","responsible","notes","inventory_item_id","inventory_quantity","quantity","unit","description","movement_id","windows_id","revision","updated_at","deleted_at"};
    private final FarmStore store;
    public ActivityStore(FarmStore store){this.store=store;}
    static void createTables(SQLiteDatabase db){db.execSQL("CREATE TABLE farm_activities(id TEXT PRIMARY KEY,activity_date TEXT NOT NULL,field_id TEXT NOT NULL,category TEXT NOT NULL,status TEXT NOT NULL,duration_minutes REAL NOT NULL CHECK(duration_minutes>=0),water_quantity_m3 REAL NOT NULL CHECK(water_quantity_m3>=0),product TEXT NOT NULL,dose REAL NOT NULL CHECK(dose>=0),dose_unit TEXT NOT NULL,cost REAL NOT NULL CHECK(cost>=0),responsible TEXT NOT NULL,notes TEXT NOT NULL,inventory_item_id TEXT NOT NULL,inventory_quantity REAL NOT NULL CHECK(inventory_quantity>=0),quantity REAL NOT NULL CHECK(quantity>=0),unit TEXT NOT NULL,description TEXT NOT NULL,movement_id TEXT NOT NULL,windows_id TEXT NOT NULL,revision INTEGER NOT NULL,updated_at INTEGER NOT NULL,deleted_at INTEGER)");db.execSQL("CREATE UNIQUE INDEX activity_windows ON farm_activities(windows_id) WHERE windows_id<>''");}
    public List<Activity> activities(){var result=new ArrayList<Activity>();try(var c=store.getReadableDatabase().rawQuery("SELECT id,activity_date,field_id,category,status,duration_minutes,water_quantity_m3,product,dose,dose_unit,cost,responsible,notes,inventory_item_id,inventory_quantity,quantity,unit,description,movement_id,windows_id FROM farm_activities WHERE deleted_at IS NULL ORDER BY activity_date DESC,updated_at DESC,id",null)){while(c.moveToNext())result.add(new Activity(c.getString(0),c.getString(1),c.getString(2),c.getString(3),c.getString(4),c.getDouble(5),c.getDouble(6),c.getString(7),c.getDouble(8),c.getString(9),c.getDouble(10),c.getString(11),c.getString(12),c.getString(13),c.getDouble(14),c.getDouble(15),c.getString(16),c.getString(17),c.getString(18),c.getString(19)));}return result;}
    static void validate(Activity a){
        if(a.date().isBlank())throw new IllegalArgumentException("Χρειάζεται ημερομηνία.");CatalogStore.validateCultivation(a.date(),"active");
        if(!CATEGORIES.contains(a.category())||!STATUSES.contains(a.status()))throw new IllegalArgumentException("Μη έγκυρο είδος ή κατάσταση εργασίας.");
        for(double value:new double[]{a.duration(),a.water(),a.dose(),a.cost(),a.inventoryQuantity(),a.quantity()})if(!Double.isFinite(value)||value<0)throw new IllegalArgumentException("Χρειάζονται μη αρνητικοί αριθμοί.");
        if(a.inventoryQuantity()>0&&a.itemId().isEmpty())throw new IllegalArgumentException("Επίλεξε είδος αποθήκης.");
    }
    static double consumption(Activity a){return a.category().equals("Λίπανση")&&a.status().equals("Ολοκληρώθηκε")?a.inventoryQuantity():0;}
    private void reference(String table,String id){if(id.isEmpty())return;try(var c=store.getReadableDatabase().rawQuery("SELECT 1 FROM "+table+" WHERE id=?",new String[]{id})){if(!c.moveToFirst())throw new IllegalArgumentException("Λείπει συνδεδεμένη εγγραφή: "+table);}}
    private int revision(SQLiteDatabase db,String id){try(var c=db.rawQuery("SELECT revision FROM farm_activities WHERE id=? AND deleted_at IS NULL",new String[]{id})){if(!c.moveToFirst())throw new IllegalArgumentException("Η εργασία δεν υπάρχει.");return c.getInt(0);}}
    private void queue(SQLiteDatabase db,String id,String operation,int revision,long now){var v=new ContentValues();v.put("operation_id",UUID.randomUUID().toString());v.put("entity","farm_activities");v.put("entity_id",id);v.put("operation",operation);v.put("revision",revision);v.put("created_at",now);db.insertOrThrow("pending_changes",null,v);}
    public String save(Activity a){return save(a,false);}
    String save(Activity a,boolean importing){validate(a);var db=store.getWritableDatabase();db.beginTransaction();try{
        reference("fields",a.fieldId());reference("inventory_items",a.itemId());
        var old=a.id()==null?null:activities().stream().filter(x->x.id().equals(a.id())).findFirst().orElseThrow();
        if(!importing){
            if(!a.windowsId().isEmpty()||(old!=null&&!old.windowsId().isEmpty()))throw new IllegalArgumentException("Το εισαγόμενο ιστορικό δεν αλλάζει.");
            if(a.category().equals("Πότισμα")?(a.duration()<=0&&a.water()<=0):(a.product().isBlank()||a.dose()<=0))throw new IllegalArgumentException("Για πότισμα συμπλήρωσε διάρκεια ή νερό. Για λίπανση συμπλήρωσε προϊόν και θετική δόση.");
            if(a.category().equals("Πότισμα")&&(!a.itemId().isEmpty()||a.inventoryQuantity()!=0))throw new IllegalArgumentException("Η αυτόματη κατανάλωση αφορά μόνο λίπανση.");
        }
        String id=a.id()==null?UUID.randomUUID().toString():a.id();int rev=old==null?1:revision(db,id)+1;long now=System.currentTimeMillis();
        String movement=importing?a.movementId():new InventoryStore(store).syncActivityConsumption(id,a,old==null?"":old.movementId());
        reference("inventory_movements",movement);
        var v=new ContentValues();v.put("activity_date",a.date());v.put("field_id",a.fieldId());v.put("category",a.category());v.put("status",a.status());v.put("duration_minutes",a.duration());v.put("water_quantity_m3",a.water());v.put("product",a.product());v.put("dose",a.dose());v.put("dose_unit",a.doseUnit());v.put("cost",a.cost());v.put("responsible",a.responsible());v.put("notes",a.notes());v.put("inventory_item_id",a.itemId());v.put("inventory_quantity",a.inventoryQuantity());v.put("quantity",a.quantity());v.put("unit",a.unit());v.put("description",a.description());v.put("windows_id",a.windowsId()); v.put("id",id);v.put("movement_id",movement);v.put("revision",rev);v.put("updated_at",now);
        if(old==null)db.insertOrThrow("farm_activities",null,v);else db.update("farm_activities",v,"id=?",new String[]{id});queue(db,id,old==null?"create":"update",rev,now);db.setTransactionSuccessful();return id;
    }finally{db.endTransaction();}}
    public void delete(String id){var db=store.getWritableDatabase();db.beginTransaction();try{var a=activities().stream().filter(x->x.id().equals(id)).findFirst().orElseThrow();if(!a.windowsId().isEmpty())throw new IllegalArgumentException("Το εισαγόμενο ιστορικό διατηρείται.");new InventoryStore(store).removeActivityConsumption(id,a.movementId());int rev=revision(db,id)+1;long now=System.currentTimeMillis();var v=new ContentValues();v.put("revision",rev);v.put("updated_at",now);v.put("deleted_at",now);db.update("farm_activities",v,"id=?",new String[]{id});queue(db,id,"delete",rev,now);db.setTransactionSuccessful();}finally{db.endTransaction();}}
}
