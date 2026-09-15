package gr.mastixa.manager;
import java.util.*;
import java.io.IOException;
import org.json.JSONObject;

final class WorkImport {
    record Data(List<WorkStore.Protection> protections,List<WorkStore.Worker> workers,List<WorkStore.Labor> labor,List<WorkStore.Planting> plantings,EquipmentImport.Data equipment) {Data(List<WorkStore.Protection> p,List<WorkStore.Worker> w,List<WorkStore.Labor> l,List<WorkStore.Planting> b){this(p,w,l,b,EquipmentImport.Data.empty());}Data(List<WorkStore.Protection> p,List<WorkStore.Worker> w,List<WorkStore.Labor> l){this(p,w,l,List.of());}static Data empty(){return new Data(List.of(),List.of(),List.of());}}
    record Result(int protections,int workers,int labor,int plantings,int skipped) {}
    private static double number(Map<String,String> row,String key) throws IOException{try{String value=row.getOrDefault(key,"0");double n=Double.parseDouble(value.isBlank()?"0":value);if(!Double.isFinite(n)||n<0)throw new NumberFormatException();return n;}catch(NumberFormatException e){throw new IOException("Μη έγκυρος αριθμός: "+key);}}
    private static int integer(Map<String,String> row,String key) throws IOException{double n=number(row,key);if(n!=Math.rint(n)||n>Integer.MAX_VALUE)throw new IOException("Μη έγκυρος ακέραιος: "+key);return (int)n;}
    static Data read(Map<String,byte[]> files,Map<String,JSONObject> tables) throws Exception {
        var protections=new ArrayList<WorkStore.Protection>();var protectionsIds=new HashSet<String>();
        for(var r:CatalogImport.rows("plant_protection_records",files,tables,List.of("id","application_date","field_id","inventory_item_id","purpose","product_name","active_ingredient","authorization_number","dose","dose_unit","spray_volume_l","area_stremma","applicator","weather","harvest_interval_days","cost","notes"))){if(r.get("id").isBlank()||!protectionsIds.add(r.get("id")))throw new IOException("Διπλή ή κενή ταυτότητα: plant_protection_records");var a=new WorkStore.Protection(null,r.get("application_date"),r.get("field_id"),r.get("inventory_item_id"),r.get("purpose"),r.get("product_name"),r.get("active_ingredient"),r.get("authorization_number"),number(r,"dose"),r.get("dose_unit"),number(r,"spray_volume_l"),number(r,"area_stremma"),r.get("applicator"),r.get("weather"),integer(r,"harvest_interval_days"),number(r,"cost"),r.get("notes"),number(r,"inventory_quantity"),"",r.get("id"));WorkStore.validate(a);protections.add(a);}
        var workers=new ArrayList<WorkStore.Worker>();var workersIds=new HashSet<String>();
        for(var r:CatalogImport.rows("workers",files,tables,List.of("id","name","role","phone","default_hourly_rate","active","notes"))){if(r.get("id").isBlank()||!workersIds.add(r.get("id")))throw new IOException("Διπλή ή κενή ταυτότητα: workers");var a=new WorkStore.Worker(null,r.get("name"),r.get("role"),r.get("phone"),number(r,"default_hourly_rate"),integer(r,"active"),r.get("notes"),r.get("id"));WorkStore.validate(a);workers.add(a);}
        var labor=new ArrayList<WorkStore.Labor>();var laborIds=new HashSet<String>();
        for(var r:CatalogImport.rows("labor_entries",files,tables,List.of("id","work_date","field_id","worker_id","work_type","hours","hourly_rate","cost","notes"))){if(r.get("id").isBlank()||!laborIds.add(r.get("id")))throw new IOException("Διπλή ή κενή ταυτότητα: labor_entries");var a=new WorkStore.Labor(null,r.get("work_date"),r.get("field_id"),r.get("worker_id"),r.get("work_type"),number(r,"hours"),number(r,"hourly_rate"),number(r,"cost"),r.get("notes"),r.get("id"));WorkStore.validate(a);labor.add(a);}
        var plantings=new ArrayList<WorkStore.Planting>();var plantingIds=new HashSet<String>();
        for(var row:CatalogImport.rows("planting_batches",files,tables,List.of("id","planting_date","field_id","trees_planted","trees_alive","material_type","source","variety","spacing","cost","notes"))){if(row.get("id").isBlank()||!plantingIds.add(row.get("id")))throw new IOException("Διπλή ή κενή ταυτότητα φύτευσης.");var a=new WorkStore.Planting(null,row.get("planting_date"),row.get("field_id"),integer(row,"trees_planted"),integer(row,"trees_alive"),row.get("material_type"),row.get("source"),row.get("variety"),row.get("spacing"),number(row,"cost"),row.get("notes"),row.get("id"));WorkStore.validate(a);plantings.add(a);}
        return new Data(List.copyOf(protections),List.copyOf(workers),List.copyOf(labor),List.copyOf(plantings),EquipmentImport.read(files,tables));
    }
    private static boolean existing(FarmStore store,String table,String windows){try(var c=store.getReadableDatabase().rawQuery("SELECT 1 FROM "+table+" WHERE windows_id=?",new String[]{windows})){return c.moveToFirst();}}
    private static String field(Map<String,String> fields,String id){if(id.isEmpty())return "";String match=fields.get(id);if(match==null)throw new IllegalArgumentException("Εξήγαγε μαζί τα αγροτεμάχια και επίλυσε τυχόν συγκρούσεις.");return match;}
    static Result process(FarmStore store,CatalogImport.Package data,Map<String,String> fields,boolean apply){
        var registry=new WorkStore(store);var stock=new InventoryStore(store);int protectionCount=0,workerCount=0,laborCount=0,skipped=0;var workerMap=new HashMap<String,String>();var names=new HashSet<String>();
        for(var w:data.work().workers()){
            if(!names.add(w.name().trim().toLowerCase(Locale.ROOT)))throw new IllegalArgumentException("Διπλό όνομα εργαζομένου στο ZIP.");
            var byId=registry.workers().stream().filter(x->x.windows_id().equals(w.windows_id())).toList();var byName=registry.workers().stream().filter(x->x.name().equalsIgnoreCase(w.name())).toList();
            if(byId.size()==1){workerMap.put(w.windows_id(),byId.get(0).id());skipped++;}
            else if(existing(store,"workers",w.windows_id())){skipped++;}
            else if(byName.size()==1){var x=byName.get(0);if(!x.role().equals(w.role())||!x.phone().equals(w.phone())||x.default_hourly_rate()!=w.default_hourly_rate()||x.active()!=w.active()||!x.notes().equals(w.notes()))throw new IllegalArgumentException("Σύγκρουση στοιχείων εργαζομένου.");workerMap.put(w.windows_id(),x.id());skipped++;}
            else {String id=apply?registry.saveWorker(w,true):"new-worker-"+w.windows_id();workerMap.put(w.windows_id(),id);workerCount++;}
        }
        for(var a:data.work().labor()){
            if(existing(store,"labor_entries",a.windows_id())){skipped++;continue;}String worker=workerMap.get(a.worker_id());if(worker==null)throw new IllegalArgumentException("Εξήγαγε μαζί το προσωπικό των εργατικών.");String field=field(fields,a.field_id());
            if(apply)registry.saveLabor(new WorkStore.Labor(null,a.work_date(),field,worker,a.work_type(),a.hours(),a.hourly_rate(),a.cost(),a.notes(),a.windows_id()),true);laborCount++;
        }
        for(var a:data.work().protections()){
            if(existing(store,"plant_protection_records",a.windows_id())){skipped++;continue;}String field=field(fields,a.field_id()),item="",movement="";
            if(!a.inventory_item_id().isEmpty()){
                var source=data.inventory().items().stream().filter(x->x.id().equals(a.inventory_item_id())).findFirst().orElseThrow(()->new IllegalArgumentException("Εξήγαγε μαζί την αποθήκη της φυτοπροστασίας."));
                var matches=stock.items().stream().filter(x->x.name().equals(source.name())&&x.unit().equals(source.unit())&&x.category().equals(source.category())&&x.minimum()==source.minimum()&&x.notes().equals(source.notes())).toList();
                if(matches.size()==1)item=matches.get(0).id();else if(!apply&&stock.items().stream().noneMatch(x->x.name().equalsIgnoreCase(source.name())))item="new-inventory-"+source.id();else throw new IllegalArgumentException("Σύγκρουση είδους αποθήκης στη φυτοπροστασία.");
            }
            var sources=data.inventory().movements().stream().filter(m->m.sourceType().equals("plant_protection")&&m.sourceId().equals(a.windows_id())).toList();double amount=a.inventory_quantity();
            if(sources.size()!=(amount>0?1:0))throw new IllegalArgumentException("Λείπει ή είναι ασυνεπής η κατανάλωση φυτοπροστασίας. Εξήγαγε μαζί την αποθήκη.");
            if(amount>0){var m=sources.get(0);if(!m.type().equals("Κατανάλωση")||!m.itemId().equals(a.inventory_item_id())||!m.fieldId().equals(a.field_id())||!m.date().equals(a.application_date())||Math.abs(m.quantity()-amount)>0.000001)throw new IllegalArgumentException("Η κατανάλωση διαφέρει από τη φυτοπροστασία Windows.");String mappedItem=item;var found=stock.movements(null).stream().filter(x->x.windowsId().equals(m.windowsId())&&x.itemId().equals(mappedItem)).toList();if(found.size()==1){var x=found.get(0);if(!x.sourceType().equals("plant_protection")||!x.sourceId().equals(a.windows_id())||!x.fieldId().equals(field)||!x.date().equals(a.application_date())||!x.type().equals("Κατανάλωση")||Math.abs(x.quantity()-amount)>0.000001)throw new IllegalArgumentException("Η υπάρχουσα κατανάλωση διαφέρει από τη φυτοπροστασία.");movement=x.id();}else if(apply)throw new IllegalArgumentException("Δεν βρέθηκε συνδεδεμένη κατανάλωση.");}
            if(apply)registry.saveProtection(new WorkStore.Protection(null,a.application_date(),field,item,a.purpose(),a.product_name(),a.active_ingredient(),a.authorization_number(),a.dose(),a.dose_unit(),a.spray_volume_l(),a.area_stremma(),a.applicator(),a.weather(),a.harvest_interval_days(),a.cost(),a.notes(),a.inventory_quantity(),movement,a.windows_id()),true);protectionCount++;
        }
        int plantingCount=0;for(var a:data.work().plantings()){if(existing(store,"planting_batches",a.windows_id())){skipped++;continue;}String field=field(fields,a.field_id());if(apply)registry.savePlanting(new WorkStore.Planting(null,a.planting_date(),field,a.trees_planted(),a.trees_alive(),a.material_type(),a.source(),a.variety(),a.spacing(),a.cost(),a.notes(),a.windows_id()),true);plantingCount++;}
        return new Result(protectionCount,workerCount,laborCount,plantingCount,skipped);
    }
}
