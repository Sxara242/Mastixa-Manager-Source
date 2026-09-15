package gr.mastixa.manager;

import android.content.ContentValues;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import java.util.Set;
import java.util.UUID;

/** Dataset-scoped verified identity registry for Phase 9 activity synchronization. */
public final class ActivityIdentityRegistry {
    private static final Set<String> SOURCE_TYPES=Set.of(
        "production","farm_activity","planting_batch","plant_protection","labor_entry","geo_point"
    );
    private ActivityIdentityRegistry() {}

    static void migrate(SQLiteDatabase db){
        db.execSQL("CREATE TABLE IF NOT EXISTS activity_sync_fields(scope_id TEXT NOT NULL,dataset_id TEXT NOT NULL,local_field_id TEXT NOT NULL,field_uuid TEXT NOT NULL,updated_at INTEGER NOT NULL CHECK(updated_at>=0),PRIMARY KEY(scope_id,dataset_id,local_field_id),UNIQUE(scope_id,dataset_id,field_uuid))");
        db.execSQL("CREATE TABLE IF NOT EXISTS activity_sync_sources(scope_id TEXT NOT NULL,dataset_id TEXT NOT NULL,source_type TEXT NOT NULL,local_source_id TEXT NOT NULL,local_field_id TEXT NOT NULL,source_uuid TEXT NOT NULL,updated_at INTEGER NOT NULL CHECK(updated_at>=0),PRIMARY KEY(scope_id,dataset_id,source_type,local_source_id),UNIQUE(scope_id,dataset_id,source_type,source_uuid))");
        db.execSQL("CREATE INDEX IF NOT EXISTS idx_activity_sync_sources_field ON activity_sync_sources(scope_id,dataset_id,local_field_id)");
    }

    public static void registerField(SQLiteDatabase db,String scopeId,String datasetId,String localFieldId,String fieldUuid,long updatedAt){
        migrate(db);String scope=text(scopeId,"scope_id"),dataset=uuid(datasetId,"dataset_id"),local=text(localFieldId,"local_field_id"),shared=uuid(fieldUuid,"field_uuid");stamp(updatedAt);
        try(Cursor c=db.rawQuery("SELECT field_uuid FROM activity_sync_fields WHERE scope_id=? AND dataset_id=? AND local_field_id=?",new String[]{scope,dataset,local})){
            if(c.moveToFirst()&&!shared.equals(c.getString(0)))throw new IllegalArgumentException("Local field already maps to another shared identity");
        }
        try(Cursor c=db.rawQuery("SELECT local_field_id FROM activity_sync_fields WHERE scope_id=? AND dataset_id=? AND field_uuid=?",new String[]{scope,dataset,shared})){
            if(c.moveToFirst()&&!local.equals(c.getString(0)))throw new IllegalArgumentException("Shared field identity already maps to another local field");
        }
        ContentValues row=new ContentValues();row.put("scope_id",scope);row.put("dataset_id",dataset);row.put("local_field_id",local);row.put("field_uuid",shared);row.put("updated_at",updatedAt);
        int changed=db.update("activity_sync_fields",row,"scope_id=? AND dataset_id=? AND local_field_id=?",new String[]{scope,dataset,local});if(changed==0)db.insertOrThrow("activity_sync_fields",null,row);
    }

    public static void registerSource(SQLiteDatabase db,String scopeId,String datasetId,String sourceType,String localSourceId,String localFieldId,String sourceUuid,long updatedAt){
        migrate(db);String scope=text(scopeId,"scope_id"),dataset=uuid(datasetId,"dataset_id"),type=text(sourceType,"source_type"),source=text(localSourceId,"local_source_id"),field=text(localFieldId,"local_field_id"),shared=uuid(sourceUuid,"source_uuid");stamp(updatedAt);if(!SOURCE_TYPES.contains(type))throw new IllegalArgumentException("Unsupported activity source type");
        try(Cursor c=db.rawQuery("SELECT 1 FROM activity_sync_fields WHERE scope_id=? AND dataset_id=? AND local_field_id=?",new String[]{scope,dataset,field})){if(!c.moveToFirst())throw new IllegalArgumentException("Source target field has no verified shared identity");}
        try(Cursor c=db.rawQuery("SELECT source_uuid FROM activity_sync_sources WHERE scope_id=? AND dataset_id=? AND source_type=? AND local_source_id=?",new String[]{scope,dataset,type,source})){
            if(c.moveToFirst()&&!shared.equals(c.getString(0)))throw new IllegalArgumentException("Local source already maps to another shared identity");
        }
        try(Cursor c=db.rawQuery("SELECT local_source_id FROM activity_sync_sources WHERE scope_id=? AND dataset_id=? AND source_type=? AND source_uuid=?",new String[]{scope,dataset,type,shared})){
            if(c.moveToFirst()&&!source.equals(c.getString(0)))throw new IllegalArgumentException("Shared source identity already maps to another local source");
        }
        ContentValues row=new ContentValues();row.put("scope_id",scope);row.put("dataset_id",dataset);row.put("source_type",type);row.put("local_source_id",source);row.put("local_field_id",field);row.put("source_uuid",shared);row.put("updated_at",updatedAt);
        int changed=db.update("activity_sync_sources",row,"scope_id=? AND dataset_id=? AND source_type=? AND local_source_id=?",new String[]{scope,dataset,type,source});if(changed==0)db.insertOrThrow("activity_sync_sources",null,row);
    }

    public static ActivityProjection.SyncRef lookup(SQLiteDatabase db,String scopeId,String datasetId,String sourceType,String localSourceId,String localFieldId){
        if(!hasTables(db))return null;String scope=text(scopeId,"scope_id"),dataset=uuid(datasetId,"dataset_id"),type=text(sourceType,"source_type"),source=text(localSourceId,"local_source_id"),field=text(localFieldId,"local_field_id");if(!SOURCE_TYPES.contains(type))throw new IllegalArgumentException("Unsupported activity source type");
        try(Cursor c=db.rawQuery("SELECT s.source_uuid,f.field_uuid FROM activity_sync_sources s JOIN activity_sync_fields f ON f.scope_id=s.scope_id AND f.dataset_id=s.dataset_id AND f.local_field_id=s.local_field_id WHERE s.scope_id=? AND s.dataset_id=? AND s.source_type=? AND s.local_source_id=? AND s.local_field_id=?",new String[]{scope,dataset,type,source,field})){
            return c.moveToFirst()?new ActivityProjection.SyncRef(dataset,c.getString(0),c.getString(1)):null;
        }
    }

    private static boolean hasTables(SQLiteDatabase db){int count=0;try(Cursor c=db.rawQuery("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('activity_sync_fields','activity_sync_sources')",null)){while(c.moveToNext())count++;}return count==2;}
    private static String text(String value,String label){String out=value==null?"":value.trim();if(out.isEmpty())throw new IllegalArgumentException(label+" is required");return out;}
    private static String uuid(String value,String label){try{String out=UUID.fromString(value).toString();if(!out.equals(value))throw new IllegalArgumentException();return out;}catch(Exception error){throw new IllegalArgumentException(label+" must be a canonical UUID",error);}}
    private static void stamp(long value){if(value<0)throw new IllegalArgumentException("updated_at must be non-negative");}
}
