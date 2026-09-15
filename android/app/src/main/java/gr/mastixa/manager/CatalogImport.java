package gr.mastixa.manager;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.zip.*;
import org.json.*;
import android.util.AtomicFile;

/** Supported Windows registries are validated together and committed atomically. */
public final class CatalogImport {
    public record Package(List<FarmStore.Field> fields,CatalogStore.Producer producer,List<CatalogStore.Product> products,List<CatalogStore.Link> links,List<PartnerStore.Partner> partners,InventoryImport.Data inventory,List<MoneyStore.Entry> money,ProductionImport.Data production,List<ActivityStore.Activity> activities,WorkImport.Data work,DocumentImport.Data documents,List<String> ignored) { public Package(List<FarmStore.Field> fields,CatalogStore.Producer producer,List<CatalogStore.Product> products,List<CatalogStore.Link> links,List<PartnerStore.Partner> partners,InventoryImport.Data inventory,List<MoneyStore.Entry> money,ProductionImport.Data production,List<ActivityStore.Activity> activities,WorkImport.Data work,List<String> ignored){this(fields,producer,products,links,partners,inventory,money,production,activities,work,DocumentImport.Data.empty(),ignored);} }
    public record Summary(int fields,int producer,int products,int links,int partners,int inventoryItems,int inventoryMovements,int income,int expenses,int harvests,int sales,int activities,int protections,int workers,int labor,int plantings,int equipment,int services,int documents,int yearLocks,int skipped,List<String> ignored) {}
    public static Package read(InputStream input) throws Exception {
        byte[] bytes=LocalBackup.read(input); if(bytes.length>10*1024*1024)throw new IOException("ZIP: όριο 10 MB / 10 MB limit"); var files=new HashMap<String,byte[]>(); int total=0,count=0;
        try(var zip=new ZipInputStream(new ByteArrayInputStream(bytes))) {
            ZipEntry entry; byte[] buffer=new byte[8192];
            while((entry=zip.getNextEntry())!=null) {
                if(++count>1000) throw new IOException("Πάρα πολλά αρχεία.");
                var out=new ByteArrayOutputStream(); int n;
                while((n=zip.read(buffer))!=-1) { total+=n; if(total>10*1024*1024) throw new IOException("Όριο 10 MB. Εξήγαγε μόνο τα υποστηριζόμενα μητρώα."); out.write(buffer,0,n); }
                if(files.put(entry.getName(),out.toByteArray())!=null) throw new IOException("Διπλό αρχείο στο ZIP.");
            }
        }
        if(!files.containsKey("manifest.json")) throw new IOException("Λείπει το manifest.");
        var manifest=new JSONObject(new String(files.get("manifest.json"),StandardCharsets.UTF_8));
        if(!"mastixa-manager-portable-export-v1".equals(manifest.getString("schema"))) throw new IOException("Μη συμβατό ZIP.");
        var tables=new HashMap<String,JSONObject>(); var ignored=new ArrayList<String>();
        var list=manifest.getJSONArray("tables");
        for(int i=0;i<list.length();i++) {
            var row=list.getJSONObject(i); String table=row.getString("table");
            if(tables.put(table,row)!=null) throw new IOException("Διπλός πίνακας.");
            if(!Set.of("fields","producer","products","product_fields","business_partners","inventory_items","inventory_movements","income","expenses","production","production_sales","farm_activities","plant_protection_records","workers","labor_entries","planting_batches","equipment","equipment_maintenance","invoice_documents","year_locks").contains(table) && row.optString("status").equals("exported")) ignored.add(table);
        }
        var fields=files.containsKey("tables/fields.csv")?WindowsImport.read(new ByteArrayInputStream(bytes)):List.<FarmStore.Field>of();
        CatalogStore.Producer producer=null;
        var producers=rows("producer",files,tables,List.of("id","name","tax_id","phone","email","notes"));
        if(producers.size()>1) throw new IOException("Περισσότεροι από ένας παραγωγοί.");
        if(!producers.isEmpty()) {
            var p=producers.get(0); if(!p.get("id").equals("1")) throw new IOException("Μη έγκυρος παραγωγός.");
            producer=new CatalogStore.Producer(p.get("name"),p.get("tax_id"),p.get("phone"),p.get("email"),p.get("notes"));
        }
        var products=new ArrayList<CatalogStore.Product>(); var ids=new HashSet<String>(); var names=new HashSet<String>();
        for(var p:rows("products",files,tables,List.of("id","name","unit","is_active"))) {
            if(p.get("id").isEmpty() || !ids.add(p.get("id")) || p.get("name").isEmpty() || !names.add(p.get("name").toLowerCase(Locale.ROOT)) || p.get("unit").isEmpty() || !Set.of("0","1").contains(p.get("is_active"))) throw new IOException("Μη έγκυρο ή διπλό προϊόν.");
            products.add(new CatalogStore.Product(p.get("id"),p.get("name"),p.get("unit"),p.get("is_active").equals("1")));
        }
        var fieldIds=new HashSet<String>(); for(var f:fields) fieldIds.add(f.id());
        var links=new ArrayList<CatalogStore.Link>(); var linkIds=new HashSet<String>();
        for(var l:rows("product_fields",files,tables,List.of("product_id","field_id","variety","planting_date","cultivation_status"))) {
            String id=l.get("product_id")+":"+l.get("field_id");
            if(!ids.contains(l.get("product_id")) || !fieldIds.contains(l.get("field_id")) || !linkIds.add(id)) throw new IOException("Λείπουν προϊόντα/αγροτεμάχια για σύνδεση ή υπάρχει διπλή σύνδεση. Εξήγαγε μαζί τα μητρώα.");
            CatalogStore.validateCultivation(l.get("planting_date"),l.get("cultivation_status"));
            links.add(new CatalogStore.Link(id,l.get("product_id"),l.get("field_id"),l.get("variety"),l.get("planting_date"),l.get("cultivation_status")));
        }
        if(!tables.keySet().stream().anyMatch(t->Set.of("fields","producer","products","product_fields","business_partners","inventory_items","inventory_movements","income","expenses","production","production_sales","farm_activities","plant_protection_records","workers","labor_entries","planting_batches","equipment","equipment_maintenance","invoice_documents","year_locks").contains(t))) throw new IOException("Το ZIP δεν περιλαμβάνει υποστηριζόμενα μητρώα.");
        if(tables.containsKey("fields") && tables.get("fields").optString("status").equals("exported") && !files.containsKey("tables/fields.csv")) throw new IOException("Λείπουν αγροτεμάχια.");
        var partners=new ArrayList<PartnerStore.Partner>(); var partnerIds=new HashSet<String>(); var partnerNames=new HashSet<String>();
        var required=new ArrayList<String>(List.of(PartnerStore.DETAILS)); required.add("id");
        for(var p:rows("business_partners",files,tables,required)) {
            if(p.get("id").isBlank() || !partnerIds.add(p.get("id")) || p.get("name").isBlank() || !partnerNames.add(p.get("name").toLowerCase(Locale.ROOT)) || !Set.of("supplier","buyer","both").contains(p.get("partner_type"))) throw new IOException("Μη έγκυρος ή διπλός συνεργάτης.");
            partners.add(new PartnerStore.Partner(p.get("id"),p.get("name"),p.get("partner_type"),p.get("tax_id"),p.get("contact_person"),p.get("phone"),p.get("email"),p.get("address"),p.get("products"),p.get("payment_terms"),p.get("notes")));
        }
        return new Package(List.copyOf(fields),producer,List.copyOf(products),List.copyOf(links),List.copyOf(partners),InventoryImport.read(files,tables,fields,partners),MoneyImport.read(files,tables,fields,partners),ProductionImport.read(files,tables,products,fields,partners),ActivityImport.read(files,tables),WorkImport.read(files,tables),DocumentImport.read(files,tables),List.copyOf(ignored));
    }
    static List<Map<String,String>> rows(String table,Map<String,byte[]> files,Map<String,JSONObject> metadata,List<String> required) throws Exception {
        String path="tables/"+table+".csv";
        if(!metadata.containsKey(table)) { if(files.containsKey(path)) throw new IOException("Λείπει περιγραφή πίνακα."); return List.of(); }
        var meta=metadata.get(table);
        if(!meta.getString("status").equals("exported")) { if(files.containsKey(path)) throw new IOException("Μη έγκυρη κατάσταση πίνακα."); return List.of(); }
        if(!path.equals(meta.getString("file")) || !files.containsKey(path)) throw new IOException("Λείπει αρχείο: "+table);
        String text=StandardCharsets.UTF_8.newDecoder().decode(java.nio.ByteBuffer.wrap(files.get(path))).toString();
        if(text.startsWith("\uFEFF")) text=text.substring(1);
        var csv=WindowsImport.parseCsv(text); if(csv.isEmpty()) throw new IOException("Λείπουν στήλες."); var header=csv.remove(0);
        if(new HashSet<>(header).size()!=header.size()) throw new IOException("Διπλή στήλη CSV.");
        for(String name:required) if(Collections.frequency(header,name)!=1) throw new IOException("Λείπει στήλη: "+name);
        if(csv.size()!=meta.getInt("rows") || csv.size()>5000) throw new IOException("Μη έγκυρο πλήθος.");
        var result=new ArrayList<Map<String,String>>();
        for(var row:csv) {
            if(row.size()!=header.size()) throw new IOException("Μη έγκυρη γραμμή CSV.");
            var mapped=new HashMap<String,String>(); for(String name:header) mapped.put(name,row.get(header.indexOf(name)).trim()); result.add(mapped);
        } return result;
    }
    private static FarmStore.Field match(FarmStore.Field source,List<FarmStore.Field> fields) {
        var candidates=fields.stream().filter(f->(!source.kaek().isEmpty()&&source.kaek().equalsIgnoreCase(f.kaek())) || (source.name().equalsIgnoreCase(f.name())&&source.location().equalsIgnoreCase(f.location()))).toList();
        if(candidates.size()!=1) return null; var f=candidates.get(0);
        return source.name().equals(f.name())&&source.area()==f.area()&&source.kaek().equals(f.kaek())&&source.location().equals(f.location())&&source.trees()==f.trees()&&source.notes().equals(f.notes())?f:null;
    }
    private static Summary process(FarmStore store,Package data,boolean apply) {
        var catalog=new CatalogStore(store); var fieldPlan=WindowsImport.preview(store,data.fields());
        var knownFields=new ArrayList<>(store.fields());
        for(var f:fieldPlan.additions()) {
            if(apply) store.saveField(null,f.name(),f.area(),f.kaek(),f.location(),f.trees(),f.notes());
            else knownFields.add(new FarmStore.Field("new-field-"+f.id(),f.name(),f.area(),f.kaek(),f.location(),f.trees(),f.notes()));
        }
        if(apply) knownFields=new ArrayList<>(store.fields());
        var fieldMap=new HashMap<String,String>(); for(var f:data.fields()) { var found=match(f,knownFields); if(found!=null) fieldMap.put(f.id(),found.id()); }
        int producerCount=0,productCount=0,linkCount=0,skipped=fieldPlan.identical()+fieldPlan.conflicts();
        if(data.producer()!=null && !data.producer().empty()) {
            if(catalog.producer().empty()) { producerCount=1; if(apply) catalog.saveProducer(data.producer()); }
            else skipped++;
        }
        var productMap=new HashMap<String,String>(); var knownProducts=catalog.products();
        for(var p:data.products()) {
            var matches=knownProducts.stream().filter(x->x.name().equalsIgnoreCase(p.name())).toList();
            if(matches.isEmpty()) { productCount++; productMap.put(p.id(),apply?catalog.saveProduct(null,p.name(),p.unit(),p.active()):"new-product-"+p.id()); }
            else { skipped++; if(matches.size()==1 && matches.get(0).name().equals(p.name()) && matches.get(0).unit().equals(p.unit()) && matches.get(0).active()==p.active()) productMap.put(p.id(),matches.get(0).id()); }
        }
        var knownLinks=catalog.links();
        for(var link:data.links()) {
            String p=productMap.get(link.productId()),f=fieldMap.get(link.fieldId());
            if(p==null || f==null || knownLinks.stream().anyMatch(x->x.productId().equals(p)&&x.fieldId().equals(f))) { skipped++; continue; }
            linkCount++; if(apply) catalog.saveLink(p,f,link.variety(),link.plantingDate(),link.status());
        }
        var registry=new PartnerStore(store); var knownPartners=new ArrayList<>(registry.partners()); int partnerCount=0;
        for(var p:data.partners()) {
            if(knownPartners.stream().anyMatch(x->x.name().equalsIgnoreCase(p.name()) || (!p.taxId().isBlank() && x.taxId().equalsIgnoreCase(p.taxId())))) { skipped++; continue; }
            partnerCount++;
            if(apply) registry.save(new PartnerStore.Partner(null,p.name(),p.type(),p.taxId(),p.contact(),p.phone(),p.email(),p.address(),p.products(),p.paymentTerms(),p.notes()));
            knownPartners.add(p);
        }
        var stock=InventoryImport.process(store,data.inventory(),fieldMap,data.partners(),apply);
        var money=MoneyImport.process(store,data,fieldMap,apply);
        var production=ProductionImport.process(store,data,productMap,fieldMap,apply);
        var activities=ActivityImport.process(store,data,fieldMap,apply);
        var work=WorkImport.process(store,data,fieldMap,apply);
        var equipment=EquipmentImport.process(store,data,apply);
        var documents=DocumentImport.process(store,data,apply);
        return new Summary(fieldPlan.additions().size(),producerCount,productCount,linkCount,partnerCount,stock.items(),stock.movements(),money.income(),money.expenses(),production.harvests(),production.sales(),activities.added(),work.protections(),work.workers(),work.labor(),work.plantings(),equipment.equipment(),equipment.services(),documents[0],documents[1],documents[2]+equipment.skipped()+work.skipped()+skipped+stock.skipped()+money.skipped()+production.skipped()+activities.skipped(),data.ignored());
    }
    public static Summary preview(FarmStore store,Package data) { return process(store,data,false); }
    public static Summary apply(FarmStore store,Package data,File recovery) throws Exception {
        var db=store.getWritableDatabase(); db.beginTransaction();
        try {
            var plan=preview(store,data);
            if(plan.fields()+plan.producer()+plan.products()+plan.links()+plan.partners()+plan.inventoryItems()+plan.inventoryMovements()+plan.income()+plan.expenses()+plan.harvests()+plan.sales()+plan.activities()+plan.protections()+plan.workers()+plan.labor()+plan.plantings()+plan.equipment()+plan.services()+plan.documents()+plan.yearLocks()>0) {
                var safe=new AtomicFile(recovery); FileOutputStream out=null;
                try { out=safe.startWrite();out.write(LocalBackup.snapshot(store));safe.finishWrite(out); }
                catch(Exception error) { if(out!=null) safe.failWrite(out);throw error; }
            }
            var result=process(store,data,true); db.setTransactionSuccessful();return result;
        } finally { db.endTransaction(); }
    }
}
