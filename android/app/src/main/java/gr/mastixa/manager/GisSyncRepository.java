package gr.mastixa.manager;

import android.content.ContentValues;
import android.database.sqlite.SQLiteDatabase;
import org.json.*;
import java.util.*;

/** Persistent per-profile, per-dataset sync state. Incoming data and acknowledgement are atomic. */
public final class GisSyncRepository {
    static final String[] TABLES={"gis_sync_state","gis_sync_cursor","gis_sync_conflicts"};
    static final String[][] COLUMNS={
        {"id","dataset","entity_id","local_hash","remote_version","revision"},
        {"id","position","revision"},
        {"id","dataset","entity_id","local_json","remote_json","reason","created_at","resolution","resolved_at","revision"}
    };
    static void create(SQLiteDatabase db){
        db.execSQL("CREATE TABLE gis_sync_state(id TEXT PRIMARY KEY,dataset TEXT NOT NULL,entity_id TEXT NOT NULL,local_hash TEXT NOT NULL,remote_version INTEGER NOT NULL CHECK(remote_version>0),revision INTEGER NOT NULL DEFAULT 1)");
        db.execSQL("CREATE UNIQUE INDEX gis_sync_identity ON gis_sync_state(dataset,entity_id)");
        db.execSQL("CREATE TABLE gis_sync_cursor(id TEXT PRIMARY KEY,position INTEGER NOT NULL CHECK(position>=0),revision INTEGER NOT NULL DEFAULT 1)");
        db.execSQL("CREATE TABLE gis_sync_conflicts(id TEXT PRIMARY KEY,dataset TEXT NOT NULL,entity_id TEXT NOT NULL,local_json TEXT NOT NULL,remote_json TEXT NOT NULL,reason TEXT NOT NULL,created_at INTEGER NOT NULL,resolution TEXT NOT NULL DEFAULT '',resolved_at INTEGER NOT NULL DEFAULT 0,revision INTEGER NOT NULL DEFAULT 1)");
        db.execSQL("CREATE INDEX gis_sync_open_conflicts ON gis_sync_conflicts(dataset,entity_id,resolution)");
    }
    static void validateBackup(int table,JSONObject row)throws JSONException{
        if(table==1){GisSyncContract.uuid(row.getString("id"));return;}
        GisSyncContract.uuid(row.getString("dataset"));GisSyncContract.uuid(row.getString("entity_id"));
        if(table==0){
            if(!row.getString("id").equals(row.getString("dataset")+":"+row.getString("entity_id"))||!row.getString("local_hash").matches("[0-9a-f]{64}")||row.getLong("remote_version")<1)throw new IllegalArgumentException("Invalid sync state");
        }else{
            GisSyncContract.uuid(row.getString("id"));JSONObject remote=new JSONObject(row.getString("remote_json"));GisSyncContract.Remote.from(remote);
            if(!remote.getJSONObject("record").getString("id").equals(row.getString("entity_id")))throw new IllegalArgumentException("Conflict identity mismatch");
            if(!row.getString("local_json").equals("null")){
                JSONObject local=GisSyncContract.validate(new JSONObject(row.getString("local_json")));
                if(!local.getString("id").equals(row.getString("entity_id")))throw new IllegalArgumentException("Conflict local identity mismatch");
            }
            if(!List.of("","local","remote").contains(row.getString("resolution")))throw new IllegalArgumentException("Invalid conflict resolution");
        }
    }
    public record State(String hash,long version){}
    public record PendingConflict(String id,JSONObject local,GisSyncContract.Remote remote,String reason){}
    private final FarmStore farm;
    private final String dataset;
    public GisSyncRepository(FarmStore farm,String dataset){GisSyncContract.uuid(dataset);this.farm=farm;this.dataset=dataset;}
    private static String hash(JSONObject value){return value==null?null:GisSyncContract.fingerprint(value);}
    private static boolean same(JSONObject a,JSONObject b){return GisSyncContract.canonical(a).equals(GisSyncContract.canonical(b));}

    private List<JSONObject> documents(SQLiteDatabase db){
        List<JSONObject> out=new ArrayList<>();
        try(var c=db.rawQuery("SELECT g.id,g.field_id,g.kind,g.payload,g.created_at,g.updated_at,g.deleted_at,f.name,f.kaek,p.deleted_at FROM gis_records g JOIN fields f ON f.id=g.field_id LEFT JOIN gis_records p ON p.field_id=g.field_id AND p.kind='parcel'",null)){
            while(c.moveToNext()){
                JSONObject payload=new JSONObject(c.getString(3));String kind=c.getString(2);JSONObject data=payload;
                if(kind.equals("parcel"))data=new JSONObject().put("name",c.getString(7)).put("kaek",c.getString(8))
                    .put("original_geometry",new JSONObject(payload.getString("original_geojson"))).put("source_crs",payload.getString("source_crs"))
                    .put("geometry_source",payload.getString("geometry_source")).put("geometry_source_date",payload.getString("geometry_source_date"));
                Long deleted=null;
                if(!c.isNull(6))deleted=c.getLong(6);else if(!c.isNull(9))deleted=c.getLong(9);
                out.add(new JSONObject().put("schema",1).put("id",c.getString(0)).put("parcel_id",c.getString(1)).put("kind",kind)
                    .put("created_at",c.getLong(4)).put("updated_at",Math.max(c.getLong(5),deleted==null?0:deleted))
                    .put("deleted_at",deleted==null?JSONObject.NULL:deleted).put("data",data));
            }
        }catch(JSONException error){throw new IllegalArgumentException("Invalid stored GIS document",error);}return out;
    }
    public List<JSONObject> documents(){SQLiteDatabase db=farm.getReadableDatabase();db.beginTransaction();try{List<JSONObject> out=documents(db);db.setTransactionSuccessful();return out;}finally{db.endTransaction();}}
    private JSONObject document(SQLiteDatabase db,String id){for(JSONObject row:documents(db))if(row.optString("id").equals(id))return row;return null;}
    public JSONObject document(String id){SQLiteDatabase db=farm.getReadableDatabase();db.beginTransaction();try{JSONObject out=document(db,id);db.setTransactionSuccessful();return out;}finally{db.endTransaction();}}
    public long cursor(){try(var c=farm.getReadableDatabase().rawQuery("SELECT position FROM gis_sync_cursor WHERE id=?",new String[]{dataset})){return c.moveToFirst()?c.getLong(0):0;}}
    public void setCursor(long value){if(value<0)throw new IllegalArgumentException("Invalid cursor");SQLiteDatabase db=farm.getWritableDatabase();db.beginTransaction();try{ContentValues row=new ContentValues();row.put("id",dataset);row.put("position",Math.max(value,cursor()));upsert(db,"gis_sync_cursor",row);db.setTransactionSuccessful();}finally{db.endTransaction();}}
    public State state(String id){return state(farm.getReadableDatabase(),id);}
    private State state(SQLiteDatabase db,String id){try(var c=db.rawQuery("SELECT local_hash,remote_version FROM gis_sync_state WHERE dataset=? AND entity_id=?",new String[]{dataset,id})){return c.moveToFirst()?new State(c.getString(0),c.getLong(1)):null;}}
    private static void upsert(SQLiteDatabase db,String table,ContentValues row){if(db.update(table,row,"id=?",new String[]{row.getAsString("id")})==0)db.insertOrThrow(table,null,row);}
    private void acknowledge(SQLiteDatabase db,String id,String digest,long version){
        if(version<1||digest==null)throw new IllegalArgumentException("Invalid acknowledgement");State previous=state(db,id);if(previous!=null&&previous.version()>version)return;
        ContentValues row=new ContentValues();row.put("id",dataset+":"+id);row.put("dataset",dataset);row.put("entity_id",id);row.put("local_hash",digest);row.put("remote_version",version);upsert(db,"gis_sync_state",row);
        ContentValues timestamp=new ContentValues();timestamp.put("last_sync_at",System.currentTimeMillis());db.update("gis_records",timestamp,"id=?",new String[]{id});
        if(digest.equals(hash(document(db,id))))db.delete("pending_changes","entity='gis_records' AND entity_id=?",new String[]{id});
    }
    public void acknowledge(String id,String digest,long version){SQLiteDatabase db=farm.getWritableDatabase();db.beginTransaction();try{acknowledge(db,id,digest,version);db.setTransactionSuccessful();}finally{db.endTransaction();}}
    public boolean blocked(String id){try(var c=farm.getReadableDatabase().rawQuery("SELECT 1 FROM gis_sync_conflicts WHERE dataset=? AND entity_id=? AND resolution=''",new String[]{dataset,id})){return c.moveToFirst();}}
    private boolean dirtyDependents(SQLiteDatabase db,String id){for(JSONObject row:documents(db))if(row.optString("parcel_id").equals(id)&&!row.optString("id").equals(id)){State state=state(db,row.optString("id"));if(state==null||!state.hash().equals(hash(row)))return true;}return false;}
    public boolean dirtyDependents(String id){SQLiteDatabase db=farm.getReadableDatabase();db.beginTransaction();try{boolean out=dirtyDependents(db,id);db.setTransactionSuccessful();return out;}finally{db.endTransaction();}}
    public void conflict(JSONObject local,GisSyncContract.Remote remote,String reason){
        SQLiteDatabase db=farm.getWritableDatabase();db.beginTransaction();try{
            String id=remote.record().optString("id"),localJson=GisSyncContract.canonical(local),remoteJson=GisSyncContract.canonical(remote.json());
            try(var c=db.rawQuery("SELECT 1 FROM gis_sync_conflicts WHERE dataset=? AND entity_id=? AND local_json=? AND remote_json=? AND resolution=''",new String[]{dataset,id,localJson,remoteJson})){
                if(!c.moveToFirst()){ContentValues row=new ContentValues();row.put("id",UUID.randomUUID().toString());row.put("dataset",dataset);row.put("entity_id",id);row.put("local_json",localJson);row.put("remote_json",remoteJson);row.put("reason",reason);row.put("created_at",System.currentTimeMillis());db.insertOrThrow("gis_sync_conflicts",null,row);}
            }db.setTransactionSuccessful();
        }finally{db.endTransaction();}
    }
    public List<PendingConflict> conflicts(){
        List<PendingConflict> out=new ArrayList<>();try(var c=farm.getReadableDatabase().rawQuery("SELECT id,local_json,remote_json,reason FROM gis_sync_conflicts WHERE dataset=? AND resolution='' ORDER BY created_at,id",new String[]{dataset})){
            while(c.moveToNext())out.add(new PendingConflict(c.getString(0),c.getString(1).equals("null")?null:new JSONObject(c.getString(1)),GisSyncContract.Remote.from(new JSONObject(c.getString(2))),c.getString(3)));
        }catch(JSONException error){throw new IllegalArgumentException("Invalid conflict journal",error);}return out;
    }
    private void apply(SQLiteDatabase db,GisSyncContract.Remote remote,String expectedHash,boolean explicit){
        try{
            JSONObject record=GisSyncContract.validate(remote.record()),data=record.getJSONObject("data");String id=record.getString("id"),parent=record.getString("parcel_id"),kind=record.getString("kind");
            JSONObject current=document(db,id);if(!Objects.equals(hash(current),expectedHash))throw new IllegalArgumentException("Local record changed since sync/conflict preview");
            if(current!=null&&(!current.getString("kind").equals(kind)||!current.getString("parcel_id").equals(parent)))throw new IllegalArgumentException("GIS identity cannot change kind or parent");
            JSONObject payload=data;
            if(kind.equals("parcel")){
                if(!record.isNull("deleted_at")&&!explicit&&dirtyDependents(db,id))throw new IllegalArgumentException("Dependent changed during parent deletion");
                ParcelGeometry geometry=ParcelGeometry.normalize(data.getJSONObject("original_geometry").toString(),data.getString("source_crs"));
                boolean exists;try(var c=db.rawQuery("SELECT deleted_at FROM fields WHERE id=?",new String[]{id})){exists=c.moveToFirst();if(exists&&!c.isNull(0)&&record.isNull("deleted_at"))throw new IllegalArgumentException("Local business field is deleted; restore it explicitly first");}
                ContentValues field=new ContentValues();field.put("id",id);field.put("name",data.getString("name"));field.put("kaek",data.getString("kaek"));
                if(!exists){field.put("area",geometry.area/1000);field.put("revision",1);field.put("updated_at",record.getLong("updated_at"));db.insertOrThrow("fields",null,field);}else db.update("fields",field,"id=?",new String[]{id});
                payload=new JSONObject().put("original_geojson",geometry.original).put("source_crs",geometry.sourceCrs).put("wgs84_geojson",geometry.wgs84)
                    .put("area_m2",geometry.area).put("perimeter_m",geometry.perimeter).put("centroid_lon",geometry.centroidLon).put("centroid_lat",geometry.centroidLat)
                    .put("bbox",new JSONArray(geometry.bbox)).put("geometry_source",data.getString("geometry_source")).put("geometry_source_date",data.getString("geometry_source_date"));
            }else try(var c=db.rawQuery("SELECT deleted_at FROM gis_records WHERE id=? AND kind='parcel'",new String[]{parent})){
                if(!c.moveToFirst()||(!c.isNull(0)&&record.isNull("deleted_at")))throw new IllegalArgumentException("Missing or deleted parent parcel");
            }
            long revision=1;try(var c=db.rawQuery("SELECT revision FROM gis_records WHERE id=?",new String[]{id})){if(c.moveToFirst())revision=c.getLong(0)+1;}
            ContentValues row=new ContentValues();row.put("id",id);row.put("field_id",parent);row.put("kind",kind);row.put("payload",payload.toString());row.put("created_at",record.getLong("created_at"));row.put("updated_at",record.getLong("updated_at"));row.put("revision",revision);
            if(record.isNull("deleted_at"))row.putNull("deleted_at");else row.put("deleted_at",record.getLong("deleted_at"));upsert(db,"gis_records",row);
            if(kind.equals("parcel")&&!record.isNull("deleted_at"))db.execSQL("UPDATE gis_records SET deleted_at=?,updated_at=max(updated_at,?),revision=revision+1 WHERE field_id=? AND kind<>'parcel' AND deleted_at IS NULL",new Object[]{record.getLong("deleted_at"),record.getLong("deleted_at"),id});
            acknowledge(db,id,hash(document(db,id)),remote.version());
        }catch(JSONException error){throw new IllegalArgumentException("Invalid remote GIS record",error);}
    }
    public void apply(GisSyncContract.Remote remote,String expectedHash){SQLiteDatabase db=farm.getWritableDatabase();db.beginTransaction();try{apply(db,remote,expectedHash,false);db.setTransactionSuccessful();}finally{db.endTransaction();}}
    public void resolve(String conflictId,String choice){
        if(!List.of("local","remote").contains(choice))throw new IllegalArgumentException("Explicit local or remote resolution required");
        SQLiteDatabase db=farm.getWritableDatabase();db.beginTransaction();try{
            PendingConflict selected=null;for(var candidate:conflicts())if(candidate.id().equals(conflictId))selected=candidate;
            if(selected==null)throw new IllegalArgumentException("Conflict missing or already resolved");String id=selected.remote().record().optString("id");JSONObject current=document(db,id);
            if(!same(current,selected.local()))throw new IllegalArgumentException("Local record changed since conflict preview");
            if(choice.equals("remote"))apply(db,selected.remote(),hash(current),true);
            else{if(current==null)throw new IllegalArgumentException("No local version to retain");acknowledge(db,id,hash(selected.remote().record()),selected.remote().version());}
            ContentValues row=new ContentValues();row.put("resolution",choice);row.put("resolved_at",System.currentTimeMillis());db.update("gis_sync_conflicts",row,"id=?",new String[]{conflictId});db.setTransactionSuccessful();
        }finally{db.endTransaction();}
    }
}
