package gr.mastixa.manager;

import org.json.*;
import java.util.*;
import java.io.*;
import android.util.Base64;

public final class DocumentImport {
    public record Data(List<DocumentStore.Document> documents,List<Map<String,String>> locks){static Data empty(){return new Data(List.of(),List.of());}}
    static Data read(Map<String,byte[]> files,Map<String,JSONObject> tables)throws Exception{
        var documents=new ArrayList<DocumentStore.Document>();var ids=new HashSet<String>();
        for(var row:CatalogImport.rows("invoice_documents",files,tables,List.of("id","original_filename","stored_filename","invoice_date","supplier","amount_text"))){
            if(row.get("id").isBlank()||!ids.add(row.get("id")))throw new IOException("Διπλό τιμολόγιο");var metadata=new JSONObject(row);metadata.put("windows_partner_id",metadata.optString("partner_id")).put("partner_id","");
            String filename=row.get("stored_filename");if(filename.contains("/")||filename.contains("\\"))throw new IOException("Invalid attachment path");byte[] bytes=files.get("invoice_files/"+filename);
            var d=new DocumentStore.Document(UUID.randomUUID().toString(),row.get("invoice_date"),metadata,bytes==null?"":Base64.encodeToString(bytes,Base64.NO_WRAP),bytes==null?"":DocumentStore.hash(bytes),"",row.get("id"));DocumentStore.validate(d);documents.add(d);
        }
        var locks=CatalogImport.rows("year_locks",files,tables,List.of("year","is_locked","reason"));ids.clear();for(var l:locks)if(!l.get("year").matches("[1-9][0-9]{3}")||!Set.of("0","1").contains(l.get("is_locked"))||!ids.add(l.get("year")))throw new IOException("Invalid year lock");return new Data(List.copyOf(documents),locks);
    }
    static int[] process(FarmStore store,CatalogImport.Package data,boolean apply){var docs=new DocumentStore(store);var db=store.getWritableDatabase();int added=0,skipped=0,locks=0;
        for(var source:data.documents().documents()){
            try(var c=db.rawQuery("SELECT id,attachment FROM invoice_documents WHERE windows_id=?",new String[]{source.windowsId()})){if(c.moveToFirst()){if(c.getString(1).isEmpty()&&!source.attachment().isEmpty()){added++;if(apply)docs.attach(c.getString(0),Base64.decode(source.attachment(),Base64.DEFAULT));}else skipped++;continue;}}
            String financial="";var m=source.metadata();String wid=m.optString("financial_entry_id"),kind=m.optString("financial_entry_type");
            if(!wid.isEmpty()){
                if(!Set.of("income","expense").contains(kind))throw new IllegalArgumentException("Μη έγκυρη οικονομική σύνδεση τιμολογίου");
                var matches=new MoneyStore(store).entries(kind).stream().filter(e->e.windowsId().equals(wid)).toList();
                if(matches.size()==1)financial=matches.get(0).id();else if(!apply&&data.money().stream().anyMatch(e->e.kind().equals(kind)&&e.windowsId().equals(wid)))financial="preview";else throw new IllegalArgumentException("Εξήγαγε τιμολόγια μαζί με τα συνδεδεμένα έσοδα/έξοδα / Export linked finances together");
            }
            if(apply){try{m=new JSONObject(m.toString());String partner=m.optString("windows_partner_id");if(!partner.isEmpty()){var sourcePartner=data.partners().stream().filter(p->p.id().equals(partner)).findFirst().orElseThrow(()->new IllegalArgumentException("Λείπει συνεργάτης τιμολογίου"));var matches=new PartnerStore(store).partners().stream().filter(p->p.name().equals(sourcePartner.name())).toList();if(matches.size()!=1)throw new IllegalArgumentException("Αμφίσημος συνεργάτης τιμολογίου");m.put("partner_id",matches.get(0).id());}}catch(JSONException e){throw new IllegalArgumentException(e);}
                docs.put(new DocumentStore.Document(source.id(),source.date(),m,source.attachment(),source.sha(),financial,source.windowsId()));}
            added++;
        }
        for(var l:data.documents().locks()){
            try(var c=db.rawQuery("SELECT 1 FROM year_locks WHERE id=?",new String[]{l.get("year")})){if(c.moveToFirst()){skipped++;continue;}}
            locks++;if(apply){YearLocks.set(db,l.get("year"),l.get("is_locked").equals("1"),l.get("reason"));var times=new android.content.ContentValues();times.put("locked_at",l.getOrDefault("locked_at",""));times.put("unlocked_at",l.getOrDefault("unlocked_at",""));db.update("year_locks",times,"id=?",new String[]{l.get("year")});}
        }
        return new int[]{added,locks,skipped};
    }
}
