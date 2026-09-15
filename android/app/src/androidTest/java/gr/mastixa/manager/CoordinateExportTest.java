package gr.mastixa.manager;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import org.json.*;
import java.util.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.zip.*;
import static org.junit.Assert.*;

public class CoordinateExportTest {
    private String text(byte[] bytes){return new String(bytes,StandardCharsets.UTF_8);}
    @Test public void formatsRetainGreekNamesHolesPartsAndAllCoordinates()throws Exception{
        String shape="{\"type\":\"MultiPolygon\",\"coordinates\":[[[[26,38],[26.01,38],[26.01,38.01],[26,38.01],[26,38]],[[26.002,38.002],[26.002,38.004],[26.004,38.004],[26.004,38.002],[26.002,38.002]]],[[[26.02,38],[26.021,38],[26.02,38.001],[26.02,38]]]]}";
        var parcel=new CoordinateExport.Parcel("synthetic","=Χωράφι / Α","001234","manual",ParcelGeometry.normalize(shape,"EPSG:4326"));var parcels=List.of(parcel);var rows=CoordinateExport.table(parcels,false);
        assertEquals(12,rows.size());assertEquals("38.00000000",rows.get(1)[10]);assertEquals("26.00000000",rows.get(1)[11]);assertArrayEquals(new String[]{"1","2","1"},Arrays.copyOfRange(rows.get(5),7,10));assertArrayEquals(new String[]{"2","1","1"},Arrays.copyOfRange(rows.get(9),7,10));
        assertTrue(text(CoordinateExport.encode(parcels,false,"csv")).contains("'=Χωράφι / Α"));var files=new HashMap<String,String>();byte[] xlsx=CoordinateExport.encode(parcels,false,"xlsx");try(var zip=new ZipInputStream(new ByteArrayInputStream(xlsx))){ZipEntry item;while((item=zip.getNextEntry())!=null){var output=new ByteArrayOutputStream();zip.transferTo(output);files.put(item.getName(),output.toString("UTF-8"));}}
        assertTrue(files.get("xl/workbook.xml").contains("Όλες οι κορυφές"));String sheet=files.get("xl/worksheets/sheet1.xml");assertTrue(sheet.contains("=Χωράφι / Α"));assertFalse(sheet.contains("<f>"));assertTrue(sheet.contains("<c r=\"K2\" t=\"n\"><v>38.00000000</v>"));
        byte[] geojson=CoordinateExport.encode(parcels,false,"geojson");var feature=new JSONObject(text(geojson)).getJSONArray("features").getJSONObject(0);assertEquals("001234",feature.getJSONObject("properties").getString("kaek"));assertTrue(feature.getJSONObject("properties").has("perimeter_m"));assertFalse(feature.getJSONObject("properties").has("perimeter_m2"));assertEquals(11,ParcelGeometry.vertices(GeometryImport.parse(geojson,"parcel.geojson","").wgs84).size());
        byte[] kml=CoordinateExport.encode(parcels,false,"kml");assertTrue(text(kml).contains("innerBoundaryIs"));assertEquals(11,ParcelGeometry.vertices(GeometryImport.parse(kml,"parcel.kml","").wgs84).size());
        byte[] pdf=CoordinateExport.encode(parcels,false,"pdf");assertTrue(text(Arrays.copyOf(pdf,4)).equals("%PDF"));var context=InstrumentationRegistry.getInstrumentation().getTargetContext();for(var ext:List.of("xlsx","pdf","geojson","kml","csv"))try(var output=new FileOutputStream(new File(context.getExternalFilesDir(null),"coordinates-test."+ext))){output.write(CoordinateExport.encode(parcels,false,ext));}
    }
    @Test public void multipleFieldsActualSourcePrecisionAndNegativeLongitude()throws Exception{
        var source=new CoordinateExport.Parcel("source","ΕΓΣΑ87","002","import",ParcelGeometry.manual("500000.12345678 4200000.12345678\n500010.12345678 4200000.12345678\n500010.12345678 4200010.12345678\n500000.12345678 4200010.12345678","EPSG:2100"));
        var west=new CoordinateExport.Parcel("west","West","003","manual",ParcelGeometry.manual("-3 38\n-2.999 38\n-2.999 38.001\n-3 38.001","EPSG:4326"));var rows=CoordinateExport.table(List.of(source,west),true);assertEquals(9,rows.size());assertEquals("EPSG:2100",rows.get(1)[3]);assertEquals("500000.12345678",rows.get(1)[10]);assertEquals("4200000.12345678",rows.get(1)[11]);assertTrue(text(CoordinateExport.encode(List.of(west),false,"csv")).contains("\"-3.00000000\""));assertFalse(text(CoordinateExport.encode(List.of(west),false,"csv")).contains("'-3"));assertEquals(2,new JSONObject(text(CoordinateExport.encode(List.of(source,west),true,"geojson"))).getJSONArray("features").length());assertTrue(CoordinateExport.filename(List.of(source,west),true,"csv").contains("2_fields"));
    }
    @Test public void snapshotKeepsFieldMetadataAndGeometryInOneTransaction() throws Exception {
        var context=InstrumentationRegistry.getInstrumentation().getTargetContext();
        assertTrue(context.getPackageName().endsWith(".checks"));
        String name="export-snapshot-"+UUID.randomUUID()+".db";
        var result=new java.util.concurrent.atomic.AtomicReference<List<CoordinateExport.Parcel>>();
        var failure=new java.util.concurrent.atomic.AtomicReference<Throwable>();
        Thread reader=null;
        try(var farm=new FarmStore(context,name)) {
            farm.setWriteAheadLoggingEnabled(true);
            farm.addField("Old field",1);
            String id=farm.fields().get(0).id();
            var geo=new GeoStore(farm);
            var oldGeometry=ParcelGeometry.manual("26 38\n26.001 38\n26.001 38.001\n26 38.001","EPSG:4326");
            var newGeometry=ParcelGeometry.manual("27 38\n27.001 38\n27.001 38.001\n27 38.001","EPSG:4326");
            geo.saveGeometry(id,oldGeometry,"old","",0);
            var db=farm.getWritableDatabase();
            assertTrue(db.isWriteAheadLoggingEnabled());
            db.beginTransactionNonExclusive();
            try {
                farm.saveField(id,"New field",1,"NEW-KAEK","",0,"");
                geo.saveGeometry(id,newGeometry,"new","",1);
                reader=new Thread(()->{try{result.set(CoordinateExport.snapshot(farm,List.of(id)));}
                    catch(Throwable error){failure.set(error);}},"export-snapshot-reader");
                reader.start();
                // The WAL writer holds the primary connection. Wait until snapshot
                // requests its transaction, then publish the paired metadata/geometry.
                long deadline=System.nanoTime()+java.util.concurrent.TimeUnit.SECONDS.toNanos(10);
                boolean waiting=false;
                while(System.nanoTime()<deadline && reader.isAlive()) {
                    for(var frame:reader.getStackTrace())
                        if(frame.getClassName().startsWith("android.database.sqlite.")
                                && frame.getMethodName().startsWith("beginTransaction")) waiting=true;
                    if(waiting)break;
                    Thread.sleep(5);
                }
                assertTrue("Reader must reach the transaction boundary",waiting);
                db.setTransactionSuccessful();
            } finally {db.endTransaction();}
            reader.join(10000);
            assertFalse("Snapshot did not finish",reader.isAlive());
            assertNull(failure.get());
            assertEquals(1,result.get().size());
            var parcel=result.get().get(0);
            assertEquals("New field",parcel.name());
            assertEquals("NEW-KAEK",parcel.kaek());
            assertEquals("new",parcel.source());
            assertEquals(newGeometry.original,parcel.geometry().original);
        } finally {
            if(reader!=null)reader.join(10000);
            context.deleteDatabase(name);
        }
    }

}
