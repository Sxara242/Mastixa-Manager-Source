package gr.mastixa.manager;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.text.InputType;
import android.view.Gravity;
import android.widget.*;
import java.time.LocalDate;
import java.util.*;

/** Phase 14D optional per-plant UI. Aggregate planting-batch totals remain independent. */
public final class PlantTrackingActivity extends Activity {
    private FarmStore store;
    private PlantTrackingStore plants;
    private ProfileStore.Profile profile;
    private AppLanguage language;
    private LinearLayout content;
    private String fieldFilter = "";
    private String statusFilter = "";
    private String query = "";
    private boolean showDeleted = false;

    private String words(String greek, String english) { return profile.language().equals("en") ? english : greek; }
    private int dp(int value) { return (int)(getResources().getDisplayMetrics().density * value); }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        profile = UserSession.valid(this) ? UserSession.profile : null;
        if (profile == null) { logout(); return; }
        language = new AppLanguage(this, profile.language());
        store = new FarmStore(this, profile.database());
        plants = new PlantTrackingStore(store);
        if (state != null) {
            fieldFilter = state.getString("field", "");
            statusFilter = state.getString("status", "");
            query = state.getString("query", "");
            showDeleted = state.getBoolean("deleted", false);
        }
        render();
    }

    @Override protected void onSaveInstanceState(Bundle state) {
        state.putString("field", fieldFilter);
        state.putString("status", statusFilter);
        state.putString("query", query);
        state.putBoolean("deleted", showDeleted);
        super.onSaveInstanceState(state);
    }

    @Override protected void onResume() {
        super.onResume();
        if (!isFinishing() && (!UserSession.valid(this) || profile == null || !UserSession.profile.id().equals(profile.id()))) logout();
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

    private TextView text(LinearLayout parent, String value, int size, boolean bold) {
        var view = new TextView(this); view.setText(value); view.setTextSize(size); view.setTextColor(Color.rgb(30,62,49));
        if (bold) view.setTypeface(null, Typeface.BOLD);
        view.setPadding(0, dp(6), 0, dp(6)); parent.addView(view); return view;
    }

    private Button button(LinearLayout parent, String title, Runnable run, boolean primary) {
        var b = new Button(this); b.setText(title); b.setAllCaps(false); b.setTextSize(15);
        b.setTextColor(primary ? Color.WHITE : Color.rgb(30,62,49));
        b.setBackground(surface(primary ? Color.rgb(35,83,62) : Color.WHITE, 14));
        var p = new LinearLayout.LayoutParams(-1, -2); p.topMargin = dp(7); p.bottomMargin = dp(2);
        b.setMinHeight(dp(48)); parent.addView(b, p); b.setOnClickListener(v -> run.run()); return b;
    }

    private LinearLayout form() {
        var f = new LinearLayout(this); f.setOrientation(LinearLayout.VERTICAL); f.setPadding(dp(20),dp(8),dp(20),0); return f;
    }

    private EditText input(LinearLayout form, String label, String value, int type) {
        text(form, label, 14, false);
        var edit = new EditText(this); edit.setText(value); edit.setContentDescription(label); edit.setInputType(type); form.addView(edit); return edit;
    }

    private Spinner choice(LinearLayout form, String label, List<String> labels, int selected) {
        text(form, label, 14, false);
        var spinner = new Spinner(this); spinner.setContentDescription(label);
        spinner.setAdapter(new ArrayAdapter<>(this, android.R.layout.simple_spinner_dropdown_item, labels));
        spinner.setSelection(Math.max(0, selected)); form.addView(spinner); return spinner;
    }

    private void message(String value) {
        new AlertDialog.Builder(this).setMessage(value).setPositiveButton(words("Εντάξει","OK"), null).show();
    }

    private void saveDialog(String title, LinearLayout form, Runnable save) {
        var scroll = new ScrollView(this); scroll.addView(form);
        var dialog = new AlertDialog.Builder(this).setTitle(title).setView(scroll)
            .setNegativeButton(words("Ακύρωση","Cancel"), null)
            .setPositiveButton(words("Αποθήκευση","Save"), null).create();
        dialog.setOnShowListener(v -> dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(w -> {
            try { save.run(); dialog.dismiss(); render(); }
            catch (UiValidationException error) { message(error.getMessage()); }
            catch (IllegalArgumentException error) { message(words("Έλεγξε τα στοιχεία.","Check the entered values.")); }
            catch (Exception error) { message(words("Δεν αποθηκεύτηκε. Δοκίμασε ξανά.","Not saved. Please try again.")); }
        }));
        dialog.show();
    }

    private String fieldName(String id) {
        return store.fields().stream().filter(f -> f.id().equals(id)).map(FarmStore.Field::name)
            .findFirst().orElse(words("Διαγραμμένο αγροτεμάχιο","Deleted field"));
    }

    private String statusLabel(String value) {
        return switch (value) {
            case "active" -> words("Ενεργό","Active");
            case "dead" -> words("Νεκρό","Dead");
            case "removed" -> words("Αφαιρέθηκε","Removed");
            default -> value;
        };
    }

    private String healthLabel(String value) {
        return switch (value) {
            case "unknown" -> words("Άγνωστη","Unknown");
            case "good" -> words("Καλή","Good");
            case "watch" -> words("Παρακολούθηση","Watch");
            case "poor" -> words("Κακή","Poor");
            default -> value;
        };
    }

    private String kindLabel(String value) {
        return switch (value) {
            case "note" -> words("Σημείωση","Note");
            case "health" -> words("Υγεία","Health");
            case "status" -> words("Κατάσταση","Status");
            default -> value;
        };
    }

    private String eventValueLabel(PlantTracking.Event event) {
        return switch (event.kind()) {
            case "health" -> healthLabel(event.value());
            case "status" -> statusLabel(event.value());
            default -> event.value();
        };
    }

    private void render() {
        var root = new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setBackgroundColor(Color.rgb(245,247,240));
        var toolbar = new LinearLayout(this); toolbar.setGravity(Gravity.CENTER_VERTICAL); toolbar.setPadding(dp(14),dp(8),dp(14),dp(4));
        var back = new Button(this); back.setText(words("‹ Πίσω","‹ Back")); back.setAllCaps(false); back.setMinHeight(dp(48)); back.setOnClickListener(v -> finish());
        toolbar.addView(back, new LinearLayout.LayoutParams(-2, -2)); root.addView(toolbar);
        var scroll = new ScrollView(this); content = new LinearLayout(this); content.setOrientation(LinearLayout.VERTICAL); content.setPadding(dp(24),dp(8),dp(24),dp(28));
        scroll.addView(content); root.addView(scroll, new LinearLayout.LayoutParams(-1,0,1)); setContentView(root);

        text(content, words("Μεμονωμένα Φυτά / Δέντρα","Individual Plants / Trees"), 28, true);
        text(content, words("Προαιρετική παρακολούθηση συγκεκριμένων φυτών με θέση και ιστορικό. Δεν αλλάζει αυτόματα τα συνολικά της παρτίδας.","Optional tracking for selected plants with position and history. It does not automatically change planting-batch totals."), 14, false);
        button(content, words("+ Νέο φυτό","+ New plant"), () -> editPlant(null), true);
        button(content, words("Αναζήτηση: ","Search: ") + (query.isEmpty() ? words("Όλα","All") : query), this::searchDialog, false);
        button(content, words("Αγροτεμάχιο: ","Field: ") + (fieldFilter.isEmpty() ? words("Όλα","All") : fieldName(fieldFilter)), this::fieldFilterDialog, false);
        button(content, words("Κατάσταση: ","Status: ") + (statusFilter.isEmpty() ? words("Όλες","All") : statusLabel(statusFilter)), this::statusFilterDialog, false);
        button(content, showDeleted ? words("Απόκρυψη διαγραμμένων","Hide deleted") : words("Εμφάνιση διαγραμμένων","Show deleted"), () -> { showDeleted = !showDeleted; render(); }, false);

        var activeIds = new HashSet<String>();
        for (var p : plants.plants(null, false)) activeIds.add(p.id());
        int visible = 0;
        for (var plant : plants.plants(null, showDeleted)) {
            boolean deleted = !activeIds.contains(plant.id());
            PlantTracking.Snapshot snapshot;
            try { snapshot = PlantTracking.project(plant, plants.events(plant.id())); }
            catch (IllegalArgumentException error) { continue; }
            if (!fieldFilter.isEmpty() && !fieldFilter.equals(plant.fieldId())) continue;
            if (!statusFilter.isEmpty() && !statusFilter.equals(snapshot.status())) continue;
            String searchable = (plant.label()+" "+plant.variety()+" "+plant.notes()+" "+fieldName(plant.fieldId())).toLowerCase(Locale.ROOT);
            if (!searchable.contains(query.toLowerCase(Locale.ROOT))) continue;
            visible++;
            var card = new LinearLayout(this); card.setOrientation(LinearLayout.VERTICAL); card.setPadding(dp(18),dp(12),dp(18),dp(14)); card.setBackground(surface(Color.WHITE,18));
            var spacing = new LinearLayout.LayoutParams(-1,-2); spacing.topMargin = dp(14); content.addView(card, spacing);
            String label = plant.label().isBlank() ? words("Χωρίς ετικέτα","Unlabelled plant") : plant.label();
            text(card, label + (deleted ? words(" · Διαγραμμένο"," · Deleted") : ""), 20, true);
            text(card, fieldName(plant.fieldId()) + (plant.variety().isBlank() ? "" : " · " + plant.variety()), 15, false);
            text(card, statusLabel(snapshot.status()) + " · " + healthLabel(snapshot.health()), 16, true);
            text(card, words("Συμβάντα: ","Events: ") + snapshot.eventCount() + (snapshot.lastEventDate().isBlank() ? "" : words(" · τελευταίο "," · latest ") + snapshot.lastEventDate()), 14, false);
            button(card, words("Στοιχεία · ","Details · ") + label, () -> details(plant.id(), deleted), false);
        }
        if (visible == 0) text(content, words("Δεν βρέθηκαν φυτά.","No plants found."), 17, false);
        text(content, visible + words(" εγγραφές"," records"), 17, true);
    }

    private void searchDialog() {
        var edit = new EditText(this); edit.setText(query); edit.setSingleLine(true);
        new AlertDialog.Builder(this).setTitle(words("Αναζήτηση","Search")).setView(edit)
            .setNegativeButton(words("Ακύρωση","Cancel"), null)
            .setPositiveButton(words("Εντάξει","OK"), (d,w) -> { query = edit.getText().toString().trim(); render(); }).show();
    }

    private void fieldFilterDialog() {
        var ids = new ArrayList<String>(); var labels = new ArrayList<String>(); ids.add(""); labels.add(words("Όλα","All"));
        for (var f : store.fields()) { ids.add(f.id()); labels.add(f.name()); }
        new AlertDialog.Builder(this).setTitle(words("Αγροτεμάχιο","Field")).setItems(labels.toArray(new String[0]), (d,n) -> { fieldFilter = ids.get(n); render(); }).show();
    }

    private void statusFilterDialog() {
        var ids = List.of("","active","dead","removed");
        var labels = List.of(words("Όλες","All"), statusLabel("active"), statusLabel("dead"), statusLabel("removed"));
        new AlertDialog.Builder(this).setTitle(words("Κατάσταση","Status")).setItems(labels.toArray(new String[0]), (d,n) -> { statusFilter = ids.get(n); render(); }).show();
    }

    private Double optionalDouble(EditText edit) {
        String value = edit.getText().toString().trim().replace(',', '.');
        if (value.isEmpty()) return null;
        try { return Double.parseDouble(value); }
        catch (NumberFormatException error) { throw new UiValidationException(words("Οι συντεταγμένες πρέπει να είναι αριθμοί.","Coordinates must be numeric.")); }
    }

    private void editPlant(PlantTracking.Plant existing) {
        var fields = store.fields();
        if (fields.isEmpty()) { message(words("Πρόσθεσε πρώτα αγροτεμάχιο.","Add a field first.")); return; }
        var f = form();
        var fieldIds = new ArrayList<String>(); var fieldNames = new ArrayList<String>();
        for (var field : fields) { fieldIds.add(field.id()); fieldNames.add(field.name()); }
        int fieldIndex = existing == null ? 0 : Math.max(0, fieldIds.indexOf(existing.fieldId()));
        var field = choice(f, words("Αγροτεμάχιο *","Field *"), fieldNames, fieldIndex);
        text(f, words("Παρτίδα φύτευσης","Planting batch"), 14, false);
        var batch = new Spinner(this); f.addView(batch);
        var batchIds = new ArrayList<String>();
        Runnable refreshBatches = () -> {
            String previous = batchIds.isEmpty() ? (existing == null ? "" : existing.plantingBatchId()) : batchIds.get(Math.max(0,batch.getSelectedItemPosition()));
            batchIds.clear(); var names = new ArrayList<String>(); batchIds.add(""); names.add(words("Χωρίς σύνδεση παρτίδας","No linked batch"));
            String selectedField = fieldIds.get(field.getSelectedItemPosition());
            for (var b : new WorkStore(store).plantings()) if (b.field_id().equals(selectedField)) { batchIds.add(b.id()); names.add(b.planting_date()+" · "+b.trees_planted()); }
            batch.setAdapter(new ArrayAdapter<>(this, android.R.layout.simple_spinner_dropdown_item, names));
            int selected = batchIds.indexOf(previous); batch.setSelection(selected < 0 ? 0 : selected);
        };
        field.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener(){public void onItemSelected(AdapterView<?> p, android.view.View v,int n,long id){refreshBatches.run();}public void onNothingSelected(AdapterView<?> p){}});
        refreshBatches.run();
        var label = input(f, words("Ετικέτα / κωδικός","Label / code"), existing == null ? "" : existing.label(), InputType.TYPE_CLASS_TEXT);
        var planted = input(f, words("Ημερομηνία φύτευσης (YYYY-MM-DD, προαιρετικό)","Planting date (YYYY-MM-DD, optional)"), existing == null ? "" : existing.plantedDate(), InputType.TYPE_CLASS_TEXT);
        var variety = input(f, words("Ποικιλία / κλώνος","Variety / clone"), existing == null ? "" : existing.variety(), InputType.TYPE_CLASS_TEXT);
        var latitude = input(f, words("Γεωγραφικό πλάτος (WGS84)","Latitude (WGS84)"), existing == null || existing.latitude() == null ? "" : String.valueOf(existing.latitude()), InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL|InputType.TYPE_NUMBER_FLAG_SIGNED);
        var longitude = input(f, words("Γεωγραφικό μήκος (WGS84)","Longitude (WGS84)"), existing == null || existing.longitude() == null ? "" : String.valueOf(existing.longitude()), InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL|InputType.TYPE_NUMBER_FLAG_SIGNED);
        var statusIds = List.of("active","dead","removed");
        var status = choice(f, words("Αρχική κατάσταση","Initial status"), statusIds.stream().map(this::statusLabel).toList(), existing == null ? 0 : Math.max(0,statusIds.indexOf(existing.status())));
        var healthIds = List.of("unknown","good","watch","poor");
        var health = choice(f, words("Αρχική υγεία","Initial health"), healthIds.stream().map(this::healthLabel).toList(), existing == null ? 0 : Math.max(0,healthIds.indexOf(existing.health())));
        var notes = input(f, words("Σημειώσεις","Notes"), existing == null ? "" : existing.notes(), InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_MULTI_LINE);
        boolean hasHistory = existing != null && !plants.events(existing.id()).isEmpty();
        if (hasHistory) { status.setEnabled(false); health.setEnabled(false); text(f, words("Υπάρχει ιστορικό. Κατάσταση και υγεία αλλάζουν με νέο συμβάν.","History exists. Change status and health by adding an event."), 13, false); }
        String id = existing == null ? UUID.randomUUID().toString() : existing.id();
        saveDialog(words("Μεμονωμένο φυτό / δέντρο","Individual plant / tree"), f, () -> {
            String batchId = batchIds.get(batch.getSelectedItemPosition());
            plants.savePlant(new PlantTracking.Plant(id, fieldIds.get(field.getSelectedItemPosition()), batchId,
                label.getText().toString(), planted.getText().toString(), variety.getText().toString(), optionalDouble(latitude), optionalDouble(longitude),
                statusIds.get(status.getSelectedItemPosition()), healthIds.get(health.getSelectedItemPosition()), notes.getText().toString()));
        });
    }

    private void addEvent(String plantId) {
        var owner = plants.plant(plantId);
        var f = form();
        var date = input(f, words("Ημερομηνία (YYYY-MM-DD) *","Date (YYYY-MM-DD) *"), LocalDate.now().toString(), InputType.TYPE_CLASS_TEXT);
        var kinds = List.of("note","health","status");
        var kind = choice(f, words("Τύπος","Type"), kinds.stream().map(this::kindLabel).toList(), 0);
        text(f, words("Νέα τιμή","New value"), 14, false);
        var valueChoice = new Spinner(this); f.addView(valueChoice);
        var noteValue = new EditText(this); noteValue.setHint(words("Σύντομη σημείωση","Short note")); f.addView(noteValue);
        var currentValues = new ArrayList<String>();
        Runnable refresh = () -> {
            int pos = kind.getSelectedItemPosition(); currentValues.clear();
            if (pos == 1) currentValues.addAll(List.of("unknown","good","watch","poor"));
            else if (pos == 2) currentValues.addAll(List.of("active","dead","removed"));
            var labels = currentValues.stream().map(v -> pos == 1 ? healthLabel(v) : statusLabel(v)).toList();
            valueChoice.setAdapter(new ArrayAdapter<>(this, android.R.layout.simple_spinner_dropdown_item, labels));
            valueChoice.setVisibility(pos == 0 ? android.view.View.GONE : android.view.View.VISIBLE);
            noteValue.setVisibility(pos == 0 ? android.view.View.VISIBLE : android.view.View.GONE);
        };
        kind.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener(){public void onItemSelected(AdapterView<?> p,android.view.View v,int n,long id){refresh.run();}public void onNothingSelected(AdapterView<?> p){}}); refresh.run();
        var notes = input(f, words("Πρόσθετες σημειώσεις","Additional notes"), "", InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_MULTI_LINE);
        saveDialog(words("Νέο συμβάν φυτού","New plant event"), f, () -> {
            String eventKind = kinds.get(kind.getSelectedItemPosition());
            String value = eventKind.equals("note") ? noteValue.getText().toString() : currentValues.get(valueChoice.getSelectedItemPosition());
            plants.appendEvent(new PlantTracking.Event(UUID.randomUUID().toString(), owner.id(), date.getText().toString(), eventKind, value, notes.getText().toString()));
        });
    }

    private void details(String id, boolean deleted) {
        var plant = plants.plant(id, true);
        var snapshot = PlantTracking.project(plant, plants.events(id));
        var body = new StringBuilder();
        body.append(fieldName(plant.fieldId())).append("\n");
        if (!plant.plantedDate().isBlank()) body.append(words("Φύτευση: ","Planted: ")).append(plant.plantedDate()).append("\n");
        if (!plant.variety().isBlank()) body.append(words("Ποικιλία: ","Variety: ")).append(plant.variety()).append("\n");
        body.append(words("Κατάσταση: ","Status: ")).append(statusLabel(snapshot.status())).append("\n");
        body.append(words("Υγεία: ","Health: ")).append(healthLabel(snapshot.health())).append("\n");
        if (plant.latitude() != null) body.append("GPS: ").append(plant.latitude()).append(", ").append(plant.longitude()).append("\n");
        if (!plant.notes().isBlank()) body.append("\n").append(plant.notes()).append("\n");
        body.append("\n").append(words("Ιστορικό:","History:"));
        for (var e : plants.events(id)) {
            String eventValue = eventValueLabel(e);
            body.append("\n").append(e.eventDate()).append(" · ").append(kindLabel(e.kind())).append(eventValue.isBlank()?"":" · "+eventValue).append(e.notes().isBlank()?"":" · "+e.notes());
        }
        String title = plant.label().isBlank() ? words("Μεμονωμένο φυτό / δέντρο","Individual plant / tree") : plant.label();
        var dialog = new AlertDialog.Builder(this).setTitle(title).setMessage(body.toString()).setNegativeButton(words("Κλείσιμο","Close"), null);
        if (deleted) dialog.setPositiveButton(words("Επαναφορά","Restore"), (d,w) -> actionRun(() -> plants.restorePlant(id)));
        else {
            dialog.setPositiveButton(words("+ Συμβάν","+ Event"), (d,w) -> addEvent(id));
            dialog.setNeutralButton(words("Ενέργειες","Actions"), (d,w) -> plantActions(plant));
        }
        dialog.show();
    }

    private void plantActions(PlantTracking.Plant plant) {
        String[] options = {words("Επεξεργασία","Edit"), words("Διαγραφή","Delete")};
        new AlertDialog.Builder(this).setTitle(plant.label().isBlank()?words("Φυτό / δέντρο","Plant / tree"):plant.label()).setItems(options, (d,n) -> {
            if (n == 0) editPlant(plant);
            else new AlertDialog.Builder(this).setMessage(words("Η εγγραφή θα κρυφτεί, αλλά το ιστορικό διατηρείται. Συνέχεια;","The record will be hidden, but its history is retained. Continue?"))
                .setNegativeButton(words("Ακύρωση","Cancel"), null).setPositiveButton(words("Διαγραφή","Delete"), (x,y) -> actionRun(() -> plants.deletePlant(plant.id()))).show();
        }).show();
    }

    private void actionRun(Runnable run) {
        try { run.run(); render(); }
        catch (IllegalArgumentException error) { message(words("Η ενέργεια δεν ολοκληρώθηκε. Έλεγξε τα στοιχεία.","Action failed. Check the entered values.")); }
        catch (Exception error) { message(words("Η ενέργεια απέτυχε.","Action failed.")); }
    }
}
