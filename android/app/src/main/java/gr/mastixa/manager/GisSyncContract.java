package gr.mastixa.manager;

import org.json.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;

/** Version 1 GIS wire documents. Original geometry is authoritative on both clients. */
public final class GisSyncContract {
    private GisSyncContract(){}
    public static String canonical(Object value){
        try{
            if(value==null||value==JSONObject.NULL)return "null";
            if(value instanceof JSONObject object){
                List<String> keys=new ArrayList<>();object.keys().forEachRemaining(keys::add);Collections.sort(keys);
                List<String> parts=new ArrayList<>();for(String key:keys)parts.add(JSONObject.quote(key)+":"+canonical(object.get(key)));
                return "{"+String.join(",",parts)+"}";
            }
            if(value instanceof JSONArray array){List<String> parts=new ArrayList<>();for(int i=0;i<array.length();i++)parts.add(canonical(array.get(i)));return "["+String.join(",",parts)+"]";}
            if(value instanceof Number number)return JSONObject.numberToString(number);
            if(value instanceof Boolean)return value.toString();
            if(value instanceof String text)return JSONObject.quote(text);
            throw new IllegalArgumentException("Unsupported JSON value");
        }catch(JSONException error){throw new IllegalArgumentException("Invalid JSON",error);}
    }
    public static String fingerprint(JSONObject value){
        try{byte[] bytes=MessageDigest.getInstance("SHA-256").digest(canonical(value).getBytes(StandardCharsets.UTF_8));StringBuilder out=new StringBuilder();for(byte b:bytes)out.append(String.format(Locale.ROOT,"%02x",b&255));return out.toString();}
        catch(java.security.NoSuchAlgorithmException error){throw new IllegalStateException(error);}
    }
    public static void uuid(String value){if(!UUID.fromString(value).toString().equals(value))throw new IllegalArgumentException("Canonical UUID required");}
    static long integer(JSONObject value,String key)throws JSONException{
        Object raw=value.get(key);if(!(raw instanceof Integer||raw instanceof Long)||((Number)raw).longValue()<0)throw new IllegalArgumentException("Invalid integer: "+key);return ((Number)raw).longValue();
    }
    public static JSONObject validate(JSONObject input){
        try{
            if(canonical(input).getBytes(StandardCharsets.UTF_8).length>4*1024*1024)throw new IllegalArgumentException("Sync record exceeds 4 MB");
            JSONObject record=new JSONObject(input.toString());if(integer(record,"schema")!=1)throw new IllegalArgumentException("Unknown sync schema");
            uuid(record.getString("id"));uuid(record.getString("parcel_id"));integer(record,"created_at");integer(record,"updated_at");
            if(!record.has("deleted_at"))throw new IllegalArgumentException("Missing deletion metadata");if(!record.isNull("deleted_at"))integer(record,"deleted_at");
            String kind=record.getString("kind");JSONObject data=record.getJSONObject("data");
            if(kind.equals("parcel")){
                if(!record.getString("id").equals(record.getString("parcel_id")))throw new IllegalArgumentException("Parcel identity mismatch");
                for(String key:List.of("name","kaek","geometry_source","geometry_source_date","source_crs"))if(!(data.get(key) instanceof String))throw new IllegalArgumentException("Invalid parcel metadata");
                if(data.getString("name").isBlank())throw new IllegalArgumentException("Parcel name required");
                ParcelGeometry.normalize(data.getJSONObject("original_geometry").toString(),data.getString("source_crs"));
            }else GeoStore.validatePayload(kind,data);
            return record;
        }catch(JSONException error){throw new IllegalArgumentException("Invalid GIS sync record",error);}
    }
    public record Remote(JSONObject record,long version,long sequence){
        public Remote {record=validate(record);if(version<1||sequence<1)throw new IllegalArgumentException("Invalid remote version/sequence");}
        public JSONObject json(){try{return new JSONObject().put("record",record).put("version",version).put("sequence",sequence);}catch(JSONException error){throw new IllegalArgumentException(error);}}
        public static Remote from(JSONObject value){try{return new Remote(value.getJSONObject("record"),integer(value,"version"),integer(value,"sequence"));}catch(JSONException error){throw new IllegalArgumentException(error);}}
    }
    public record Batch(long cursor,List<Remote> rows){}
    public static final class Conflict extends Exception {public final Remote remote;public Conflict(Remote remote){super("Remote record changed");this.remote=remote;}}
    public interface Transport {Batch pull(long cursor)throws Exception;Remote push(JSONObject record,long expectedVersion)throws Exception;}
    public record Result(int pulled,int pushed,int conflicts){}
    /** Invoke on a worker. Transport is injected; this class never guesses a server/account. */
    public static Result run(GisSyncRepository repository,Transport transport)throws Exception{
        int pulled=0,pushed=0,conflicts=0;long oldCursor=repository.cursor();Batch batch=transport.pull(oldCursor);
        if(batch.cursor()<oldCursor)throw new IllegalArgumentException("Invalid remote cursor");
        List<Remote> rows=new ArrayList<>(batch.rows());for(Remote row:rows)if(row.sequence()>batch.cursor())throw new IllegalArgumentException("Remote sequence exceeds cursor");
        rows.sort(Comparator.comparing((Remote row)->!row.record().optString("kind").equals("parcel")).thenComparingLong(Remote::sequence));
        for(Remote remote:rows){
            JSONObject incoming=remote.record();String id=incoming.getString("id");var state=repository.state(id);
            if(state!=null&&remote.version()<=state.version())continue;
            JSONObject current=repository.document(id);String digest=current==null?null:fingerprint(current);
            if(canonical(current).equals(canonical(incoming))){repository.acknowledge(id,digest,remote.version());continue;}
            boolean dirty=current!=null&&(state==null||!digest.equals(state.hash()));
            boolean dependents=incoming.getString("kind").equals("parcel")&&!incoming.isNull("deleted_at")&&repository.dirtyDependents(id);
            if(dirty||dependents||repository.blocked(id)){repository.conflict(current,remote,"Concurrent edit or deletion");conflicts++;}
            else try{repository.apply(remote,digest);pulled++;}catch(IllegalArgumentException error){repository.conflict(repository.document(id),remote,error.getMessage());conflicts++;}
        }
        repository.setCursor(batch.cursor());
        List<JSONObject> local=repository.documents();local.sort(Comparator.comparing((JSONObject r)->!r.optString("kind").equals("parcel")).thenComparingLong(r->r.optLong("created_at")).thenComparing(r->r.optString("id")));
        Set<String> parents=new HashSet<>();for(JSONObject row:local)if(row.optString("kind").equals("parcel"))parents.add(row.optString("id"));
        for(JSONObject current:local){
            String id=current.getString("id"),digest=fingerprint(current);var state=repository.state(id);
            if(state!=null&&digest.equals(state.hash()))continue;if(repository.blocked(id)||repository.blocked(current.getString("parcel_id")))continue;
            // Unmapped fields can hold GPS records locally; keep them pending until the parcel is transferable.
            if(!current.getString("kind").equals("parcel")&&!parents.contains(current.getString("parcel_id")))continue;
            try{Remote remote=transport.push(validate(current),state==null?0:state.version());
                if(!canonical(remote.record()).equals(canonical(current)))throw new IllegalArgumentException("Upload acknowledged different content");
                repository.acknowledge(id,digest,remote.version());pushed++;
            }catch(Conflict error){repository.conflict(current,error.remote,"Remote compare-and-swap conflict");conflicts++;}
        }
        return new Result(pulled,pushed,conflicts);
    }
}
