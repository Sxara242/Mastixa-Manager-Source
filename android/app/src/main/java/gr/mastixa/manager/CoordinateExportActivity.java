package gr.mastixa.manager;

import android.app.*;
import android.content.*;
import android.os.*;
import android.view.*;
import android.widget.*;
import java.io.*;
import java.util.*;
import java.util.concurrent.*;

/** Preview a frozen selection, prepare privately, then use Android's document picker. */
public final class CoordinateExportActivity extends Activity {
    private static final int SAVE=203;
    private static final String[] FORMATS={"csv","xlsx","pdf","geojson","kml"};
    private ProfileStore.Profile profile;
    private final LinkedHashMap<String,CheckBox> choices=new LinkedHashMap<>();
    private List<CoordinateExport.Parcel> snapshot=List.of();
    private Spinner format,coordinates;
    private TextView preview;
    private Button save;
    private boolean ready;
    private int generation;
    private File pending;
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    // Only preview work may be cancelled by a selection change. Accepted saves must drain.
    private Future<?> task;
    private String w(String el,String en){return profile.language().equals("en")?en:el;}
    private int dp(int value){return Math.round(value*getResources().getDisplayMetrics().density);}
    private boolean authorised(){if(profile!=null&&UserSession.valid(this)&&UserSession.profile.id().equals(profile.id()))return true;startActivity(new Intent(this,WelcomeActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK));finish();return false;}
    private void message(String text){if(!isFinishing()&&!isDestroyed())new AlertDialog.Builder(this).setMessage(text).setPositiveButton(w("Εντάξει","OK"),null).show();}
    private Button button(LinearLayout parent,String title,Runnable action){var result=new Button(this);result.setText(title);result.setAllCaps(false);result.setMinHeight(dp(48));parent.addView(result);result.setOnClickListener(v->{if(authorised())action.run();});return result;}
    @Override public void onCreate(Bundle state){
        super.onCreate(state);profile=UserSession.valid(this)?UserSession.profile:null;if(!authorised())return;
        if(state!=null&&!profile.id().equals(state.getString("profile_id"))){File abandoned=preparedFile(state);if(abandoned!=null)abandoned.delete();state=null;}
        var scroll=new ScrollView(this);var body=new LinearLayout(this);body.setOrientation(LinearLayout.VERTICAL);body.setPadding(dp(16),dp(12),dp(16),dp(24));scroll.addView(body);setContentView(scroll);
        scroll.setOnApplyWindowInsetsListener((v,insets)->{if(Build.VERSION.SDK_INT>=30){var bars=insets.getInsets(WindowInsets.Type.systemBars());v.setPadding(bars.left,bars.top,bars.right,bars.bottom);}else v.setPadding(insets.getSystemWindowInsetLeft(),insets.getSystemWindowInsetTop(),insets.getSystemWindowInsetRight(),insets.getSystemWindowInsetBottom());return insets;});
        button(body,w("‹ Πίσω","‹ Back"),this::finish);var heading=new TextView(this);heading.setText(w("Εξαγωγή κορυφών / συντεταγμένων","Export vertices / coordinates"));heading.setTextSize(22);body.addView(heading);
        var selected=state==null?new ArrayList<String>():state.getStringArrayList("selected");if(selected==null)selected=new ArrayList<>();if(state==null&&getIntent().hasExtra("field_id"))selected.add(getIntent().getStringExtra("field_id"));
        try(var farm=new FarmStore(this,profile.database())){var available=new HashSet<String>();for(var row:new GeoStore(farm).records(null,"parcel"))available.add(row.fieldId());var fields=farm.fields();var note=new TextView(this);note.setText(available.size()+" / "+fields.size()+w(" αγροτεμάχια διαθέτουν όρια."," fields have saved boundaries."));body.addView(note);
            for(var field:fields)if(available.contains(field.id())){var checkbox=new CheckBox(this);checkbox.setText(field.name()+" · KAEK: "+field.kaek());checkbox.setChecked(selected.contains(field.id()));body.addView(checkbox);choices.put(field.id(),checkbox);checkbox.setOnCheckedChangeListener((v,b)->{if(ready)refresh();});}}
        button(body,w("Επιλογή όλων","Select all"),()->selectAll(true));button(body,w("Καμία επιλογή","Select none"),()->selectAll(false));
        format=new Spinner(this);format.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,new String[]{"CSV","XLSX","PDF","GeoJSON","KML"}));body.addView(format);
        coordinates=new Spinner(this);coordinates.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,new String[]{w("WGS84 · Γεωγραφικό πλάτος / μήκος","WGS84 · Latitude / Longitude"),w("Αρχικό CRS · X Y","Original source CRS · X Y")}));body.addView(coordinates);
        var listener=new AdapterView.OnItemSelectedListener(){public void onItemSelected(AdapterView<?> parent,View view,int position,long id){if(ready)refresh();}public void onNothingSelected(AdapterView<?> parent){}};format.setOnItemSelectedListener(listener);coordinates.setOnItemSelectedListener(listener);
        if(state!=null){format.setSelection(state.getInt("format"));coordinates.setSelection(state.getInt("coordinates"));pending=preparedFile(state);}
        preview=new TextView(this);preview.setTextSize(15);preview.setTextIsSelectable(true);preview.setPadding(0,dp(18),0,dp(18));body.addView(preview);save=button(body,w("Αποθήκευση αρχείου","Save file"),this::prepare);ready=true;refresh();
    }
    private File preparedFile(Bundle state){String name=state.getString("pending","");if(!name.matches("coordinates-[a-f0-9-]+\\.tmp"))return null;File file=new File(getCacheDir(),name);return file.isFile()?file:null;}
    private void selectAll(boolean checked){ready=false;for(var checkbox:choices.values())checkbox.setChecked(checked);ready=true;refresh();}
    private ArrayList<String> selected(){var ids=new ArrayList<String>();for(var item:choices.entrySet())if(item.getValue().isChecked())ids.add(item.getKey());return ids;}
    private boolean source(){return format.getSelectedItemPosition()<3&&coordinates.getSelectedItemPosition()==1;}
    private void refresh(){
        coordinates.setEnabled(format.getSelectedItemPosition()<3);save.setEnabled(false);snapshot=List.of();var ids=selected();int token=++generation;boolean source=source();boolean standardWgs=format.getSelectedItemPosition()>=3;if(task!=null)task.cancel(true);
        if(ids.isEmpty()){preview.setText(w("Επίλεξε αγροτεμάχια με αποθηκευμένα όρια.","Select fields with saved boundaries."));return;}
        preview.setText(w("Προετοιμασία προεπισκόπησης…","Preparing preview…"));
        task=worker.submit(()->{try{List<CoordinateExport.Parcel> values;try(var farm=new FarmStore(getApplicationContext(),profile.database())){values=CoordinateExport.snapshot(farm,ids);}var rows=CoordinateExport.table(values,source);var text=new StringBuilder();for(var parcel:values)text.append(parcel.name()).append(" · KAEK: ").append(parcel.kaek()).append(" · ").append(source?parcel.geometry().sourceCrs:"EPSG:4326").append(" · ").append(ParcelGeometry.vertices(parcel.geometry().original).size()).append(w(" κορυφές\n"," vertices\n"));text.append(source?w("Αρχικές συντεταγμένες X Y\n","Original source X Y\n"):w("WGS84 Γεωγραφικό πλάτος / μήκος\n","WGS84 Latitude / Longitude\n"));text.append(w("Τμήμα/Δακτύλιος/Κορυφή\n","Part/Ring/Vertex\n"));for(var row:rows.subList(1,Math.min(6,rows.size())))text.append(row[7]).append('/').append(row[8]).append('/').append(row[9]).append(" : ").append(row[10]).append(" : ").append(row[11]).append('\n');if(standardWgs)text.append(w("GeoJSON / KML: WGS84 γεωγραφικό μήκος, πλάτος· αρχικό CRS στα μεταδεδομένα.","GeoJSON / KML: WGS84 longitude,latitude; source CRS in metadata."));
            runOnUiThread(()->{if(isDestroyed()||isFinishing()||token!=generation||!authorised())return;snapshot=values;preview.setText(text);save.setEnabled(true);});
        }catch(Exception error){runOnUiThread(()->{if(!isDestroyed()&&!isFinishing()&&token==generation)preview.setText(w("Η προεπισκόπηση απέτυχε. Έλεγξε τα αποθηκευμένα όρια και τα δεδομένα συντεταγμένων.","Preview failed. Check the saved boundaries and coordinate data."));});}});
    }
    private void prepare(){
        if(snapshot.isEmpty())return;var values=snapshot;boolean source=source();String extension=FORMATS[format.getSelectedItemPosition()];int token=generation;save.setEnabled(false);preview.append(w("\nΔημιουργία αρχείου…","\nPreparing file…"));
        worker.submit(()->{File file=null;try{byte[] bytes=CoordinateExport.encode(values,source,extension);file=new File(getCacheDir(),"coordinates-"+UUID.randomUUID()+".tmp");try(var output=new FileOutputStream(file)){output.write(bytes);}File generated=file;runOnUiThread(()->{if(isDestroyed()||isFinishing()||token!=generation||!authorised()){generated.delete();return;}if(pending!=null)pending.delete();pending=generated;save.setEnabled(true);String mime=switch(extension){case "xlsx"->"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";case "pdf"->"application/pdf";case "geojson"->"application/geo+json";case "kml"->"application/vnd.google-earth.kml+xml";default->"text/csv";};openDocumentPicker(new Intent(Intent.ACTION_CREATE_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE).setType(mime).putExtra(Intent.EXTRA_TITLE,CoordinateExport.filename(values,source,extension)));});}
            catch(Exception error){if(file!=null)file.delete();runOnUiThread(()->{if(!isDestroyed()&&!isFinishing()){save.setEnabled(true);message(w("Η εξαγωγή απέτυχε. Έλεγξε τα δεδομένα αγροτεμαχίων και τον διαθέσιμο χώρο.","Export failed. Check parcel data and available storage."));}});}});
    }
    private void openDocumentPicker(Intent intent){try{startActivityForResult(intent,SAVE);}catch(ActivityNotFoundException|SecurityException error){if(pending!=null)pending.delete();pending=null;save.setEnabled(!snapshot.isEmpty());message(w("Ο επιλογέας αρχείου δεν είναι διαθέσιμος. Επανέλαβε την εξαγωγή.","Document picker unavailable. Export again."));}}
    @Override protected void onActivityResult(int request,int result,Intent data){super.onActivityResult(request,result,data);if(request!=SAVE||!authorised())return;File file=pending;pending=null;if(file==null||!file.isFile()){message(w("Το προσωρινό αρχείο δεν υπάρχει. Επανέλαβε την εξαγωγή.","Prepared file is unavailable. Export again."));return;}if(result!=RESULT_OK||data==null||data.getData()==null){file.delete();return;}var uri=data.getData();save.setEnabled(false);
        worker.submit(()->{String error=null;try(var input=new FileInputStream(file);var output=getContentResolver().openOutputStream(uri,"wt")){if(output==null)throw new IOException("Cannot open destination");byte[] buffer=new byte[8192];int count;while((count=input.read(buffer))!=-1)output.write(buffer,0,count);}catch(Exception e){error=w("Η αποθήκευση απέτυχε. Το αρχείο προορισμού μπορεί να είναι ελλιπές. Δοκίμασε διαφορετικό προορισμό.","Save failed. The destination file may be incomplete. Try a different destination.");}finally{file.delete();}String resultText=error==null?w("Το αρχείο αποθηκεύτηκε.","File saved."):error;runOnUiThread(()->{if(!isDestroyed()&&!isFinishing()&&authorised()){save.setEnabled(!snapshot.isEmpty());message(resultText);}});});
    }
    @Override protected void onResume(){super.onResume();if(profile!=null)authorised();}
    @Override protected void onSaveInstanceState(Bundle out){if(ready){out.putString("profile_id",profile.id());out.putStringArrayList("selected",selected());out.putInt("format",format.getSelectedItemPosition());out.putInt("coordinates",coordinates.getSelectedItemPosition());if(pending!=null)out.putString("pending",pending.getName());}super.onSaveInstanceState(out);}
    @Override protected void onDestroy(){if(task!=null)task.cancel(true);worker.shutdown();if(isFinishing()&&pending!=null)pending.delete();super.onDestroy();}
}
