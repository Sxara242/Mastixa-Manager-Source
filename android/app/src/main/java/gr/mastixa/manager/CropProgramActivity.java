package gr.mastixa.manager;

import android.app.Activity;
import android.app.AlertDialog;
import android.database.Cursor;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.text.InputType;
import android.view.View;
import android.widget.*;
import java.time.LocalDate;
import java.util.*;

/** Phase 12 crop-program editor for Android. Phase 13 owns the broader calendar/reminder surface. */
public final class CropProgramActivity extends Activity {
    private static final List<String> CATEGORIES = List.of(
        "irrigation", "fertilization", "cultivation", "plant_protection",
        "inspection", "pruning", "other"
    );
    private static final List<String> STATUSES = List.of("pending", "completed", "skipped");

    private record ProgramRow(String id, String name, String crop, String description, boolean active) {}

    private FarmStore store;
    private ProfileStore.Profile profile;
    private AppLanguage language;
    private LinearLayout content;

    private String t(String value) { return language.t(value); }
    private String words(String greek, String english) { return profile.language().equals("en") ? english : greek; }
    private int dp(int value) { return (int)(getResources().getDisplayMetrics().density * value); }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        profile = UserSession.valid(this) ? UserSession.profile : null;
        if (profile == null) { logout(); return; }
        language = new AppLanguage(this, profile.language());
        store = new FarmStore(this, profile.database());
        new CropProgramStore(store); // Lazily ensure the additive Phase 12 tables exist.
        render();
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
        startActivity(new android.content.Intent(this, WelcomeActivity.class)
            .addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK | android.content.Intent.FLAG_ACTIVITY_CLEAR_TASK));
        finish();
    }

    private android.graphics.drawable.GradientDrawable surface(int color, int radius) {
        var shape = new android.graphics.drawable.GradientDrawable();
        shape.setColor(color); shape.setCornerRadius(dp(radius)); return shape;
    }

    private TextView textValue(String value, int size, boolean bold) {
        var view = new TextView(this); view.setText(value); view.setTextSize(size);
        view.setTextColor(Color.rgb(30, 62, 49));
        if (bold) view.setTypeface(null, Typeface.BOLD);
        view.setPadding(0, dp(7), 0, dp(7)); content.addView(view); return view;
    }

    private Button action(String title, Runnable run, boolean primary) {
        var button = new Button(this); button.setText(t(title)); button.setAllCaps(false); button.setTextSize(16);
        button.setTextColor(primary ? Color.WHITE : Color.rgb(30, 62, 49));
        button.setBackground(surface(primary ? Color.rgb(35,83,62) : Color.WHITE, 14));
        var params = new LinearLayout.LayoutParams(-1, -2); params.topMargin = dp(8); params.bottomMargin = dp(3);
        button.setMinHeight(dp(50)); content.addView(button, params); button.setOnClickListener(v -> run.run()); return button;
    }

    private EditText input(LinearLayout form, String label, String value, int type) {
        var caption = new TextView(this); caption.setText(label); form.addView(caption);
        var edit = new EditText(this); edit.setText(value); edit.setContentDescription(label); edit.setInputType(type); form.addView(edit); return edit;
    }

    private Spinner choice(LinearLayout form, String label, List<String> labels, int selected) {
        var caption = new TextView(this); caption.setText(label); form.addView(caption);
        var spinner = new Spinner(this); spinner.setContentDescription(label);
        spinner.setAdapter(new ArrayAdapter<>(this, android.R.layout.simple_spinner_dropdown_item, labels));
        spinner.setSelection(Math.max(0, selected)); form.addView(spinner); return spinner;
    }

    private LinearLayout form() {
        var form = new LinearLayout(this); form.setOrientation(LinearLayout.VERTICAL); form.setPadding(dp(20), dp(8), dp(20), 0); return form;
    }

    private void message(String value) {
        new AlertDialog.Builder(this).setMessage(value).setPositiveButton(words("Εντάξει", "OK"), null).show();
    }

    private void saveDialog(String title, LinearLayout form, Runnable save) {
        var scroll = new ScrollView(this); scroll.addView(form);
        var dialog = new AlertDialog.Builder(this).setTitle(title).setView(scroll)
            .setNegativeButton(words("Ακύρωση", "Cancel"), null)
            .setPositiveButton(words("Αποθήκευση", "Save"), null).create();
        dialog.setOnShowListener(v -> dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(w -> {
            try { save.run(); dialog.dismiss(); render(); }
            catch (UiValidationException error) { message(error.getMessage()); }
            catch (IllegalArgumentException error) { message(words("Έλεγξε τα υποχρεωτικά πεδία και τις ημερομηνίες.", "Check the required fields and dates.")); }
            catch (Exception error) { message(words("Δεν αποθηκεύτηκε. Δοκίμασε ξανά.", "Not saved. Please try again.")); }
        }));
        dialog.show();
    }

    private CropProgramStore registry() { return new CropProgramStore(store); }

    private List<ProgramRow> programs(boolean includeArchived) {
        var rows = new ArrayList<ProgramRow>();
        try (Cursor cursor = store.getReadableDatabase().query(
            "crop_programs", new String[]{"id","name","crop","description","active"},
            includeArchived ? null : "active=1", null, null, null, "active DESC,name COLLATE NOCASE,id"
        )) {
            while (cursor.moveToNext()) rows.add(new ProgramRow(
                cursor.getString(0), cursor.getString(1), cursor.getString(2), cursor.getString(3), cursor.getInt(4) == 1
            ));
        }
        return List.copyOf(rows);
    }

    private static Integer nullableInt(Cursor cursor, int index) { return cursor.isNull(index) ? null : cursor.getInt(index); }

    private List<CropProgram.Rule> rules(String programId) {
        var rows = new ArrayList<CropProgram.Rule>();
        try (Cursor cursor = store.getReadableDatabase().query(
            "crop_program_rules",
            new String[]{"rule_id","title","category","schedule_kind","notes","month","day","start_month","start_day","end_month","end_day","every_days"},
            "program_id=?", new String[]{programId}, null, null, "position,rule_id"
        )) {
            while (cursor.moveToNext()) rows.add(new CropProgram.Rule(
                cursor.getString(0), cursor.getString(1), cursor.getString(2), cursor.getString(3), cursor.getString(4),
                nullableInt(cursor,5), nullableInt(cursor,6), nullableInt(cursor,7), nullableInt(cursor,8),
                nullableInt(cursor,9), nullableInt(cursor,10), nullableInt(cursor,11)
            ));
        }
        return List.copyOf(rows);
    }

    private void render() {
        var root = new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setBackgroundColor(Color.rgb(245,247,240));
        var toolbar = new LinearLayout(this); toolbar.setGravity(android.view.Gravity.CENTER_VERTICAL); toolbar.setPadding(dp(14), dp(8), dp(14), dp(4));
        var back = new Button(this); back.setText(words("‹ Πίσω", "‹ Back")); back.setAllCaps(false); back.setMinHeight(dp(48)); back.setOnClickListener(v -> finish());
        toolbar.addView(back, new LinearLayout.LayoutParams(-2, -2)); root.addView(toolbar);
        var scroll = new ScrollView(this); content = new LinearLayout(this); content.setOrientation(LinearLayout.VERTICAL); content.setPadding(dp(24), dp(8), dp(24), dp(28)); scroll.addView(content); root.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1)); setContentView(root);

        textValue(words("Πρόγραμμα Καλλιέργειας", "Crop Program"), 28, true);
        textValue(words("Δημιούργησε δικούς σου κανόνες εργασιών και παρήγαγε προγραμματισμένες εργασίες ανά αγροτεμάχιο και έτος.", "Create your own work rules and generate planned tasks per field and season year."), 15, false);
        textValue(words("Δεν περιλαμβάνονται έτοιμες γεωπονικές οδηγίες. Οι κανόνες ορίζονται ή εγκρίνονται από εσένα.", "No agronomic recommendations are preloaded. Rules are defined or approved by you."), 14, false);
        action(words("+ Νέο πρόγραμμα", "+ New program"), () -> editProgram(null), true);

        var all = programs(true);
        var active = programs(false);
        if (active.isEmpty()) textValue(words("Δεν υπάρχουν ενεργά προγράμματα.", "No active programs."), 17, false);
        for (var program : active) {
            textValue(program.name(), 21, true);
            if (!program.crop().isBlank()) textValue(words("Καλλιέργεια: ", "Crop: ") + program.crop(), 16, false);
            if (!program.description().isBlank()) textValue(program.description(), 15, false);
            int ruleCount = rules(program.id()).size();
            int taskCount = registry().tasks(program.id(), null, null).size();
            action(words("Κανόνες: ", "Rules: ") + ruleCount, () -> manageRules(program), false);
            action(words("Ανάθεση / Δημιουργία εργασιών", "Assign / Generate tasks"), () -> assign(program), true);
            action(words("Εργασίες: ", "Tasks: ") + taskCount, () -> showTasks(program), false);
            action(words("Επεξεργασία προγράμματος", "Edit program"), () -> editProgram(program), false);
            action(words("Αρχειοθέτηση προγράμματος", "Archive program"), () -> archive(program), false);
        }
        long archived = all.stream().filter(p -> !p.active()).count();
        if (archived > 0) textValue(words("Αρχειοθετημένα προγράμματα: ", "Archived programs: ") + archived, 14, false);
    }

    private void editProgram(ProgramRow program) {
        var f = form();
        var name = input(f, words("Όνομα προγράμματος *", "Program name *"), program == null ? "" : program.name(), InputType.TYPE_CLASS_TEXT);
        var crop = input(f, words("Καλλιέργεια", "Crop"), program == null ? "" : program.crop(), InputType.TYPE_CLASS_TEXT);
        var description = input(f, words("Περιγραφή", "Description"), program == null ? "" : program.description(), InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_MULTI_LINE);
        String id = program == null ? UUID.randomUUID().toString() : program.id();
        var existingRules = program == null ? List.<CropProgram.Rule>of() : rules(id);
        saveDialog(words(program == null ? "Νέο πρόγραμμα" : "Επεξεργασία προγράμματος", program == null ? "New program" : "Edit program"), f,
            () -> registry().saveProgram(id, name.getText().toString(), crop.getText().toString(), description.getText().toString(), existingRules));
    }

    private void manageRules(ProgramRow program) {
        var currentRules = rules(program.id());
        String[] labels = currentRules.stream().map(this::ruleSummary).toArray(String[]::new);
        var dialog = new AlertDialog.Builder(this).setTitle(program.name())
            .setItems(labels, (d, index) -> ruleMenu(program, currentRules.get(index)))
            .setNegativeButton(words("Κλείσιμο", "Close"), null)
            .setPositiveButton(words("+ Νέος κανόνας", "+ New rule"), (d, w) -> editRule(program, null));
        if (currentRules.isEmpty()) dialog.setMessage(words("Δεν υπάρχουν κανόνες ακόμη.", "No rules yet."));
        dialog.show();
    }

    private void ruleMenu(ProgramRow program, CropProgram.Rule rule) {
        new AlertDialog.Builder(this).setTitle(rule.title())
            .setItems(new String[]{words("Επεξεργασία", "Edit"), words("Διαγραφή", "Delete")}, (d, index) -> {
                if (index == 0) editRule(program, rule);
                else new AlertDialog.Builder(this).setMessage(words("Να διαγραφεί ο κανόνας; Οι ολοκληρωμένες/παραλειφθείσες εργασίες δεν διαγράφονται στην επόμενη αναγέννηση.", "Delete this rule? Completed/skipped task history is preserved on regeneration."))
                    .setNegativeButton(words("Ακύρωση", "Cancel"), null)
                    .setPositiveButton(words("Διαγραφή", "Delete"), (x, y) -> {
                        var next = new ArrayList<>(rules(program.id())); next.removeIf(r -> r.id().equals(rule.id()));
                        registry().saveProgram(program.id(), program.name(), program.crop(), program.description(), next); render();
                    }).show();
            }).show();
    }

    private void editRule(ProgramRow program, CropProgram.Rule existing) {
        var f = form();
        var title = input(f, words("Τίτλος εργασίας *", "Task title *"), existing == null ? "" : existing.title(), InputType.TYPE_CLASS_TEXT);
        var category = choice(f, words("Κατηγορία", "Category"), CATEGORIES.stream().map(this::categoryLabel).toList(), existing == null ? 0 : Math.max(0, CATEGORIES.indexOf(existing.category())));
        var schedule = choice(f, words("Πρόγραμμα ημερομηνίας", "Schedule"), List.of(words("Σταθερή ημερομηνία", "Fixed date"), words("Επανάληψη σε διάστημα", "Repeat in date window")), existing != null && existing.scheduleKind().equals("interval_window") ? 1 : 0);
        var fixed = input(f, words("Ημερομηνία (DD/MM) *", "Date (DD/MM) *"), existing != null && existing.scheduleKind().equals("fixed_date") ? dayMonth(existing.day(), existing.month()) : "", InputType.TYPE_CLASS_TEXT);
        var start = input(f, words("Έναρξη (DD/MM) *", "Start (DD/MM) *"), existing != null && existing.scheduleKind().equals("interval_window") ? dayMonth(existing.startDay(), existing.startMonth()) : "", InputType.TYPE_CLASS_TEXT);
        var end = input(f, words("Λήξη (DD/MM) *", "End (DD/MM) *"), existing != null && existing.scheduleKind().equals("interval_window") ? dayMonth(existing.endDay(), existing.endMonth()) : "", InputType.TYPE_CLASS_TEXT);
        var every = input(f, words("Κάθε πόσες ημέρες *", "Every N days *"), existing != null && existing.everyDays() != null ? String.valueOf(existing.everyDays()) : "7", InputType.TYPE_CLASS_NUMBER);
        var notes = input(f, words("Σημειώσεις", "Notes"), existing == null ? "" : existing.notes(), InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_MULTI_LINE);
        Runnable update = () -> { boolean interval = schedule.getSelectedItemPosition() == 1; fixed.setEnabled(!interval); start.setEnabled(interval); end.setEnabled(interval); every.setEnabled(interval); };
        schedule.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            public void onItemSelected(AdapterView<?> parent, View view, int position, long id) { update.run(); }
            public void onNothingSelected(AdapterView<?> parent) {}
        }); update.run();
        String id = existing == null ? UUID.randomUUID().toString() : existing.id();
        saveDialog(words(existing == null ? "Νέος κανόνας" : "Επεξεργασία κανόνα", existing == null ? "New rule" : "Edit rule"), f, () -> {
            boolean interval = schedule.getSelectedItemPosition() == 1;
            CropProgram.Rule rule;
            if (!interval) {
                int[] dm = parseDayMonth(fixed.getText().toString());
                rule = new CropProgram.Rule(id, title.getText().toString().trim(), CATEGORIES.get(category.getSelectedItemPosition()), "fixed_date", notes.getText().toString(), dm[0], dm[1], null, null, null, null, null);
            } else {
                int[] from = parseDayMonth(start.getText().toString()), to = parseDayMonth(end.getText().toString());
                int days = positiveInt(every.getText().toString(), words("Το διάστημα πρέπει να είναι θετικός ακέραιος.", "Interval must be a positive integer."));
                rule = new CropProgram.Rule(id, title.getText().toString().trim(), CATEGORIES.get(category.getSelectedItemPosition()), "interval_window", notes.getText().toString(), null, null, from[0], from[1], to[0], to[1], days);
            }
            var next = new ArrayList<>(rules(program.id()));
            if (existing == null) next.add(rule); else { int index = -1; for (int n = 0; n < next.size(); n++) if (next.get(n).id().equals(existing.id())) index = n; if (index < 0) throw new UiValidationException(words("Ο κανόνας δεν υπάρχει πλέον.", "Rule no longer exists.")); next.set(index, rule); }
            registry().saveProgram(program.id(), program.name(), program.crop(), program.description(), next);
        });
    }

    private void assign(ProgramRow program) {
        var fields = store.fields();
        if (fields.isEmpty()) { message(words("Πρόσθεσε πρώτα αγροτεμάχιο.", "Add a field first.")); return; }
        if (rules(program.id()).isEmpty()) { message(words("Πρόσθεσε πρώτα τουλάχιστον έναν κανόνα.", "Add at least one rule first.")); return; }
        var f = form();
        var field = choice(f, words("Αγροτεμάχιο", "Field"), fields.stream().map(FarmStore.Field::name).toList(), 0);
        var year = input(f, words("Έτος καλλιεργητικής περιόδου *", "Season year *"), String.valueOf(LocalDate.now().getYear()), InputType.TYPE_CLASS_NUMBER);
        saveDialog(words("Ανάθεση προγράμματος", "Assign program"), f, () -> {
            int season = boundedYear(year.getText().toString());
            registry().generateForField(program.id(), fields.get(field.getSelectedItemPosition()).id(), season);
        });
    }

    private void showTasks(ProgramRow program) {
        var tasks = registry().tasks(program.id(), null, null);
        if (tasks.isEmpty()) { message(words("Δεν υπάρχουν παραγμένες εργασίες.", "No generated tasks.")); return; }
        String[] labels = tasks.stream().map(task -> task.dueDate() + " · " + fieldName(task.fieldId()) + "\n" + task.title() + " · " + statusLabel(task.status())).toArray(String[]::new);
        new AlertDialog.Builder(this).setTitle(program.name()).setItems(labels, (d, index) -> taskStatus(program, tasks.get(index)))
            .setNegativeButton(words("Κλείσιμο", "Close"), null).show();
    }

    private void taskStatus(ProgramRow program, CropProgramStore.TaskRecord task) {
        String[] labels = STATUSES.stream().map(this::statusLabel).toArray(String[]::new);
        new AlertDialog.Builder(this).setTitle(task.title() + " · " + task.dueDate()).setSingleChoiceItems(labels, Math.max(0, STATUSES.indexOf(task.status())), (d, index) -> {
            registry().setTaskStatus(task.generationKey(), STATUSES.get(index)); d.dismiss(); render();
        }).setNegativeButton(words("Ακύρωση", "Cancel"), null).show();
    }

    private void archive(ProgramRow program) {
        new AlertDialog.Builder(this).setTitle(words("Αρχειοθέτηση προγράμματος", "Archive program"))
            .setMessage(words("Οι εκκρεμείς εργασίες αφαιρούνται. Οι ολοκληρωμένες και παραλειφθείσες διατηρούνται ως ιστορικό.", "Pending tasks are removed. Completed and skipped task history is preserved."))
            .setNegativeButton(words("Ακύρωση", "Cancel"), null)
            .setPositiveButton(words("Αρχειοθέτηση", "Archive"), (d, w) -> { registry().archiveProgram(program.id()); render(); }).show();
    }

    private String fieldName(String id) {
        return store.fields().stream().filter(f -> f.id().equals(id)).map(FarmStore.Field::name).findFirst().orElse(words("Διαγραμμένο αγροτεμάχιο", "Deleted field"));
    }

    private String categoryLabel(String value) {
        return switch (value) {
            case "irrigation" -> words("Άρδευση", "Irrigation");
            case "fertilization" -> words("Λίπανση", "Fertilization");
            case "cultivation" -> words("Καλλιεργητική εργασία", "Cultivation");
            case "plant_protection" -> words("Φυτοπροστασία", "Plant protection");
            case "inspection" -> words("Έλεγχος", "Inspection");
            case "pruning" -> words("Κλάδεμα", "Pruning");
            default -> words("Άλλο", "Other");
        };
    }

    private String statusLabel(String value) {
        return switch (value) {
            case "completed" -> words("Ολοκληρωμένη", "Completed");
            case "skipped" -> words("Παραλείφθηκε", "Skipped");
            default -> words("Εκκρεμής", "Pending");
        };
    }

    private String ruleSummary(CropProgram.Rule rule) {
        String schedule = rule.scheduleKind().equals("fixed_date")
            ? dayMonth(rule.day(), rule.month())
            : dayMonth(rule.startDay(), rule.startMonth()) + " → " + dayMonth(rule.endDay(), rule.endMonth()) + words(" κάθε ", " every ") + rule.everyDays() + words(" ημέρες", " days");
        return rule.title() + " · " + categoryLabel(rule.category()) + "\n" + schedule;
    }

    private static String dayMonth(Integer day, Integer month) {
        if (day == null || month == null) return "";
        return String.format(Locale.ROOT, "%02d/%02d", day, month);
    }

    private int[] parseDayMonth(String value) {
        String[] parts = value == null ? new String[0] : value.trim().split("/");
        if (parts.length != 2) throw new UiValidationException(words("Χρησιμοποίησε ημερομηνία DD/MM.", "Use DD/MM date format."));
        try {
            int day = Integer.parseInt(parts[0].trim()), month = Integer.parseInt(parts[1].trim());
            LocalDate.of(2000, month, day);
            return new int[]{month, day};
        } catch (RuntimeException error) { throw new UiValidationException(words("Χρησιμοποίησε έγκυρη ημερομηνία DD/MM.", "Use a valid DD/MM date.")); }
    }

    private int positiveInt(String value, String error) {
        try { int n = Integer.parseInt(value.trim()); if (n <= 0) throw new NumberFormatException(); return n; }
        catch (RuntimeException ex) { throw new UiValidationException(error); }
    }

    private int boundedYear(String value) {
        int year = positiveInt(value, words("Χρειάζεται έγκυρο έτος.", "Enter a valid year."));
        if (year < 1900 || year > 9998) throw new UiValidationException(words("Το έτος πρέπει να είναι από 1900 έως 9998.", "Year must be between 1900 and 9998."));
        return year;
    }
}
