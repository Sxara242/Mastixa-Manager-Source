package gr.mastixa.manager;
import org.json.*;
import org.junit.Test;
import static org.junit.Assert.*;

public class ParcelGeometryTest {
    @Test public void orderedVerticesGeodesicMetricsAndBoundaryContainment(){
        var g=ParcelGeometry.manual("26 38\n26.001 38\n26.001 38.001\n26 38.001","EPSG:4326");
        assertEquals(4,ParcelGeometry.vertices(g.original).size());
        assertEquals(9749.0283474,g.area,.01);assertEquals(397.6567015,g.perimeter,.001);
        assertTrue(g.contains(26,38));assertTrue(g.contains(26.0005,38.0005));assertFalse(g.contains(26.01,38));
        assertEquals(1,ParcelGeometry.vertices(g.original).get(0).index());
    }
    @Test public void holesAreExcludedRegardlessOfWinding()throws Exception{
        var outer=ParcelGeometry.manual("26 38\n26.001 38\n26.001 38.001\n26 38.001","EPSG:4326");
        var hole=ParcelGeometry.manual("26.0002 38.0002\n26.0004 38.0002\n26.0004 38.0004\n26.0002 38.0004","EPSG:4326");
        var json=new JSONObject(outer.original);json.getJSONArray("coordinates").put(new JSONObject(hole.original).getJSONArray("coordinates").getJSONArray(0));
        var g=ParcelGeometry.normalize(json.toString(),"EPSG:4326");
        assertEquals(outer.area-hole.area,g.area,.001);assertEquals(outer.perimeter+hole.perimeter,g.perimeter,.001);
        assertFalse(g.contains(26.0003,38.0003));assertEquals(8,ParcelGeometry.vertices(g.original).size());
    }
    @Test public void originalProjectedCoordinatesArePreserved(){
        var g=ParcelGeometry.manual("500000 4200000\n500100 4200000\n500100 4200100\n500000 4200100","EPSG:2100");
        assertEquals(500000,ParcelGeometry.vertices(g.original).get(0).x(),0);
        assertEquals("EPSG:2100",g.sourceCrs);assertTrue(g.centroidLon>23&&g.centroidLon<25);assertTrue(g.centroidLat>37&&g.centroidLat<39);
    }
    @Test public void invalidSelfIntersectionAndUnknownCrsRejected(){
        for(String source:new String[]{"EPSG:4326","EPSG:999999"}){
            try{ParcelGeometry.manual("0 0\n1 1\n0 1\n1 0",source);fail("Expected invalid geometry/CRS");}catch(RuntimeException expected){}
        }
        try{ParcelGeometry.manual("200 38\n201 38\n201 39","EPSG:4326");fail("Expected invalid position");}catch(IllegalArgumentException expected){}
    }
}
