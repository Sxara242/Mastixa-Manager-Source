package gr.mastixa.manager;

import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import static org.junit.Assert.*;

public class FieldCardProjectionTest {
    private final android.content.Context context=InstrumentationRegistry.getInstrumentation().getTargetContext();

    private ActivityStore.Activity watering(String field,String description){
        return new ActivityStore.Activity(null,"2026-09-08",field,"Πότισμα","Ολοκληρώθηκε",30,0,"",0,"",0,"","Water note","",0,0,"",description,"","");
    }

    @Test public void fieldCardUsesSharedProjectionWithGisOrderingAndFieldIsolation() throws Exception {
        String name="field-card-projection.db";context.deleteDatabase(name);
        try(var store=new FarmStore(context,name)){
            store.addField("Field A",1);
            store.addField("Field B",1);
            String fieldA=store.fields().stream().filter(f->f.name().equals("Field A")).findFirst().orElseThrow().id();
            String fieldB=store.fields().stream().filter(f->f.name().equals("Field B")).findFirst().orElseThrow().id();

            var activities=new ActivityStore(store);
            activities.save(watering(fieldA,"Water A"));
            activities.save(watering(fieldB,"Other field"));

            var geo=new GeoStore(store);
            String point=geo.savePoint(null,fieldA,"note","GIS note","Observed on site",25.1,38.1,3,0);
            store.getWritableDatabase().execSQL("UPDATE gis_records SET created_at=? WHERE id=?",new Object[]{1788955200000L,point});

            var rows=new ReportStore(store,true).report(
                "Καρτέλα Αγροτεμαχίου",
                new ReportStore.Filter("","",fieldA,"","")
            );

            int gis=-1,irrigation=-1;
            for(int i=0;i<rows.size();i++){
                String left=rows.get(i)[0],right=rows.get(i)[1];
                if(left.contains("GIS observation")&&right.contains("GIS note"))gis=i;
                if(left.contains(" · Irrigation")&&right.contains("Water A"))irrigation=i;
                assertFalse(left+" | "+right,(left+" "+right).contains("Other field"));
            }
            assertTrue("GIS projection row missing",gis>=0);
            assertTrue("Irrigation projection row missing",irrigation>=0);
            assertTrue("Projection order must be preserved",gis<irrigation);
            assertTrue(rows.get(gis)[0].startsWith("2026-09-09 12:00 UTC"));
            long irrigationTimelineRows=rows.stream().filter(r->r[0].contains(" · Irrigation")).count();
            assertEquals("Old raw-table timeline row must not duplicate projection",1,irrigationTimelineRows);
        } finally { context.deleteDatabase(name); }
    }
}
