package gr.mastixa.manager;
import java.io.*;
import java.util.*;
import java.util.zip.*;
import org.json.*;
import android.util.Base64;
/** Interoperable invoice archive; financial source metadata is retained for review. */
public final class DocumentPackage {
    public record Attachment(String documentId,byte[] bytes){}
    /** Legacy Windows invoice archives omit financial links: attach only to reviewed portable metadata. */
    public static List<Attachment> preview(FarmStore store,InputStream input)throws Exception{
        byte[] archive=LocalBackup.read(input);if(archive.length>10*1024*1024)throw new IOException("ZIP: όριο 10 MB / 10 MB limit");var files=new HashMap<String,byte[]>();int total=0;
        try(var zip=new ZipInputStream(new ByteArrayInputStream(archive))){ZipEntry entry;byte[] buffer=new byte[8192];while((entry=zip.getNextEntry())!=null){if(files.size()>=1000)throw new IOException("Too many files");var out=new ByteArrayOutputStream();int n;while((n=zip.read(buffer))!=-1){total+=n;if(total>10*1024*1024)throw new IOException("Expanded ZIP exceeds 10 MB");out.write(buffer,0,n);}if(files.put(entry.getName(),out.toByteArray())!=null)throw new IOException("Duplicate ZIP entry");}}
        if(!files.containsKey("manifest.json"))throw new IOException("Missing manifest");var manifest=new JSONObject(new String(files.get("manifest.json"),java.nio.charset.StandardCharsets.UTF_8));if(!manifest.getString("schema").equals("mastixa-invoice-package-v1"))throw new IOException("Invalid invoice package");var rows=manifest.getJSONArray("invoices");if(rows.length()!=manifest.getInt("count"))throw new IOException("Invalid count");var result=new ArrayList<Attachment>();var seen=new HashSet<String>();var docs=new DocumentStore(store).list();
        for(int n=0;n<rows.length();n++){var row=rows.getJSONObject(n);String id=row.getString("id"),name=row.getString("filename");if(name.contains("/")||name.contains("\\")||!seen.add(id))throw new IOException("Invalid invoice reference");DocumentStore.mime(name);var matches=docs.stream().filter(d->d.windowsId().equals(id)||d.id().equals(id)).toList();if(matches.size()!=1)throw new IOException("Εισήγαγε πρώτα το γενικό ZIP δεδομένων με τα τιμολόγια / Import the general data ZIP with invoice metadata first");var d=matches.get(0);if(!d.date().equals(row.optString("invoice_date"))||!d.metadata().optString("invoice_number").equals(row.optString("invoice_number"))||!d.metadata().optString("supplier").equals(row.optString("supplier")))throw new IOException("Τα στοιχεία τιμολογίου δεν ταιριάζουν / Invoice metadata does not match");
            byte[] bytes=files.get("invoices/"+name);if(bytes==null){if(row.optBoolean("attachment_missing"))continue;throw new IOException("Missing attachment");}if(bytes.length==0||bytes.length>5*1024*1024)throw new IOException("Attachment exceeds 5 MB or is empty");String hash=DocumentStore.hash(bytes);if(!row.optString("sha256").isEmpty()&&!hash.equals(row.optString("sha256")))throw new IOException("Attachment checksum mismatch");if(!d.attachment().isEmpty()){if(!d.sha().equals(hash))throw new IOException("Διαφορετικό υπάρχον συνημμένο / Existing attachment differs");continue;}if(!DocumentStore.mime(name).equals(DocumentStore.mime(d.metadata().getString("original_filename"))))throw new IOException("Attachment type mismatch");result.add(new Attachment(d.id(),bytes));
        }return List.copyOf(result);
    }
    public static void apply(FarmStore store,List<Attachment> attachments,File recovery)throws Exception{
        var db=store.getWritableDatabase();db.beginTransaction();try{if(!attachments.isEmpty()){var safe=new android.util.AtomicFile(recovery);FileOutputStream out=null;try{out=safe.startWrite();out.write(LocalBackup.snapshot(store));safe.finishWrite(out);}catch(Exception e){if(out!=null)safe.failWrite(out);throw e;}}var docs=new DocumentStore(store);for(var a:attachments)docs.attach(a.documentId(),a.bytes());db.setTransactionSuccessful();}finally{db.endTransaction();}
    }
    public static byte[] export(List<DocumentStore.Document> documents)throws Exception{
        if(documents.isEmpty())throw new IOException("Δεν υπάρχουν έγγραφα / No documents");var manifest=new JSONArray();var out=new ByteArrayOutputStream();
        try(var zip=new ZipOutputStream(out)){for(var d:documents){var m=new JSONObject(d.metadata().toString());String filename=d.id()+"-"+m.getString("original_filename");m.put("id",d.windowsId().isEmpty()?d.id():d.windowsId()).put("invoice_date",d.date()).put("amount",m.optString("amount_text")).put("filename",filename).put("android_financial_id",d.financialId()).put("attachment_missing",d.attachment().isEmpty()).put("sha256",d.sha());manifest.put(m);if(!d.attachment().isEmpty()){zip.putNextEntry(new ZipEntry("invoices/"+filename));zip.write(Base64.decode(d.attachment(),Base64.DEFAULT));zip.closeEntry();}}
            zip.putNextEntry(new ZipEntry("manifest.json"));zip.write(new JSONObject().put("schema","mastixa-invoice-package-v1").put("generated_at",java.time.Instant.now().toString()).put("count",manifest.length()).put("invoices",manifest).toString(2).getBytes(java.nio.charset.StandardCharsets.UTF_8));zip.closeEntry();
        }return out.toByteArray();
    }
}
