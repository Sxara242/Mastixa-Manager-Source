package gr.mastixa.manager;

import java.util.*;
import java.io.IOException;
import org.json.JSONObject;

final class MoneyImport {
    record Result(int income,int expenses,int skipped) {}
    static List<MoneyStore.Entry> read(Map<String,byte[]> files,Map<String,JSONObject> tables,List<FarmStore.Field> fields,List<PartnerStore.Partner> partners) throws Exception {
        var result=new ArrayList<MoneyStore.Entry>();
        for(String table:List.of("income","expenses")){
            boolean income=table.equals("income");var required=new ArrayList<>(List.of("id","entry_date","field_id","description","payment_method","amount","notes",income?"partner":"supplier"));if(!income)required.add("category");var ids=new HashSet<String>();
            for(var r:CatalogImport.rows(table,files,tables,required)){
                double amount;try{amount=Double.parseDouble(r.get("amount"));}catch(NumberFormatException ex){throw new IOException("Μη έγκυρο οικονομικό ποσό.");}
                var e=new MoneyStore.Entry(null,income?"income":"expense",r.get("entry_date"),r.get("field_id"),income?"":r.get("category"),r.get("description"),r.getOrDefault("partner_id",""),r.get(income?"partner":"supplier"),r.get("payment_method"),amount,r.get("notes"),r.getOrDefault("source_type",""),r.getOrDefault("source_id",""),r.get("id"));MoneyStore.validate(e);
                if(e.windowsId().isBlank()||!ids.add(e.windowsId()))throw new IOException("Διπλή οικονομική εγγραφή.");
                if((!e.fieldId().isEmpty()&&fields.stream().noneMatch(f->f.id().equals(e.fieldId())))||(!e.partnerId().isEmpty()&&partners.stream().noneMatch(p->p.id().equals(e.partnerId()))))throw new IOException("Εξήγαγε μαζί με τα οικονομικά Αγροτεμάχια και Προμηθευτές & Αγοραστές.");result.add(e);
            }
        }
        return List.copyOf(result);
    }
    static Result process(FarmStore store,CatalogImport.Package data,Map<String,String> fieldMap,boolean apply){
        var db=store.getWritableDatabase();var registry=new MoneyStore(store);var partners=new PartnerStore(store).partners();var partnerMap=new HashMap<String,String>();
        for(var p:data.partners()){var found=partners.stream().filter(x->x.name().equalsIgnoreCase(p.name())&&x.taxId().equalsIgnoreCase(p.taxId())).toList();if(found.size()==1)partnerMap.put(p.id(),found.get(0).id());else if(!apply&&partners.stream().noneMatch(x->x.name().equalsIgnoreCase(p.name())||(!p.taxId().isEmpty()&&x.taxId().equalsIgnoreCase(p.taxId()))))partnerMap.put(p.id(),"new-partner-"+p.id());}
        int incomes=0,expenses=0,skipped=0;var receiptSources=new HashSet<String>();
        for(var e:data.money()){
            try(var c=db.rawQuery("SELECT 1 FROM money_entries WHERE kind=? AND windows_id=?",new String[]{e.kind(),e.windowsId()})){if(c.moveToFirst()){skipped++;continue;}}
            String field=e.fieldId().isEmpty()?"":fieldMap.get(e.fieldId()),partner=e.partnerId().isEmpty()?"":partnerMap.get(e.partnerId());if(field==null||partner==null)throw new IllegalArgumentException("Σύγκρουση σχέσεων οικονομικής εγγραφής. Δεν έγινε εισαγωγή.");
            String source=e.sourceType().isEmpty()?"":"windows:"+e.sourceType(),sourceId=e.sourceId();
            if(e.kind().equals("expense")){
                var linked=data.inventory().movements().stream().filter(m->m.expenseId().equals(e.windowsId())).toList();
                if(linked.size()>1)throw new IllegalArgumentException("Πολλές παραλαβές δείχνουν στο ίδιο έξοδο.");
                if(e.sourceType().equals("inventory_receipt")&&e.sourceId().isEmpty())throw new IllegalArgumentException("Λείπει η ταυτότητα της συνδεδεμένης παραλαβής.");
                String windowsMovement=e.sourceType().equals("inventory_receipt")?e.sourceId():linked.isEmpty()?"":linked.get(0).windowsId();
                if(!windowsMovement.isEmpty()){
                    if(!linked.isEmpty()&&!linked.get(0).windowsId().equals(windowsMovement))throw new IllegalArgumentException("Ασυνεπής σύνδεση παραλαβής/εξόδου.");
                    var found=new InventoryStore(store).movements(null).stream().filter(m->m.windowsId().equals(windowsMovement)).toList();
                    if(found.size()==1){var m=found.get(0);if(!m.type().equals("Παραλαβή")||Math.abs(m.cost()-e.amount())>0.005)throw new IllegalArgumentException("Το κόστος παραλαβής διαφέρει από το έξοδο.");sourceId=m.id();}
                    else if(found.isEmpty()&&!apply){var incoming=data.inventory().movements().stream().filter(m->m.windowsId().equals(windowsMovement)).toList();if(incoming.size()!=1||!incoming.get(0).type().equals("Παραλαβή")||Math.abs(incoming.get(0).cost()-e.amount())>0.005)throw new IllegalArgumentException("Λείπει ή διαφέρει η συνδεδεμένη παραλαβή. Εξήγαγε μαζί Αποθήκη και Οικονομικά.");sourceId="new-movement-"+windowsMovement;}
                    else throw new IllegalArgumentException("Λείπει ή είναι αμφίσημη η παραλαβή. Εξήγαγε μαζί Αποθήκη και Οικονομικά.");
                    source="inventory_receipt";if(!receiptSources.add(sourceId))throw new IllegalArgumentException("Διπλό έξοδο για την ίδια παραλαβή.");
                    try(var c=db.rawQuery("SELECT 1 FROM money_entries WHERE kind='expense' AND source_type='inventory_receipt' AND source_id=?",new String[]{sourceId})){if(c.moveToFirst())throw new IllegalArgumentException("Υπάρχει ήδη έξοδο για την παραλαβή.");}
                }
            }
            if(e.kind().equals("income"))incomes++;else expenses++;
            if(apply)MoneyStore.put(db,new MoneyStore.Entry(null,e.kind(),e.date(),field,e.category(),e.description(),partner,e.partnerName(),e.payment(),e.amount(),e.notes(),source,sourceId,e.windowsId()));
        }
        return new Result(incomes,expenses,skipped);
    }
}
