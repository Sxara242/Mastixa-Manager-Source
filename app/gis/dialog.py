"""Parcel map UI; import is previewed before a transactional geometry replacement."""
import json
from pathlib import Path
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,
    QCheckBox,QComboBox,QFileDialog,QInputDialog,QMessageBox,QPlainTextEdit,QApplication)
from PySide6.QtWidgets import QTableWidget,QTableWidgetItem,QFormLayout,QLineEdit,QDoubleSpinBox,QDialogButtonBox
from .geometry import normalize,manual_coordinates
from .importers import import_geometry,MAX_BYTES
from .store import GeometryStore
from .providers import BASEMAPS,UnverifiedCadastreProvider,offline_pack
from .map_view import ParcelMap


class ParcelMapDialog(QDialog):
    def __init__(self,db,field_id,parent=None):
        super().__init__(parent)
        self.db=db;self.field_id=field_id;self.store=GeometryStore(db);self.record=None
        self.setWindowTitle('Χάρτης αγροτεμαχίου');self.resize(950,740)
        layout=QVBoxLayout(self)
        self.info=QLabel();self.info.setWordWrap(True);self.info.setTextFormat(self.info.textFormat().PlainText)
        # This label combines UI captions with domain names/source filenames. Translate
        # the template before interpolation so dictionary words in data remain intact.
        self.info.setProperty('mastixaI18nSkipText',True)
        self._info_template='';self._info_values={}
        self._language=getattr(QApplication.instance(),'_mastixa_language_controller',None)
        if self._language:self._language.language_changed.connect(self._translate_info)
        layout.addWidget(self.info)
        self.map=ParcelMap(db.path.parent/'map-http-cache',self);layout.addWidget(self.map,1)
        row=QHBoxLayout();layout.addLayout(row)
        fit=QPushButton('Στο αγροτεμάχιο');fit.clicked.connect(self.map.fit_parcel);row.addWidget(fit)
        boundary=QCheckBox('Όρια');boundary.setChecked(True)
        boundary.toggled.connect(self.map.show_boundaries);row.addWidget(boundary)
        dots=QCheckBox('Κορυφές');dots.setChecked(True)
        dots.toggled.connect(self.map.show_vertices);row.addWidget(dots)
        self.basemap=QComboBox();self.basemap.addItems(['Χωρίς υπόβαθρο','OpenStreetMap · Διαδίκτυο','Google · Δορυφορικό','Copernicus / Sentinel']);row.addWidget(self.basemap)
        self.basemap.currentIndexChanged.connect(self.select_basemap)
        self.attribution=QLabel('Τοπική γεωμετρία · χωρίς δικτυακό υπόβαθρο')
        self.attribution.setOpenExternalLinks(True);layout.addWidget(self.attribution)
        actions=QHBoxLayout();layout.addLayout(actions)
        for title,callback in [('Εισαγωγή ορίων',self.import_file),
                               ('Συντεταγμένες',self.manual),
                               ('Ανάκτηση ορίων από Κτηματολόγιο',self.cadastre),
                               ('Λήψη χάρτη για χρήση εκτός σύνδεσης',self.offline)]:
            button=QPushButton(title);button.clicked.connect(callback);actions.addWidget(button)
        objects=QHBoxLayout();layout.addLayout(objects)
        for title,callback in [('Σημεία',self.points),('Διαδρομές',self.tracks)]:
            button=QPushButton(title);button.clicked.connect(callback);objects.addWidget(button)
        close=QPushButton('Κλείσιμο');close.clicked.connect(self.accept);layout.addWidget(close)
        self.finished.connect(lambda _:self.map.shutdown())
        self.reload();QTimer.singleShot(0,self.map.fit_parcel)

    def _translate_info(self,*_):
        template=self._language.translate(self._info_template) if self._language else self._info_template
        self.info.setText(template.format(**self._info_values))

    def reload(self):
        self.record=self.store.get(self.field_id)
        field=self.db.query_one('SELECT name,kaek FROM fields WHERE id=?',(self.field_id,))
        if not field:self.reject();return
        if not self.record:
            self._info_template='{name} · ΚΑΕΚ: {kaek}\nΔεν έχουν αποθηκευτεί όρια'
            self._info_values={'name':field['name'],'kaek':field['kaek']}
            self._translate_info()
            return
        record=self.record
        geometry=normalize(json.loads(record['original_geojson']),record['source_crs'])
        self.map.set_geometry(geometry)
        self.map.set_points(self.store.points(record['id']))
        from datetime import datetime
        updated=datetime.fromtimestamp(record['updated_at']/1000).isoformat(timespec='seconds')
        self._info_template=('{name} · ΚΑΕΚ: {kaek}\n{area:.2f} m² · Περίμετρος: {perimeter:.2f} m · '
            '{vertices} κορυφές\nCRS: {crs} · Πηγή: {source} · {updated}')
        self._info_values={'name':field['name'],'kaek':field['kaek'],'area':geometry.area_m2,
            'perimeter':geometry.perimeter_m,'vertices':geometry.vertex_count,'crs':geometry.source_crs,
            'source':record['geometry_source'],'updated':updated}
        self._translate_info()

    def select_basemap(self,index):
        provider=BASEMAPS[index]
        if provider.unavailable_reason:
            QMessageBox.information(self,'Υπόβαθρο',('Απαιτείται επίσημο SDK/API και ρύθμιση' if provider.identity=='google' else 'Δεν έχει ρυθμιστεί υπηρεσία εικόνων'))
            self.basemap.setCurrentIndex(0);return
        self.map.set_provider(provider)
        self.attribution.setText('<a href="https://www.openstreetmap.org/copyright">© OpenStreetMap contributors</a> · Η ορατή περιοχή ζητείται από τον πάροχο μέσω διαδικτύου'
                                 if provider.identity=='osm' else 'Χωρίς υπόβαθρο · τοπική γεωμετρία')

    def source_crs(self,default=''):
        text,ok=QInputDialog.getText(self,'Σύστημα συντεταγμένων πηγής',
            'Πραγματικό EPSG πηγής (κενό για CRS αρχείου / WGS84 GeoJSON-KML)',text=default)
        return text.strip() if ok else None

    def import_file(self):
        filename,_=QFileDialog.getOpenFileName(self,'Εισαγωγή ορίων','',
            'Γεωμετρία (*.geojson *.json *.kml *.gml *.xml *.zip *.dxf)')
        if not filename:return
        crs=self.source_crs()
        if crs is None:return
        try:
            with open(filename,'rb') as stream:data=stream.read(MAX_BYTES+1)
            geometry=import_geometry(data,filename,crs)
            self.confirm_geometry(geometry,Path(filename).name)
        except Exception:QMessageBox.warning(self,'Εισαγωγή','Η εισαγωγή απέτυχε. Έλεγξε τη μορφή αρχείου, τα όρια και το EPSG πηγής.')

    def manual(self):
        crs=self.source_crs('EPSG:4326')
        if crs is None:return
        dialog=QDialog(self);dialog.setWindowTitle('X Y / γεωγραφικό μήκος και πλάτος');layout=QVBoxLayout(dialog)
        layout.addWidget(QLabel('Μία κορυφή ανά γραμμή, X Y (γεωγραφικό μήκος, πλάτος). Τελεία δεκαδικών.'))
        editor=QPlainTextEdit();editor.setPlaceholderText('26.00000000 38.00000000');layout.addWidget(editor)
        button=QPushButton('Προεπισκόπηση');button.clicked.connect(dialog.accept);layout.addWidget(button)
        dialog.resize(600,400)
        if dialog.exec()!=QDialog.DialogCode.Accepted:return
        try:self.confirm_geometry(manual_coordinates(editor.toPlainText(),crs),'manual')
        except Exception:QMessageBox.warning(self,'Συντεταγμένες','Δεν ήταν δυνατή η αποθήκευση. Έλεγξε τις συντεταγμένες και το EPSG πηγής ή άνοιξε ξανά τον χάρτη αν τα όρια άλλαξαν.')

    def confirm_geometry(self,geometry,source):
        # The original data is untouched until confirmation, then revision checked.
        preview=f'{geometry.source_crs} · {geometry.vertex_count} κορυφές\n{geometry.area_m2:.2f} m² · {geometry.perimeter_m:.2f} m\n'
        from .geometry import vertices
        preview+='\n'.join(f'{p}/{r}/{v}: {x:.8f}, {y:.8f}' for p,r,v,x,y in list(vertices(geometry.original))[:5])
        if self.record:preview+='\nΘα αντικατασταθούν τα αποθηκευμένα όρια.'
        answer=QMessageBox.question(self,'Αποθήκευση ορίων;',preview)
        if answer!=QMessageBox.StandardButton.Yes:return
        self.store.save(self.field_id,geometry,source,expected_revision=self.record['revision'] if self.record else None)
        self.reload()

    def cadastre(self):
        field=self.db.query_one('SELECT kaek FROM fields WHERE id=?',(self.field_id,))
        try:UnverifiedCadastreProvider().fetch(field['kaek'] if field else '')
        except ValueError:QMessageBox.information(self,'Κτηματολόγιο','Συμπλήρωσε ΚΑΕΚ')
        except ConnectionError:
            from .providers import CADASTRE_LAYER
            QMessageBox.information(self,'Κτηματολόγιο','Το δημοσιευμένο ArcGIS layer επέστρεψε HTTP 404 στον τελευταίο έλεγχο. Δεν έχουν επαληθευτεί τα πεδία, το CRS και τα ερωτήματα. Χρησιμοποίησε εξουσιοδοτημένο αρχείο ορίων.\n'+CADASTRE_LAYER)

    def offline(self):
        if not self.record:
            QMessageBox.information(self,'Χάρτης εκτός σύνδεσης','Εισήγαγε πρώτα όρια');return
        state=offline_pack(self.record['id'],json.loads(self.record['bbox']))
        QMessageBox.information(self,'Χάρτης εκτός σύνδεσης','Δεν έχει ρυθμιστεί πάροχος με άδεια λήψης εκτός σύνδεσης\n'+
            f'Πλαίσιο με περιθώριο: {state.bbox}\n0 bytes · 0% · Δεν έγινε λήψη')

    def points(self):
        if not self.record:
            QMessageBox.information(self,'Σημεία','Εισήγαγε πρώτα όρια');return
        dialog=QDialog(self);dialog.setWindowTitle('Σημεία');dialog.resize(750,430);layout=QVBoxLayout(dialog)
        table=QTableWidget(0,5);table.setHorizontalHeaderLabels(['Τίτλος','Τύπος','Γεωγραφικό πλάτος','Γεωγραφικό μήκος','Ακρίβεια (m)'])
        table.setSelectionBehavior(table.SelectionBehavior.SelectRows);table.setEditTriggers(table.EditTrigger.NoEditTriggers);layout.addWidget(table)
        rows=[]
        from .store import POINT_TYPES
        point_labels=dict(zip(POINT_TYPES,['Δέντρο','Βάνα','Άρδευση','Δεξαμενή','Γεώτρηση','Πρόβλημα','Σημείωση','Άλλο']))
        def refresh(*_):
            rows[:]=self.store.points(self.record['id']);table.setRowCount(len(rows))
            for index,row in enumerate(rows):
                for col,value in enumerate([row['title'],self._language.translate(point_labels.get(row['point_type'],row['point_type'])) if self._language else point_labels.get(row['point_type'],row['point_type']),f"{row['latitude']:.8f}",f"{row['longitude']:.8f}",row['accuracy']]):table.setItem(index,col,QTableWidgetItem(str(value)))
            self.map.set_points(rows)
        def edit(existing=None):
            form=QDialog(dialog);form.setWindowTitle('Σημείο');fields=QFormLayout(form)
            title=QLineEdit(existing['title'] if existing else '');notes=QPlainTextEdit(existing['notes'] if existing else '')
            from .store import POINT_TYPES
            kind=QComboBox();kind.addItems(['Δέντρο','Βάνα','Άρδευση','Δεξαμενή','Γεώτρηση','Πρόβλημα','Σημείωση','Άλλο'])
            kind.setCurrentIndex(POINT_TYPES.index(existing['point_type']) if existing else 0)
            fields.addRow('Τίτλος',title);fields.addRow('Τύπος',kind);fields.addRow('Σημειώσεις',notes)
            coordinates=[]
            for key,low,high in [('longitude',-180,180),('latitude',-90,90),('accuracy',0,1000000)]:
                spin=QDoubleSpinBox();spin.setRange(low,high);spin.setDecimals(8 if key!='accuracy' else 2)
                default=self.record['centroid_lon' if key=='longitude' else 'centroid_lat'] if key!='accuracy' else 0
                spin.setValue(existing[key] if existing else default);fields.addRow({'longitude':'Γεωγραφικό μήκος · WGS84','latitude':'Γεωγραφικό πλάτος · WGS84','accuracy':'Δηλωμένη ακρίβεια (m)'}[key],spin);coordinates.append(spin)
            buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel);fields.addRow(buttons);buttons.rejected.connect(form.reject)
            buttons.button(QDialogButtonBox.StandardButton.Save).setText('Αποθήκευση');buttons.button(QDialogButtonBox.StandardButton.Cancel).setText('Ακύρωση')
            def save():
                try:
                    self.store.save_point(self.record['id'],POINT_TYPES[kind.currentIndex()],title.text(),notes.toPlainText(),*[s.value() for s in coordinates],identity=existing['id'] if existing else None,expected_revision=existing['revision'] if existing else None)
                    form.accept();refresh()
                except ValueError:QMessageBox.warning(form,'Σημείο','Δεν ήταν δυνατή η αποθήκευση. Έλεγξε τις τιμές ή άνοιξε ξανά τη φόρμα αν το σημείο άλλαξε.')
            buttons.accepted.connect(save);form.exec()
        def selected():
            index=table.currentRow();return rows[index] if 0<=index<len(rows) else None
        def delete():
            row=selected()
            if row and QMessageBox.question(dialog,'Διαγραφή','Διαγραφή επιλεγμένου σημείου;')==QMessageBox.StandardButton.Yes:
                try:self.store.delete_object('geo_points',row['id'],row['revision']);refresh()
                except ValueError:QMessageBox.warning(dialog,'Σημείο','Δεν ήταν δυνατή η διαγραφή. Άνοιξε ξανά τη λίστα αν το σημείο άλλαξε.')
        actions=QHBoxLayout();layout.addLayout(actions)
        for text,callback in [('Νέο',lambda:edit()),('Επεξεργασία',lambda:edit(selected()) if selected() else None),('Διαγραφή',delete),('Κλείσιμο',dialog.accept)]:
            button=QPushButton(text);button.clicked.connect(callback);actions.addWidget(button)
        refresh()
        if self._language:self._language.language_changed.connect(refresh)
        try:dialog.exec()
        finally:
            if self._language:self._language.language_changed.disconnect(refresh)

    def tracks(self):
        rows=self.store.tracks(self.record['id']) if self.record else []
        if not rows:QMessageBox.information(self,'Διαδρομές','Δεν υπάρχουν αποθηκευμένες διαδρομές');return
        labels=[f"{index+1}. {row['title']} · {row['distance_m']:.1f} m · {row['duration_ms']/1000:.0f} s" for index,row in enumerate(rows)]
        choice,ok=QInputDialog.getItem(self,'Διαδρομές','Προβολή',labels,editable=False)
        if ok:
            row=rows[labels.index(choice)];self.map.set_track(json.loads(row['positions_json']),json.loads(row['segment_starts_json']))
