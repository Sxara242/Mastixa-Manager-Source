"""Regression for the Windows 10+ package boundary and retained PDF behavior."""
import ast
import json
from pathlib import Path
import runpy
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
policy=runpy.run_path(str(ROOT/'packaging/qt_exclusions.py'))

class WindowsDistributionAuditTests(unittest.TestCase):
    def test_os_forwarders_and_keyboard_orphans_are_removed_but_required_dlls_remain(self):
        removed=[policy['SOURCE_ONLY_LEGAL_SUFFIX'],'api-ms-win-crt-runtime-l1-1-0.dll','ext-ms-win-ntuser-window-l1-1-0.dll',
                 'ucrtbase.dll',*policy['UNUSED_QT_DLLS'],'Qt6VirtualKeyboard.dll','opengl32sw.dll']
        retained=['Qt6Core.dll','Qt6Gui.dll','Qt6Pdf.dll','qpdf.dll',
                  'MSVCP140.dll','VCRUNTIME140.dll','qwindows.dll','libssl-3.dll']
        toc=[(name,'wheel/'+name,'BINARY') for name in removed+retained]
        self.assertEqual(retained,[r[0] for r in policy['without_unused_windows_components'](toc)])

    def test_windows_sources_do_not_import_removed_qt_bindings_or_dynamic_qml(self):
        names={'PySide6.QtQuick','PySide6.QtQml','PySide6.QtOpenGL','PySide6.QtVirtualKeyboard'}
        for p in [ROOT/'main.py',*(ROOT/'app').rglob('*.py')]:
            text=p.read_text(encoding='utf-8-sig')
            for node in ast.walk(ast.parse(text)):
                if isinstance(node,(ast.Import,ast.ImportFrom)):
                    imports=[a.name for a in node.names]+[getattr(node,'module','')]
                    self.assertFalse(names.intersection(imports),p)
            self.assertNotIn('QQmlApplicationEngine',text,p)
            self.assertNotIn('QQuickWidget',text,p)

    def test_real_export_can_still_be_previewed_through_pdf_image_plugin(self):
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QPixmap
        from app.annual_report_exports import AnnualSnapshot,export_annual_pdf
        app=QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'invoice.pdf'
            snapshot=AnnualSnapshot(year=2026,product_id=None,product_name='',products=(),total_income=0,other_income=0,expenses=0)
            export_annual_pdf(p,snapshot)
            self.assertTrue(p.read_bytes().startswith(b'%PDF-'))
            self.assertFalse(QPixmap(str(p)).isNull())

    def test_bundle_gate_rejects_os_dll_and_qml_orphan(self):
        gate=runpy.run_path(str(ROOT/'packaging/validate_windows_release.py'))
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);internal=root/'_internal';internal.mkdir()
            for name in ('api-ms-win-core-file-l1-1-0.dll','Qt6Qml.dll'):
                (internal/name).write_bytes(b'fixture')
            errors=gate['bundle_errors'](root)
            self.assertTrue(any('api-ms-win-core-file' in e for e in errors))
            self.assertTrue(any('Qt6Qml.dll' in e for e in errors))
