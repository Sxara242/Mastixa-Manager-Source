package gr.mastixa.manager;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.*;
import java.math.BigDecimal;
import java.util.*;

/** Phase 15E read-only sensor dashboard: latest values, history, stale/suspect flags. */
public final class SensorDataActivity extends Activity {
    private FarmStore store;
    private SensorDataStore sensors;
    private ProfileStore.Profile profile;
    private LinearLayout content;

    private String words(String greek, String english) { return profile.language().equals("en") ? english : greek; }
    private int dp(int value) { return (int)(getResources().getDisplayMetrics().density * value); }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        profile = UserSession.valid(this) ? UserSession.profile : null;
        if (profile == null) { logout(); return; }
        store = new FarmStore(this, profile.database());
        sensors = new SensorDataStore(store);
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
        view.setPadding(0, dp(5), 0, dp(5)); parent.addView(view); return view;
    }

    private Button button(LinearLayout parent, String title, Runnable run, boolean primary) {
        var b = new Button(this); b.setText(title); b.setAllCaps(false); b.setTextSize(15);
        b.setTextColor(primary ? Color.WHITE : Color.rgb(30,62,49));
        b.setBackground(surface(primary ? Color.rgb(35,83,62) : Color.WHITE, 14));
        var p = new LinearLayout.LayoutParams(-1, -2); p.topMargin = dp(7); p.bottomMargin = dp(2);
        b.setMinHeight(dp(48)); parent.addView(b, p); b.setOnClickListener(v -> run.run()); return b;
    }

    private String fieldName(String id) {
        if (id == null || id.isBlank()) return words("Χωρίς αγροτεμάχιο", "No field");
        for (var field : store.fields()) if (field.id().equals(id)) return field.name();
        return words("Διαγραμμένο αγροτεμάχιο", "Deleted field");
    }

    private String metricLabel(String metric) {
        return switch (metric) {
            case "air_temperature" -> words("Θερμοκρασία αέρα", "Air temperature");
            case "soil_temperature" -> words("Θερμοκρασία εδάφους", "Soil temperature");
            case "air_humidity" -> words("Υγρασία αέρα", "Air humidity");
            case "soil_moisture" -> words("Υγρασία εδάφους", "Soil moisture");
            case "rainfall" -> words("Βροχόπτωση", "Rainfall");
            case "battery" -> words("Μπαταρία", "Battery");
            case "water_level" -> words("Στάθμη νερού", "Water level");
            case "pressure" -> words("Πίεση", "Pressure");
            case "wind_speed" -> words("Ταχύτητα ανέμου", "Wind speed");
            case "soil_ec" -> words("Αγωγιμότητα εδάφους", "Soil EC");
            case "soil_ph" -> words("pH εδάφους", "Soil pH");
            default -> metric.startsWith("custom.") ? metric.substring(7).replace('_', ' ') : metric;
        };
    }

    private String unitLabel(String unit) {
        return switch (unit) {
            case "celsius" -> "°C";
            case "percent" -> "%";
            case "millimeter" -> "mm";
            case "hectopascal" -> "hPa";
            case "meter_per_second" -> "m/s";
            case "microsiemens_per_cm" -> "µS/cm";
            case "ph" -> "pH";
            default -> unit;
        };
    }

    private String compact(double value) {
        return BigDecimal.valueOf(value).stripTrailingZeros().toPlainString();
    }

    private String readingState(String observedAt, String quality, String now) {
        SensorView.ReadingState state = SensorView.classify(observedAt, quality, now);
        if (!state.hasReading()) return words("Χωρίς μέτρηση", "No reading");
        var flags = new ArrayList<String>();
        if (state.suspect()) flags.add(words("Ύποπτη", "Suspect"));
        if (state.stale()) flags.add(words("Παρωχημένη", "Stale"));
        return flags.isEmpty() ? "OK" : String.join(" · ", flags);
    }

    private void render() {
        var root = new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setBackgroundColor(Color.rgb(245,247,240));
        var toolbar = new LinearLayout(this); toolbar.setGravity(Gravity.CENTER_VERTICAL); toolbar.setPadding(dp(14),dp(8),dp(14),dp(4));
        var back = new Button(this); back.setText(words("‹ Πίσω", "‹ Back")); back.setAllCaps(false); back.setMinHeight(dp(48)); back.setOnClickListener(v -> finish());
        toolbar.addView(back, new LinearLayout.LayoutParams(-2, -2)); root.addView(toolbar);
        var scroll = new ScrollView(this); content = new LinearLayout(this); content.setOrientation(LinearLayout.VERTICAL); content.setPadding(dp(24),dp(8),dp(24),dp(28));
        scroll.addView(content); root.addView(scroll, new LinearLayout.LayoutParams(-1,0,1)); setContentView(root);

        text(content, words("Αισθητήρες / API", "Sensors / API"), 28, true);
        text(content, words(
            "Τελευταίες μετρήσεις και ιστορικό από τα τοπικά αποθηκευμένα δεδομένα. Παρωχημένη = πάνω από 24 ώρες χωρίς νέα μέτρηση.",
            "Latest readings and history from locally stored data. Stale = more than 24 hours without a new reading."
        ), 14, false);
        button(content, words("Ανανέωση", "Refresh"), this::render, true);

        List<SensorData.Device> devices = sensors.devices(false);
        if (devices.isEmpty()) {
            text(content, words("Δεν υπάρχουν αποθηκευμένοι αισθητήρες.", "No stored sensors."), 17, false);
            return;
        }
        String now = SensorView.nowUtc();
        for (SensorData.Device device : devices) {
            SensorData.Snapshot snapshot;
            try { snapshot = sensors.snapshot(device.id()); }
            catch (IllegalArgumentException error) { continue; }
            var card = new LinearLayout(this); card.setOrientation(LinearLayout.VERTICAL); card.setPadding(dp(18),dp(12),dp(18),dp(14)); card.setBackground(surface(Color.WHITE,18));
            var spacing = new LinearLayout.LayoutParams(-1,-2); spacing.topMargin = dp(14); content.addView(card, spacing);
            text(card, snapshot.name(), 21, true);
            String status = snapshot.status().equals("active") ? words("Ενεργή", "Active") : words("Απενεργοποιημένη", "Disabled");
            text(card, snapshot.provider() + " · " + fieldName(snapshot.fieldId()) + " · " + status, 14, false);
            if (snapshot.channels().isEmpty()) {
                text(card, words("Δεν υπάρχουν κανάλια μέτρησης.", "No measurement channels."), 15, false);
                continue;
            }
            for (SensorData.ChannelSnapshot channel : snapshot.channels()) {
                var row = new LinearLayout(this); row.setOrientation(LinearLayout.VERTICAL); row.setPadding(dp(14),dp(8),dp(14),dp(10)); row.setBackground(surface(Color.rgb(248,250,246),14));
                var rowParams = new LinearLayout.LayoutParams(-1,-2); rowParams.topMargin = dp(9); card.addView(row,rowParams);
                String label = channel.label().isBlank() ? metricLabel(channel.metric()) : channel.label();
                text(row, label, 17, true);
                String value = channel.latestValue() == null ? "—" : compact(channel.latestValue()) + " " + unitLabel(channel.unit());
                text(row, value + " · " + readingState(channel.latestObservedAt(), channel.latestQuality(), now), 18, true);
                text(row, metricLabel(channel.metric()) + " · " + (channel.latestObservedAt().isBlank() ? words("χωρίς χρόνο", "no timestamp") : channel.latestObservedAt()), 13, false);
                text(row, words("Μετρήσεις: ", "Readings: ") + channel.observationCount(), 13, false);
                button(row, words("Ιστορικό · ", "History · ") + label, () -> history(channel.channelId(), label, channel.unit()), false);
            }
        }
    }

    private void history(String channelId, String label, String unit) {
        List<SensorData.Observation> rows = sensors.observations(channelId);
        StringBuilder body = new StringBuilder();
        int start = Math.max(0, rows.size() - 50);
        for (int n = rows.size() - 1; n >= start; n--) {
            SensorData.Observation row = rows.get(n);
            body.append(row.observedAt()).append("  ·  ")
                .append(compact(row.value())).append(" ").append(unitLabel(unit)).append("  ·  ")
                .append(row.quality().equals("suspect") ? words("Ύποπτη", "Suspect") : words("Καλή", "Good"));
            if (!row.sourceRef().isBlank()) body.append("  ·  ").append(row.sourceRef());
            body.append("\n");
        }
        if (body.length() == 0) body.append(words("Δεν υπάρχουν μετρήσεις.", "No readings."));
        new AlertDialog.Builder(this)
            .setTitle(words("Ιστορικό · ", "History · ") + label)
            .setMessage(body.toString().trim())
            .setPositiveButton(words("Κλείσιμο", "Close"), null)
            .show();
    }
}
