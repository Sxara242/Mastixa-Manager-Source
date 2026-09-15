package gr.mastixa.manager;

import android.location.Location;
import org.json.*;
import net.sf.geographiclib.Geodesic;

/** Foreground-only recording. Each accepted fix is durable; gaps start new segments. */
final class GpsTrack {
    private final GeoStore store;
    private final String field;
    private GeoStore.Record row;
    private long tick;
    private boolean newSegment=true;
    GpsTrack(GeoStore store,String field){this.store=store;this.field=field;
        for(var item:store.records(field,"track"))if(!item.payload().optString("state").equals("stopped"))row=item;
        // An interrupted process has no monotonic clock continuity. Retain only durable duration.
        if(row!=null&&recording())change("paused",System.currentTimeMillis(),-1);
    }
    GeoStore.Record current(){return row;}
    boolean recording(){return row!=null&&row.payload().optString("state").equals("recording");}
    private void persist(JSONObject payload){String id=store.save(row==null?null:row.id(),field,"track",payload,row==null?0:row.revision());
        for(var item:store.records(field,"track"))if(item.id().equals(id)){row=item;break;}}
    void start(String title,long wall,long elapsed){
        if(row!=null&&!row.payload().optString("state").equals("stopped"))throw new IllegalArgumentException("Finish the existing track first");
        if(title.isBlank())throw new IllegalArgumentException("Track title required");
        row=null;try{persist(new JSONObject().put("title",title.trim()).put("positions",new JSONArray()).put("segment_starts",new JSONArray())
            .put("state","recording").put("distance_m",0).put("duration_ms",0).put("started_at",wall).put("ended_at",0));}
        catch(JSONException e){throw new IllegalArgumentException(e);}tick=elapsed;newSegment=true;
    }
    void change(String state,long wall,long elapsed){
        if(row==null)return;
        String previous=row.payload().optString("state");
        if(previous.equals("stopped")||(!state.equals("paused")&&!state.equals("recording")&&!state.equals("stopped")))throw new IllegalArgumentException("Invalid track transition");
        try{var payload=new JSONObject(row.payload().toString());
            if(recording()&&elapsed>=tick&&elapsed>=0)payload.put("duration_ms",payload.getLong("duration_ms")+elapsed-tick);
            payload.put("state",state).put("ended_at",state.equals("stopped")?wall:0);persist(payload);
        }catch(JSONException e){throw new IllegalArgumentException(e);}tick=elapsed;newSegment=true;
    }
    void append(Location fix,long elapsedNanos){
        if(!recording()||!GpsFix.usable(fix,elapsedNanos))return;
        try{var payload=new JSONObject(row.payload().toString());var points=payload.getJSONArray("positions");
            if(points.length()>=20000){change("paused",System.currentTimeMillis(),elapsedNanos/1_000_000);throw new IllegalArgumentException("Track limit reached: 20000 positions. Start a new track.");}
            JSONArray previous=points.length()==0?null:points.getJSONArray(points.length()-1);
            if(previous!=null&&fix.getTime()<=previous.getLong(3))return;
            var segments=payload.optJSONArray("segment_starts");if(segments==null){segments=new JSONArray();if(points.length()>0)segments.put(0);payload.put("segment_starts",segments);}
            if(newSegment)segments.put(points.length());
            else if(previous!=null)payload.put("distance_m",payload.getDouble("distance_m")+Geodesic.WGS84.Inverse(previous.getDouble(1),previous.getDouble(0),fix.getLatitude(),fix.getLongitude()).s12);
            points.put(new JSONArray().put(fix.getLongitude()).put(fix.getLatitude()).put(fix.getAccuracy()).put(fix.getTime()));
            long elapsed=elapsedNanos/1_000_000;
            payload.put("duration_ms",payload.getLong("duration_ms")+Math.max(0,elapsed-tick));persist(payload);tick=elapsed;newSegment=false;
        }catch(JSONException e){throw new IllegalArgumentException(e);}
    }
}
