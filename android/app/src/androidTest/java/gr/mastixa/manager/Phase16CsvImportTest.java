package gr.mastixa.manager;

import org.junit.Test;
import org.json.JSONObject;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import static org.junit.Assert.*;

/** Focused portable CSV boundary tests; database apply/retry/rollback uses existing tests. */
public class Phase16CsvImportTest {
    private Map<String, JSONObject> metadata(String table, int count) throws Exception {
        return Map.of(table, new JSONObject().put("status", "exported")
                .put("file", "tables/" + table + ".csv").put("rows", count));
    }

    private List<Map<String,String>> rows(byte[] data, int count) throws Exception {
        return CatalogImport.rows("production", Map.of("tables/production.csv", data),
                metadata("production", count), List.of("id", "entry_date"));
    }

    private ProductionImport.Data production(String body) throws Exception {
        String csv = "id;entry_date;product;field_id;quantity_kg;notes\r\n" + body;
        return ProductionImport.read(Map.of("tables/production.csv", csv.getBytes(StandardCharsets.UTF_8)),
                metadata("production", WindowsImport.parseCsv(body).size()),
                List.of(new CatalogStore.Product("p", "Μαστίχα", "kg", true)), List.of(), List.of());
    }

    @Test public void validUnicodeDecimalLeapDateAndExtraColumn() throws Exception {
        var result = rows(("\uFEFFid;entry_date;extra\r\n001;2024-02-29;\"Ελλάδα; \"\"Χίος\"\"\r\nγραμμή\"\r\n")
                .getBytes(StandardCharsets.UTF_8), 1);
        assertEquals("001", result.get(0).get("id"));
        assertEquals("Ελλάδα; \"Χίος\"\r\nγραμμή", result.get(0).get("extra"));
        var harvest = production("001;2024-02-29;Μαστίχα;;12.375;Ελληνικά\r\n").harvests().get(0);
        assertEquals(12.375, harvest.quantity(), 0);
        assertEquals("2024-02-29", harvest.date());
        assertEquals("001", harvest.windowsId());
        assertEquals("Ελληνικά", harvest.notes());
    }

    @Test public void malformedColumnsRowsQuotesCountsAndUtf8Rejected() throws Exception {
        for (String csv : List.of(
                "id;other\r\n1;x\r\n", "id;entry_date;id\r\n1;x;1\r\n",
                "id;entry_date\r\n1\r\n", "id;entry_date\r\n1;x;extra\r\n",
                "id;entry_date\r\n1;\"unterminated", "id;entry_date\r\n1;\"date\"junk\r\n",
                "id;entry_date\r\n1;da\"te\r\n", "id;entry_date\r\n")) {
            try { rows(csv.getBytes(StandardCharsets.UTF_8), 1); fail(csv); }
            catch (IOException expected) { }
        }
        try { rows(new byte[]{(byte)0xc3, 0x28}, 1); fail("invalid UTF-8"); }
        catch (IOException expected) { }
    }

    @Test public void invalidNumbersAndDatesRejectEntireParsedBatch() throws Exception {
        String first = "1;2024-02-29;Μαστίχα;;1.25;valid first row\r\n";
        for (String number : List.of("NaN", "Infinity", "1e309", "-1", "12,375", "")) {
            try { production(first + "2;2024-02-29;Μαστίχα;;" + number + ";bad\r\n"); fail(number); }
            catch (IOException | IllegalArgumentException expected) { }
        }
        for (String date : List.of("", "2025-02-29", "2024-13-01", "29/02/2024", "2024-02-29T12:00:00Z")) {
            try { production(first + "2;" + date + ";Μαστίχα;;1;bad\r\n"); fail(date); }
            catch (IOException | IllegalArgumentException expected) { }
        }
    }

    @Test public void duplicateSourceIdsRejectedButDistinctSameDateRowsRetained() throws Exception {
        String first = "1;2024-02-29;Μαστίχα;;1.25;first\r\n";
        try { production(first + first); fail("duplicate id"); }
        catch (IOException expected) { }
        assertEquals(2, production(first + "2;2024-02-29;Μαστίχα;;1.25;first\r\n").harvests().size());
    }
}
