package gr.mastixa.manager;

import java.util.*;
import java.io.IOException;
import org.json.JSONObject;

final class InventoryImport {
    record Data(List<InventoryStore.Item> items,List<InventoryStore.Movement> movements) {}
    record Result(int items,int movements,int skipped) {}

    static Data read(Map<String,byte[]> files,Map<String,JSONObject> tables,List<FarmStore.Field> fields,List<PartnerStore.Partner> partners) throws Exception {
        var items=new ArrayList<InventoryStore.Item>();var ids=new HashSet<String>();var names=new HashSet<String>();
        for(var r:CatalogImport.rows("inventory_items",files,tables,List.of("id","name","category","unit","minimum_stock","notes"))){
            var item=new InventoryStore.Item(r.get("id"),r.get("name"),r.get("category"),r.get("unit"),number(r.get("minimum_stock")),r.get("notes"));InventoryStore.validateItem(item);
            if(item.id().isBlank()||!ids.add(item.id())||!names.add(item.name().toLowerCase(Locale.ROOT)))throw new IOException("Διπλό ή μη έγκυρο είδος αποθήκης.");items.add(item);
        }
        var movements=new ArrayList<InventoryStore.Movement>();var movementIds=new HashSet<String>();
        for(var r:CatalogImport.rows("inventory_movements",files,tables,List.of("id","item_id","movement_date","movement_type","quantity","field_id","partner_id","supplier_name","unit_price","total_cost","notes","source_type","source_id","expense_id"))){
            var m=new InventoryStore.Movement(null,r.get("item_id"),r.get("movement_date"),r.get("movement_type"),number(r.get("quantity")),r.get("field_id"),r.get("partner_id"),r.get("supplier_name"),number(r.get("unit_price")),number(r.get("total_cost")),r.get("notes"),r.get("source_type"),r.get("source_id"),r.get("expense_id"),r.get("id"));InventoryStore.validateMovement(m);
            if(m.windowsId().isBlank()||!movementIds.add(m.windowsId())||!ids.contains(m.itemId()))throw new IOException("Λείπει είδος ή υπάρχει διπλή κίνηση αποθήκης.");
            if((!m.fieldId().isEmpty()&&fields.stream().noneMatch(f->f.id().equals(m.fieldId())))||(!m.partnerId().isEmpty()&&partners.stream().noneMatch(p->p.id().equals(m.partnerId()))))throw new IOException("Εξήγαγε μαζί με την αποθήκη Αγροτεμάχια και Προμηθευτές & Αγοραστές για τις συνδεδεμένες κινήσεις.");movements.add(m);
        }
        return new Data(List.copyOf(items),List.copyOf(movements));
    }

    private static double number(String value) throws IOException {try {double n=Double.parseDouble(value);if(!Double.isFinite(n)||n<0)throw new NumberFormatException();return n;}catch(NumberFormatException e){throw new IOException("Μη έγκυρος αριθμός αποθήκης.");}}

    private static boolean sameImportedMovement(InventoryStore.Movement a,InventoryStore.Movement b){
        return a.itemId().equals(b.itemId())
            && a.date().equals(b.date())
            && a.type().equals(b.type())
            && Double.compare(a.quantity(),b.quantity())==0
            && a.fieldId().equals(b.fieldId())
            && a.partnerId().equals(b.partnerId())
            && a.supplier().equals(b.supplier())
            && Double.compare(a.price(),b.price())==0
            && Double.compare(a.cost(),b.cost())==0
            && a.notes().equals(b.notes())
            && a.sourceType().equals(b.sourceType())
            && a.sourceId().equals(b.sourceId())
            && a.expenseId().equals(b.expenseId())
            && a.windowsId().equals(b.windowsId());
    }

    static Result process(FarmStore store,Data data,Map<String,String> fieldMap,List<PartnerStore.Partner> sourcePartners,boolean apply){
        var inventory=new InventoryStore(store);var itemMap=new HashMap<String,String>();int itemCount=0,movementCount=0,skipped=0;
        var known=inventory.items();
        for(var i:data.items()){
            var candidates=known.stream().filter(x->x.name().equalsIgnoreCase(i.name())).toList();
            if(candidates.isEmpty()){itemCount++;itemMap.put(i.id(),apply?inventory.saveItem(new InventoryStore.Item(null,i.name(),i.category(),i.unit(),i.minimum(),i.notes())):"new-inventory-"+i.id());}
            else {skipped++;var x=candidates.get(0);if(candidates.size()==1&&x.name().equals(i.name())&&x.category().equals(i.category())&&x.unit().equals(i.unit())&&x.minimum()==i.minimum()&&x.notes().equals(i.notes()))itemMap.put(i.id(),x.id());}
        }
        var partnerMap=new HashMap<String,String>();var partners=new PartnerStore(store).partners();
        for(var p:sourcePartners){var matches=partners.stream().filter(x->x.name().equalsIgnoreCase(p.name())&&x.taxId().equalsIgnoreCase(p.taxId())).toList();if(matches.size()==1)partnerMap.put(p.id(),matches.get(0).id());else if(!apply&&partners.stream().noneMatch(x->x.name().equalsIgnoreCase(p.name())||(!p.taxId().isEmpty()&&p.taxId().equalsIgnoreCase(x.taxId()))))partnerMap.put(p.id(),"new-partner-"+p.id());}
        var existing=inventory.movements(null);var additions=new ArrayList<InventoryStore.Movement>();
        for(var m:data.movements()){
            String item=itemMap.get(m.itemId()),field=m.fieldId().isEmpty()?"":fieldMap.get(m.fieldId()),partner=m.partnerId().isEmpty()?"":partnerMap.get(m.partnerId());
            if(item==null)throw new IllegalArgumentException("Σύγκρουση είδους αποθήκης. Δεν εισάγονται κινήσεις με διαφορετικά στοιχεία είδους.");
            if(field==null||partner==null)throw new IllegalArgumentException("Σύγκρουση αγροτεμαχίου ή συνεργάτη σε κίνηση αποθήκης. Δεν έγινε εισαγωγή.");
            var mapped=new InventoryStore.Movement(null,item,m.date(),m.type(),m.quantity(),field,partner,m.supplier(),m.price(),m.cost(),m.notes(),m.sourceType(),m.sourceId(),m.expenseId(),m.windowsId());
            var previous=existing.stream().filter(x->x.windowsId().equals(m.windowsId())).toList();
            if(!previous.isEmpty()){
                if(previous.size()==1&&sameImportedMovement(previous.get(0),mapped)){skipped++;continue;}
                throw new IllegalArgumentException("Η ίδια κίνηση Windows έχει αλλάξει από προηγούμενη εισαγωγή. Δεν έγινε σιωπηλή αντικατάσταση ή διπλοεγγραφή.");
            }
            additions.add(mapped);movementCount++;
        }
        var balances=new HashMap<String,Double>();for(var m:additions){balances.putIfAbsent(m.itemId(),inventory.stock(m.itemId()));balances.merge(m.itemId(),InventoryStore.signed(m.type(),m.quantity()),Double::sum);}
        if(balances.values().stream().anyMatch(n->!Double.isFinite(n)||n < -0.000001))throw new IllegalArgumentException("Οι κινήσεις του πακέτου θα έκαναν το απόθεμα αρνητικό.");
        // All additions share the outer import transaction. Receipts first avoid false intermediate deficits.
        additions.sort(Comparator.comparingDouble(m->-InventoryStore.signed(m.type(),m.quantity())));
        if(apply)for(var m:additions)inventory.saveMovement(m,true);
        return new Result(itemCount,movementCount,skipped);
    }
}
