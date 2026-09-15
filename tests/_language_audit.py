from __future__ import annotations

import os
import ast
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QApplication,
    QAbstractButton,
    QComboBox,
    QDoubleSpinBox,
    QGroupBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QWidget,
)

from app.appearance_theme import ThemeController
from app.database import Database
from app.language import LanguageController, _has_greek
from app.main_window import MainWindow, STYLESHEET, build_app_palette
from app.profile_manager import ProfileManager


def audit() -> None:
    app = QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
        manager = ProfileManager(Path(folder))
        Database(manager.active_profile.database_path)
        palette = build_app_palette()
        theme = ThemeController(app, STYLESHEET, palette)
        language = LanguageController(app, manager)
        window = MainWindow(theme, manager, language)
        window.show()
        language.set_language("en")
        QTest.qWait(150)
        missing: set[str] = set()
        roots = [window, *(page for _name, page in window.pages)]
        for root in roots:
            language.apply_to(root)
        widgets = []
        seen_widgets: set[int] = set()
        for root in roots:
            for widget in [root, *root.findChildren(QWidget)]:
                if id(widget) not in seen_widgets:
                    seen_widgets.add(id(widget))
                    widgets.append(widget)
        for widget in widgets:
            candidates = [
                widget.windowTitle(), widget.toolTip(), widget.statusTip(),
                widget.whatsThis(), widget.accessibleName(),
            ]
            if isinstance(widget, (QLabel, QAbstractButton)):
                candidates.append(widget.text())
            if isinstance(widget, QGroupBox):
                candidates.append(widget.title())
            if isinstance(widget, QLineEdit):
                candidates.append(widget.placeholderText())
            if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                candidates.extend((widget.prefix(), widget.suffix(), widget.specialValueText()))
            if isinstance(widget, QTabWidget):
                candidates.extend(widget.tabText(index) for index in range(widget.count()))
            if isinstance(widget, QTableWidget):
                candidates.extend(
                    item.text()
                    for index in range(widget.columnCount())
                    if (item := widget.horizontalHeaderItem(index)) is not None
                )
            # Numeric userData identifies profile/product/field records. Static
            # options without userData must also be translated.
            if isinstance(widget, QComboBox) and (
                not widget.isEditable()
                or widget.property("mastixaI18nStaticItems")
            ):
                candidates.extend(
                    widget.itemText(index)
                    for index in range(widget.count())
                    if widget.itemData(index) is None
                    and widget.itemText(index) not in {"Μαστίχα", "Κύριο προφίλ"}
                )
            for text in candidates:
                if text and _has_greek(text) and text != "Ελληνικά":
                    missing.add(text)
        for text in sorted(missing, key=lambda value: (len(value), value)):
            print(text.replace("\n", "\\n"))
        print(f"MISSING_COUNT={len(missing)}")

        dialog_calls = {
            "information", "warning", "critical", "question", "getText",
            "getOpenFileName", "getSaveFileName", "getExistingDirectory",
        }
        dialog_sources: set[str] = set()
        for path in (Path(__file__).resolve().parents[1] / "app").glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                name = node.func.attr if isinstance(node.func, ast.Attribute) else ""
                if name not in dialog_calls:
                    continue
                for argument in node.args:
                    dialog_sources.update(
                        child.value
                        for child in ast.walk(argument)
                        if isinstance(child, ast.Constant)
                        and isinstance(child.value, str)
                        and _has_greek(child.value)
                    )
        dialog_missing = {
            source for source in dialog_sources
            if _has_greek(language.translate(source))
        }
        for text in sorted(dialog_missing, key=lambda value: (len(value), value)):
            print("DIALOG: " + text.replace("\n", "\\n"))
        print(f"DIALOG_LITERAL_MISSING_COUNT={len(dialog_missing)}")
        window._skip_close_backup = True
        window.close()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    audit()
