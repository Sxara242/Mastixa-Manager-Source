from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QTableWidget, QWidget


class CrudPage(QWidget):
    """Common helpers for pages that use a searchable CRUD table."""

    @staticmethod
    def filter_table(table: QTableWidget, text: str) -> None:
        search_text = text.strip().casefold()

        for row in range(table.rowCount()):
            matches = not search_text

            if search_text:
                for column in range(table.columnCount()):
                    item = table.item(row, column)
                    if item is not None and search_text in item.text().casefold():
                        matches = True
                        break

            table.setRowHidden(row, not matches)

    @staticmethod
    def confirm_delete(parent: QWidget, title: str, message: str) -> bool:
        answer = QMessageBox.question(
            parent,
            title,
            f"{message}\n\nΗ ενέργεια δεν μπορεί να αναιρεθεί.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return answer == QMessageBox.StandardButton.Yes
