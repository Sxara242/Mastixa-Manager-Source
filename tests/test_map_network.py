import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from PySide6.QtCore import QBuffer,QIODevice
from PySide6.QtGui import QImage,QColor
from PySide6.QtWidgets import QApplication
from app.gis.map_view import ParcelMap
from app.gis.geometry import manual_coordinates
from app.gis.providers import BasemapProvider


class MapNetworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.qt=QApplication.instance() or QApplication([])

    def drain(self,predicate,seconds=5):
        deadline=time.monotonic()+seconds
        while not predicate() and time.monotonic()<deadline:self.qt.processEvents();time.sleep(.01)
        self.assertTrue(predicate(),'Qt network request did not finish within bound')

    def test_real_http_failure_retries_and_rejects_invalid_image_without_losing_geometry(self):
        image=QImage(256,256,QImage.Format.Format_RGB32);image.fill(QColor('white'));buffer=QBuffer();buffer.open(QIODevice.OpenModeFlag.WriteOnly);image.save(buffer,'PNG');png=bytes(buffer.data())
        response={'status':503,'body':b'unavailable'}
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                self.send_response(response['status']);self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(response['body'])));self.end_headers()
                try:self.wfile.write(response['body'])
                except (BrokenPipeError,ConnectionResetError):pass
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            with tempfile.TemporaryDirectory() as folder:
                view=ParcelMap(Path(folder));view.resize(320,360);view.set_geometry(manual_coordinates('26 38\n26.001 38\n26.001 38.001\n26 38.001','EPSG:4326'));view.show();self.qt.processEvents()
                provider=BasemapProvider('fixture','Fixture',tile_template=f'http://127.0.0.1:{server.server_port}/{{z}}/{{x}}/{{y}}.png')
                try:
                    view.set_provider(provider);view.load_visible_tiles();self.drain(lambda:not view.pending and bool(view.failed))
                    self.assertTrue(view.boundaries);self.assertFalse(view.tiles)
                    deadline=time.monotonic()+31;response.update(status=200,body=png)
                    with patch('app.gis.map_view.time.monotonic',return_value=deadline):view.load_visible_tiles()
                    self.drain(lambda:not view.pending and bool(view.tiles));self.assertFalse(view.failed)
                    response.update(status=200,body=b'not an image');view.set_provider(provider);view.load_visible_tiles();self.drain(lambda:not view.pending and bool(view.failed))
                    self.assertFalse(view.tiles);self.assertEqual(4,len(view.markers))
                    response['body']=b'x'*(1024*1024+1);view.set_provider(provider);view.load_visible_tiles();self.drain(lambda:not view.pending and bool(view.failed))
                    self.assertFalse(view.tiles);self.assertTrue(view.boundaries)
                finally:view.shutdown();view.close();view.deleteLater();self.qt.processEvents()
        finally:server.shutdown();server.server_close();thread.join(2)

    def test_old_reply_cannot_remove_new_request_or_poison_provider(self):
        class Reply:
            deleted=False
            def deleteLater(self):self.deleted=True
        with tempfile.TemporaryDirectory() as folder:
            view=ParcelMap(Path(folder));old=Reply();new=Reply();key=(1,0,0);provider=BasemapProvider('fixture','Fixture')
            try:
                view.provider=provider;view.generation=2;view.pending[key]=new
                view.tile_finished(key,old,provider,1,bytearray())
                self.assertIs(new,view.pending[key]);self.assertFalse(view.failed);self.assertTrue(old.deleted)
                view.pending.clear()
            finally:view.shutdown();view.close();view.deleteLater();self.qt.processEvents()


if __name__=='__main__':unittest.main()
