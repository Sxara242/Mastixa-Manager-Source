package gr.mastixa.manager;

import android.content.ContentValues;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import java.util.*;

/** Phase 15B profile-local sensor persistence. Observations are append-only. */
public final class SensorDataStore {
    public static final String[] DEVICE_COLUMNS = {
        "id","name","provider","field_id","external_id","status","notes","created_at","updated_at","deleted_at"
    };
    public static final String[] CHANNEL_COLUMNS = {
        "id","device_id","metric","unit","label","created_at","updated_at"
    };
    public static final String[] OBSERVATION_COLUMNS = {
        "id","channel_id","observed_at","numeric_value","quality","source_ref","created_at"
    };

    private final FarmStore store;

    public SensorDataStore(FarmStore store) {
        this.store = Objects.requireNonNull(store, "store");
        create(store.getWritableDatabase());
    }

    public static void create(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE IF NOT EXISTS sensor_devices(" +
            "id TEXT PRIMARY KEY,name TEXT NOT NULL,provider TEXT NOT NULL,field_id TEXT NOT NULL DEFAULT ''," +
            "external_id TEXT NOT NULL DEFAULT '',status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','disabled'))," +
            "notes TEXT NOT NULL DEFAULT '',created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL,deleted_at INTEGER)");
        db.execSQL("CREATE TABLE IF NOT EXISTS sensor_channels(" +
            "id TEXT PRIMARY KEY,device_id TEXT NOT NULL,metric TEXT NOT NULL,unit TEXT NOT NULL,label TEXT NOT NULL DEFAULT ''," +
            "created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL)");
        db.execSQL("CREATE TABLE IF NOT EXISTS sensor_observations(" +
            "id TEXT PRIMARY KEY,channel_id TEXT NOT NULL,observed_at TEXT NOT NULL,numeric_value REAL NOT NULL," +
            "quality TEXT NOT NULL DEFAULT 'good' CHECK(quality IN ('good','suspect')),source_ref TEXT NOT NULL DEFAULT ''," +
            "created_at INTEGER NOT NULL)");
        db.execSQL("CREATE INDEX IF NOT EXISTS idx_sensor_devices_field ON sensor_devices(field_id,deleted_at)");
        db.execSQL("CREATE INDEX IF NOT EXISTS idx_sensor_channels_device ON sensor_channels(device_id,id)");
        db.execSQL("CREATE INDEX IF NOT EXISTS idx_sensor_observations_channel_time ON sensor_observations(channel_id,observed_at,id)");
    }

    private static String text(String value) { return value == null ? "" : value.trim(); }

    private void requireField(String fieldId) {
        if (fieldId.isEmpty()) return;
        try (Cursor c = store.getReadableDatabase().rawQuery(
            "SELECT 1 FROM fields WHERE id=? AND deleted_at IS NULL", new String[]{fieldId}
        )) {
            if (!c.moveToFirst()) throw new IllegalArgumentException("Field does not exist");
        }
    }

    private static SensorData.Device device(Cursor c) {
        return new SensorData.Device(c.getString(0),c.getString(1),c.getString(2),c.getString(3),c.getString(4),c.getString(5),c.getString(6));
    }
    private static SensorData.Channel channel(Cursor c) {
        return new SensorData.Channel(c.getString(0),c.getString(1),c.getString(2),c.getString(3),c.getString(4));
    }
    private static SensorData.Observation observation(Cursor c) {
        return new SensorData.Observation(c.getString(0),c.getString(1),c.getString(2),c.getDouble(3),c.getString(4),c.getString(5));
    }

    private static SensorData.Device normalized(SensorData.Device d) {
        return new SensorData.Device(text(d.id()),text(d.name()),text(d.provider()),text(d.fieldId()),text(d.externalId()),text(d.status()),text(d.notes()));
    }
    private static SensorData.Channel normalized(SensorData.Channel c) {
        return new SensorData.Channel(text(c.id()),text(c.deviceId()),text(c.metric()),text(c.unit()),text(c.label()));
    }
    private static SensorData.Observation normalized(SensorData.Observation o) {
        return new SensorData.Observation(text(o.id()),text(o.channelId()),text(o.observedAt()),o.value(),text(o.quality()),text(o.sourceRef()));
    }

    public void saveDevice(SensorData.Device input) {
        SensorData.Device value = normalized(Objects.requireNonNull(input,"device"));
        SensorData.project(value,List.of(),List.of());
        requireField(value.fieldId());
        Long created = null;
        try (Cursor c=store.getReadableDatabase().rawQuery("SELECT created_at,deleted_at FROM sensor_devices WHERE id=?",new String[]{value.id()})) {
            if(c.moveToFirst()) {
                if(!c.isNull(1)) throw new IllegalArgumentException("Deleted sensor device must be restored before editing");
                created=c.getLong(0);
            }
        }
        long now=System.currentTimeMillis();
        ContentValues row=new ContentValues();
        row.put("id",value.id()); row.put("name",value.name()); row.put("provider",value.provider()); row.put("field_id",value.fieldId());
        row.put("external_id",value.externalId()); row.put("status",value.status()); row.put("notes",value.notes());
        row.put("created_at",created==null?now:created); row.put("updated_at",now); row.putNull("deleted_at");
        SQLiteDatabase db=store.getWritableDatabase();
        if(created==null) db.insertOrThrow("sensor_devices",null,row);
        else if(db.update("sensor_devices",row,"id=?",new String[]{value.id()})!=1) throw new IllegalArgumentException("Sensor device does not exist");
    }

    public SensorData.Device device(String id) { return device(id,false); }
    public SensorData.Device device(String id, boolean includeDeleted) {
        String sql="SELECT id,name,provider,field_id,external_id,status,notes FROM sensor_devices WHERE id=?"+(includeDeleted?"":" AND deleted_at IS NULL");
        try(Cursor c=store.getReadableDatabase().rawQuery(sql,new String[]{text(id)})) {
            if(!c.moveToFirst()) throw new IllegalArgumentException("Sensor device does not exist");
            return device(c);
        }
    }

    public List<SensorData.Device> devices(boolean includeDeleted) {
        List<SensorData.Device> rows=new ArrayList<>();
        String sql="SELECT id,name,provider,field_id,external_id,status,notes FROM sensor_devices"+(includeDeleted?"":" WHERE deleted_at IS NULL")+" ORDER BY name COLLATE NOCASE,id";
        try(Cursor c=store.getReadableDatabase().rawQuery(sql,null)){while(c.moveToNext())rows.add(device(c));}
        return List.copyOf(rows);
    }

    public void saveChannel(SensorData.Channel input) {
        SensorData.Channel value=normalized(Objects.requireNonNull(input,"channel"));
        SensorData.Device owner=device(value.deviceId());
        SensorData.project(owner,List.of(value),List.of());
        Long created=null; String oldDevice=null,oldMetric=null,oldUnit=null;
        try(Cursor c=store.getReadableDatabase().rawQuery("SELECT device_id,metric,unit,created_at FROM sensor_channels WHERE id=?",new String[]{value.id()})){
            if(c.moveToFirst()){oldDevice=c.getString(0);oldMetric=c.getString(1);oldUnit=c.getString(2);created=c.getLong(3);}
        }
        if(created!=null){
            try(Cursor c=store.getReadableDatabase().rawQuery("SELECT COUNT(*) FROM sensor_observations WHERE channel_id=?",new String[]{value.id()})){
                c.moveToFirst();
                if(c.getLong(0)>0 && (!oldDevice.equals(value.deviceId())||!oldMetric.equals(value.metric())||!oldUnit.equals(value.unit())))
                    throw new IllegalArgumentException("Observed channel identity cannot be changed");
            }
        }
        long now=System.currentTimeMillis(); ContentValues row=new ContentValues();
        row.put("id",value.id());row.put("device_id",value.deviceId());row.put("metric",value.metric());row.put("unit",value.unit());row.put("label",value.label());
        row.put("created_at",created==null?now:created);row.put("updated_at",now);
        SQLiteDatabase db=store.getWritableDatabase();
        if(created==null)db.insertOrThrow("sensor_channels",null,row);else db.update("sensor_channels",row,"id=?",new String[]{value.id()});
    }

    public SensorData.Channel channel(String id) {
        try(Cursor c=store.getReadableDatabase().rawQuery("SELECT id,device_id,metric,unit,label FROM sensor_channels WHERE id=?",new String[]{text(id)})){
            if(!c.moveToFirst())throw new IllegalArgumentException("Sensor channel does not exist");return channel(c);
        }
    }

    public List<SensorData.Channel> channels(String deviceId) {
        List<SensorData.Channel> rows=new ArrayList<>();
        try(Cursor c=store.getReadableDatabase().rawQuery("SELECT id,device_id,metric,unit,label FROM sensor_channels WHERE device_id=? ORDER BY id",new String[]{text(deviceId)})){
            while(c.moveToNext())rows.add(channel(c));
        }
        return List.copyOf(rows);
    }

    public void appendObservation(SensorData.Observation input) {
        SensorData.Observation value=normalized(Objects.requireNonNull(input,"observation"));
        try(Cursor c=store.getReadableDatabase().rawQuery("SELECT 1 FROM sensor_observations WHERE id=?",new String[]{value.id()})){
            if(c.moveToFirst())throw new IllegalArgumentException("Sensor observation id already exists");
        }
        SensorData.Channel channel=channel(value.channelId()); SensorData.Device owner=device(channel.deviceId());
        if(!owner.status().equals("active"))throw new IllegalArgumentException("Disabled sensor device cannot accept observations");
        SensorData.project(owner,List.of(channel),List.of(value));
        ContentValues row=new ContentValues();row.put("id",value.id());row.put("channel_id",value.channelId());row.put("observed_at",value.observedAt());
        row.put("numeric_value",value.value());row.put("quality",value.quality());row.put("source_ref",value.sourceRef());row.put("created_at",System.currentTimeMillis());
        store.getWritableDatabase().insertOrThrow("sensor_observations",null,row);
    }

    public List<SensorData.Observation> observations(String channelId) {
        List<SensorData.Observation> rows=new ArrayList<>();
        try(Cursor c=store.getReadableDatabase().rawQuery("SELECT id,channel_id,observed_at,numeric_value,quality,source_ref FROM sensor_observations WHERE channel_id=? ORDER BY observed_at,id",new String[]{text(channelId)})){
            while(c.moveToNext())rows.add(observation(c));
        }
        return List.copyOf(rows);
    }

    public SensorData.Snapshot snapshot(String deviceId) {
        SensorData.Device d=device(deviceId); List<SensorData.Channel> channels=channels(d.id()); List<SensorData.Observation> observations=new ArrayList<>();
        for(SensorData.Channel c:channels)observations.addAll(observations(c.id()));
        return SensorData.project(d,channels,observations);
    }

    public void deleteDevice(String id) {
        long now=System.currentTimeMillis();ContentValues row=new ContentValues();row.put("deleted_at",now);row.put("updated_at",now);
        if(store.getWritableDatabase().update("sensor_devices",row,"id=? AND deleted_at IS NULL",new String[]{text(id)})!=1)
            throw new IllegalArgumentException("Sensor device does not exist");
    }
    public void restoreDevice(String id) {
        SensorData.Device d=device(id,true);requireField(d.fieldId());ContentValues row=new ContentValues();row.putNull("deleted_at");row.put("updated_at",System.currentTimeMillis());
        if(store.getWritableDatabase().update("sensor_devices",row,"id=? AND deleted_at IS NOT NULL",new String[]{d.id()})!=1)
            throw new IllegalArgumentException("Deleted sensor device does not exist");
    }
}
