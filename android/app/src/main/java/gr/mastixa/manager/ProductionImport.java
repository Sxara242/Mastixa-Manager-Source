package gr.mastixa.manager;

import java.util.*;
import java.io.IOException;
import org.json.JSONObject;

final class ProductionImport {
    record Data(List<ProductionStore.Harvest> harvests,List<ProductionStore.Sale> sales) {}
    record Result(int harvests,int sales,int skipped) {}
    private static double number(String value)throws IOException{try{double n=Double.parseDouble(value);if(!Double.isFinite(n)||n<0)throw new NumberFormatException();return n;}catch(NumberFormatException e){throw new IOException("Μη έγκυρη ποσότητα/τιμή παραγωγής.");}}
    private static String product(Map<String,String> r,List<CatalogStore.Product> products)throws IOException{String id=r.getOrDefault("product_id","");var found=products.stream().filter(p->id.isEmpty()?p.name().equalsIgnoreCase(r.get("product")):p.id().equals(id)).toList();if(found.size()!=1)throw new IOException("Εξήγαγε μαζί τα Προϊόντα και καλλιέργειες για την παραγωγή/πωλήσεις.");return found.get(0).id();}
    static Data read(Map<String,byte[]> files,Map<String,JSONObject> tables,List<CatalogStore.Product> products,List<FarmStore.Field> fields,List<PartnerStore.Partner> partners)throws Exception{
        var harvests=new ArrayList<ProductionStore.Harvest>();var sales=new ArrayList<ProductionStore.Sale>();var ids=new HashSet<String>();
        for(var r:CatalogImport.rows("production",files,tables,List.of("id","entry_date","product","field_id","quantity_kg","notes"))){var h=new ProductionStore.Harvest(null,r.get("entry_date"),product(r,products),r.get("product"),r.get("field_id"),number(r.get("quantity_kg")),r.get("notes"),r.get("id"));ProductionStore.validate(h);if(h.windowsId().isEmpty()||!ids.add(h.windowsId())||(!h.fieldId().isEmpty()&&fields.stream().noneMatch(f->f.id().equals(h.fieldId()))))throw new IOException("Λείπει αγροτεμάχιο ή υπάρχει διπλή παραγωγή.");harvests.add(h);}
        ids.clear();var incomes=new HashSet<String>();
        for(var r:CatalogImport.rows("production_sales",files,tables,List.of("id","sale_date","product","buyer_id","buyer_name","quantity_kg","price_per_kg","total_amount","payment_method","notes","income_id"))){var s=new ProductionStore.Sale(null,r.get("sale_date"),product(r,products),r.get("product"),r.get("buyer_id"),r.get("buyer_name"),number(r.get("quantity_kg")),number(r.get("price_per_kg")),number(r.get("total_amount")),r.get("payment_method"),r.get("notes"),r.get("income_id"),r.get("id"));ProductionStore.validate(s);if(s.windowsId().isEmpty()||!ids.add(s.windowsId())||s.incomeWindowsId().isEmpty()||!incomes.add(s.incomeWindowsId())||(!s.buyerId().isEmpty()&&partners.stream().noneMatch(p->p.id().equals(s.buyerId()))))throw new IOException("Λείπει αγοραστής/αναφορά εσόδου ή υπάρχει διπλή πώληση.");sales.add(s);}
        return new Data(List.copyOf(harvests),List.copyOf(sales));
    }
    static Result process(FarmStore store,CatalogImport.Package data,Map<String,String> productMap,Map<String,String> fieldMap,boolean apply){
        var registry=new ProductionStore(store);var partners=new PartnerStore(store).partners();var partnerMap=new HashMap<String,String>();for(var p:data.partners()){var found=partners.stream().filter(x->x.name().equalsIgnoreCase(p.name())&&x.taxId().equalsIgnoreCase(p.taxId())).toList();if(found.size()==1)partnerMap.put(p.id(),found.get(0).id());else if(!apply&&partners.stream().noneMatch(x->x.name().equalsIgnoreCase(p.name())||(!p.taxId().isEmpty()&&p.taxId().equalsIgnoreCase(x.taxId()))))partnerMap.put(p.id(),"new-partner-"+p.id());}
        int harvestCount=0,saleCount=0,skipped=0;var balances=new HashMap<String,Double>();var newHarvests=new ArrayList<ProductionStore.Harvest>();var newSales=new ArrayList<ProductionStore.Sale>();var incomeMap=new HashMap<String,MoneyStore.Entry>();
        for(var h:data.production().harvests()){
            try(var c=store.getReadableDatabase().rawQuery("SELECT 1 FROM production WHERE windows_id=?",new String[]{h.windowsId()})){if(c.moveToFirst()){skipped++;continue;}}
            String product=productMap.get(h.productId()),field=h.fieldId().isEmpty()?"":fieldMap.get(h.fieldId());if(product==null||field==null)throw new IllegalArgumentException("Σύγκρουση προϊόντος/αγροτεμαχίου παραγωγής.");balances.putIfAbsent(product,registry.available(product));balances.merge(product,h.quantity(),Double::sum);newHarvests.add(new ProductionStore.Harvest(null,h.date(),product,h.productName(),field,h.quantity(),h.notes(),h.windowsId()));harvestCount++;
        }
        for(var s:data.production().sales()){
            try(var c=store.getReadableDatabase().rawQuery("SELECT 1 FROM production_sales WHERE windows_id=?",new String[]{s.windowsId()})){if(c.moveToFirst()){skipped++;continue;}}
            String product=productMap.get(s.productId()),buyer=s.buyerId().isEmpty()?"":partnerMap.get(s.buyerId());if(product==null||buyer==null)throw new IllegalArgumentException("Σύγκρουση προϊόντος/αγοραστή πώλησης.");
            var candidates=new MoneyStore(store).entries("income").stream().filter(e->e.windowsId().equals(s.incomeWindowsId())).toList();MoneyStore.Entry income=candidates.size()==1?candidates.get(0):null;
            if(income==null&&!apply)income=data.money().stream().filter(e->e.kind().equals("income")&&e.windowsId().equals(s.incomeWindowsId())).findFirst().orElse(null);
            if(income==null||!income.sourceType().isEmpty()||Math.abs(income.amount()-s.total())>0.005||!income.date().equals(s.date())||!(income.partnerId().equals(buyer)||(!apply&&income.id()==null&&income.partnerId().equals(s.buyerId()))))throw new IllegalArgumentException("Λείπει ή διαφέρει το έσοδο πώλησης. Εξήγαγε μαζί Πωλήσεις και Έσοδα / Έξοδα.");
            incomeMap.put(s.windowsId(),income);balances.putIfAbsent(product,registry.available(product));balances.merge(product,-s.quantity(),Double::sum);newSales.add(new ProductionStore.Sale(null,s.date(),product,s.productName(),buyer,s.buyerName(),s.quantity(),s.price(),s.total(),s.payment(),s.notes(),s.incomeWindowsId(),s.windowsId()));saleCount++;
        }
        if(balances.values().stream().anyMatch(n->!Double.isFinite(n)||n < -0.000001))throw new IllegalArgumentException("Οι πωλήσεις ξεπερνούν τη διαθέσιμη παραγωγή. Εξήγαγε όλη τη σχετική παραγωγή.");
        if(apply){for(var h:newHarvests)registry.saveHarvest(h,true);for(var s:newSales){String id=registry.saveSale(s,true);var e=incomeMap.get(s.windowsId());MoneyStore.put(store.getWritableDatabase(),new MoneyStore.Entry(e.id(),e.kind(),e.date(),e.fieldId(),e.category(),e.description(),e.partnerId(),e.partnerName(),e.payment(),e.amount(),e.notes(),"production_sale",id,e.windowsId()));}}
        return new Result(harvestCount,saleCount,skipped);
    }
}
