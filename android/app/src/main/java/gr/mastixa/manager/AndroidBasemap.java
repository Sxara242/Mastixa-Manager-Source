package gr.mastixa.manager;

import android.content.Context;
import android.graphics.*;
import android.net.http.HttpResponseCache;
import android.os.*;
import android.util.LruCache;
import java.io.*;
import java.net.*;
import java.util.*;
import java.util.concurrent.*;

/** Visible tiles only. HTTP disk cache honors provider expiry; no offline prefetch API. */
final class AndroidBasemap implements AutoCloseable {
    record Tile(int z,int x,int y){}
    interface Source { String url(Tile tile); String attribution(); }
    static final Source OSM=new Source(){public String url(Tile tile){return "https://tile.openstreetmap.org/"+tile.z()+"/"+tile.x()+"/"+tile.y()+".png";}public String attribution(){return "© OpenStreetMap contributors · openstreetmap.org/copyright";}};
    private static final double WORLD=2*Math.PI*6378137;
    private final LruCache<Tile,Bitmap> images=new LruCache<>(96);
    private final Set<Tile> pending=new HashSet<>();
    private final Map<Tile,Long> failed=new HashMap<>();
    private volatile Set<Tile> visible=Set.of();
    private final Set<HttpURLConnection> connections=ConcurrentHashMap.newKeySet();
    private final ExecutorService workers=Executors.newFixedThreadPool(2);
    private final Handler ui=new Handler(Looper.getMainLooper());
    private final Context context;
    private final Runnable redraw;
    private final Source source;
    private final Paint paint=new Paint(Paint.FILTER_BITMAP_FLAG);
    private final RectF target=new RectF();
    private volatile boolean closed;
    private long networkGeneration;
    private final Runnable retry=()->{if(!closed)redrawIfOpen();};
    private void redrawIfOpen(){if(!closed)redraw.run();}
    AndroidBasemap(Context context,Source source,Runnable redraw){this.context=context.getApplicationContext();this.source=source;this.redraw=redraw;}
    static List<Tile> visible(double cx,double cy,double scale,int width,int height){
        if(width<=0||height<=0||!Double.isFinite(scale)||scale<=0)return List.of();
        int z=Math.max(0,Math.min(19,(int)Math.floor(Math.log(WORLD*scale/256)/Math.log(2))));int n=1<<z;double span=WORLD/n;
        int left=Math.max(0,(int)Math.floor((cx-width/(2*scale)+WORLD/2)/span));int right=Math.min(n-1,(int)Math.floor((cx+width/(2*scale)+WORLD/2)/span));
        int top=Math.max(0,(int)Math.floor((WORLD/2-cy-height/(2*scale))/span));int bottom=Math.min(n-1,(int)Math.floor((WORLD/2-cy+height/(2*scale))/span));
        if((long)(right-left+1)*(bottom-top+1)>64)return List.of();var result=new ArrayList<Tile>();for(int x=left;x<=right;x++)for(int y=top;y<=bottom;y++)result.add(new Tile(z,x,y));return result;
    }
    void draw(Canvas canvas,double cx,double cy,double scale,int width,int height){
        if(closed)return;var tiles=visible(cx,cy,scale,width,height);visible=Set.copyOf(tiles);failed.keySet().retainAll(visible);
        for(var tile:tiles){var bitmap=images.get(tile);if(bitmap!=null){double span=WORLD/(1<<tile.z());float left=(float)((-WORLD/2+tile.x()*span-cx)*scale+width/2.0),top=(float)((cy-(WORLD/2-tile.y()*span))*scale+height/2.0);target.set(left,top,(float)(left+span*scale),(float)(top+span*scale));canvas.drawBitmap(bitmap,null,target,paint);}
            else if(!pending.contains(tile)&&pending.size()<64&&SystemClock.elapsedRealtime()-failed.getOrDefault(tile,-30001L)>30000){pending.add(tile);long generation=networkGeneration;workers.execute(()->fetch(tile,generation));}}
    }
    /** Called on the UI thread after connectivity returns; retains decoded/cache tiles. */
    void networkAvailable(){if(closed)return;networkGeneration++;failed.clear();ui.removeCallbacks(retry);redraw.run();}
    private static synchronized void cache(Context context)throws IOException{if(HttpResponseCache.getInstalled()==null)HttpResponseCache.install(new File(context.getCacheDir(),"map-http"),64L*1024*1024);}
    private void fetch(Tile tile,long generation){
        Bitmap image=null;HttpURLConnection connection=null;
        try{if(closed||!visible.contains(tile))return;cache(context);connection=(HttpURLConnection)new URL(source.url(tile)).openConnection();connections.add(connection);connection.setConnectTimeout(5000);connection.setReadTimeout(5000);connection.setUseCaches(true);connection.setInstanceFollowRedirects(false);connection.setRequestProperty("User-Agent","MastixaManager/0.40 (+https://github.com/Sxara242/Mastixa-Manager)");
            if(connection.getResponseCode()!=200)throw new IOException("Tile HTTP status");if(connection.getContentLengthLong()>1024*1024)throw new IOException("Oversize tile");
            byte[] bytes;try(var input=connection.getInputStream();var output=new ByteArrayOutputStream()){byte[] buffer=new byte[8192];int count;while((count=input.read(buffer))!=-1){if(output.size()+count>1024*1024)throw new IOException("Oversize tile");output.write(buffer,0,count);}bytes=output.toByteArray();}
            var size=new BitmapFactory.Options();size.inJustDecodeBounds=true;BitmapFactory.decodeByteArray(bytes,0,bytes.length,size);if(size.outWidth!=256||size.outHeight!=256)throw new IOException("Unexpected tile dimensions");image=BitmapFactory.decodeByteArray(bytes,0,bytes.length);
        }catch(IOException|RuntimeException e){/* Neutral background remains usable; retry is bounded and stopped on close. */}
        finally{if(connection!=null){connections.remove(connection);connection.disconnect();}Bitmap loaded=image;ui.post(()->{pending.remove(tile);if(closed)return;if(loaded!=null){images.put(tile,loaded);failed.remove(tile);}else if(visible.contains(tile)&&generation==networkGeneration){failed.put(tile,SystemClock.elapsedRealtime());ui.removeCallbacks(retry);ui.postDelayed(retry,30001);}redraw.run();});}
    }
    @Override public void close(){closed=true;visible=Set.of();workers.shutdownNow();for(var connection:connections)connection.disconnect();ui.removeCallbacksAndMessages(null);images.evictAll();}
}
