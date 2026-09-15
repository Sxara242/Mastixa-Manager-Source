package gr.mastixa.manager;
import org.junit.Test;
import static org.junit.Assert.*;
public class BasemapTest {
    @Test public void visibleTilesAreBoundedAndStayWithinWorld(){double[] xy=ParcelMapView.project(26,38);for(double scale:new double[]{.00001,.1,1,20}){var tiles=AndroidBasemap.visible(xy[0],xy[1],scale,1080,900);assertTrue(tiles.size()<=64);for(var tile:tiles){assertTrue(tile.z()>=0&&tile.z()<=19);assertTrue(tile.x()>=0&&tile.x()<(1<<tile.z()));assertTrue(tile.y()>=0&&tile.y()<(1<<tile.z()));}}assertTrue(AndroidBasemap.visible(0,0,Double.NaN,100,100).isEmpty());assertTrue(AndroidBasemap.visible(0,0,1,0,100).isEmpty());}
}
