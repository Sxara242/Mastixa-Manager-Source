package gr.mastixa.manager;

import java.util.*;
import java.nio.charset.StandardCharsets;
import org.json.*;

/** Immutable geometry snapshot shared by preview and all export formats. */
final class CoordinateExport {
    record Parcel(String id,String name,String kaek,String source,ParcelGeometry geometry){}
    static List<Parcel> snapshot(FarmStore farm,Collection<String> selected){
        var result=new ArrayList<Parcel>();var geo=new GeoStore(farm);var fields=new HashMap<String,FarmStore.Field>();int count=0;
        var database=farm.getReadableDatabase();database.beginTransaction();try{
            for(var field:farm.fields())fields.put(field.id(),field);
            for(String id:new LinkedHashSet<>(selected)){var row=geo.parcel(id);var field=fields.get(id);if(row==null||field==null)throw new IllegalArgumentException("Selected field has no saved geometry");var geometry=GeoStore.geometry(row);count+=ParcelGeometry.vertices(geometry.original).size();if(count>100000)throw new IllegalArgumentException("Export exceeds 100000 vertices; select fewer fields");result.add(new Parcel(id,field.name(),field.kaek(),row.payload().optString("geometry_source"),geometry));}
            if(result.isEmpty())throw new IllegalArgumentException("Select fields with saved boundaries");database.setTransactionSuccessful();return List.copyOf(result);
        }finally{database.endTransaction();}
    }
    static List<String[]> table(List<Parcel> parcels,boolean source){
        var rows=new ArrayList<String[]>();rows.add(new String[]{"Field Name","KAEK","Coordinate System","EPSG","Area (m²)","Perimeter (m)","Vertex count","Part","Ring","Vertex",source?"X / Longitude":"Latitude",source?"Y / Latitude":"Longitude"});
        for(var parcel:parcels){var g=parcel.geometry();var vertices=ParcelGeometry.vertices(source?g.original:g.wgs84);
            for(var v:vertices)rows.add(new String[]{parcel.name(),parcel.kaek(),source?"Original source XY":"WGS84 / GPS",source?g.sourceCrs:"EPSG:4326",number(g.area,2),number(g.perimeter,2),Integer.toString(vertices.size()),Integer.toString(v.part()),Integer.toString(v.ring()),Integer.toString(v.index()),number(source?v.x():v.y(),8),number(source?v.y():v.x(),8)});
        }return rows;
    }
    private static String number(double value,int precision){return String.format(Locale.ROOT,"%."+precision+"f",value);}
    static String filename(List<Parcel> parcels,boolean source,String extension){
        if(!List.of("csv","xlsx","pdf","geojson","kml").contains(extension))throw new IllegalArgumentException("Unsupported format");
        String name=parcels.size()==1?parcels.get(0).name()+"_KAEK_"+parcels.get(0).kaek():"Mastixa_"+parcels.size()+"_fields";
        name=name.replaceAll("[<>:\"/\\\\|?*\\p{Cntrl}]","_").replaceAll("[ .]+$","");if(name.length()>100)name=name.substring(0,100);if(name.isBlank())name="Mastixa";
        if(name.toUpperCase(Locale.ROOT).matches("(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\\..*)?"))name="_"+name;
        return name+"_coordinates_"+(source?"source":"WGS84")+"."+extension;
    }
    private static JSONObject properties(Parcel parcel)throws JSONException{var g=parcel.geometry();return new JSONObject().put("field_id",parcel.id()).put("field_name",parcel.name()).put("kaek",parcel.kaek()).put("geometry_source",parcel.source()).put("source_crs",g.sourceCrs).put("coordinate_system","WGS84").put("epsg","EPSG:4326").put("area_m2",g.area).put("perimeter_m",g.perimeter).put("vertex_count",ParcelGeometry.vertices(g.original).size());}
    private static byte[] csv(List<String[]> rows){var text=new StringBuilder("\uFEFF");for(int r=0;r<rows.size();r++){var row=rows.get(r);for(int c=0;c<row.length;c++){if(c>0)text.append(';');String value=row[c];if((r==0||c<4)&&!value.stripLeading().isEmpty()&&"=+-@".indexOf(value.stripLeading().charAt(0))>=0)value="'"+value;text.append('"').append(value.replace("\"","\"\"")).append('"');}text.append("\r\n");}return text.toString().getBytes(StandardCharsets.UTF_8);}
    private static String xml(String value){var clean=new StringBuilder();value.codePoints().filter(c->c==9||c==10||c==13||(c>=32&&c<=0xd7ff)||(c>=0xe000&&c<=0xfffd)||(c>=0x10000&&c<=0x10ffff)).forEach(clean::appendCodePoint);return clean.toString().replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace("\"","&quot;");}
    static byte[] encode(List<Parcel> parcels,boolean source,String extension)throws Exception{
        if(extension.equals("csv"))return csv(table(parcels,source));
        if(extension.equals("xlsx"))return ReportStore.xlsx(table(parcels,source),"Όλες οι κορυφές",true);
        if(extension.equals("pdf")){
            var rows=new ArrayList<String[]>();int count=0;
            for(var parcel:parcels){var g=parcel.geometry();var vertices=table(List.of(parcel),source);count+=vertices.size()-1;if(count>20000)throw new IllegalArgumentException("PDF exceeds 20000 vertices; select fewer fields");
                rows.add(new String[]{"Field / Αγροτεμάχιο",parcel.name()});rows.add(new String[]{"KAEK",parcel.kaek()});rows.add(new String[]{source?"Original source XY":"WGS84 / GPS",source?g.sourceCrs:"EPSG:4326"});rows.add(new String[]{"Area (m²)",number(g.area,2),"Perimeter (m)",number(g.perimeter,2),"Vertices",Integer.toString(vertices.size()-1)});rows.add(new String[]{"Source",parcel.source(),"Source CRS",g.sourceCrs});rows.add(new String[]{"Part/Ring/Vertex",vertices.get(0)[10],vertices.get(0)[11]});
                for(var row:vertices.subList(1,vertices.size()))rows.add(new String[]{row[7]+"/"+row[8]+"/"+row[9],row[10],row[11]});rows.add(new String[]{" "});
            }return ReportStore.pdf(rows);
        }
        if(extension.equals("geojson")){var features=new JSONArray();for(var parcel:parcels)features.put(new JSONObject().put("type","Feature").put("id",parcel.id()).put("properties",properties(parcel)).put("geometry",new JSONObject(parcel.geometry().wgs84)));return new JSONObject().put("type","FeatureCollection").put("features",features).toString().getBytes(StandardCharsets.UTF_8);}
        if(extension.equals("kml")){var text=new StringBuilder("<?xml version=\"1.0\" encoding=\"UTF-8\"?><kml xmlns=\"http://www.opengis.net/kml/2.2\"><Document>");
            for(var parcel:parcels){text.append("<Placemark><name>").append(xml(parcel.name())).append("</name><ExtendedData>");var properties=properties(parcel);for(var keys=properties.keys();keys.hasNext();){String key=keys.next();text.append("<Data name=\"").append(key).append("\"><value>").append(xml(properties.get(key).toString())).append("</value></Data>");}text.append("</ExtendedData>");var polygons=ParcelGeometry.parts(new JSONObject(parcel.geometry().wgs84));if(polygons.length()>1)text.append("<MultiGeometry>");
                for(int p=0;p<polygons.length();p++){text.append("<Polygon>");var polygon=polygons.getJSONArray(p);for(int r=0;r<polygon.length();r++){String kind=r==0?"outerBoundaryIs":"innerBoundaryIs";text.append('<').append(kind).append("><LinearRing><coordinates>");var ring=polygon.getJSONArray(r);for(int v=0;v<ring.length();v++){var xy=ring.getJSONArray(v);text.append(number(xy.getDouble(0),8)).append(',').append(number(xy.getDouble(1),8)).append(",0 ");}text.append("</coordinates></LinearRing></").append(kind).append('>');}text.append("</Polygon>");}if(polygons.length()>1)text.append("</MultiGeometry>");text.append("</Placemark>");
            }return text.append("</Document></kml>").toString().getBytes(StandardCharsets.UTF_8);
        }throw new IllegalArgumentException("Unsupported export format");
    }
}
