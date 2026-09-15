package gr.mastixa.manager;

import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import static org.junit.Assert.*;

public class AppLanguageWordingTest {
    @Test public void exactUiWordingIsLocalizedWithoutChangingDomainValues() {
        var context=InstrumentationRegistry.getInstrumentation().getTargetContext();
        var el=new AppLanguage(context,"el");
        var en=new AppLanguage(context,"en");

        assertEquals("Πίνακας ελέγχου",el.t("Dashboard"));
        assertEquals("Πίνακας ελέγχου · Συνολική εικόνα",el.t("Dashboard · Συνολική εικόνα"));
        assertEquals("Αντίγραφα",el.t("Backup"));
        assertEquals("Τοπικό αντίγραφο ασφαλείας  ›",el.t("Τοπικό backup  ›"));
        assertEquals("Αναφορά Πωλήσεων & Αποθέματος",el.t("Αναφορά Πωλήσεων & Stock"));
        assertEquals("Είδος συντήρησης *",el.t("Είδος service *"));
        assertEquals("Επόμενη συντήρηση (YYYY-MM-DD, προαιρετική)",el.t("Επόμενο service (YYYY-MM-DD, προαιρετικό)"));

        assertEquals("Profile and language",en.t("Προφίλ και γλώσσα"));
        assertEquals("Records · Cultivation",en.t("Καταχωρήσεις · Καλλιέργεια"));
        assertEquals("We're building this section",en.t("Ετοιμάζουμε αυτή την ενότητα"));
        assertEquals("Crop Program  ›",en.t("Πρόγραμμα Καλλιέργειας  ›"));
        assertEquals("Category: Records · Cultivation",en.t("Κατηγορία: Καταχωρήσεις · Καλλιέργεια"));
        assertEquals("Reports · Inventory & Fields\nUnder construction",en.t("Αναφορές · Αποθήκη & Αγροτεμάχια\nΥπό κατασκευή"));

        String domain="Παραγωγή / Αποθήκη — RAW_USER_VALUE";
        assertEquals(domain,el.t(domain));
        assertEquals(domain,en.t(domain));
    }
}
