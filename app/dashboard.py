from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .backup_manager import BackupError, BackupManager
from .database import BASE_DIR, Database
from .ui_helpers import format_kg


class DashboardPage(QWidget):
    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db
        self.backup_manager = self._build_backup_manager()

        layout = QVBoxLayout(self)

        title = QLabel("Mastixa Manager")
        title.setObjectName("pageTitle")
        self.subtitle = QLabel("Συνολική εικόνα εκμετάλλευσης")
        self.subtitle.setObjectName("pageSubtitle")
        layout.addWidget(title)
        layout.addWidget(self.subtitle)

        grid = QGridLayout()
        self.production = self._card("Παραγωγή", "0 kg")
        self.income = self._card("Έσοδα", "0,00 €")
        self.expenses = self._card("Έξοδα", "0,00 €")
        self.balance = self._card("Καθαρό αποτέλεσμα", "0,00 €")
        grid.addWidget(self.production[0], 0, 0)
        grid.addWidget(self.income[0], 0, 1)
        grid.addWidget(self.expenses[0], 1, 0)
        grid.addWidget(self.balance[0], 1, 1)
        layout.addLayout(grid)

        safety_box = QGroupBox()
        safety_layout = QVBoxLayout(safety_box)

        safety_title = QLabel("Ασφάλεια δεδομένων")
        safety_title.setStyleSheet(
            "font-weight: 700; font-size: 15px; color: #26382f;"
        )
        safety_layout.addWidget(safety_title)

        self.backup_status = QLabel()
        self.backup_status.setWordWrap(True)
        safety_layout.addWidget(self.backup_status)

        self.auto_backup_status = QLabel()
        self.auto_backup_status.setWordWrap(True)
        self.auto_backup_status.setStyleSheet("color: #67746d;")
        safety_layout.addWidget(self.auto_backup_status)

        buttons = QHBoxLayout()

        create_button = QPushButton("Δημιουργία Backup")
        create_button.clicked.connect(self.create_backup)
        buttons.addWidget(create_button)

        restore_button = QPushButton("Επαναφορά Backup")
        restore_button.clicked.connect(self.restore_backup)
        buttons.addWidget(restore_button)

        open_button = QPushButton("Φάκελος Backups")
        open_button.clicked.connect(self.open_backup_folder)
        buttons.addWidget(open_button)

        buttons.addStretch()
        safety_layout.addLayout(buttons)

        layout.addWidget(safety_box)
        layout.addStretch()

        self.refresh()

    def _build_backup_manager(self) -> BackupManager:
        saved_dir = self.db.get_app_setting("backup_dir", "").strip()
        backup_dir = Path(saved_dir) if saved_dir else BASE_DIR / "backups"
        kwargs = {
            "database_path": self.db.path,
            "auto_keep": self.db.get_app_setting_int(
                "auto_backup_keep", 30, minimum=1, maximum=365
            ),
            "pre_restore_keep": self.db.get_app_setting_int(
                "pre_restore_keep", 10, minimum=1, maximum=100
            ),
        }
        try:
            return BackupManager(backup_dir=backup_dir, **kwargs)
        except OSError:
            # A saved external/network path may be unavailable. Never block
            # the Dashboard; fall back to the local application backup folder.
            return BackupManager(backup_dir=BASE_DIR / "backups", **kwargs)

    def _card(self, caption: str, value: str):
        box = QGroupBox()
        box.setObjectName("metricCard")
        card_layout = QVBoxLayout(box)

        caption_label = QLabel(caption)
        caption_label.setObjectName("metricCaption")

        value_label = QLabel(value)
        value_label.setObjectName("metricValue")

        card_layout.addWidget(caption_label)
        card_layout.addWidget(value_label)
        return box, value_label

    @staticmethod
    def _money(value: float) -> str:
        return (
            f"{value:,.2f} €"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    def refresh(self) -> None:
        self.backup_manager = self._build_backup_manager()
        farm_name = self.db.get_app_setting("farm_name", "").strip()
        self.subtitle.setText(
            "Συνολική εικόνα εκμετάλλευσης"
            + (f" — {farm_name}" if farm_name else "")
        )

        prod = self.db.query_one(
            "SELECT COALESCE(SUM(quantity_kg), 0) AS total FROM production"
        )
        inc = self.db.query_one(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM income"
        )
        exp = self.db.query_one(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses"
        )

        production = float(prod["total"] or 0)
        income = float(inc["total"] or 0)
        expenses = float(exp["total"] or 0)

        self.production[1].setText(format_kg(production))
        self.income[1].setText(self._money(income))
        self.expenses[1].setText(self._money(expenses))
        self.balance[1].setText(self._money(income - expenses))

        self._refresh_backup_status()

    def _refresh_backup_status(self) -> None:
        auto_enabled = self.db.get_app_setting_bool(
            "auto_backup_enabled", True
        )
        if auto_enabled:
            self.auto_backup_status.setText(
                "Αυτόματο ημερήσιο backup: ενεργό — "
                f"κρατούνται έως {self.backup_manager.auto_keep} "
                "αυτόματα backups. Τα χειροκίνητα backups δεν "
                "διαγράφονται αυτόματα."
            )
        else:
            self.auto_backup_status.setText(
                "Αυτόματο ημερήσιο backup: απενεργοποιημένο. "
                "Τα χειροκίνητα backups παραμένουν διαθέσιμα."
            )

        backups = self.backup_manager.list_backups()

        if not backups:
            self.backup_status.setText(
                "Δεν υπάρχει ακόμα αποθηκευμένο backup."
            )
            return

        latest = backups[0]
        modified = latest.stat().st_mtime
        from datetime import datetime

        timestamp = datetime.fromtimestamp(modified).strftime(
            "%d/%m/%Y %H:%M"
        )

        auto_count = len(self.backup_manager.list_auto_backups())

        self.backup_status.setText(
            f"Τελευταίο backup: {latest.name} — {timestamp}\n"
            f"Αυτόματα ημερήσια backups: {auto_count} / "
            f"{self.backup_manager.auto_keep}"
        )

    def create_backup(self) -> None:
        try:
            target = self.backup_manager.create_backup()
        except BackupError as exc:
            QMessageBox.critical(
                self,
                "Αποτυχία Backup",
                str(exc),
            )
            return

        self._refresh_backup_status()
        QMessageBox.information(
            self,
            "Backup",
            f"Το αντίγραφο δημιουργήθηκε επιτυχώς:\n{target}",
        )

    def restore_backup(self) -> None:
        backup_dir = self.backup_manager.backup_dir
        backup_dir.mkdir(parents=True, exist_ok=True)

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Επίλεξε backup για επαναφορά",
            str(backup_dir),
            "SQLite Database (*.db);;Όλα τα αρχεία (*)",
        )
        if not path:
            return

        answer = QMessageBox.warning(
            self,
            "Επαναφορά Backup",
            "Πρόκειται να αντικατασταθούν τα τρέχοντα δεδομένα "
            "με το επιλεγμένο backup.\n\n"
            "Πριν την επαναφορά θα δημιουργηθεί αυτόματα ένα νέο "
            "αντίγραφο ασφαλείας της τρέχουσας βάσης.\n\n"
            "Θέλεις να συνεχίσεις;",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            restored_from, safety_backup = (
                self.backup_manager.restore_backup(Path(path))
            )

            # Ensure any schema additions are created if restoring an older
            # compatible Mastixa Manager database.
            self.db.initialize()
            self.refresh()

        except BackupError as exc:
            QMessageBox.critical(
                self,
                "Αποτυχία επαναφοράς",
                str(exc),
            )
            return

        QMessageBox.information(
            self,
            "Επαναφορά ολοκληρώθηκε",
            "Η βάση δεδομένων επαναφέρθηκε επιτυχώς.\n\n"
            f"Επαναφορά από:\n{restored_from}\n\n"
            "Αυτόματο backup πριν την επαναφορά:\n"
            f"{safety_backup}\n\n"
            "Οι υπόλοιπες σελίδες θα ανανεωθούν όταν τις ανοίξεις.",
        )

    def open_backup_folder(self) -> None:
        folder = self.backup_manager.backup_dir
        folder.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(
            QUrl.fromLocalFile(str(folder.resolve()))
        )
