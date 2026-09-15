from __future__ import annotations

from PySide6.QtWidgets import QComboBox

PARTNER_TYPES = (
    ("Προμηθευτής", "supplier"),
    ("Αγοραστής", "buyer"),
    ("Προμηθευτής & Αγοραστής", "both"),
)


def ensure_partner_link_schema(db) -> None:
    # The registry is needed before MoneyPage is constructed.
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS business_partners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            partner_type TEXT NOT NULL DEFAULT 'supplier',
            tax_id TEXT NOT NULL DEFAULT '',
            contact_person TEXT NOT NULL DEFAULT '',
            phone TEXT NOT NULL DEFAULT '',
            email TEXT NOT NULL DEFAULT '',
            address TEXT NOT NULL DEFAULT '',
            products TEXT NOT NULL DEFAULT '',
            payment_terms TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_business_partners_name
        ON business_partners(LOWER(TRIM(name)))
        """
    )

    for table_name in ("income", "expenses", "invoice_documents"):
        exists = db.query_one(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name=?
            """,
            (table_name,),
        )
        if exists is None:
            continue

        columns = {
            row["name"]
            for row in db.query(f"PRAGMA table_info({table_name})")
        }
        if "partner_id" not in columns:
            db.execute(
                f"ALTER TABLE {table_name} ADD COLUMN partner_id INTEGER"
            )
        db.execute(
            f"""
            CREATE INDEX IF NOT EXISTS idx_{table_name}_partner_id
            ON {table_name}(partner_id)
            """
        )

    # Safe legacy backfill: exact case-insensitive name only.
    if db.query_one(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='income'"
    ):
        db.execute(
            """
            UPDATE income
            SET partner_id=(
                SELECT p.id
                FROM business_partners p
                WHERE LOWER(TRIM(p.name))=LOWER(TRIM(income.partner))
                LIMIT 1
            )
            WHERE
                partner_id IS NULL
                AND TRIM(COALESCE(partner,'')) <> ''
                AND EXISTS(
                    SELECT 1
                    FROM business_partners p
                    WHERE LOWER(TRIM(p.name))=LOWER(TRIM(income.partner))
                )
            """
        )

    if db.query_one(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='expenses'"
    ):
        db.execute(
            """
            UPDATE expenses
            SET partner_id=(
                SELECT p.id
                FROM business_partners p
                WHERE LOWER(TRIM(p.name))=LOWER(TRIM(expenses.supplier))
                LIMIT 1
            )
            WHERE
                partner_id IS NULL
                AND TRIM(COALESCE(supplier,'')) <> ''
                AND EXISTS(
                    SELECT 1
                    FROM business_partners p
                    WHERE LOWER(TRIM(p.name))=LOWER(TRIM(expenses.supplier))
                )
            """
        )

    if db.query_one(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='invoice_documents'"
    ):
        db.execute(
            """
            UPDATE invoice_documents
            SET partner_id=(
                SELECT p.id
                FROM business_partners p
                WHERE LOWER(TRIM(p.name))=LOWER(TRIM(invoice_documents.supplier))
                LIMIT 1
            )
            WHERE
                partner_id IS NULL
                AND TRIM(COALESCE(supplier,'')) <> ''
                AND EXISTS(
                    SELECT 1
                    FROM business_partners p
                    WHERE LOWER(TRIM(p.name))=LOWER(TRIM(invoice_documents.supplier))
                )
            """
        )

    # SQLite cannot add FKs with ALTER TABLE. This keeps links safe on deletes.
    db.execute(
        """
        CREATE TRIGGER IF NOT EXISTS partner_link_cleanup_before_delete
        BEFORE DELETE ON business_partners
        BEGIN
            UPDATE income
            SET partner_id=NULL
            WHERE partner_id=OLD.id;

            UPDATE expenses
            SET partner_id=NULL
            WHERE partner_id=OLD.id;

            UPDATE invoice_documents
            SET partner_id=NULL
            WHERE partner_id=OLD.id;

            UPDATE production_sales
            SET buyer_id=NULL
            WHERE buyer_id=OLD.id;
        END
        """
    )


def match_partner_id(db, text: str) -> int | None:
    value = (text or "").strip()
    if not value:
        return None

    row = db.query_one(
        """
        SELECT id
        FROM business_partners
        WHERE LOWER(TRIM(name))=LOWER(TRIM(?))
        LIMIT 1
        """,
        (value,),
    )
    return int(row["id"]) if row else None


def canonical_partner_name(db, partner_id: int | None, fallback: str = "") -> str:
    if partner_id is None:
        return (fallback or "").strip()

    row = db.query_one(
        "SELECT name FROM business_partners WHERE id=?",
        (partner_id,),
    )
    if row is None:
        return (fallback or "").strip()

    return str(row["name"] or "").strip()


def sync_partner_names(db, partner_id: int, new_name: str) -> None:
    ensure_partner_link_schema(db)

    db.execute(
        "UPDATE income SET partner=? WHERE partner_id=?",
        (new_name, partner_id),
    )
    db.execute(
        "UPDATE expenses SET supplier=? WHERE partner_id=?",
        (new_name, partner_id),
    )
    db.execute(
        "UPDATE invoice_documents SET supplier=? WHERE partner_id=?",
        (new_name, partner_id),
    )

    if db.query_one(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='production_sales'"
    ):
        db.execute(
            "UPDATE production_sales SET buyer_name=? WHERE buyer_id=?",
            (new_name, partner_id),
        )

    if db.query_one(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='inventory_movements'"
    ):
        columns = {
            row["name"]
            for row in db.query(
                "PRAGMA table_info(inventory_movements)"
            )
        }
        if "supplier_name" in columns and "partner_id" in columns:
            db.execute(
                "UPDATE inventory_movements SET supplier_name=? WHERE partner_id=?",
                (new_name, partner_id),
            )


class PartnerComboBox(QComboBox):
    """
    Editable partner selector with legacy free-text fallback.

    selected_partner_id() returns an ID only while the visible text still
    matches the selected registry item. If the user edits the text manually,
    the row remains valid as legacy/free text with partner_id=NULL.
    """

    def __init__(self, db, role: str | None = None) -> None:
        super().__init__()
        self.db = db
        self.role = role
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.refresh_options()

    def setPlaceholderText(self, text: str) -> None:
        if self.lineEdit() is not None:
            self.lineEdit().setPlaceholderText(text)

    def refresh_options(
        self,
        selected_id: int | None = None,
        text: str | None = None,
    ) -> None:
        visible_text = self.currentText() if text is None else text
        current_id = (
            self.selected_partner_id()
            if selected_id is None
            else selected_id
        )

        self.blockSignals(True)
        self.clear()

        ensure_partner_link_schema(self.db)

        where = ""
        if self.role == "supplier":
            where = "WHERE partner_type IN ('supplier','both')"
        elif self.role == "buyer":
            where = "WHERE partner_type IN ('buyer','both')"

        for row in self.db.query(
            f"""
            SELECT id,name
            FROM business_partners
            {where}
            ORDER BY name,id
            """
        ):
            self.addItem(row["name"], int(row["id"]))

        if current_id is not None:
            index = self.findData(current_id)
            if index >= 0:
                self.setCurrentIndex(index)
                self.blockSignals(False)
                return

        if visible_text:
            matched = match_partner_id(self.db, visible_text)
            if matched is not None:
                index = self.findData(matched)
                if index >= 0:
                    self.setCurrentIndex(index)
                else:
                    self.setEditText(visible_text)
            else:
                self.setCurrentIndex(-1)
                self.setEditText(visible_text)
        else:
            self.setCurrentIndex(-1)
            self.setEditText("")

        self.blockSignals(False)

    def selected_partner_id(self) -> int | None:
        index = self.currentIndex()
        if index < 0:
            return None

        data = self.itemData(index)
        if data is None:
            return None

        if self.currentText().strip().casefold() != self.itemText(index).strip().casefold():
            return None

        try:
            return int(data)
        except (TypeError, ValueError):
            return None

    def text(self) -> str:
        return self.currentText().strip()

    def setText(
        self,
        text: str,
        partner_id: int | None = None,
    ) -> None:
        self.refresh_options(partner_id, text)

    def clear(self) -> None:
        super().clear()
        if self.isEditable():
            self.setCurrentIndex(-1)
            self.setEditText("")
