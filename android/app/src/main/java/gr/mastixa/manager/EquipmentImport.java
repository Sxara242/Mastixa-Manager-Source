package gr.mastixa.manager;
import java.util.*;
import java.io.IOException;
import org.json.JSONObject;

final class EquipmentImport {
    record Data(List<WorkStore.Equipment> equipment,List<WorkStore.Service> services){static Data empty(){return new Data(List.of(),List.of());}}
    record Result(int equipment,int services,int skipped) {}
    private static double number(String value) throws IOException{try{double n=Double.parseDouble(value);if(!Double.isFinite(n)||n<0)throw new NumberFormatException();return n;}catch(NumberFormatException e){throw new IOException("Μη έγκυρος αριθμός μηχανήματος/service.");}}
    static Data read(Map<String,byte[]> files,Map<String,JSONObject> tables) throws Exception{
        var equipment=new ArrayList<WorkStore.Equipment>();var services=new ArrayList<WorkStore.Service>();var ids=new HashSet<String>();
        for(var r:CatalogImport.rows("equipment",files,tables,List.of("id","name","category","brand_model","equipment_code","purchase_date","fuel","meter_type","current_meter","status","notes"))){if(r.get("id").isBlank()||!ids.add(r.get("id")))throw new IOException("Διπλό μηχάνημα.");var a=new WorkStore.Equipment(null,r.get("name"),r.get("category"),r.get("brand_model"),r.get("equipment_code"),r.get("purchase_date"),r.get("fuel"),r.get("meter_type"),number(r.get("current_meter")),r.get("status"),r.get("notes"),r.get("id"));WorkStore.validate(a);equipment.add(a);}
        ids.clear();for(var r:CatalogImport.rows("equipment_maintenance",files,tables,List.of("id","equipment_id","service_date","service_type","cost","meter_value","technician","notes","next_service_date","next_service_meter"))){if(r.get("id").isBlank()||!ids.add(r.get("id")))throw new IOException("Διπλή συντήρηση.");var a=new WorkStore.Service(null,r.get("equipment_id"),r.get("service_date"),r.get("service_type"),number(r.get("cost")),number(r.get("meter_value")),r.get("technician"),r.get("notes"),r.get("next_service_date"),r.get("next_service_meter").isBlank()?null:number(r.get("next_service_meter")),r.getOrDefault("expense_id",""),r.get("id"));WorkStore.validate(a);services.add(a);}
        return new Data(List.copyOf(equipment),List.copyOf(services));
    }
    static Result process(FarmStore store,CatalogImport.Package data,boolean apply){
        var work=new WorkStore(store);var known=work.equipment();var mapping=new HashMap<String,String>();int count=0,serviceCount=0,skipped=0;
        for(var a:data.work().equipment().equipment()){
            var existing=known.stream().filter(e->e.windows_id().equals(a.windows_id())).toList();if(existing.size()==1){mapping.put(a.windows_id(),existing.get(0).id());skipped++;continue;}
            try(var c=store.getReadableDatabase().rawQuery("SELECT 1 FROM equipment WHERE windows_id=?",new String[]{a.windows_id()})){if(c.moveToFirst()){skipped++;continue;}}
            var matches=known.stream().filter(e->e.windows_id().isEmpty()&&e.name().equals(a.name())&&e.equipment_code().equals(a.equipment_code())).toList();
            if(!matches.isEmpty()){if(matches.size()!=1)throw new IllegalArgumentException("Αμφίσημη αντιστοίχιση μηχανήματος.");var e=matches.get(0);if(mapping.containsValue(e.id()))throw new IllegalArgumentException("Πολλά μηχανήματα Windows αντιστοιχούν στην ίδια τοπική εγγραφή.");if(!e.category().equals(a.category())||!e.brand_model().equals(a.brand_model())||!e.purchase_date().equals(a.purchase_date())||!e.fuel().equals(a.fuel())||!e.meter_type().equals(a.meter_type())||e.current_meter()!=a.current_meter()||!e.status().equals(a.status())||!e.notes().equals(a.notes()))throw new IllegalArgumentException("Σύγκρουση στοιχείων μηχανήματος.");mapping.put(a.windows_id(),e.id());skipped++;}
            else{mapping.put(a.windows_id(),apply?work.saveEquipment(a,true):"new-equipment-"+a.windows_id());count++;}
        }
        var expenseIds=new HashSet<String>();
        for(var a:data.work().equipment().services()){
            try(var c=store.getReadableDatabase().rawQuery("SELECT 1 FROM equipment_maintenance WHERE windows_id=?",new String[]{a.windows_id()})){if(c.moveToFirst()){skipped++;continue;}}
            String equipment=mapping.get(a.equipment_id());if(equipment==null)throw new IllegalArgumentException("Εξήγαγε μαζί τα μηχανήματα της συντήρησης.");MoneyStore.Entry expense=null;
            if(a.cost()>0){if(a.expense_windows_id().isEmpty()||!expenseIds.add(a.expense_windows_id()))throw new IllegalArgumentException("Λείπει ή επαναχρησιμοποιείται έξοδο συντήρησης. Εξήγαγε μαζί τα οικονομικά.");expense=new MoneyStore(store).entries("expense").stream().filter(e->e.windowsId().equals(a.expense_windows_id())).findFirst().orElse(null);if(expense==null&&!apply)expense=data.money().stream().filter(e->e.kind().equals("expense")&&e.windowsId().equals(a.expense_windows_id())).findFirst().orElse(null);
                if(expense==null||Math.abs(expense.amount()-a.cost())>0.005||!expense.date().equals(a.service_date())||(!expense.sourceType().isEmpty()&&(!Set.of("equipment_maintenance","windows:equipment_maintenance").contains(expense.sourceType())||!expense.sourceId().equals(a.windows_id()))))throw new IllegalArgumentException("Λείπει ή διαφέρει το συνδεδεμένο έξοδο συντήρησης.");
            }else if(!a.expense_windows_id().isEmpty())throw new IllegalArgumentException("Service χωρίς κόστος έχει συνδεδεμένο έξοδο.");
            if(apply){String id=work.saveService(new WorkStore.Service(null,equipment,a.service_date(),a.service_type(),a.cost(),a.meter_value(),a.technician(),a.notes(),a.next_service_date(),a.next_service_meter(),a.expense_windows_id(),a.windows_id()),true);if(expense!=null)MoneyStore.put(store.getWritableDatabase(),new MoneyStore.Entry(expense.id(),expense.kind(),expense.date(),expense.fieldId(),expense.category(),expense.description(),expense.partnerId(),expense.partnerName(),expense.payment(),expense.amount(),expense.notes(),"equipment_maintenance",id,expense.windowsId()));}serviceCount++;
        }return new Result(count,serviceCount,skipped);
    }
}
