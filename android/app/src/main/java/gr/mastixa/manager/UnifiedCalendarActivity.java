package gr.mastixa.manager;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.text.InputType;
import android.view.View;
import android.widget.*;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.*;

/** Phase 13 Android unified calendar. Read-only; edits stay in their owner pages. */
public final class UnifiedCalendarActivity extends Activity {
    private static final List<String> MONTHS_EL = List.of("Όλοι οι μήνες","Ιανουάριος","Φεβρουάριος","Μάρτιος","Απρίλιος","Μάιος","Ιούνιος","Ιούλιος","Αύγουστος","Σεπτέμβριος","Οκτώβριος","Νοέμβριος","Δεκέμβριος");
    private static final List<String> MONTHS_EN = List.of("All months","January","February","March","April","May","June","July","August","September","October","November","December");
    private static final List<String> SOURCE_IDS = List.of("","production","activity","protection","labor","planting","crop_task");

    private FarmStore store;
    private ProfileStore.Profile profile;
    private LinearLayout content;
    private Integer yearFilter = null;
    private Integer monthFilter = null;
    private String fieldFilter = "";
    private String sourceFilter = "";
    private String query = "";
    private String focusTask = "";

    private String words(String greek, String english) { return profile.language().equals("en") ? english : greek; }
    private int dp(int value) { return (int)(getResources().getDisplayMetrics().density * value); }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        profile = UserSession.valid(this) ? UserSession.profile : null;
        if (profile == null) { logout(); return; }
        store = new FarmStore(this, profile.database());
        focusTask = getIntent().getStringExtra("focus_task") == null ? "" : getIntent().getStringExtra("focus_task");
        render();
    }

    @Override protected void onResume() {
        super.onResume();
        if (!isFinishing() && (!UserSession.valid(this) || profile == null || !UserSession.profile.id().equals(profile.id()))) logout();
        else if (store != null) render();
    }

    @Override protected void onDestroy() {
        if (store != null) store.close();
        super.onDestroy();
    }

    private void logout() {
        UserSession.clear();
        startActivity(new Intent(this, WelcomeActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK));
        finish();
    }

    private android.graphics.drawable.GradientDrawable surface(int color, int radius) {
        var shape = new android.graphics.drawable.GradientDrawable();
        shape.setColor(color); shape.setCornerRadius(dp(radius)); return shape;
    }

    private TextView textValue(String value, int size, boolean bold) {
        var view = new TextView(this); view.setText(value); view.setTextSize(size); view.setTextColor(Color.rgb(30,62,49));
        if (bold) view.setTypeface(null, Typeface.BOLD); view.setPadding(0,dp(6),0,dp(6)); content.addView(view); return view;
    }

    private Button action(String title, Runnable run, boolean primary) {
        var button = new Button(this); button.setText(title); button.setAllCaps(false); button.setTextSize(15);
        button.setTextColor(primary ? Color.WHITE : Color.rgb(30,62,49));
        button.setBackground(surface(primary ? Color.rgb(35,83,62) : Color.WHITE,14));
        var params = new LinearLayout.LayoutParams(-1,-2); params.topMargin=dp(6); params.bottomMargin=dp(2); button.setMinHeight(dp(48)); content.addView(button,params); button.setOnClickListener(v->run.run()); return button;
    }

    private String sourceLabel(String source) {
        return switch (source) {
            case "production" -> words("Παραγωγή","Production");
            case "activity" -> words("Άρδευση & Λίπανση","Irrigation & Fertilization");
            case "protection" -> words("Φυτοπροστασία","Plant protection");
            case "labor" -> words("Εργατικά","Labor");
            case "planting" -> words("Φυτεύσεις & Δέντρα","Plantings & Trees");
            case "crop_task" -> words("Πρόγραμμα Καλλιέργειας","Crop Program");
            default -> words("Όλες οι ενότητες","All sections");
        };
    }

    private void render() {
        var root = new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setBackgroundColor(Color.rgb(245,247,240));
        var toolbar = new LinearLayout(this); toolbar.setGravity(android.view.Gravity.CENTER_VERTICAL); toolbar.setPadding(dp(14),dp(8),dp(14),dp(4));
        var back = new Button(this); back.setText(words("‹ Πίσω","‹ Back")); back.setAllCaps(false); back.setMinHeight(dp(48)); back.setOnClickListener(v->finish()); toolbar.addView(back,new LinearLayout.LayoutParams(-2,-2)); root.addView(toolbar);
        var scroll = new ScrollView(this); content = new LinearLayout(this); content.setOrientation(LinearLayout.VERTICAL); content.setPadding(dp(22),dp(8),dp(22),dp(28)); scroll.addView(content); root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1)); setContentView(root);

        textValue(words("Ενιαίο Ημερολόγιο","Unified Calendar"),28,true);
        textValue(words("Ιστορικές καλλιεργητικές καταχωρήσεις και προγραμματισμένες εργασίες σε μία προβολή.","Historical farm records and planned tasks in one view."),15,false);

        var projection = new UnifiedCalendarStore(store, profile.language().equals("en"));
        var all = projection.entries(LocalDate.now());
        var years = all.stream().map(e->LocalDate.parse(e.date()).getYear()).distinct().sorted(Comparator.reverseOrder()).toList();
        action(words("Έτος: ","Year: ") + (yearFilter==null?words("Όλα","All"):yearFilter), () -> chooseYear(years), false);
        var months = profile.language().equals("en") ? MONTHS_EN : MONTHS_EL;
        action(words("Μήνας: ","Month: ") + months.get(monthFilter==null?0:monthFilter), this::chooseMonth, false);
        action(words("Αγροτεμάχιο: ","Field: ") + fieldLabel(), this::chooseField, false);
        action(words("Ενότητα: ","Section: ") + sourceLabel(sourceFilter), this::chooseSource, false);
        action(words("Αναζήτηση: ","Search: ") + (query.isBlank()?words("—","—"):query), this::chooseSearch, false);

        var visible = UnifiedCalendarStore.filter(all,yearFilter,monthFilter,fieldFilter,sourceFilter,query);
        if (!focusTask.isBlank()) visible = visible.stream().filter(e->e.source().equals("crop_task")&&e.recordId().equals(focusTask)).toList();
        if (!focusTask.isBlank()) action(words("Εμφάνιση όλων","Show all"),()->{focusTask="";render();},true);
        textValue(visible.size()+words(" καταχωρήσεις"," entries"),18,true);
        if (visible.isEmpty()) textValue(words("Δεν υπάρχουν καταχωρήσεις που να ταιριάζουν στα φίλτρα.","No entries match the filters."),16,false);
        for (var row : visible) card(row);
    }

    private void card(UnifiedCalendarStore.Entry row) {
        var parent=content; var card=new LinearLayout(this); card.setOrientation(LinearLayout.VERTICAL); card.setPadding(dp(16),dp(10),dp(16),dp(12)); card.setBackground(surface(Color.WHITE,16));
        var params=new LinearLayout.LayoutParams(-1,-2); params.topMargin=dp(10); parent.addView(card,params); content=card;
        LocalDate date=LocalDate.parse(row.date()); textValue(date.format(DateTimeFormatter.ofPattern("dd/MM/yyyy"))+" · "+row.section(),15,true);
        textValue(row.title(),20,true); textValue(row.fieldName(),15,false); if(!row.detail().isBlank())textValue(row.detail(),14,false);
        if(row.source().equals("crop_task")) action(words("Άνοιγμα Προγράμματος Καλλιέργειας","Open Crop Program"),()->startActivity(new Intent(this,CropProgramActivity.class)),false);
        content=parent;
    }

    private String fieldLabel() {
        if(fieldFilter.isBlank()) return words("Όλα","All");
        return store.fields().stream().filter(f->f.id().equals(fieldFilter)).map(FarmStore.Field::name).findFirst().orElse(words("Αγροτεμάχιο ιστορικού","Historical field"));
    }

    private void chooseYear(List<Integer> years) {
        var labels=new ArrayList<String>(); labels.add(words("Όλα","All")); for(var y:years)labels.add(String.valueOf(y));
        new AlertDialog.Builder(this).setTitle(words("Έτος","Year")).setItems(labels.toArray(new String[0]),(d,n)->{yearFilter=n==0?null:years.get(n-1);render();}).show();
    }
    private void chooseMonth() {
        var labels=(profile.language().equals("en")?MONTHS_EN:MONTHS_EL).toArray(new String[0]);
        new AlertDialog.Builder(this).setTitle(words("Μήνας","Month")).setItems(labels,(d,n)->{monthFilter=n==0?null:n;render();}).show();
    }
    private void chooseField() {
        var ids=new ArrayList<String>(); var labels=new ArrayList<String>(); ids.add("");labels.add(words("Όλα","All"));
        for(var f:store.fields()){ids.add(f.id());labels.add(f.name());}
        new AlertDialog.Builder(this).setTitle(words("Αγροτεμάχιο","Field")).setItems(labels.toArray(new String[0]),(d,n)->{fieldFilter=ids.get(n);render();}).show();
    }
    private void chooseSource() {
        var labels=SOURCE_IDS.stream().map(this::sourceLabel).toArray(String[]::new);
        new AlertDialog.Builder(this).setTitle(words("Ενότητα","Section")).setItems(labels,(d,n)->{sourceFilter=SOURCE_IDS.get(n);render();}).show();
    }
    private void chooseSearch() {
        var input=new EditText(this); input.setText(query); input.setInputType(InputType.TYPE_CLASS_TEXT); input.setContentDescription(words("Αναζήτηση ημερολογίου","Calendar search"));
        new AlertDialog.Builder(this).setTitle(words("Αναζήτηση","Search")).setView(input).setNegativeButton(words("Ακύρωση","Cancel"),null).setPositiveButton(words("Εντάξει","OK"),(d,n)->{query=input.getText().toString().trim();render();}).show();
    }
}
