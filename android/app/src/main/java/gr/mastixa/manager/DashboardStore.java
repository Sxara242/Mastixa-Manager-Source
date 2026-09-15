package gr.mastixa.manager;

import java.util.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.temporal.ChronoUnit;

/** Read-only, profile-scoped summaries. Notifications are derived, never duplicated in a queue. */
public final class DashboardStore {
    public record Product(String id,String name,String unit,double produced,double available){}
    public record Alert(String id,String kind,String recordId,int severity,String date,String subject,String message){}
    public record Snapshot(int fields,double area,long trees,BigDecimal income,BigDecimal expenses,List<Product> products,List<Alert> alerts){}
    private final FarmStore store;private final boolean english;
    public DashboardStore(FarmStore store,boolean english){this.store=store;this.english=english;}
    private String w(String el,String en){return english?en:el;}
    public Snapshot snapshot(String year,LocalDate today){
        if(!year.isEmpty()&&!year.matches("[1-9][0-9]{3}"))throw new IllegalArgumentException("Invalid year");
        var db=store.getWritableDatabase();db.beginTransaction();try{
            var fields=store.fields();var money=new MoneyStore(store).entries(null).stream().filter(e->year.isEmpty()||e.date().startsWith(year+"-")).toList();
            var production=new ProductionStore(store);var harvests=production.harvests();var sales=production.sales();var products=new ArrayList<Product>();
            for(var p:new CatalogStore(store).products()){double produced=0,all=0,sold=0;for(var h:harvests)if(h.productId().equals(p.id())){all+=h.quantity();if(year.isEmpty()||h.date().startsWith(year+"-"))produced+=h.quantity();}for(var s:sales)if(s.productId().equals(p.id()))sold+=s.quantity();products.add(new Product(p.id(),p.name(),p.unit(),produced,all-sold));}
            var result=new Snapshot(fields.size(),fields.stream().mapToDouble(FarmStore.Field::area).sum(),fields.stream().mapToLong(FarmStore.Field::trees).sum(),MoneyStore.total(money.stream().filter(e->e.kind().equals("income")).toList()),MoneyStore.total(money.stream().filter(e->e.kind().equals("expense")).toList()),List.copyOf(products),alerts(today));db.setTransactionSuccessful();return result;
        }finally{db.endTransaction();}
    }
    public List<String> years(){var years=new TreeSet<String>(Comparator.reverseOrder());for(var e:new MoneyStore(store).entries(null))years.add(e.date().substring(0,4));for(var e:new ProductionStore(store).harvests())years.add(e.date().substring(0,4));return List.copyOf(years);}
    public List<Alert> alerts(LocalDate today){var db=store.getWritableDatabase();db.beginTransaction();try{var result=buildAlerts(today);db.setTransactionSuccessful();return result;}finally{db.endTransaction();}}
    private List<Alert> buildAlerts(LocalDate today){var result=new ArrayList<Alert>();var fields=new HashMap<String,String>();for(var f:store.fields())fields.put(f.id(),f.name());
        for(var a:new ActivityStore(store).activities()){
            if(!a.status().equals("Προγραμματισμένη"))continue;LocalDate date=LocalDate.parse(a.date());if(date.isAfter(today.plusDays(7)))continue;
            int severity=date.isBefore(today)?0:date.equals(today)?1:2;
            String category=a.category().equals("Πότισμα")?w("Πότισμα","Irrigation"):w("Λίπανση","Fertilization");String prefix=severity==0?w("Εκπρόθεσμη εργασία: ","Overdue activity: "):severity==1?w("Εργασία για σήμερα: ","Activity due today: "):w("Εργασία εντός 7 ημερών: ","Activity within 7 days: ");
            result.add(new Alert("activity:"+a.id(),"activity",a.id(),severity,a.date(),fields.getOrDefault(a.fieldId(),w("Αγροτεμάχιο ιστορικού","Historical field")),prefix+category+(a.description().isBlank()?"":" · "+a.description())));
        }
        for(var item:new ReportStore(store,english).stock()){
            if(item.quantity()>0&&!item.status().equals(w("Χαμηλό","Low")))continue;int severity=item.quantity()<=0?0:1;
            result.add(new Alert("inventory:"+item.id(),"inventory",item.id(),severity,"",item.name(),(severity==0?w("Εξαντλημένο απόθεμα: ","Stock depleted: "):w("Χαμηλό απόθεμα: ","Low stock: "))+ReportStore.n(item.quantity())+" "+item.unit()));
        }
        var work=new WorkStore(store);var next=new HashMap<String,WorkStore.Service>();for(var s:work.services())if(!s.next_service_date().isEmpty()||s.next_service_meter()!=null)next.putIfAbsent(s.equipment_id(),s);
        for(var e:work.equipment()){
            if(Set.of("Πωλήθηκε","Εκτός λειτουργίας").contains(e.status()))continue;var s=next.get(e.id());if(s==null)continue;LocalDate due=s.next_service_date().isEmpty()?null:LocalDate.parse(s.next_service_date());
            boolean overdue=(due!=null&&due.isBefore(today))||(s.next_service_meter()!=null&&e.current_meter()>=s.next_service_meter());boolean upcoming=(due!=null&&!due.isBefore(today)&&!due.isAfter(today.plusDays(30)))||(s.next_service_meter()!=null&&s.next_service_meter()>e.current_meter()&&s.next_service_meter()-e.current_meter()<=50);if(!overdue&&!upcoming)continue;
            String detail=s.next_service_date();if(s.next_service_meter()!=null)detail+=(detail.isEmpty()?"":" · ")+ReportStore.n(s.next_service_meter())+" "+(e.meter_type().equals("hours")?w("ώρες","hours"):e.meter_type().equals("km")?"km":"");
            result.add(new Alert("equipment:"+e.id(),"equipment",e.id(),overdue?0:1,s.next_service_date(),e.name(),(overdue?w("Εκπρόθεσμη συντήρηση: ","Overdue service: "):w("Πλησιάζει συντήρηση: ","Service approaching: "))+detail));
        }
        for(var p:work.protections()){
            if(p.harvest_interval_days()<=0)continue;LocalDate date=LocalDate.parse(p.application_date());LocalDate end=date.plusDays(p.harvest_interval_days());long days=ChronoUnit.DAYS.between(today,end);if(days<=0)continue;
            result.add(new Alert("harvest_wait:"+p.id(),"harvest_wait",p.id(),days>=3?0:1,p.application_date(),fields.getOrDefault(p.field_id(),w("Αγροτεμάχιο ιστορικού","Historical field")),p.product_name()+" · "+w("Καταγεγραμμένη αναμονή έως ","Recorded waiting period through ")+end+" · "+days+w(" ημέρες ακόμη"," days remaining")+(date.isAfter(today)?w(" · Μελλοντική ημερομηνία επέμβασης — έλεγξε την εγγραφή."," · Future application date — check the record."):"")));
        }
        result.sort(Comparator.comparingInt(Alert::severity).thenComparing(a->a.date().isEmpty()?"9999-12-31":a.date()).thenComparing(Alert::subject).thenComparing(Alert::id));return List.copyOf(result);
    }
    public static List<Alert> filter(List<Alert> alerts,String kind,int severity,String query){String q=query.trim().toLowerCase(Locale.ROOT);return alerts.stream().filter(a->(kind.isEmpty()||a.kind().equals(kind))&&(severity<0||a.severity()==severity)&&(a.subject()+" "+a.message()+" "+a.date()).toLowerCase(Locale.ROOT).contains(q)).toList();}
}
