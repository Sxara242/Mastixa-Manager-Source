package gr.mastixa.manager;

import android.util.Xml;
import org.xmlpull.v1.XmlPullParser;
import org.json.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.Locale;

/** Bounded geometry file parsing, no network or external XML entities. */
public final class GeometryImport {
    public static final int LIMIT=10*1024*1024;
    public static byte[] read(InputStream input)throws IOException{
        if(input==null)throw new IOException("Cannot open file");ByteArrayOutputStream output=new ByteArrayOutputStream();byte[] buffer=new byte[8192];int count;
        while((count=input.read(buffer))!=-1){if(output.size()+count>LIMIT)throw new IOException("Geometry exceeds 10 MB");output.write(buffer,0,count);}return output.toByteArray();
    }
    public static ParcelGeometry parse(byte[] data,String filename,String declared)throws Exception{
        if(data.length>LIMIT)throw new IOException("Geometry exceeds 10 MB");String text=new String(data,StandardCharsets.UTF_8);if(text.startsWith("\uFEFF"))text=text.substring(1);
        String name=filename.toLowerCase(Locale.ROOT);
        if(name.endsWith(".json")||name.endsWith(".geojson")||text.stripLeading().startsWith("{")){
            JSONObject value=new JSONObject(text);String embedded="";
            if(value.has("crs"))embedded=epsg(value.getJSONObject("crs").getJSONObject("properties").getString("name"));
            String source=declared.isBlank()?(embedded.isEmpty()?"EPSG:4326":embedded):epsg(declared);
            if(!embedded.isEmpty()&&!source.equals(embedded))throw new IllegalArgumentException("Declared/file CRS conflict");
            if(value.getString("type").equals("FeatureCollection")){var features=value.getJSONArray("features");if(features.length()!=1)throw new IllegalArgumentException("Exactly one Feature required");value=features.getJSONObject(0);}
            if(value.getString("type").equals("Feature"))value=value.getJSONObject("geometry");
            return ParcelGeometry.normalize(value.toString(),source);
        }
        if(!(name.endsWith(".kml")||name.endsWith(".gml")||name.endsWith(".xml")))throw new IllegalArgumentException("Android: GeoJSON, KML, GML or manual coordinates. Convert Shapefile/DXF using Desktop first.");
        boolean kml=name.endsWith(".kml");
        XmlPullParser parser=Xml.newPullParser();parser.setFeature(XmlPullParser.FEATURE_PROCESS_NAMESPACES,true);parser.setInput(new StringReader(text));
        JSONArray polygons=new JSONArray(),rings=null;String source=kml?"EPSG:4326":declared.isBlank()?"":epsg(declared),inherited="",capture=null;StringBuilder coordinates=new StringBuilder();
        int event;boolean exteriorSeen=false;
        while((event=parser.nextToken())!=XmlPullParser.END_DOCUMENT){
            if(event==XmlPullParser.DOCDECL||event==XmlPullParser.ENTITY_REF)throw new IllegalArgumentException("XML entities/DOCTYPE are not allowed");
            if(event==XmlPullParser.START_TAG){
                String tag=parser.getName();String srs=parser.getAttributeValue(null,"srsName");
                if(srs!=null){String actual=epsg(srs);if(!source.isEmpty()&&!source.equals(actual))throw new IllegalArgumentException("Mixed or conflicting GML CRS");inherited=actual;}
                if(tag.equals("Polygon")){if(rings!=null)throw new IllegalArgumentException("Nested polygon");rings=new JSONArray();exteriorSeen=false;if(!kml&&source.isEmpty())source=inherited;}
                if(rings!=null&&(tag.equals("outerBoundaryIs")||tag.equals("exterior"))){if(exteriorSeen)throw new IllegalArgumentException("Duplicate exterior");exteriorSeen=true;}
                if(rings!=null&&(tag.equals("innerBoundaryIs")||tag.equals("interior"))&&!exteriorSeen)throw new IllegalArgumentException("Exterior ring must precede holes");
                if(rings!=null&&(tag.equals("coordinates")||tag.equals("posList"))){
                    if(!exteriorSeen)throw new IllegalArgumentException("Missing exterior boundary");String dimension=parser.getAttributeValue(null,"srsDimension");if(dimension!=null&&!dimension.equals("2"))throw new IllegalArgumentException("Only 2D GML supported");
                    capture=tag;coordinates.setLength(0);
                }
            }else if((event==XmlPullParser.TEXT||event==XmlPullParser.CDSECT)&&capture!=null)coordinates.append(parser.getText());
            else if(event==XmlPullParser.END_TAG){
                String tag=parser.getName();
                if(tag.equals(capture)){
                    JSONArray ring=new JSONArray();String raw=coordinates.toString().trim();
                    if(tag.equals("coordinates")){
                        if(!kml)throw new IllegalArgumentException("GML requires explicit 2D posList");
                        for(String token:raw.split("\\s+")){String[] values=token.split(",");if(values.length<2||values.length>3||(values.length==3&&Double.parseDouble(values[2])!=0))throw new IllegalArgumentException("Only 2D / zero-altitude KML supported");ring.put(new JSONArray().put(Double.parseDouble(values[0])).put(Double.parseDouble(values[1])));}
                    }else{
                        if(kml)throw new IllegalArgumentException("KML requires coordinates");String[] values=raw.split("\\s+");if(values.length%2!=0)throw new IllegalArgumentException("Odd coordinate count");
                        // GML authority axis order for WGS84 is latitude, longitude.
                        // Other geographic CRS require Desktop's full axis metadata support.
                        boolean swap=source.equals("EPSG:4326");
                        if(!swap&&!source.equals("EPSG:2100")&&!source.equals("EPSG:3857")&&!source.matches("EPSG:32[67][0-9]{2}"))throw new IllegalArgumentException("GML CRS axis order requires Desktop import");
                        for(int i=0;i<values.length;i+=2){double x=Double.parseDouble(values[i]),y=Double.parseDouble(values[i+1]);ring.put(new JSONArray().put(swap?y:x).put(swap?x:y));}
                    }
                    rings.put(ring);capture=null;
                }
                if(tag.equals("Polygon")){if(rings==null||rings.length()==0)throw new IllegalArgumentException("Empty polygon");polygons.put(rings);rings=null;}
            }
        }
        if(source.isEmpty()||polygons.length()==0)throw new IllegalArgumentException("Polygon and source CRS required");
        if(!declared.isBlank()&&!source.equals(epsg(declared)))throw new IllegalArgumentException("Declared/file CRS conflict");
        return ParcelGeometry.normalize(new JSONObject().put("type",polygons.length()==1?"Polygon":"MultiPolygon").put("coordinates",polygons.length()==1?polygons.getJSONArray(0):polygons).toString(),source);
    }
    private static String epsg(String value){
        String source=value.trim();if(source.toLowerCase(Locale.ROOT).startsWith("urn:ogc:def:crs:epsg:"))source="EPSG:"+source.substring(source.lastIndexOf(':')+1);
        return ParcelGeometry.crs(source);
    }
}
