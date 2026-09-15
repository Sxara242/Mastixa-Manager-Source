"""Select one, multiple or all mapped fields; preview the exact export snapshot."""
import os
import tempfile
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QLabel,QListWidget,QListWidgetItem,
    QPushButton,QComboBox,QTableWidget,QTableWidgetItem,QFileDialog,QMessageBox)
from .store import GeometryStore
from . import exports


class CoordinateExportDialog(QDialog):
    def __init__(self,db,field_id=None,parent=None):
        super().__init__(parent);self.setWindowTitle('Εξαγωγή κορυφών');self.resize(920,640)
        self.records=GeometryStore(db).all();self.parcels=[];layout=QVBoxLayout(self)
        count=db.query_one('SELECT count(*) AS n FROM fields')['n']
        layout.addWidget(QLabel(f'{len(self.records)} / {count} αγροτεμάχια διαθέτουν αποθηκευμένα όρια.'))
        self.fields=QListWidget();layout.addWidget(self.fields)
        for row in self.records:
            item=QListWidgetItem(row['current_name']+' · KAEK: '+row['current_kaek']);item.setFlags(item.flags()|Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if row['field_id']==field_id else Qt.CheckState.Unchecked);self.fields.addItem(item)
        actions=QHBoxLayout();layout.addLayout(actions)
        for title,checked in [('Όλα',True),('Κανένα',False)]:
            button=QPushButton(title);button.clicked.connect(lambda _,checked=checked:self.select_all(checked));actions.addWidget(button)
        self.format=QComboBox();self.format.addItems(['CSV','XLSX','PDF','GeoJSON','KML']);actions.addWidget(self.format)
        self.mode=QComboBox();self.mode.addItems(['WGS84 · Γεωγραφικό πλάτος / μήκος','Αρχικό CRS · X Y']);actions.addWidget(self.mode)
        self.note=QLabel();self.note.setWordWrap(True);layout.addWidget(self.note)
        self.preview=QTableWidget();self.preview.setEditTriggers(self.preview.EditTrigger.NoEditTriggers);layout.addWidget(self.preview)
        save=QPushButton('Εξαγωγή');save.clicked.connect(self.export);layout.addWidget(save)
        self.fields.itemChanged.connect(self.refresh);self.mode.currentIndexChanged.connect(self.refresh);self.format.currentIndexChanged.connect(self.refresh);self.refresh()

    def select_all(self,checked):
        self.fields.blockSignals(True)
        for index in range(self.fields.count()):self.fields.item(index).setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        self.fields.blockSignals(False);self.refresh()

    def effective_mode(self):return 'wgs84' if self.format.currentIndex()>=3 or self.mode.currentIndex()==0 else 'source'

    def refresh(self,*_):
        self.mode.setEnabled(self.format.currentIndex()<3)
        selected=[row for i,row in enumerate(self.records) if self.fields.item(i).checkState()==Qt.CheckState.Checked]
        self.parcels=[];self.preview.clear();self.preview.setRowCount(0)
        if not selected:self.note.setText('Επίλεξε αγροτεμάχια');return
        try:
            self.parcels=exports.snapshot(selected);rows=exports.table(self.parcels,self.effective_mode());self.preview.setColumnCount(len(rows[0]));self.preview.setHorizontalHeaderLabels(['Αγροτεμάχιο','KAEK','Σύστημα συντεταγμένων','EPSG','Έκταση (m²)','Περίμετρος (m)','Αριθμός κορυφών','Τμήμα','Δακτύλιος','Κορυφή',*(['Γεωγραφικό πλάτος','Γεωγραφικό μήκος'] if self.effective_mode()=='wgs84' else ['X / Γεωγραφικό μήκος','Y / Γεωγραφικό πλάτος'])]);self.preview.setRowCount(min(5,len(rows)-1))
            for r,row in enumerate(rows[1:6]):
                for c,value in enumerate(row):self.preview.setItem(r,c,QTableWidgetItem(str(value)))
            self.note.setText(f'{len(self.parcels)} αγροτεμάχια · {len(rows)-1} κορυφές\nGeoJSON / KML: WGS84 γεωγραφικό μήκος,πλάτος · αρχικό CRS στα μεταδεδομένα.')
            self.preview.resizeColumnsToContents()
        except Exception:self.parcels=[];self.note.setText('Η προεπισκόπηση δεν είναι διαθέσιμη. Έλεγξε τα επιλεγμένα όρια και τον αριθμό κορυφών.')

    def export(self):
        if not self.parcels:QMessageBox.information(self,'Εξαγωγή','Επίλεξε διαθέσιμα αγροτεμάχια');return
        extension=self.format.currentText().lower();mode=self.effective_mode()
        name,_=QFileDialog.getSaveFileName(self,'Εξαγωγή',exports.filename(self.parcels,mode,extension),f'{extension.upper()} (*.{extension})')
        if not name:return
        output=Path(name)
        if output.suffix.lower()!='.'+extension:
            output=output.with_name(output.name+'.'+extension)
            if output.exists():
                QMessageBox.warning(self,'Εξαγωγή','Το όνομα με τη σωστή επέκταση υπάρχει ήδη. Επίλεξέ το στον διάλογο αρχείου για επιβεβαίωση αντικατάστασης.');return
        staging=None
        try:
            descriptor,staging=tempfile.mkstemp(prefix='.mastixa-export-',suffix='.'+extension,dir=output.parent);os.close(descriptor)
            exports.write(staging,self.parcels,mode,extension);os.replace(staging,output);staging=None
            QMessageBox.information(self,'Εξαγωγή','Το αρχείο αποθηκεύτηκε')
        except Exception:QMessageBox.warning(self,'Εξαγωγή','Η εξαγωγή απέτυχε. Έλεγξε τα επιλεγμένα όρια, τα δικαιώματα εγγραφής και τον διαθέσιμο χώρο.')
        finally:
            if staging:Path(staging).unlink(missing_ok=True)
