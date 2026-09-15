package gr.mastixa.manager;
import org.junit.Test;
import static org.junit.Assert.*;
import java.nio.charset.StandardCharsets;

public class GeometryImportTest {
    @Test public void geojsonKmlGmlProduceEquivalentGeometry()throws Exception{
        String geometry="{\"type\":\"Polygon\",\"coordinates\":[[[26,38],[26.001,38],[26.001,38.001],[26,38.001],[26,38]]]}";
        var json=GeometryImport.parse(geometry.getBytes(StandardCharsets.UTF_8),"field.geojson","");
        String kml="<kml xmlns='http://www.opengis.net/kml/2.2'><Placemark><Polygon><outerBoundaryIs><LinearRing><coordinates>26,38,0 26.001,38,0 26.001,38.001,0 26,38.001,0 26,38,0</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark></kml>";
        var fromKml=GeometryImport.parse(kml.getBytes(StandardCharsets.UTF_8),"field.kml","");
        String gml="<gml:Polygon xmlns:gml='http://www.opengis.net/gml/3.2' srsName='urn:ogc:def:crs:EPSG::4326'><gml:exterior><gml:LinearRing><gml:posList>38 26 38 26.001 38.001 26.001 38.001 26 38 26</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon>";
        var fromGml=GeometryImport.parse(gml.getBytes(StandardCharsets.UTF_8),"field.gml","");
        assertEquals(json.area,fromKml.area,.001);assertEquals(json.area,fromGml.area,.001);
        assertEquals(ParcelGeometry.vertices(json.original),ParcelGeometry.vertices(fromGml.original));
    }
    @Test public void missingCrsEntitiesAndMultipleFeaturesRejected()throws Exception{
        for(String text:new String[]{"<!DOCTYPE x [<!ENTITY e SYSTEM 'file:///private'>]><x>&e;</x>","<Polygon><exterior><LinearRing><posList>0 0 1 0 1 1 0 0</posList></LinearRing></exterior></Polygon>","{\"type\":\"FeatureCollection\",\"features\":[]}"}){
            try{GeometryImport.parse(text.getBytes(StandardCharsets.UTF_8),"field.gml","");fail("Expected rejection");}catch(Exception expected){}
        }
    }
}
