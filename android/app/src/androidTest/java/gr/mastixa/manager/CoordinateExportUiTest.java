package gr.mastixa.manager;
import android.app.Activity;
import android.content.Intent;
import android.os.*;
import android.widget.*;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import java.io.*;
import java.util.*;
import static org.junit.Assert.*;

public class CoordinateExportUiTest {
    private Object field(Activity a,String name){try{var f=CoordinateExportActivity.class.getDeclaredField(name);f.setAccessible(true);return f.get(a);}catch(Exception e){throw new RuntimeException(e);}}
    private void set(Activity a,String name,Object value){try{var f=CoordinateExportActivity.class.getDeclaredField(name);f.setAccessible(true);f.set(a,value);}catch(Exception e){throw new RuntimeException(e);}}
    private void invoke(Activity a,String name,Class<?>[] types,Object...values){try{var method=CoordinateExportActivity.class.getDeclaredMethod(name,types);method.setAccessible(true);method.invoke(a,values);}catch(Exception e){throw new RuntimeException(e);}}
    private void ready(Activity a,int size)throws Exception{var i=InstrumentationRegistry.getInstrumentation();long deadline=SystemClock.elapsedRealtime()+10000;boolean[] done={false};while(!done[0]&&SystemClock.elapsedRealtime()<deadline){Thread.sleep(40);i.runOnMainSync(()->done[0]=((List<?>)field(a,"snapshot")).size()==size&&((Button)field(a,"save")).isEnabled());}assertTrue("Preview must complete",done[0]);}
    @Test public void multiFieldPreviewAndDocumentResultPreserveData()throws Exception{
        var i=InstrumentationRegistry.getInstrumentation();var context=i.getTargetContext();assertTrue(context.getPackageName().endsWith(".checks"));var profile=new ProfileStore.Profile("export-ui","Export test","test","en");context.deleteDatabase(profile.database());String id;byte[] before;
        try(var farm=new FarmStore(context,profile.database())){farm.addField("First",1);farm.addField("Second",2);var geo=new GeoStore(farm);for(var f:farm.fields())geo.saveGeometry(f.id(),ParcelGeometry.manual("26 38\n26.001 38\n26.001 38.001\n26 38.001","EPSG:4326"),"manual","",0);id=farm.fields().get(0).id();before=LocalBackup.snapshot(farm);}
        Activity screen=null;File output=new File(context.getCacheDir(),"export-ui-output.geojson"),prepared=new File(context.getCacheDir(),"coordinates-00000000-0000-0000-0000-000000000001.tmp");
        try{i.runOnMainSync(()->{UserSession.clear();UserSession.signIn(profile);});screen=i.startActivitySync(new Intent(context,CoordinateExportActivity.class).putExtra("field_id",id).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));var a=screen;ready(a,1);
            i.runOnMainSync(()->invoke(a,"selectAll",new Class[]{boolean.class},true));ready(a,2);
            i.runOnMainSync(()->{((Spinner)field(a,"coordinates")).setSelection(1);((Spinner)field(a,"format")).setSelection(3);});i.waitForIdleSync();ready(a,2);
            i.runOnMainSync(()->assertFalse(((Spinner)field(a,"coordinates")).isEnabled()));
            List<CoordinateExport.Parcel> values;try(var farm=new FarmStore(context,profile.database())){values=CoordinateExport.snapshot(farm,farm.fields().stream().map(FarmStore.Field::id).toList());}
            java.nio.file.Files.write(prepared.toPath(),CoordinateExport.encode(values,false,"geojson"));
            i.runOnMainSync(()->{set(a,"pending",prepared);var state=new Bundle();invoke(a,"onSaveInstanceState",new Class[]{Bundle.class},state);assertEquals(prepared.getName(),state.getString("pending"));invoke(a,"onActivityResult",new Class[]{int.class,int.class,Intent.class},203,Activity.RESULT_OK,new Intent().setData(android.net.Uri.fromFile(output)));});
            long deadline=SystemClock.elapsedRealtime()+5000;while(prepared.exists()&&SystemClock.elapsedRealtime()<deadline)Thread.sleep(40);assertFalse(prepared.exists());assertEquals(2,new org.json.JSONObject(new String(java.nio.file.Files.readAllBytes(output.toPath()),java.nio.charset.StandardCharsets.UTF_8)).getJSONArray("features").length());
            try(var farm=new FarmStore(context,profile.database())){assertArrayEquals(before,LocalBackup.snapshot(farm));}
        }finally{var a=screen;i.runOnMainSync(()->{if(a!=null)a.finish();UserSession.clear();});output.delete();prepared.delete();}
    }
}
