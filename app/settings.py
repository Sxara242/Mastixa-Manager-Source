from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QApplication,
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .database import BASE_DIR, Database
from .appearance_theme import DARK_ICON, LIGHT_ICON, ThemeController
from .language import LanguageController
from .app_logging import log_path
from .profile_manager import ProfileError, ProfileManager, UserProfile


def profile_icon(profile: UserProfile, size: int = 40) -> QIcon:
    if profile.avatar_path and profile.avatar_path.is_file():
        return QIcon(str(profile.avatar_path))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(profile.color))
    painter.drawEllipse(1, 1, size - 2, size - 2)
    painter.setPen(QColor("#FFFFFF"))
    font = QFont()
    font.setBold(True)
    font.setPixelSize(max(12, size // 2))
    painter.setFont(font)
    initials = "".join(word[0] for word in profile.name.split()[:2]).upper() or "Π"
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, initials)
    painter.end()
    return QIcon(pixmap)


class ProfileSelectionDialog(QDialog):
    """Small login-like chooser shown before the main window."""

    def __init__(
        self,
        profiles: ProfileManager,
        language: LanguageController | None = None,
    ) -> None:
        super().__init__()
        self.profiles = profiles
        self.language = language or LanguageController(
            QApplication.instance(), profiles
        )
        self.setWindowTitle("Επιλογή προφίλ")
        self.setMinimumWidth(440)
        layout = QVBoxLayout(self)

        language_row = QHBoxLayout()
        language_label = QLabel("🌐")
        language_label.setToolTip("Επιλογή γλώσσας")
        language_row.addWidget(language_label)
        self.language_combo = QComboBox()
        self.language_combo.setProperty("mastixaI18nSkipItems", True)
        for pack in self.language.available_languages():
            self.language_combo.addItem(pack.native_name, pack.code)
        selected_language = self.language_combo.findData(self.language.language)
        self.language_combo.setCurrentIndex(max(0, selected_language))
        self.language_combo.currentIndexChanged.connect(
            self._language_changed
        )
        language_row.addWidget(self.language_combo, 1)
        layout.addLayout(language_row)

        title = QLabel("Ποιος θα χρησιμοποιήσει το Mastixa;")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        description = QLabel(
            "Επίλεξε το προσωπικό προφίλ για να ανοίξει η δική του βάση δεδομένων."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        self.combo = QComboBox()
        self.combo.setProperty("mastixaI18nSkipItems", True)
        self.combo.setIconSize(QSize(36, 36))
        for profile in profiles.profiles():
            self.combo.addItem(profile_icon(profile), profile.name, profile.id)
        self.combo.setCurrentIndex(max(0, self.combo.findData(profiles.active_profile.id)))
        self.combo.currentIndexChanged.connect(self._profile_changed)
        layout.addWidget(self.combo)
        self.pin_label = QLabel("PIN")
        self.pin_edit = QLineEdit()
        self.pin_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.pin_edit.setMaxLength(8)
        self.pin_edit.setPlaceholderText("4–8 ψηφία")
        self.pin_edit.returnPressed.connect(self.accept)
        layout.addWidget(self.pin_label)
        layout.addWidget(self.pin_edit)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Open | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Open).setText("Άνοιγμα")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._sync_pin()

    @property
    def selected_profile_id(self) -> str:
        return str(self.combo.currentData())

    @property
    def selected_language(self) -> str:
        return str(self.language_combo.currentData() or "el")

    def _language_changed(self, *_args) -> None:
        self.language.set_language(self.selected_language, persist=False)

    def _profile_changed(self, *_args) -> None:
        try:
            profile = self.profiles.get(self.selected_profile_id)
        except ProfileError:
            self._sync_pin()
            return
        index = self.language_combo.findData(profile.language)
        if index >= 0:
            self.language_combo.blockSignals(True)
            self.language_combo.setCurrentIndex(index)
            self.language_combo.blockSignals(False)
            self.language.set_language(profile.language, persist=False)
        self._sync_pin()

    def _sync_pin(self, *_args) -> None:
        protected = self.profiles.has_pin(self.selected_profile_id)
        self.pin_label.setVisible(protected)
        self.pin_edit.setVisible(protected)
        self.pin_edit.clear()
        if protected:
            self.pin_edit.setFocus()

    def accept(self) -> None:
        if not self.profiles.verify_pin(self.selected_profile_id, self.pin_edit.text()):
            QMessageBox.warning(self, "PIN", "Το PIN δεν είναι σωστό.")
            self.pin_edit.selectAll()
            self.pin_edit.setFocus()
            return
        self.profiles.set_language(
            self.selected_profile_id,
            self.selected_language,
        )
        super().accept()


class SettingsPage(QWidget):
    """Application-wide settings kept separate from per-product settings."""

    profile_switch_requested = Signal(str)

    def __init__(
        self,
        db: Database,
        theme: ThemeController,
        profiles: ProfileManager,
        language: LanguageController,
    ) -> None:
        super().__init__()
        self.db = db
        self.theme = theme
        self.profiles = profiles
        self.language = language

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        outer.addWidget(scroll)

        content = QWidget()
        content.setObjectName("settingsContent")
        content.setStyleSheet(
            "QWidget#settingsContent { background: #f5f6f3; }"
        )
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 18, 16, 20)
        layout.setSpacing(12)
        scroll.setWidget(content)

        title = QLabel("Ρυθμίσεις")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        subtitle = QLabel(
            "Γενικές ρυθμίσεις εφαρμογής, εκμετάλλευσης και αντιγράφων ασφαλείας"
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        layout.addWidget(self.tabs)

        self._build_general_tab()
        self._build_backup_tab()
        self._build_open_source_tab()

        actions = QHBoxLayout()
        self.save_button = QPushButton("Αποθήκευση ρυθμίσεων")
        self.save_button.clicked.connect(self.save)
        actions.addWidget(self.save_button)

        reset_button = QPushButton("Επαναφορά προεπιλογών")
        reset_button.clicked.connect(self.reset_defaults)
        actions.addWidget(reset_button)
        actions.addStretch()
        layout.addLayout(actions)
        layout.addStretch()

        self.refresh()

    def _build_general_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(12)

        profile_box = QGroupBox("Προφίλ χρηστών")
        profile_layout = QVBoxLayout(profile_box)
        profile_layout.setSpacing(10)

        profile_intro = QLabel(
            "Κάθε προφίλ έχει ανεξάρτητη βάση δεδομένων, αγροτεμάχια, "
            "καταχωρήσεις, συνεργάτες, προϊόντα και αντίγραφα ασφαλείας."
        )
        profile_intro.setWordWrap(True)
        profile_layout.addWidget(profile_intro)

        profile_row = QHBoxLayout()
        profile_row.addWidget(QLabel("Προφίλ"))
        self.profile_combo = QComboBox()
        self.profile_combo.setProperty("mastixaI18nSkipItems", True)
        self.profile_combo.setIconSize(QSize(28, 28))
        self.profile_combo.setMinimumContentsLength(16)
        self.profile_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.profile_combo.currentIndexChanged.connect(
            self._update_profile_actions
        )
        profile_row.addWidget(self.profile_combo, 1)

        self.activate_profile_button = QPushButton("Ενεργοποίηση")
        self.activate_profile_button.setMaximumWidth(125)
        self.activate_profile_button.clicked.connect(self.activate_profile)
        profile_layout.addLayout(profile_row)

        profile_actions = QHBoxLayout()
        profile_actions.addWidget(self.activate_profile_button)
        self.create_profile_button = QPushButton("Νέο προφίλ")
        self.create_profile_button.clicked.connect(self.create_profile)
        profile_actions.addWidget(self.create_profile_button)

        self.rename_profile_button = QPushButton("Μετονομασία")
        self.rename_profile_button.clicked.connect(self.rename_profile)
        profile_actions.addWidget(self.rename_profile_button)

        self.archive_profile_button = QPushButton("Διαγραφή προφίλ")
        self.archive_profile_button.clicked.connect(self.archive_profile)
        profile_actions.addWidget(self.archive_profile_button)
        profile_actions.addStretch()
        profile_layout.addLayout(profile_actions)

        identity_row = QHBoxLayout()
        self.profile_avatar = QLabel()
        self.profile_avatar.setFixedSize(56, 56)
        self.profile_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        identity_row.addWidget(self.profile_avatar)

        identity_actions = QVBoxLayout()
        identity_top = QHBoxLayout()
        self.choose_avatar_button = QPushButton("Εικόνα…")
        self.choose_avatar_button.clicked.connect(self.choose_profile_avatar)
        identity_top.addWidget(self.choose_avatar_button)
        self.remove_avatar_button = QPushButton("Αφαίρεση εικόνας")
        self.remove_avatar_button.clicked.connect(self.remove_profile_avatar)
        identity_top.addWidget(self.remove_avatar_button)
        self.profile_color_button = QPushButton("Χρώμα…")
        self.profile_color_button.clicked.connect(self.choose_profile_color)
        identity_top.addWidget(self.profile_color_button)
        identity_top.addStretch()
        identity_actions.addLayout(identity_top)

        security_row = QGridLayout()
        self.profile_pin_button = QPushButton("Ορισμός PIN")
        self.profile_pin_button.clicked.connect(self.change_profile_pin)
        security_row.addWidget(self.profile_pin_button, 0, 0)
        self.remove_pin_button = QPushButton("Αφαίρεση PIN")
        self.remove_pin_button.clicked.connect(self.remove_profile_pin)
        security_row.addWidget(self.remove_pin_button, 0, 1)
        self.export_profile_button = QPushButton("Εξαγωγή προφίλ…")
        self.export_profile_button.clicked.connect(self.export_profile)
        security_row.addWidget(self.export_profile_button, 1, 0)
        self.import_profile_button = QPushButton("Εισαγωγή προφίλ…")
        self.import_profile_button.clicked.connect(self.import_profile)
        security_row.addWidget(self.import_profile_button, 1, 1)
        security_row.setColumnStretch(2, 1)
        identity_actions.addLayout(security_row)
        identity_row.addLayout(identity_actions, 1)
        profile_layout.addLayout(identity_row)

        self.ask_profile_on_startup = QCheckBox(
            "Επιλογή προφίλ κατά την εκκίνηση"
        )
        self.ask_profile_on_startup.toggled.connect(
            self.profiles.set_ask_on_startup
        )
        profile_layout.addWidget(self.ask_profile_on_startup)

        self.profile_status = QLabel()
        self.profile_status.setWordWrap(True)
        self.profile_status.setMinimumWidth(0)
        self.profile_status.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Preferred,
        )
        profile_layout.addWidget(self.profile_status)
        layout.addWidget(profile_box)

        appearance_box = QGroupBox("Εμφάνιση εφαρμογής")
        appearance_layout = QVBoxLayout(appearance_box)
        appearance_layout.setSpacing(10)

        buttons = QHBoxLayout()
        buttons.setSpacing(14)
        self.light_theme_button = self._theme_button(
            "Φωτεινή λειτουργία", LIGHT_ICON
        )
        self.dark_theme_button = self._theme_button(
            "Σκοτεινή λειτουργία", DARK_ICON
        )
        self.light_theme_button.clicked.connect(
            lambda: self.theme.set_theme("light")
        )
        self.dark_theme_button.clicked.connect(
            lambda: self.theme.set_theme("dark")
        )
        buttons.addWidget(self.light_theme_button, 1)
        buttons.addWidget(self.dark_theme_button, 1)
        appearance_layout.addLayout(buttons)

        self.theme_status = QLabel()
        self.theme_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        appearance_layout.addWidget(self.theme_status)
        layout.addWidget(appearance_box)
        self.theme.theme_changed.connect(self._sync_theme_controls)
        self._sync_theme_controls(self.theme.theme)

        language_box = QGroupBox("Γλώσσα εφαρμογής")
        language_layout = QVBoxLayout(language_box)
        language_layout.setSpacing(10)
        language_buttons = QHBoxLayout()
        language_buttons.setSpacing(14)
        self.language_buttons: dict[str, QToolButton] = {}
        for pack in self.language.available_languages():
            button = QToolButton()
            button.setProperty("appearanceChoice", True)
            button.setProperty("mastixaI18nSkipText", True)
            button.setText(pack.native_name)
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.setToolButtonStyle(
                Qt.ToolButtonStyle.ToolButtonTextOnly
            )
            button.setMinimumHeight(58)
            button.clicked.connect(
                lambda _checked=False, code=pack.code: self.language.set_language(code)
            )
            self.language_buttons[pack.code] = button
            language_buttons.addWidget(button, 1)
        language_layout.addLayout(language_buttons)
        language_note = QLabel(
            "Η γλώσσα αλλάζει αμέσως και αποθηκεύεται ξεχωριστά για κάθε προφίλ."
        )
        language_note.setWordWrap(True)
        language_layout.addWidget(language_note)
        self.language_status = QLabel()
        self.language_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        language_layout.addWidget(self.language_status)
        layout.addWidget(language_box)
        self.language.language_changed.connect(self._sync_language_controls)
        self._sync_language_controls(self.language.language)

        farm_box = QGroupBox("Στοιχεία εκμετάλλευσης")
        form = QFormLayout(farm_box)

        self.farm_name = QLineEdit()
        self.farm_name.setPlaceholderText(
            "π.χ. Κτήμα Χίου — προαιρετικό"
        )
        form.addRow("Όνομα εκμετάλλευσης", self.farm_name)

        self.database_path = QLineEdit()
        self.database_path.setReadOnly(True)
        self.database_path.setText(str(self.db.path.resolve()))
        form.addRow("Βάση δεδομένων", self.database_path)

        info = QLabel(
            "Τα στοιχεία παραγωγού (όνομα, ΑΦΜ, τηλέφωνο κ.λπ.) παραμένουν "
            "στην υπάρχουσα σελίδα «Παραγωγός». Εδώ αποθηκεύονται μόνο "
            "ρυθμίσεις ολόκληρης της εφαρμογής."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #6A7A72;")
        layout.addWidget(farm_box)
        layout.addWidget(info)

        diagnostics_box = QGroupBox("Διαγνωστικά & Log")
        diagnostics_form = QFormLayout(diagnostics_box)
        self.diagnostics_path = QLineEdit()
        self.diagnostics_path.setReadOnly(True)
        current_log = log_path()
        self.diagnostics_path.setText(str(current_log or ""))
        diagnostics_form.addRow("Αρχείο log", self.diagnostics_path)
        open_log_button = QPushButton("Άνοιγμα φακέλου log")
        open_log_button.clicked.connect(self.open_log_folder)
        diagnostics_form.addRow("", open_log_button)
        diagnostics_note = QLabel(
            "Το τεχνικό log έχει περιορισμένο μέγεθος και δεν καταγράφει PIN "
            "ή περιεχόμενο των καταχωρήσεων."
        )
        diagnostics_note.setWordWrap(True)
        diagnostics_form.addRow("", diagnostics_note)
        layout.addWidget(diagnostics_box)
        layout.addStretch()

        self.tabs.addTab(tab, "Γενικά")

    def _refresh_profiles(self, selected_id: str | None = None) -> None:
        if not hasattr(self, "profile_combo"):
            return
        if selected_id is None:
            selected_id = self.profile_combo.currentData()
        if selected_id is None:
            selected_id = self.profiles.active_profile.id

        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        selected_index = -1
        for profile in self.profiles.profiles():
            suffix = (
                self.language.translate(" — ενεργό")
                if profile.is_active
                else ""
            )
            self.profile_combo.addItem(
                profile_icon(profile, 32), profile.name + suffix, profile.id
            )
            if profile.id == selected_id:
                selected_index = self.profile_combo.count() - 1
        if selected_index < 0:
            selected_index = self.profile_combo.findData(
                self.profiles.active_profile.id
            )
        self.profile_combo.setCurrentIndex(max(0, selected_index))
        self.profile_combo.blockSignals(False)
        self._update_profile_actions()

    def _selected_profile_id(self) -> str | None:
        value = self.profile_combo.currentData()
        return str(value) if value else None

    def _update_profile_actions(self, *_args) -> None:
        profile_id = self._selected_profile_id()
        if profile_id is None:
            self.activate_profile_button.setEnabled(False)
            self.rename_profile_button.setEnabled(False)
            self.archive_profile_button.setEnabled(False)
            self.profile_status.clear()
            return
        try:
            profile = self.profiles.get(profile_id)
        except ProfileError:
            self._refresh_profiles()
            return

        self.activate_profile_button.setEnabled(not profile.is_active)
        self.rename_profile_button.setEnabled(True)
        self.archive_profile_button.setEnabled(
            not profile.is_active
            and profile.id != self.profiles.DEFAULT_ID
        )
        self.profile_avatar.setPixmap(
            profile_icon(profile, 52).pixmap(QSize(52, 52))
        )
        self.profile_color_button.setStyleSheet(
            f"border-left: 14px solid {profile.color};"
        )
        self.remove_avatar_button.setEnabled(bool(profile.avatar_path))
        self.profile_pin_button.setText(
            "Αλλαγή PIN" if profile.has_pin else "Ορισμός PIN"
        )
        self.remove_pin_button.setEnabled(profile.has_pin)
        state = "Ενεργό προφίλ" if profile.is_active else "Ανενεργό προφίλ"
        pin_state = "PIN ενεργό" if profile.has_pin else "χωρίς PIN"
        self.profile_status.setText(
            f"{state} · {pin_state}\nΒάση: {profile.database_path}"
        )

    def create_profile(self) -> None:
        name, accepted = QInputDialog.getText(
            self,
            "Νέο προφίλ",
            "Όνομα χρήστη ή προφίλ:",
        )
        if not accepted:
            return
        try:
            profile = self.profiles.create(name)
        except ProfileError as exc:
            QMessageBox.warning(self, "Νέο προφίλ", str(exc))
            return
        self._refresh_profiles(profile.id)
        QMessageBox.information(
            self,
            "Νέο προφίλ",
            f"Δημιουργήθηκε το προφίλ «{profile.name}» με κενή, "
            "ανεξάρτητη βάση δεδομένων.\n\n"
            "Πάτησε «Ενεργοποίηση» για να μεταβείς σε αυτό.",
        )

    def rename_profile(self) -> None:
        profile_id = self._selected_profile_id()
        if profile_id is None:
            return
        profile = self.profiles.get(profile_id)
        name, accepted = QInputDialog.getText(
            self,
            "Μετονομασία προφίλ",
            "Νέο όνομα:",
            text=profile.name,
        )
        if not accepted:
            return
        try:
            renamed = self.profiles.rename(profile_id, name)
        except ProfileError as exc:
            QMessageBox.warning(self, "Μετονομασία προφίλ", str(exc))
            return
        self._refresh_profiles(renamed.id)

    def choose_profile_avatar(self) -> None:
        profile_id = self._selected_profile_id()
        if profile_id is None:
            return
        selected, _filter = QFileDialog.getOpenFileName(
            self,
            "Εικόνα προφίλ",
            "",
            "Εικόνες (*.png *.jpg *.jpeg *.webp *.bmp)",
        )
        if not selected:
            return
        try:
            self.profiles.set_avatar(profile_id, Path(selected))
        except ProfileError as exc:
            QMessageBox.warning(self, "Εικόνα προφίλ", str(exc))
            return
        self._refresh_profiles(profile_id)

    def remove_profile_avatar(self) -> None:
        profile_id = self._selected_profile_id()
        if profile_id is None:
            return
        self.profiles.set_avatar(profile_id, None)
        self._refresh_profiles(profile_id)

    def choose_profile_color(self) -> None:
        profile_id = self._selected_profile_id()
        if profile_id is None:
            return
        profile = self.profiles.get(profile_id)
        color = QColorDialog.getColor(QColor(profile.color), self, "Χρώμα προφίλ")
        if not color.isValid():
            return
        self.profiles.set_color(profile_id, color.name())
        self._refresh_profiles(profile_id)

    def _request_profile_pin(self, profile_id: str, title: str) -> bool:
        if not self.profiles.has_pin(profile_id):
            return True
        pin, accepted = QInputDialog.getText(
            self,
            title,
            "PIN προφίλ:",
            QLineEdit.EchoMode.Password,
        )
        if not accepted:
            return False
        if not self.profiles.verify_pin(profile_id, pin):
            QMessageBox.warning(self, title, "Το PIN δεν είναι σωστό.")
            return False
        return True

    def change_profile_pin(self) -> None:
        profile_id = self._selected_profile_id()
        if profile_id is None or not self._request_profile_pin(profile_id, "PIN προφίλ"):
            return
        pin, accepted = QInputDialog.getText(
            self,
            "Νέο PIN",
            "Νέο PIN (4–8 ψηφία):",
            QLineEdit.EchoMode.Password,
        )
        if not accepted:
            return
        confirmation, accepted = QInputDialog.getText(
            self,
            "Επιβεβαίωση PIN",
            "Γράψε ξανά το νέο PIN:",
            QLineEdit.EchoMode.Password,
        )
        if not accepted:
            return
        if pin != confirmation:
            QMessageBox.warning(self, "PIN", "Τα δύο PIN δεν είναι ίδια.")
            return
        try:
            self.profiles.set_pin(profile_id, pin)
        except ProfileError as exc:
            QMessageBox.warning(self, "PIN", str(exc))
            return
        self._refresh_profiles(profile_id)
        QMessageBox.information(self, "PIN", "Το PIN αποθηκεύτηκε με ασφάλεια.")

    def remove_profile_pin(self) -> None:
        profile_id = self._selected_profile_id()
        if profile_id is None or not self._request_profile_pin(profile_id, "Αφαίρεση PIN"):
            return
        answer = QMessageBox.question(
            self,
            "Αφαίρεση PIN",
            "Να αφαιρεθεί η προστασία PIN από αυτό το προφίλ;",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.profiles.clear_pin(profile_id)
        self._refresh_profiles(profile_id)

    def export_profile(self) -> None:
        profile_id = self._selected_profile_id()
        if profile_id is None or not self._request_profile_pin(profile_id, "Εξαγωγή προφίλ"):
            return
        profile = self.profiles.get(profile_id)
        selected, _filter = QFileDialog.getSaveFileName(
            self,
            "Εξαγωγή προφίλ",
            f"{profile.name}.mastixaprofile",
            "Προφίλ Mastixa (*.mastixaprofile)",
        )
        if not selected:
            return
        try:
            exported = self.profiles.export_profile(profile_id, Path(selected))
        except ProfileError as exc:
            QMessageBox.warning(self, "Εξαγωγή προφίλ", str(exc))
            return
        QMessageBox.information(
            self, "Εξαγωγή προφίλ", f"Το πλήρες προφίλ αποθηκεύτηκε εδώ:\n{exported}"
        )

    def import_profile(self) -> None:
        selected, _filter = QFileDialog.getOpenFileName(
            self,
            "Εισαγωγή προφίλ",
            "",
            "Προφίλ Mastixa (*.mastixaprofile)",
        )
        if not selected:
            return
        try:
            profile = self.profiles.import_profile(Path(selected))
        except ProfileError as exc:
            QMessageBox.warning(self, "Εισαγωγή προφίλ", str(exc))
            return
        self._refresh_profiles(profile.id)
        QMessageBox.information(
            self,
            "Εισαγωγή προφίλ",
            f"Το προφίλ «{profile.name}» εισήχθη με τη δική του βάση δεδομένων.",
        )

    def archive_profile(self) -> None:
        profile_id = self._selected_profile_id()
        if profile_id is None:
            return
        profile = self.profiles.get(profile_id)
        if not self._request_profile_pin(profile_id, "Διαγραφή προφίλ"):
            return
        answer = QMessageBox.warning(
            self,
            "Διαγραφή προφίλ",
            f"Να αφαιρεθεί το προφίλ «{profile.name}»;\n\n"
            "Η βάση και τα backups του θα μεταφερθούν σε φάκελο "
            "ανάκτησης και δεν θα διαγραφούν οριστικά.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            recovery_path = self.profiles.archive(profile_id)
        except ProfileError as exc:
            QMessageBox.warning(self, "Διαγραφή προφίλ", str(exc))
            return
        self._refresh_profiles()
        QMessageBox.information(
            self,
            "Το προφίλ αφαιρέθηκε",
            f"Τα αρχεία του παραμένουν ανακτήσιμα εδώ:\n{recovery_path}",
        )

    def activate_profile(self) -> None:
        profile_id = self._selected_profile_id()
        if profile_id is None:
            return
        profile = self.profiles.get(profile_id)
        if profile.is_active:
            return
        if not self._request_profile_pin(profile_id, "Ενεργοποίηση προφίλ"):
            return
        answer = QMessageBox.question(
            self,
            "Ενεργοποίηση προφίλ",
            f"Να ενεργοποιηθεί το προφίλ «{profile.name}»;\n\n"
            "Το παράθυρο θα ανανεωθεί αμέσως με την ανεξάρτητη βάση του. "
            "Αποθήκευσε πρώτα τυχόν φόρμες που επεξεργάζεσαι.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.profile_switch_requested.emit(profile_id)

    def _theme_button(self, text: str, icon_path: Path) -> QToolButton:
        button = QToolButton()
        button.setProperty("appearanceChoice", True)
        button.setText(text)
        button.setCheckable(True)
        button.setAutoExclusive(True)
        button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        button.setIcon(QIcon(str(icon_path)))
        button.setIconSize(QSize(36, 36))
        button.setMinimumHeight(72)
        return button

    def _sync_theme_controls(self, theme: str) -> None:
        is_dark = theme == "dark"
        for button, checked in (
            (self.light_theme_button, not is_dark),
            (self.dark_theme_button, is_dark),
        ):
            button.blockSignals(True)
            button.setChecked(checked)
            button.blockSignals(False)
            button.setProperty("themeActive", checked)
            button.style().unpolish(button)
            button.style().polish(button)
        active = "Σκοτεινή" if is_dark else "Φωτεινή"
        self.theme_status.setText(f"Ενεργή επιλογή: {active} λειτουργία")

    def _sync_language_controls(self, language: str) -> None:
        for code, button in self.language_buttons.items():
            checked = code == language
            button.blockSignals(True)
            button.setChecked(checked)
            button.blockSignals(False)
            button.setProperty("themeActive", checked)
            button.style().unpolish(button)
            button.style().polish(button)
        self.language_status.setText(
            f"Ενεργή γλώσσα: {self.language.native_name(language)}"
        )
        self._refresh_profiles()

    def _build_backup_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(12)

        backup_box = QGroupBox("Αυτόματα αντίγραφα ασφαλείας")
        form = QFormLayout(backup_box)

        self.auto_backup_enabled = QCheckBox(
            "Ενεργοποίηση αυτόματου ημερήσιου backup"
        )
        self.auto_backup_enabled.toggled.connect(
            self._update_backup_controls
        )
        form.addRow("", self.auto_backup_enabled)

        self.auto_backup_keep = QSpinBox()
        self.auto_backup_keep.setRange(1, 365)
        self.auto_backup_keep.setSuffix(" αντίγραφα")
        form.addRow(
            "Διατήρηση αυτόματων backups",
            self.auto_backup_keep,
        )

        self.pre_restore_keep = QSpinBox()
        self.pre_restore_keep.setRange(1, 100)
        self.pre_restore_keep.setSuffix(" αντίγραφα")
        form.addRow(
            "Backups πριν από επαναφορά",
            self.pre_restore_keep,
        )

        folder_row = QWidget()
        folder_layout = QHBoxLayout(folder_row)
        folder_layout.setContentsMargins(0, 0, 0, 0)
        folder_layout.setSpacing(6)

        self.backup_dir = QLineEdit()
        folder_layout.addWidget(self.backup_dir, 1)

        browse_button = QPushButton("Επιλογή…")
        browse_button.clicked.connect(self.choose_backup_folder)
        folder_layout.addWidget(browse_button)

        default_button = QPushButton("Προεπιλογή")
        default_button.clicked.connect(self.use_default_backup_folder)
        folder_layout.addWidget(default_button)

        form.addRow("Φάκελος backups", folder_row)

        open_folder_button = QPushButton("Άνοιγμα φακέλου backups")
        open_folder_button.clicked.connect(self.open_backup_folder)
        form.addRow("", open_folder_button)

        note = QLabel(
            "Τα χειροκίνητα backups δεν διαγράφονται αυτόματα. Η αλλαγή "
            "φακέλου ή πολιτικής backup εφαρμόζεται αμέσως στις επόμενες "
            "λειτουργίες backup."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #6A7A72;")

        layout.addWidget(backup_box)
        layout.addWidget(note)
        layout.addStretch()
        self.tabs.addTab(tab, "Αντίγραφα ασφαλείας")

    def _build_open_source_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(12)

        box = QGroupBox("Open Source")
        box_layout = QVBoxLayout(box)

        message = QLabel(
            "Η άδεια open-source και οι λεπτομέρειες δημόσιας διάθεσης "
            "δεν έχουν οριστικοποιηθεί ακόμη. Η επιλογή άδειας θα γίνει "
            "πριν από την πρώτη δημόσια έκδοση και δεν επηρεάζει τα "
            "δεδομένα της εφαρμογής."
        )
        message.setWordWrap(True)
        box_layout.addWidget(message)

        self.tabs.addTab(tab, "Open Source")
        layout.addWidget(box)
        layout.addStretch()

    def refresh(self) -> None:
        self._refresh_profiles()
        self.ask_profile_on_startup.blockSignals(True)
        self.ask_profile_on_startup.setChecked(self.profiles.ask_on_startup)
        self.ask_profile_on_startup.blockSignals(False)
        self.farm_name.setText(
            self.db.get_app_setting("farm_name", "")
        )
        self.auto_backup_enabled.setChecked(
            self.db.get_app_setting_bool(
                "auto_backup_enabled",
                True,
            )
        )
        self.auto_backup_keep.setValue(
            self.db.get_app_setting_int(
                "auto_backup_keep",
                30,
                minimum=1,
                maximum=365,
            )
        )
        self.pre_restore_keep.setValue(
            self.db.get_app_setting_int(
                "pre_restore_keep",
                10,
                minimum=1,
                maximum=100,
            )
        )

        saved_dir = self.db.get_app_setting(
            "backup_dir",
            "",
        ).strip()
        self.backup_dir.setText(
            saved_dir
            or str(self.profiles.default_backup_dir().resolve())
        )
        self._update_backup_controls()

    def _update_backup_controls(self) -> None:
        enabled = self.auto_backup_enabled.isChecked()
        self.auto_backup_keep.setEnabled(enabled)

    def choose_backup_folder(self) -> None:
        start = self.backup_dir.text().strip()
        if not start:
            start = str(self.profiles.default_backup_dir().resolve())
        selected = QFileDialog.getExistingDirectory(
            self,
            "Επιλογή φακέλου backups",
            start,
        )
        if selected:
            self.backup_dir.setText(selected)

    def use_default_backup_folder(self) -> None:
        self.backup_dir.setText(
            str(self.profiles.default_backup_dir().resolve())
        )

    def open_backup_folder(self) -> None:
        folder = Path(
            self.backup_dir.text().strip()
            or self.profiles.default_backup_dir()
        ).expanduser()
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            QMessageBox.critical(
                self,
                "Φάκελος backups",
                f"Δεν ήταν δυνατή η δημιουργία του φακέλου.\n\n{exc}",
            )
            return
        QDesktopServices.openUrl(
            QUrl.fromLocalFile(str(folder.resolve()))
        )

    def open_log_folder(self) -> None:
        current_log = log_path()
        if current_log is None:
            return
        current_log.parent.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(
            QUrl.fromLocalFile(str(current_log.parent.resolve()))
        )

    def save(self) -> None:
        folder_text = self.backup_dir.text().strip()
        folder = Path(
            folder_text or self.profiles.default_backup_dir()
        ).expanduser()

        try:
            folder.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            QMessageBox.critical(
                self,
                "Μη έγκυρος φάκελος backups",
                "Δεν ήταν δυνατή η χρήση του επιλεγμένου φακέλου.\n\n"
                f"{exc}",
            )
            return

        default_dir = self.profiles.default_backup_dir().resolve()
        resolved_dir = folder.resolve()
        stored_dir = "" if resolved_dir == default_dir else str(resolved_dir)

        self.db.save_app_settings(
            {
                "farm_name": self.farm_name.text().strip(),
                "auto_backup_enabled": (
                    "1" if self.auto_backup_enabled.isChecked() else "0"
                ),
                "auto_backup_keep": self.auto_backup_keep.value(),
                "pre_restore_keep": self.pre_restore_keep.value(),
                "backup_dir": stored_dir,
            }
        )

        QMessageBox.information(
            self,
            "Ρυθμίσεις",
            "Οι ρυθμίσεις αποθηκεύτηκαν επιτυχώς.",
        )

    def reset_defaults(self) -> None:
        answer = QMessageBox.question(
            self,
            "Επαναφορά προεπιλογών",
            "Να επανέλθουν οι γενικές ρυθμίσεις στις προεπιλεγμένες τιμές;\n\n"
            "Δεν επηρεάζονται προϊόντα, παραγωγή, οικονομικά ή άλλα δεδομένα.",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        self.db.reset_app_settings()
        self.refresh()
        QMessageBox.information(
            self,
            "Ρυθμίσεις",
            "Οι προεπιλεγμένες ρυθμίσεις επανήλθαν.",
        )
