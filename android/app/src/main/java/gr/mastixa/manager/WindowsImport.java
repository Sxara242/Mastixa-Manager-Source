package gr.mastixa.manager;

import android.database.sqlite.SQLiteDatabase;
import android.util.AtomicFile;
import org.json.JSONObject;
import java.io.*;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.zip.*;

/** Additive import of the existing Windows portable export. Desktop IDs are local to a profile. */
public final class WindowsImport {
    private static final int LIMIT = 10 * 1024 * 1024;
    public record Preview(List<FarmStore.Field> additions, int identical, int conflicts) {}

    public static List<FarmStore.Field> read(InputStream input) throws Exception {
        byte[] bytes = LocalBackup.read(input);
        if(bytes.length>LIMIT)throw new IOException("ZIP: όριο 10 MB / 10 MB limit");
        byte[] csv = null, manifest = null;
        int expanded = 0, entries = 0;
        try (ZipInputStream zip = new ZipInputStream(new ByteArrayInputStream(bytes))) {
            ZipEntry entry;
            while ((entry = zip.getNextEntry()) != null) {
                if (++entries > 1000) throw new IOException("Το ZIP περιέχει υπερβολικά πολλά αρχεία.");
                ByteArrayOutputStream out = new ByteArrayOutputStream();
                byte[] buffer = new byte[8192]; int count;
                while ((count = zip.read(buffer)) != -1) {
                    expanded += count;
                    if (expanded > LIMIT) throw new IOException("Το ZIP υπερβαίνει τα 10 MB αποσυμπιεσμένων δεδομένων. Εξήγαγε μόνο αγροτεμάχια.");
                    out.write(buffer, 0, count);
                }
                if (entry.getName().equals("tables/fields.csv")) {
                    if (csv != null) throw new IOException("Διπλό αρχείο αγροτεμαχίων.");
                    csv = out.toByteArray();
                }
                if (entry.getName().equals("manifest.json")) {
                    if (manifest != null) throw new IOException("Διπλό αρχείο περιγραφής.");
                    manifest = out.toByteArray();
                }
                zip.closeEntry();
            }
        }
        if (csv == null || manifest == null) throw new IOException("Επίλεξε ZIP από «Εξαγωγή Δεδομένων» των Windows με επιλεγμένα τα αγροτεμάχια.");
        JSONObject info = new JSONObject(decode(manifest));
        if (!"mastixa-manager-portable-export-v1".equals(info.getString("schema"))) throw new IOException("Μη συμβατή έκδοση εξαγωγής.");
        int expected = -1;
        var tables = info.getJSONArray("tables");
        for (int i = 0; i < tables.length(); i++) {
            var table = tables.getJSONObject(i);
            if ("fields".equals(table.getString("table"))) {
                if (expected != -1 || !"exported".equals(table.getString("status")) || !"tables/fields.csv".equals(table.getString("file"))) throw new IOException("Μη έγκυρη περιγραφή αγροτεμαχίων.");
                expected = table.getInt("rows");
                if (expected < 0 || expected > 5000) throw new IOException("Επιτρέπονται έως 5.000 αγροτεμάχια.");
            }
        }
        List<List<String>> rows = parseCsv(decode(csv));
        if (rows.isEmpty()) throw new IOException("Λείπουν οι στήλες αγροτεμαχίων.");
        List<String> header = rows.remove(0);
        String[] required = {"id", "name", "area_stremma", "kaek", "location", "productive_trees", "notes"};
        for (String column : required) if (Collections.frequency(header, column) != 1) throw new IOException("Λείπει ή επαναλαμβάνεται η στήλη: " + column);
        if (expected != rows.size()) throw new IOException("Το πλήθος αγροτεμαχίων δεν συμφωνεί με το ZIP.");
        List<FarmStore.Field> fields = new ArrayList<>(); Set<String> ids = new HashSet<>();
        for (int i = 0; i < rows.size(); i++) {
            var row = rows.get(i);
            try {
                if (row.size() != header.size()) throw new IllegalArgumentException();
                String id = value(row, header, "id"), name = value(row, header, "name");
                double area = Double.parseDouble(value(row, header, "area_stremma"));
                int trees = Integer.parseInt(value(row, header, "productive_trees"));
                if (id.isEmpty() || !ids.add(id) || name.isEmpty() || !Double.isFinite(area) || area < 0 || trees < 0) throw new IllegalArgumentException();
                fields.add(new FarmStore.Field(id, name, area, value(row, header, "kaek"), value(row, header, "location"), trees, value(row, header, "notes")));
            } catch (IllegalArgumentException error) { throw new IOException("Μη έγκυρα στοιχεία στο αγροτεμάχιο " + (i + 1) + ". Δεν εισήχθη καμία εγγραφή."); }
        }
        return List.copyOf(fields);
    }
    private static String decode(byte[] bytes) throws Exception {
        String text = StandardCharsets.UTF_8.newDecoder().decode(ByteBuffer.wrap(bytes)).toString();
        return text.startsWith("\uFEFF") ? text.substring(1) : text;
    }
    private static String value(List<String> row, List<String> header, String column) { return row.get(header.indexOf(column)).trim(); }
    // Python csv.writer output: semicolon separator, doubled quotes, CRLF and embedded newlines.
    static List<List<String>> parseCsv(String text) throws IOException {
        List<List<String>> rows = new ArrayList<>(); List<String> row = new ArrayList<>();
        StringBuilder cell = new StringBuilder(); boolean quoted = false, closed = false;
        for (int i = 0; i < text.length(); i++) {
            char c = text.charAt(i);
            if (quoted) {
                if (c == '"') {
                    if (i + 1 < text.length() && text.charAt(i + 1) == '"') { cell.append('"'); i++; }
                    else { quoted = false; closed = true; }
                } else cell.append(c);
            } else if (c == ';' || c == '\n' || c == '\r') {
                row.add(cell.toString()); cell.setLength(0); closed = false;
                if (c != ';') {
                    rows.add(row); row = new ArrayList<>();
                    if (rows.size() > 5001) throw new IOException("Επιτρέπονται έως 5.000 αγροτεμάχια.");
                    if (c == '\r' && i + 1 < text.length() && text.charAt(i + 1) == '\n') i++;
                }
            } else if (c == '"' && cell.length() == 0 && !closed) quoted = true;
            else {
                if (closed || c == '"') throw new IOException("Μη έγκυρη μορφή CSV.");
                cell.append(c);
            }
        }
        if (quoted) throw new IOException("Μη ολοκληρωμένο κείμενο CSV.");
        if (closed || cell.length() > 0 || !row.isEmpty()) { row.add(cell.toString()); rows.add(row); }
        return rows;
    }
    private static boolean same(FarmStore.Field a, FarmStore.Field b) {
        return a.name().equals(b.name()) && a.area() == b.area() && a.kaek().equals(b.kaek()) && a.location().equals(b.location()) && a.trees() == b.trees() && a.notes().equals(b.notes());
    }
    public static Preview preview(FarmStore store, List<FarmStore.Field> incoming) {
        List<FarmStore.Field> known = new ArrayList<>(store.fields()), additions = new ArrayList<>();
        int identical = 0, conflicts = 0;
        for (var field : incoming) {
            List<FarmStore.Field> matches = new ArrayList<>();
            for (var existing : known) {
                if ((!field.kaek().isEmpty() && field.kaek().equalsIgnoreCase(existing.kaek())) || (field.name().equalsIgnoreCase(existing.name()) && field.location().equalsIgnoreCase(existing.location()))) matches.add(existing);
            }
            if (matches.isEmpty()) { additions.add(field); known.add(field); }
            else if (matches.size() == 1 && same(field, matches.get(0))) identical++;
            else conflicts++;
        }
        return new Preview(List.copyOf(additions), identical, conflicts);
    }
    public static Preview apply(FarmStore store, List<FarmStore.Field> incoming, File recovery) throws Exception {
        SQLiteDatabase db = store.getWritableDatabase(); db.beginTransaction();
        try {
            Preview plan = preview(store, incoming);
            if (!plan.additions().isEmpty()) {
                AtomicFile safe = new AtomicFile(recovery); FileOutputStream out = null;
                try { out = safe.startWrite(); out.write(LocalBackup.snapshot(store)); safe.finishWrite(out); }
                catch (Exception error) { if (out != null) safe.failWrite(out); throw error; }
                for (var field : plan.additions()) store.saveField(null, field.name(), field.area(), field.kaek(), field.location(), field.trees(), field.notes());
            }
            db.setTransactionSuccessful(); return plan;
        } finally { db.endTransaction(); }
    }
}
