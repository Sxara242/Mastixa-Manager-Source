from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .database import Database


class ProducerPage(QWidget):
    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db
        layout = QVBoxLayout(self)
        title = QLabel("Στοιχεία παραγωγού")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        self.name = QLineEdit()
        self.tax_id = QLineEdit()
        self.phone = QLineEdit()
        self.email = QLineEdit()
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(120)

        form = QFormLayout()
        form.addRow("Ονοματεπώνυμο / Επωνυμία", self.name)
        form.addRow("ΑΦΜ", self.tax_id)
        form.addRow("Τηλέφωνο", self.phone)
        form.addRow("Email", self.email)
        form.addRow("Σημειώσεις", self.notes)
        layout.addLayout(form)

        save = QPushButton("Αποθήκευση")
        save.clicked.connect(self.save)
        layout.addWidget(save, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addStretch()
        self.load()

    def load(self) -> None:
        row = self.db.query_one("SELECT * FROM producer WHERE id=1")
        if row:
            self.name.setText(row["name"])
            self.tax_id.setText(row["tax_id"])
            self.phone.setText(row["phone"])
            self.email.setText(row["email"])
            self.notes.setPlainText(row["notes"])

    def save(self) -> None:
        self.db.execute(
            "UPDATE producer SET name=?, tax_id=?, phone=?, email=?, notes=? WHERE id=1",
            (self.name.text().strip(), self.tax_id.text().strip(), self.phone.text().strip(),
             self.email.text().strip(), self.notes.toPlainText().strip()),
        )
        QMessageBox.information(self, "Αποθήκευση", "Τα στοιχεία παραγωγού αποθηκεύτηκαν.")
