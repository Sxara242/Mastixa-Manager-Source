"""Income/expense sort labels translate without changing financial state."""
import tempfile
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication, QLabel

from app.database import Database
from app.money import MoneyPage
from tests.language_fixture import scoped_language


RAW = "Ταξινόμηση Αποθήκευση Ω <raw> {year}"
KEYS = ["date_desc", "date_asc", "amount_asc", "amount_desc"]


class MoneySortLocalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def check_page(self, kind, initial_language, languages):
        with tempfile.TemporaryDirectory() as folder:
            db = Database(Path(folder) / "money.db")
            with scoped_language(self.app, initial_language) as controller:
                page = MoneyPage(db, kind)
                try:
                    for date, amount in (("2027-01-03", 30), ("2027-01-01", 10),
                                         ("2027-01-02", 20)):
                        if kind == "income":
                            db.execute("INSERT INTO income(entry_date,description,amount) VALUES(?,?,?)",
                                       (date, RAW, amount))
                        else:
                            db.execute("INSERT INTO expenses(entry_date,category,description,amount) VALUES(?,?,?,?)",
                                       (date, RAW, RAW, amount))
                    page.refresh()
                    page.sort_order.setCurrentIndex(page.sort_order.findData("amount_asc"))
                    page.description.setText(RAW)
                    page.search.setText(RAW)
                    with db.connect() as connection:
                        before = tuple(connection.iterdump())
                    changed = Mock()
                    page.sort_order.currentIndexChanged.connect(changed)
                    for code in languages:
                        with self.subTest(kind=kind, language=code):
                            with patch.object(db, "execute", wraps=db.execute) as write:
                                controller.set_language(code, persist=False)
                                controller.apply_to(page)
                                self.app.processEvents()
                                write.assert_not_called()
                            labels = [label.text() for label in page.findChildren(QLabel)]
                            self.assertIn("Sort" if code == "en" else "Ταξινόμηση", labels)
                            self.assertEqual(KEYS, [page.sort_order.itemData(i) for i in range(4)])
                            self.assertEqual("amount_asc", page.sort_order.currentData())
                            changed.assert_not_called()
                            self.assertEqual(RAW, page.description.text())
                            self.assertEqual(RAW, page.search.text())
                            description_column = 2 if kind == "income" else 3
                            amount_column = 5 if kind == "income" else 6
                            self.assertEqual([RAW] * 3, [page.table.item(i, description_column).text() for i in range(3)])
                            self.assertEqual(["10.00 €", "20.00 €", "30.00 €"],
                                             [page.table.item(i, amount_column).text() for i in range(3)])
                            with db.connect() as connection:
                                self.assertEqual(before, tuple(connection.iterdump()))
                finally:
                    page.close()
                    page.deleteLater()
                    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def test_income_english_startup(self):
        self.check_page("income", "en", ("en",))

    def test_expenses_english_startup(self):
        self.check_page("expenses", "en", ("en",))

    def test_income_live_language_cycle_preserves_sort_and_data(self):
        self.check_page("income", "el", ("el", "en", "el", "en"))

    def test_expenses_live_language_cycle_preserves_sort_and_data(self):
        self.check_page("expenses", "el", ("el", "en", "el", "en"))


if __name__ == "__main__":
    unittest.main()
