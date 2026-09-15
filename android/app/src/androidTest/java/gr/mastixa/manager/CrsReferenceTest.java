package gr.mastixa.manager;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import org.json.*;
import static org.junit.Assert.*;

public class CrsReferenceTest {
    @Test public void publishedReferencePairsAndReverseTransforms()throws Exception{
        byte[] bytes;try(var input=InstrumentationRegistry.getInstrumentation().getContext().getAssets().open("crs_reference.json")){bytes=GeometryImport.read(input);}var cases=new JSONObject(new String(bytes,java.nio.charset.StandardCharsets.UTF_8)).getJSONArray("references");
        for(int i=0;i<cases.length();i++){var c=cases.getJSONObject(i);var xy=c.getJSONArray("input");var expected=c.getJSONArray("output");var actual=ParcelGeometry.transform(xy.getDouble(0),xy.getDouble(1),c.getString("source"),c.getString("target"));for(int axis=0;axis<2;axis++)assertEquals(c.getString("name"),expected.getDouble(axis),actual[axis],c.getDouble("tolerance"));var back=ParcelGeometry.transform(actual[0],actual[1],c.getString("target"),c.getString("source"));for(int axis=0;axis<2;axis++)assertEquals(c.getString("name")+" reverse",xy.getDouble(axis),back[axis],c.getDouble("reverse_tolerance"));}
        var wrong=ParcelGeometry.transform(12,15,"EPSG:4326","EPSG:3857");assertTrue(Math.abs(wrong[0]-1669792.3618991035)>100000);
    }
    @Test public void unsupported3dAndGeocentricCrsAreNotSilentlyFlattened(){for(String code:new String[]{"EPSG:4978","EPSG:4979","EPSG:999999"}){try{ParcelGeometry.crs(code);fail("Unsupported CRS accepted: "+code);}catch(RuntimeException expected){}}}
}
