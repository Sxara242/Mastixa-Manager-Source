package gr.mastixa.manager;

import java.util.*;
import java.io.IOException;
import org.json.JSONObject;

final class ActivityImport {
    record Result(int added,int skipped) {}
    private static double number(Map<String,String> row,String key) throws IOException {try{String value=row.getOrDefault(key,"0");double n=Double.parseDouble(value.isBlank()?"0":value);if(!Double.isFinite(n)||n<0)throw new NumberFormatException();return n;}catch(NumberFormatException e){throw new IOException("Μη έγκυρος αριθμός εργασίας: "+key);}}
    static List<ActivityStore.Activity> read(Map<String,byte[]> files,Map<String,JSONObject> tables) throws Exception {
        var result=new ArrayList<ActivityStore.Activity>();var ids=new HashSet<String>();
        for(var r:CatalogImport.rows("farm_activities",files,tables,List.of("id","activity_date","field_id","category","status","description","notes"))){
            if(r.get("id").isBlank()||!ids.add(r.get("id")))throw new IOException("Διπλή ή κενή ταυτότητα εργασίας.");
            var a=new ActivityStore.Activity(null,r.get("activity_date"),r.get("field_id"),r.get("category"),r.get("status"),number(r,"duration_minutes"),number(r,"water_quantity_m3"),r.getOrDefault("product",""),number(r,"dose"),r.getOrDefault("dose_unit",""),number(r,"cost"),r.getOrDefault("responsible",""),r.get("notes"),r.getOrDefault("inventory_item_id",""),number(r,"inventory_quantity"),number(r,"quantity"),r.getOrDefault("unit",""),r.get("description"),"",r.get("id"));ActivityStore.validate(a);result.add(a);
        }return List.copyOf(result);
    }
    static Result process(FarmStore store,CatalogImport.Package data,Map<String,String> fields,boolean apply){
        var registry=new ActivityStore(store);var stock=new InventoryStore(store);int added=0,skipped=0;
        for(var a:data.activities()){
            try(var c=store.getReadableDatabase().rawQuery("SELECT 1 FROM farm_activities WHERE windows_id=?",new String[]{a.windowsId()})){if(c.moveToFirst()){skipped++;continue;}}
            String field=a.fieldId().isEmpty()?"":fields.get(a.fieldId()),item="",movement="";
            if(field==null)throw new IllegalArgumentException("Εξήγαγε μαζί τα αγροτεμάχια της άρδευσης/λίπανσης και επίλυσε τυχόν συγκρούσεις.");
            if(!a.itemId().isEmpty()){
                var source=data.inventory().items().stream().filter(x->x.id().equals(a.itemId())).findFirst().orElseThrow(()->new IllegalArgumentException("Εξήγαγε μαζί την αποθήκη της λίπανσης."));
                var matches=stock.items().stream().filter(x->x.name().equals(source.name())&&x.unit().equals(source.unit())&&x.category().equals(source.category())&&x.minimum()==source.minimum()&&x.notes().equals(source.notes())).toList();
                if(matches.size()==1)item=matches.get(0).id();else if(!apply&&stock.items().stream().noneMatch(x->x.name().equalsIgnoreCase(source.name())))item="new-inventory-"+source.id();else throw new IllegalArgumentException("Σύγκρουση είδους αποθήκης στη λίπανση.");
            }
            var sources=data.inventory().movements().stream().filter(m->m.sourceType().equals("farm_activity")&&m.sourceId().equals(a.windowsId())).toList();
            double amount=ActivityStore.consumption(a);
            if(sources.size()!=(amount>0?1:0))throw new IllegalArgumentException("Λείπει ή είναι ασυνεπής η κατανάλωση της εργασίας. Εξήγαγε μαζί Άρδευση & Λίπανση και Αποθήκη & Εφόδια.");
            if(amount>0){
                var m=sources.get(0);if(!m.type().equals("Κατανάλωση")||!m.itemId().equals(a.itemId())||!m.fieldId().equals(a.fieldId())||!m.date().equals(a.date())||Math.abs(m.quantity()-amount)>0.000001)throw new IllegalArgumentException("Η κατανάλωση διαφέρει από την εργασία Windows.");
                String mappedItem=item;var found=stock.movements(null).stream().filter(x->x.windowsId().equals(m.windowsId())&&x.itemId().equals(mappedItem)).toList();
                if(found.size()==1){var x=found.get(0);if(!x.sourceType().equals("farm_activity")||!x.sourceId().equals(a.windowsId())||!x.fieldId().equals(field)||!x.date().equals(a.date())||!x.type().equals("Κατανάλωση")||Math.abs(x.quantity()-amount)>0.000001)throw new IllegalArgumentException("Η υπάρχουσα κατανάλωση διαφέρει από την εργασία.");movement=x.id();}
                else if(apply)throw new IllegalArgumentException("Δεν βρέθηκε η συνδεδεμένη κατανάλωση.");
            }
            if(apply)registry.save(new ActivityStore.Activity(null,a.date(),field,a.category(),a.status(),a.duration(),a.water(),a.product(),a.dose(),a.doseUnit(),a.cost(),a.responsible(),a.notes(),item,a.inventoryQuantity(),a.quantity(),a.unit(),a.description(),movement,a.windowsId()),true);
            added++;
        }return new Result(added,skipped);
    }
}
