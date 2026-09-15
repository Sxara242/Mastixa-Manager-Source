from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "android" / "app" / "src" / "main" / "java" / "gr" / "mastixa" / "manager" / "MainActivity.java"
DOCUMENT_STORE = ROOT / "android" / "app" / "src" / "main" / "java" / "gr" / "mastixa" / "manager" / "DocumentStore.java"
OFFLINE_OCR = ROOT / "android" / "app" / "src" / "main" / "java" / "gr" / "mastixa" / "manager" / "OfflineOcr.java"


class AndroidMainLocalizationBoundaryTests(unittest.TestCase):
    def test_raw_backend_exception_text_is_not_rendered_by_main_ui_boundaries(self):
        source = MAIN.read_text(encoding="utf-8")
        forbidden = (
            "String.valueOf(error.getMessage())",
            "backupMessage(String.valueOf(e.getMessage()))",
            "backupMessage(e.getMessage()==null?",
            "words(error.getMessage(),",
            "words(e.getMessage(),",
            "+failure)",
            "catch(Exception e){backupMessage(e.getMessage());}",
        )
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, source)

    def test_unavailable_page_status_has_a_greek_source(self):
        source = MAIN.read_text(encoding="utf-8")
        self.assertNotIn('text("UNDER CONSTRUCTION",14,true)', source)
        self.assertIn('words("ΥΠΟ ΚΑΤΑΣΚΕΥΗ","UNDER CONSTRUCTION")', source)

    def test_restore_and_catalog_confirmations_use_greek_backup_wording(self):
        source = MAIN.read_text(encoding="utf-8")
        self.assertNotIn("Τα παλιά backup αδειάζουν", source)
        self.assertNotIn("Θα κρατηθεί backup πριν τις προσθήκες.", source)
        self.assertIn("Τα παλιά αντίγραφα ασφαλείας αδειάζουν", source)
        self.assertIn("Θα κρατηθεί αντίγραφο ασφαλείας πριν τις προσθήκες.", source)
        self.assertIn("Older backups clear any newer registries they do not contain. An internal backup will be kept.", source)
        self.assertIn("A backup is kept before additions.", source)

    def test_producer_and_partner_email_labels_are_localized_without_translating_values(self):
        source = MAIN.read_text(encoding="utf-8")
        self.assertNotIn('textValue("Email: "+p.email()', source)
        self.assertNotIn('var email=input(form,"Email",p.email()', source)
        self.assertNotIn('words("Τηλέφωνο","Phone"),"Email",', source)
        self.assertIn('words("Ηλεκτρονικό ταχυδρομείο: ","Email: ")+p.email()', source)
        self.assertIn('input(form,words("Ηλεκτρονικό ταχυδρομείο","Email"),p.email()', source)
        self.assertIn('words("Ηλεκτρονικό ταχυδρομείο","Email")', source)
        self.assertNotIn('t(p.email())', source)
        self.assertIn('append(i==1?partnerType(p.type()):values[i])', source)

    def test_ocr_status_codes_are_localized_only_at_display_boundary(self):
        source = MAIN.read_text(encoding="utf-8")
        document_store = DOCUMENT_STORE.read_text(encoding="utf-8")
        offline_ocr = OFFLINE_OCR.read_text(encoding="utf-8")
        self.assertIn('case "pending"->words("Σε αναμονή","Pending")', source)
        self.assertIn('case "review_required"->words("Χρειάζεται έλεγχος","Review required")', source)
        self.assertIn('case "no_text"->words("Δεν βρέθηκε κείμενο","No text found")', source)
        self.assertIn('ocrStatusLabel(m.optString("ocr_status"))', source)
        self.assertNotIn('"\\nOCR: "+m.optString("ocr_status")', source)
        self.assertIn('.put("ocr_status","pending")', document_store)
        self.assertIn('text.isBlank()?"no_text":"review_required"', offline_ocr)


if __name__ == "__main__":
    unittest.main()
