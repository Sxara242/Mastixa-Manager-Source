package gr.mastixa.manager;

import android.app.Activity;
import android.content.Intent;
import android.os.SystemClock;
import android.view.View;
import android.view.ViewGroup;
import android.widget.*;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import java.time.LocalDate;
import java.util.*;
import static org.junit.Assert.*;

/** Profile-language display checks; fixtures live only in the isolated checks app. */
public class RemainingLocalizationUiTest {
    private final android.app.Instrumentation i=InstrumentationRegistry.getInstrumentation();
    private final android.content.Context context=i.getTargetContext();
    private Object field(Object target,String name) {
        try { var f=target.getClass().getDeclaredField(name);f.setAccessible(true);return f.get(target); }
        catch(ReflectiveOperationException e) { throw new AssertionError(e); }
    }
    private Object invoke(Object target,String name,Class<?>[] types,Object...args) {
        try { var m=target.getClass().getDeclaredMethod(name,types);m.setAccessible(true);return m.invoke(target,args); }
        catch(ReflectiveOperationException e) { throw new AssertionError(e); }
    }
    private void set(Object target,String name,Object value) {
        try { var f=target.getClass().getDeclaredField(name);f.setAccessible(true);f.set(target,value); }
        catch(ReflectiveOperationException e) { throw new AssertionError(e); }
    }
    private List<View> views(View root) {
        var result=new ArrayList<View>();result.add(root);
        if(root instanceof ViewGroup group)for(int n=0;n<group.getChildCount();n++)result.addAll(views(group.getChildAt(n)));
        return result;
    }
    private View topWindow() {
        var roots=android.view.inspector.WindowInspector.getGlobalWindowViews();
        assertFalse("Expected an activity/dialog window",roots.isEmpty());return roots.get(roots.size()-1);
    }
    private void dialogButton(int id) {
        var button=(Button)topWindow().findViewById(id);assertNotNull("Missing dialog button "+id,button);button.performClick();
    }
    private Activity launch(ProfileStore.Profile profile,Class<? extends Activity> type,String fieldId) {
        assertTrue(context.getPackageName().endsWith(".checks"));
        i.runOnMainSync(()->{UserSession.clear();UserSession.signIn(profile);});
        return i.startActivitySync(new Intent(context,type).putExtra("field_id",fieldId)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));
    }
    private void finish(Activity activity) {
        i.runOnMainSync(()->{if(activity!=null)activity.finish();});i.waitForIdleSync();
        i.runOnMainSync(UserSession::clear);
    }
    private String preview(Activity activity,String expected) throws Exception {
        long deadline=SystemClock.elapsedRealtime()+10000;String[] actual={""};boolean[] ready={false};
        do {
            i.runOnMainSync(()->{actual[0]=((TextView)field(activity,"preview")).getText().toString();
                ready[0]=((Button)field(activity,"save")).isEnabled()&&actual[0].contains(expected);});
            if(ready[0])return actual[0];
            Thread.sleep(40);
        } while(SystemClock.elapsedRealtime()<deadline);
        throw new AssertionError("Expected completed preview containing "+expected+"; actual: "+actual[0]);
    }
    private String visibleText(View root) {
        var text=new StringBuilder();if(root instanceof TextView v)text.append(v.getText()).append('\n');
        if(root instanceof ViewGroup group)for(int n=0;n<group.getChildCount();n++)text.append(visibleText(group.getChildAt(n)));
        return text.toString();
    }

    @Test public void coordinatePreviewUsesProfileLanguageWithoutChangingExportData() throws Exception {
        var base=new ProfileStore.Profile("localization-coordinate","User backup / Χωράφι","test","el");
        assertTrue(context.getPackageName().endsWith(".checks"));context.deleteDatabase(base.database());
        String id;byte[] before;List<CoordinateExport.Parcel> original;
        try(var farm=new FarmStore(context,base.database())) {
            farm.addField("Χωράφι / Original source X Y — user",1);id=farm.fields().get(0).id();
            new GeoStore(farm).saveGeometry(id,ParcelGeometry.manual("500000 4200000\n500100 4200000\n500100 4200100\n500000 4200100","EPSG:2100"),"manual","",0);
            original=CoordinateExport.snapshot(farm,List.of(id));before=LocalBackup.snapshot(farm);
        }
        try {
            for(String language:List.of("el","en")) {
                boolean en=language.equals("en");Activity screen=null;
                try {
                    screen=launch(new ProfileStore.Profile(base.id(),base.name(),base.username(),language),CoordinateExportActivity.class,id);var a=screen;
                    String text=preview(a,en?"WGS84 Latitude / Longitude\n":"WGS84 Γεωγραφικό πλάτος / μήκος\n");
                    assertTrue(text.contains(original.get(0).name()));
                    assertTrue(text.contains(en?"Part/Ring/Vertex\n":"Τμήμα/Δακτύλιος/Κορυφή\n"));
                    i.runOnMainSync(()->assertEquals(en?"WGS84 · Latitude / Longitude":"WGS84 · Γεωγραφικό πλάτος / μήκος",((Spinner)field(a,"coordinates")).getItemAtPosition(0)));
                    if(!en){assertFalse(text.contains("WGS84 Latitude / Longitude\n"));assertFalse(text.contains("Part/Ring/Vertex\n"));}
                    i.runOnMainSync(()->((Spinner)field(a,"coordinates")).setSelection(1));i.waitForIdleSync();
                    text=preview(a,en?"\nOriginal source X Y\n":"\nΑρχικές συντεταγμένες X Y\n");
                    if(!en)assertFalse(text.contains("\nOriginal source X Y\n")); // User name above must stay verbatim.
                    assertTrue(text.contains("EPSG:2100"));
                    i.runOnMainSync(()->((Spinner)field(a,"format")).setSelection(3));i.waitForIdleSync();
                    text=preview(a,en?"source CRS in metadata.":"αρχικό CRS στα μεταδεδομένα.");
                    if(!en)assertFalse(text.contains("GeoJSON / KML: WGS84 longitude,latitude; source CRS in metadata."));
                    try(var farm=new FarmStore(context,base.database())) {
                        var current=CoordinateExport.snapshot(farm,List.of(id));assertArrayEquals(before,LocalBackup.snapshot(farm));
                        for(boolean source:new boolean[]{false,true}) {
                            var expected=CoordinateExport.table(original,source);var actual=CoordinateExport.table(current,source);
                            assertEquals(expected.size(),actual.size());for(int n=0;n<expected.size();n++)assertArrayEquals(expected.get(n),actual.get(n));
                            assertArrayEquals(new String[]{"Field Name","KAEK","Coordinate System","EPSG","Area (m²)","Perimeter (m)","Vertex count","Part","Ring","Vertex",source?"X / Longitude":"Latitude",source?"Y / Latitude":"Longitude"},actual.get(0));
                            for(String format:List.of("csv","geojson","kml")) {
                                assertArrayEquals(CoordinateExport.encode(original,source,format),CoordinateExport.encode(current,source,format));
                                assertEquals(CoordinateExport.filename(original,source,format),CoordinateExport.filename(current,source,format));
                            }
                        }
                    }
                } finally { finish(screen); }
            }
        } finally { context.deleteDatabase(base.database()); }
    }

    @Test public void mapDescriptionAndTrackLabelsFollowProfileWithoutTranslatingStoredStates() throws Exception {
        for(String language:List.of("el","en")) {
            boolean en=language.equals("en");var profile=new ProfileStore.Profile("localization-track-"+language,"Track test","test",language);
            assertTrue(context.getPackageName().endsWith(".checks"));context.deleteDatabase(profile.database());String id;
            try(var farm=new FarmStore(context,profile.database())){farm.addField("Τοπικό backup / User field",1);id=farm.fields().get(0).id();}
            Activity screen=null;
            try {
                screen=launch(profile,ParcelMapActivity.class,id);var a=screen;
                i.runOnMainSync(()->{
                    assertEquals(en?"Parcel map":"Χάρτης αγροτεμαχίου",((View)field(a,"map")).getContentDescription());
                    var track=(GpsTrack)field(a,"track");var farm=(FarmStore)field(a,"farm");
                    String title="recording / Τοπικό backup — User";track.start(title,100000,1000);String trackId=track.current().id();
                    String[] states={"recording","paused","stopped"};String[] labels=en?new String[]{"Recording","Paused","Stopped"}:new String[]{"Καταγραφή","Σε παύση","Σταματημένο"};
                    for(int n=0;n<states.length;n++) {
                        if(n>0)track.change(states[n],100000+n*1000,1000+n*1000);
                        try {
                            byte[] before=LocalBackup.snapshot(farm);invoke(a,"showTrack",new Class[]{});
                            assertTrue(((TextView)field(a,"trackStatus")).getText().toString().startsWith(title+" · "+labels[n]+" · "));
                            assertArrayEquals(before,LocalBackup.snapshot(farm));
                        } catch(Exception e){throw new AssertionError(e);}
                        var stored=new GeoStore(farm).records(id,"track");assertEquals(1,stored.size());assertEquals(trackId,stored.get(0).id());
                        assertEquals(states[n],stored.get(0).payload().optString("state"));assertEquals(title,stored.get(0).payload().optString("title"));
                    }
                });
            } finally { finish(screen);context.deleteDatabase(profile.database()); }
        }
    }

    @Test public void maintenanceAlertWordingLeavesIdentityDatesAndServiceDataUntouched() throws Exception {
        assertTrue(context.getPackageName().endsWith(".checks"));String db="localization-maintenance.db";context.deleteDatabase(db);
        try(var farm=new FarmStore(context,db)) {
            var work=new WorkStore(farm);var today=LocalDate.of(2026,9,13);
            String equipment=work.saveEquipment(new WorkStore.Equipment(null,"service / backup — user μηχάνημα","","","","","","hours",100,"Ενεργό","",""));
            work.saveService(new WorkStore.Service(null,equipment,"2026-09-01","service — user type",0,100,"","","2026-09-12",null,"",""));
            byte[] before=LocalBackup.snapshot(farm);
            for(var date:List.of(today,today.minusDays(2))) {
                var el=new DashboardStore(farm,false).alerts(date);var en=new DashboardStore(farm,true).alerts(date);assertEquals(1,el.size());assertEquals(1,en.size());
                var greek=el.get(0);var english=en.get(0);
                assertEquals((date.equals(today)?"Εκπρόθεσμη συντήρηση: ":"Πλησιάζει συντήρηση: ")+"2026-09-12",greek.message());
                assertEquals((date.equals(today)?"Overdue service: ":"Service approaching: ")+"2026-09-12",english.message());
                assertFalse(greek.message().contains("service"));assertEquals("equipment:"+equipment,greek.id());
                assertEquals(english.id(),greek.id());assertEquals(english.recordId(),greek.recordId());assertEquals(english.kind(),greek.kind());assertEquals(english.severity(),greek.severity());assertEquals(english.date(),greek.date());
                assertEquals("service / backup — user μηχάνημα",greek.subject());assertEquals(greek.subject(),english.subject());
            }
            assertEquals("service — user type",work.services().get(0).service_type());assertArrayEquals(before,LocalBackup.snapshot(farm));
        } finally { context.deleteDatabase(db); }
    }

    @Test public void yearLockExplanationIsLocalizedAndBackupNavigationIdRemainsCanonical() throws Exception {
        for(String language:List.of("el","en")) {
            var profile=new ProfileStore.Profile("localization-year-"+language,"backup — User","test",language);
            assertTrue(context.getPackageName().endsWith(".checks"));context.deleteDatabase(profile.database());Activity screen=null;
            try {
                screen=launch(profile,MainActivity.class,"");var a=screen;
                i.runOnMainSync(()->{
                    invoke(a,"navigate",new Class[]{String.class},"Κλείδωμα Έτους");
                    String text=visibleText((View)field(a,"content"));
                    assertTrue(text.contains(language.equals("en")?"Full backup restore also replaces year locks.":"Η πλήρης επαναφορά αντιγράφου ασφαλείας αντικαθιστά και τα κλειδώματα."));
                    if(language.equals("el"))assertFalse(text.contains("backup"));
                    invoke(a,"navigate",new Class[]{String.class},"Τοπικό backup");assertEquals("Τοπικό backup",field(a,"currentPage"));
                    assertTrue(Arrays.stream(PageCatalog.GROUPS).flatMap(Arrays::stream).anyMatch("Τοπικό backup"::equals));
                    assertEquals("backup — User",UserSession.profile.name());
                });
            } finally { finish(screen);context.deleteDatabase(profile.database()); }
        }
    }

    @Test public void manualHintKeepsCoordinateSyntaxAndOrderingInBothLanguages() throws Exception {
        for(String language:List.of("el","en")) {
            boolean en=language.equals("en");var profile=new ProfileStore.Profile("localization-manual-"+language,"Manual test","test",language);
            assertTrue(context.getPackageName().endsWith(".checks"));context.deleteDatabase(profile.database());String id;
            try(var farm=new FarmStore(context,profile.database())){farm.addField("User longitude / latitude",1);id=farm.fields().get(0).id();}
            Activity screen=null;
            try {
                screen=launch(profile,ParcelMapActivity.class,id);var a=screen;
                for(String crs:List.of("EPSG:4326","EPSG:2100")) {
                    boolean wgs=crs.equals("EPSG:4326");String coordinates=wgs?"26 38\n26.001 38\n26.001 38.001\n26 38.001":"500000 4200000\n500100 4200000\n500100 4200100\n500000 4200100";
                    i.runOnMainSync(()->invoke(a,"manual",new Class[]{}));i.waitForIdleSync();
                    i.runOnMainSync(()->{
                        var inputs=views(topWindow()).stream().filter(v->v instanceof EditText).map(v->(EditText)v).toList();assertEquals(2,inputs.size());
                        String hint=inputs.get(1).getHint().toString();
                        assertEquals(en?"Each line: X Y / longitude latitude · decimal dot":"Ανά γραμμή: X Y ή γεωγραφικό μήκος και πλάτος · δεκαδική τελεία",hint);
                        if(!en){assertFalse(hint.contains("longitude"));assertFalse(hint.contains("latitude"));}
                        inputs.get(0).setText(crs);inputs.get(1).setText(coordinates);dialogButton(android.R.id.button1);
                    });i.waitForIdleSync();
                    i.runOnMainSync(()->{
                        String text=visibleText(topWindow());assertTrue(text,text.contains("User longitude / latitude"));assertTrue(text,text.contains(crs));
                        assertTrue(text,text.contains(wgs?"26.00000000  38.00000000":"500000.00000000  4200000.00000000"));
                        dialogButton(android.R.id.button2); // Preview only: no synthetic or real record is saved.
                    });i.waitForIdleSync();
                }
                try(var farm=new FarmStore(context,profile.database())){assertNull(new GeoStore(farm).parcel(id));}
            } finally { finish(screen);context.deleteDatabase(profile.database()); }
        }
    }

    @Test public void mapStatusUsesGreekWordingAndKeepsEnglishAndAttribution() throws Exception {
        for(String language:List.of("el","en")) {
            boolean en=language.equals("en");var profile=new ProfileStore.Profile("localization-status-"+language,"Status test","test",language);
            assertTrue(context.getPackageName().endsWith(".checks"));context.deleteDatabase(profile.database());String id;
            try(var farm=new FarmStore(context,profile.database())){farm.addField("User internet",1);id=farm.fields().get(0).id();}
            Activity screen=null;
            try {
                screen=launch(profile,ParcelMapActivity.class,id);var a=screen;
                i.runOnMainSync(()->{
                    var connectivity=(android.net.ConnectivityManager)field(a,"connectivity");
                    try {
                        invoke(a,"showMapStatus",new Class[]{});
                        assertEquals(en?"Offline map · Boundaries and GPS work without internet.":"Χάρτης εκτός σύνδεσης · Τα όρια και το GPS λειτουργούν χωρίς σύνδεση στο διαδίκτυο.",((TextView)field(a,"mapStatus")).getText().toString());
                        set(a,"basemapChoice",1);
                        // Exercise absent connectivity without changing device/network settings.
                        set(a,"connectivity",null);invoke(a,"showMapStatus",new Class[]{});
                        String suffix="\n"+AndroidBasemap.OSM.attribution()+"\n"+(en?"Boundaries and GPS work without internet.":"Όρια και GPS λειτουργούν χωρίς σύνδεση στο διαδίκτυο.");
                        assertEquals((en?"Offline · Only available cached tiles.":"Εκτός σύνδεσης · Μόνο διαθέσιμα πλακίδια προσωρινής μνήμης.")+suffix,((TextView)field(a,"mapStatus")).getText().toString());
                        set(a,"connectivity",connectivity);invoke(a,"showMapStatus",new Class[]{});
                        var caps=connectivity==null?null:connectivity.getNetworkCapabilities(connectivity.getActiveNetwork());
                        boolean online=caps!=null&&caps.hasCapability(android.net.NetworkCapabilities.NET_CAPABILITY_VALIDATED);
                        String prefix=online?(en?"OSM online · Blank tiles: loading or unavailable.":"OSM σε σύνδεση · Κενά πλακίδια: αναμονή ή μη διαθέσιμα."):(en?"Offline · Only available cached tiles.":"Εκτός σύνδεσης · Μόνο διαθέσιμα πλακίδια προσωρινής μνήμης.");
                        String text=((TextView)field(a,"mapStatus")).getText().toString();assertEquals(prefix+suffix,text);
                        if(!en)for(String word:List.of("Offline","online","internet"))assertFalse(text,text.contains(word));
                        android.util.Log.i("LocalizationStatusTest",language+" validated network branch="+online);
                    } finally {set(a,"connectivity",connectivity);set(a,"basemapChoice",0);}
                });
            } finally { finish(screen);context.deleteDatabase(profile.database()); }
        }
    }

    @Test public void profileCreationHelpUsesSelectedLanguageWithoutChangingAccounts() throws Exception {
        assertTrue(context.getPackageName().endsWith(".checks"));List<ProfileStore.Profile> before;
        try(var registry=new ProfileStore(context)){before=registry.profiles();}
        Activity screen=null;
        try {
            i.runOnMainSync(UserSession::clear);
            screen=i.startActivitySync(new Intent(context,WelcomeActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));var a=screen;
            for(String language:List.of("el","en")) {
                i.runOnMainSync(()->{set(a,"language",language);set(a,"creating",true);invoke(a,"render",new Class[]{});});i.waitForIdleSync();
                i.runOnMainSync(()->{
                    String text=visibleText((View)field(a,"body"));
                    assertTrue(text,text.contains(language.equals("en")?"Username: 3–40 Latin letters, numbers or . _ -\nPassword: 8–128 characters.":"Όνομα χρήστη: 3–40 λατινικοί χαρακτήρες, αριθμοί ή . _ -\nΚωδικός: 8–128 χαρακτήρες."));
                    if(language.equals("el"))assertFalse(text.contains("Username:"));
                });
            }
            try(var registry=new ProfileStore(context)){assertEquals(before,registry.profiles());}
        } finally { finish(screen); }
    }

    @Test public void providerWordingPreservesEnglishCapabilitiesBoundsAndEndpoint() {
        assertArrayEquals(new String[]{"Neutral / offline","OSM street map","Google satellite (setup required)","Copernicus / Sentinel (setup required)"},MapProviders.labels("en"));
        assertArrayEquals(new String[]{"Ουδέτερο / εκτός σύνδεσης","Οδικός χάρτης OSM","Google δορυφορικό (ρύθμιση)","Copernicus / Sentinel (ρύθμιση)"},MapProviders.labels("el"));
        for(String label:MapProviders.labels("el"))assertFalse(label.contains("offline"));
        String[] descriptions={
            "Offline neutral background. Boundaries, points and GNSS remain available.",
            "OSM downloads only visible map tiles. The provider receives the viewed area. HTTP caching follows server expiry; offline packs are not available.",
            "Requires official Google SDK/API configuration and restricted credentials. No imagery download or boundary digitization.",
            "Requires a configured, licensed Copernicus/Sentinel imagery service."
        };
        for(int index=0;index<descriptions.length;index++) {
            assertEquals(descriptions[index],MapProviders.description(index,"en"));
            assertFalse(MapProviders.description(index,"el").contains("offline"));
        }
        assertEquals("Ουδέτερο υπόβαθρο εκτός σύνδεσης. Όρια, σημεία και GNSS παραμένουν διαθέσιμα.",MapProviders.description(0,"el"));
        assertTrue(MapProviders.description(1,"el").endsWith("δεν διατίθενται πακέτα εκτός σύνδεσης."));
        var geometry=ParcelGeometry.manual("26 38\n26.001 38\n26.001 38.001\n26 38.001","EPSG:4326");
        String original=geometry.original;double[] bbox=geometry.bbox.clone();
        for(var selected:new ParcelGeometry[]{null,geometry}) {
            String box=selected==null?"—":"25.998000, 37.998000 — 26.003000, 38.003000";
            assertEquals("Download blocked: no configured provider permits offline packs. Public OSM bulk downloads and Google imagery caching are not enabled.\nBBox + margin: "+box+"\nProgress: 0% · Storage: 0 bytes\nLast update: — · No pack to delete.",MapProviders.offlinePack(selected,"en"));
            String el=MapProviders.offlinePack(selected,"el");assertFalse(el.contains("offline"));
            assertTrue(el.contains("πάροχος με άδεια για πακέτα εκτός σύνδεσης."));
            assertTrue(el.endsWith("BBox + περιθώριο: "+box+"\nΠρόοδος: 0% · Χώρος: 0 bytes\nΤελευταία ενημέρωση: — · Δεν υπάρχει πακέτο για διαγραφή."));
        }
        assertEquals(original,geometry.original);assertArrayEquals(bbox,geometry.bbox,0);
        String endpoint="https://gis.ktimanet.gr/inspire/rest/services/cadastralparcels/CadastralParcel/MapServer/0";
        assertEquals("Live verification blocked: this published ArcGIS layer and its JSON metadata returned HTTP 404 from the test environment (2026-09-09). Its fields, CRS and KAEK query capability remain unverified. Use file/manual import. This is separate from the old INSPIRE portal's 404.\n"+endpoint,MapProviders.cadastreMessage("en"));
        String el=MapProviders.cadastreMessage("el");
        for(String word:List.of(" layer "," metadata "," portal"))assertFalse(el.contains(word));
        for(String text:List.of("επίπεδο ArcGIS","μεταδεδομένα JSON","πύλης INSPIRE","HTTP 404","CRS","ΚΑΕΚ","2026-09-09"))assertTrue(el.contains(text));
        assertTrue(el.endsWith("\n"+endpoint));assertEquals(el.indexOf(endpoint),el.lastIndexOf(endpoint));
    }

    @Test public void offlineButtonWordingKeepsDialogAndDomainValues() throws Exception {
        for(String language:List.of("el","en")) {
            boolean en=language.equals("en");var profile=new ProfileStore.Profile("localization-provider-"+language,"Provider test","test",language);
            assertTrue(context.getPackageName().endsWith(".checks"));context.deleteDatabase(profile.database());String id;byte[] before;
            try(var farm=new FarmStore(context,profile.database())){farm.addField("offline — User αγροτεμάχιο",1);id=farm.fields().get(0).id();before=LocalBackup.snapshot(farm);}
            Activity screen=null;
            try {
                screen=launch(profile,ParcelMapActivity.class,id);var a=screen;
                i.runOnMainSync(()->{
                    var body=(View)field(a,"body");String expected=en?"Download offline map":"Λήψη χάρτη για χρήση εκτός σύνδεσης";
                    var button=views(body).stream().filter(v->v instanceof Button b&&expected.contentEquals(b.getText())).map(v->(Button)v).findFirst().orElseThrow(()->new AssertionError("Missing button "+expected));
                    if(!en)assertFalse(button.getText().toString().contains("offline"));
                    assertTrue(visibleText(body).contains("offline — User αγροτεμάχιο"));button.performClick();
                });i.waitForIdleSync();
                i.runOnMainSync(()->{assertEquals(MapProviders.offlinePack(null,language),((TextView)topWindow().findViewById(android.R.id.message)).getText().toString());dialogButton(android.R.id.button1);});i.waitForIdleSync();
                try(var farm=new FarmStore(context,profile.database())){assertArrayEquals(before,LocalBackup.snapshot(farm));}
            } finally { finish(screen);context.deleteDatabase(profile.database()); }
        }
    }

    @Test public void gisDatesUseProfileLocaleAndPreserveSourceTimestampsAndExports() throws Exception {
        Locale originalLocale=Locale.getDefault();String zone=TimeZone.getDefault().getID();
        final long epoch=java.time.Instant.parse("2026-01-02T03:04:05Z").toEpochMilli();
        for(String language:List.of("el","en")) {
            boolean en=language.equals("en");var profile=new ProfileStore.Profile("localization-dates-"+language,"Date test","test",language);
            assertTrue(context.getPackageName().endsWith(".checks"));context.deleteDatabase(profile.database());String id;byte[] before;byte[] exported;
            try(var farm=new FarmStore(context,profile.database())) {
                farm.addField("User Jan / Ιαν",1);id=farm.fields().get(0).id();var geo=new GeoStore(farm);
                geo.saveGeometry(id,ParcelGeometry.manual("26 38\n26.001 38\n26.001 38.001\n26 38.001","EPSG:4326"),"manual","2026-01-02T03:04:05Z",0);
                geo.savePoint(null,id,"note","User date","ISO 2026-01-02T03:04:05Z",26,38,5,0);
                var track=new GpsTrack(geo,id);track.start("User track",epoch,1000);track.change("stopped",epoch+1000,2000);
                before=LocalBackup.snapshot(farm);exported=CoordinateExport.encode(CoordinateExport.snapshot(farm,List.of(id)),false,"geojson");
            }
            Activity screen=null;
            try {
                // Profile locale must win over the process default; timezone is left untouched.
                Locale.setDefault(en?Locale.forLanguageTag("el-GR"):Locale.ENGLISH);
                screen=launch(profile,ParcelMapActivity.class,id);var a=screen;
                var locale=en?Locale.ENGLISH:Locale.forLanguageTag("el-GR");
                var formatter=java.text.DateFormat.getDateTimeInstance(java.text.DateFormat.MEDIUM,java.text.DateFormat.MEDIUM,locale);
                String expected=formatter.format(new Date(epoch));
                assertEquals(!en,expected.matches("(?s).*[\\p{IsGreek}].*"));
                i.runOnMainSync(()->{
                    assertEquals(expected,invoke(a,"formatUiDate",new Class[]{long.class},epoch));
                    var parcel=(GeoStore.Record)field(a,"parcel");assertTrue(((TextView)field(a,"metadata")).getText().toString().contains(formatter.format(new Date(parcel.updated()))));
                    var fix=new android.location.Location("test");fix.setTime(epoch);fix.setLatitude(38);fix.setLongitude(26);fix.setAccuracy(5);fix.setElapsedRealtimeNanos(SystemClock.elapsedRealtimeNanos());
                    set(a,"fix",fix);invoke(a,"showFix",new Class[]{});assertTrue(((TextView)field(a,"gpsStatus")).getText().toString().contains(expected));assertEquals(epoch,fix.getTime());
                    var row=((GeoStore)field(a,"geo")).records(id,"point").get(0);fix.setTime(row.created());
                    invoke(a,"pointForm",new Class[]{GeoStore.Record.class,android.location.Location.class},row,fix);
                });i.waitForIdleSync();
                i.runOnMainSync(()->{
                    var row=((GeoStore)field(a,"geo")).records(id,"point").get(0);
                    assertTrue(visibleText(topWindow()).contains(formatter.format(new Date(row.created()))));dialogButton(android.R.id.button2);
                });i.waitForIdleSync();
                i.runOnMainSync(()->invoke(a,"tracks",new Class[]{}));i.waitForIdleSync();
                i.runOnMainSync(()->{
                    var list=views(topWindow()).stream().filter(v->v instanceof ListView).map(v->(ListView)v).findFirst().orElseThrow();
                    list.performItemClick(list.getChildAt(0),0,list.getAdapter().getItemId(0));
                });i.waitForIdleSync();
                i.runOnMainSync(()->{assertTrue(visibleText(topWindow()).contains(expected));dialogButton(android.R.id.button1);});i.waitForIdleSync();
                try(var farm=new FarmStore(context,profile.database())) {
                    assertArrayEquals(before,LocalBackup.snapshot(farm));var geo=new GeoStore(farm);
                    assertEquals("2026-01-02T03:04:05Z",geo.parcel(id).payload().optString("geometry_source_date"));
                    assertEquals(epoch,geo.records(id,"track").get(0).payload().optLong("started_at"));
                    assertEquals(epoch+1000,geo.records(id,"track").get(0).payload().optLong("ended_at"));
                    assertArrayEquals(exported,CoordinateExport.encode(CoordinateExport.snapshot(farm,List.of(id)),false,"geojson"));
                }
                assertEquals(zone,TimeZone.getDefault().getID());
            } finally { finish(screen);Locale.setDefault(originalLocale);context.deleteDatabase(profile.database()); }
        }
    }
}
