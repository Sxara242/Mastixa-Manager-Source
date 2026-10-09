"""Independent source contracts and runtime routing for the exact Phase 3 scope."""
import hashlib
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import numpy as np
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication
from app import icon_normalization as norm, icon_theme
from tests.test_icon_mask_prototype import rgba, assert_protected_rgba

FIX=Path(__file__).parent/'fixtures/icon_mask_phase3'
MANIFEST=json.loads((FIX/'manifest.json').read_text())
READY={'cultivation.png','expenses.png','income.png','invoice_documents.png',
       'plant_protection.png','sales.png','suppliers_buyers.png','warehouse.png'}
REVIEW={'alerts.png','declaration.png','fields.png','producer.png','products.png','search.png','settings.png'}
# Historical Phase 3 assets may be superseded by later owner-approved
# Phase 4 or runtime-QA recomposition contracts.
PHASE4_SUPERSEDED = REVIEW & set(norm._PHASE4_RECOMPOSED_SOURCE_SHA256)
RUNTIME_QA_SUPERSEDED = (READY | REVIEW | set(MANIFEST['out_of_scope_sha256'])) & set(norm._RUNTIME_QA_RECOMPOSED_SOURCE_SHA256)
ACTIVE_READY = READY - RUNTIME_QA_SUPERSEDED
ACTIVE_REVIEW = REVIEW - PHASE4_SUPERSEDED - RUNTIME_QA_SUPERSEDED
GLINTS={'cultivation.png':(256,56),'expenses.png':(256,56),'income.png':(256,56),
        'invoice_documents.png':(256,55),'plant_protection.png':(256,21),
        'sales.png':(256,46),'suppliers_buyers.png':(256,56),'warehouse.png':(256,56)}

def fixture(name):
    folder=FIX/Path(name).stem
    return (rgba(QImage(str(folder/'original.png'))),
            rgba(QImage(str(icon_theme._ICON_DIR/name))),
            rgba(QImage(str(folder/'independent_protected.png')))[:,:,0]>0,
            rgba(QImage(str(folder/'approved_removal.png')))[:,:,0]>0)

class Phase3SourceTests(unittest.TestCase):
    def test_exact_scope_and_only_validated_sources_registered(self):
        self.assertEqual(READY|REVIEW,set(MANIFEST['icons']))
        self.assertEqual(ACTIVE_READY,set(norm._PHASE3_MASKED_SOURCE_SHA256))
        self.assertEqual(READY,{n for n,e in MANIFEST['icons'].items() if e['status']=='VALIDATED_SOURCE'})
        self.assertEqual(REVIEW, PHASE4_SUPERSEDED)
        self.assertEqual({'sales.png'}, READY & RUNTIME_QA_SUPERSEDED)

    def test_frozen_originals_and_masks_match_pinned_hashes(self):
        for name,e in MANIFEST['icons'].items():
            with self.subTest(icon=name):
                for file,key in [('original.png','original_sha256'),('independent_protected.png','protected_sha256'),('approved_removal.png','removal_sha256')]:
                    self.assertEqual(e[key],hashlib.sha256((FIX/Path(name).stem/file).read_bytes()).hexdigest())

    def test_source_annotation_coordinates_are_frozen(self):
        self.assertEqual(MANIFEST['annotations_sha256'],hashlib.sha256((FIX/'source_annotations.json').read_bytes()).hexdigest())

    def test_every_protected_pixel_exact_prescaling_rgba(self):
        for name in ACTIVE_READY|ACTIVE_REVIEW:
            with self.subTest(icon=name):
                a,b,p,_=fixture(name)
                self.assertEqual((512,512,4),b.shape)
                assert_protected_rgba(self,a,b,p)

    def test_every_rgb_byte_unchanged_including_transparent_pixels(self):
        for name in ACTIVE_READY|ACTIVE_REVIEW:
            with self.subTest(icon=name):
                a,b,_,_=fixture(name)
                self.assertTrue(np.array_equal(a[:,:,:3],b[:,:,:3]))

    def test_alpha_changes_only_within_separate_removal_annotation(self):
        for name in ACTIVE_READY|ACTIVE_REVIEW:
            with self.subTest(icon=name):
                a,b,p,m=fixture(name);changed=a[:,:,3]!=b[:,:,3]
                self.assertFalse(np.any(changed&~m))
                self.assertFalse(np.any(p&m))
                self.assertTrue(np.all(b[:,:,3][m]==0))
                self.assertEqual(name in ACTIVE_READY,bool(changed.any()))

    def test_independent_reference_is_not_inverse_cleanup_mask(self):
        for name in ACTIVE_READY:
            with self.subTest(icon=name):
                _,_,p,m=fixture(name)
                self.assertFalse(np.array_equal(p,~m))

    def test_complete_rgba_raster_matches_review_snapshot(self):
        for name in ACTIVE_READY|ACTIVE_REVIEW:
            e=MANIFEST['icons'][name]
            with self.subTest(icon=name):
                _,b,_,_=fixture(name)
                self.assertEqual(e['expected_rgba_sha256'],hashlib.sha256(b.tobytes()).hexdigest())

    def test_all_protected_bright_highlights_222_and_above_survive(self):
        for name,(x,y) in GLINTS.items():
            if name not in ACTIVE_READY:
                continue
            with self.subTest(icon=name):
                a,b,p,_=fixture(name);bright=p&(a[:,:,:3].min(2)>=222)&(a[:,:,3]>0)
                self.assertTrue(bright[y,x])
                self.assertTrue(np.array_equal(a[bright],b[bright]))

    def test_one_deleted_metallic_highlight_fails_exact_contract(self):
        for name,(x,y) in GLINTS.items():
            if name not in ACTIVE_READY:
                continue
            with self.subTest(icon=name):
                a,b,p,_=fixture(name);self.assertTrue(p[y,x]);b[y,x,3]=0
                with self.assertRaisesRegex(AssertionError,'Protected source RGBA changed'):
                    assert_protected_rgba(self,a,b,p)

    def test_one_darkened_metallic_highlight_fails_exact_contract(self):
        for name,(x,y) in GLINTS.items():
            if name not in ACTIVE_READY:
                continue
            with self.subTest(icon=name):
                a,b,p,_=fixture(name);b[y,x,:3]=0
                with self.assertRaisesRegex(AssertionError,'Protected source RGBA changed'):
                    assert_protected_rgba(self,a,b,p)

    def test_dark_rim_and_colored_artwork_exact(self):
        for name in ACTIVE_READY:
            with self.subTest(icon=name):
                a,b,p,_=fixture(name);rgb=a[:,:,:3].astype(int)
                dark=p&(rgb.max(2)<=150)&(a[:,:,3]>0)
                colored=p&(np.ptp(rgb,axis=2)>30)&(a[:,:,3]>0)
                self.assertGreater(int(dark.sum()),0);self.assertGreater(int(colored.sum()),0)
                self.assertTrue(np.array_equal(a[dark|colored],b[dark|colored]))

    def test_approved_metal_boundary_has_no_alpha_holes(self):
        for name in ACTIVE_READY:
            with self.subTest(icon=name):
                a,b,p,_=fixture(name);inner=p.copy()
                for dy,dx in ((0,1),(0,-1),(1,0),(-1,0)):
                    inner &= np.roll(p,(dy,dx),axis=(0,1))
                edge=p&~inner
                self.assertTrue(np.all(a[:,:,3][edge]>0))
                self.assertTrue(np.array_equal(a[edge],b[edge]))

    def test_review_sources_remain_byte_identical(self):
        for name in ACTIVE_REVIEW:
            with self.subTest(icon=name):
                self.assertEqual((FIX/Path(name).stem/'original.png').read_bytes(),(icon_theme._ICON_DIR/name).read_bytes())

    def test_every_out_of_scope_asset_unchanged_from_checkpoint(self):
        expected=MANIFEST['out_of_scope_sha256']
        self.assertEqual(19,len(expected))
        self.assertFalse(set(expected)&(READY|REVIEW))
        superseded=set(norm._PHASE4_RECOMPOSED_SOURCE_SHA256) | set(norm._RUNTIME_QA_RECOMPOSED_SOURCE_SHA256)
        for name,digest in expected.items():
            if name in superseded:
                continue
            with self.subTest(icon=name):
                self.assertEqual(digest,hashlib.sha256((icon_theme._ICON_DIR/name).read_bytes()).hexdigest())

class Phase3RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.app=QApplication.instance() or QApplication([])

    def test_validated_sources_bypass_every_destructive_cleaner(self):
        for name in ACTIVE_READY:
            with self.subTest(icon=name),patch.object(norm,'_normalize_image',side_effect=AssertionError('legacy')),patch.object(norm,'_clear_outer_light_neutral_ring',side_effect=AssertionError('radial')),patch.object(norm,'_clear_outer_white_component',side_effect=AssertionError('flood')):
                icon=norm._normalized_icon(icon_theme._ICON_DIR/name,{})
                self.assertIsNotNone(icon);self.assertFalse(icon.isNull())

    def test_review_sources_keep_fallback(self):
        for name in ACTIVE_REVIEW:
            with self.subTest(icon=name),patch.object(norm,'_normalize_image',wraps=norm._normalize_image) as legacy:
                self.assertFalse(norm._normalized_icon(icon_theme._ICON_DIR/name,{}).isNull())
                legacy.assert_called_once()

    def test_original_content_cannot_inherit_cleaned_filename_bypass(self):
        for name in ACTIVE_READY:
            original=(FIX/Path(name).stem/'original.png').read_bytes()
            with self.subTest(icon=name),patch.object(Path,'read_bytes',return_value=original),patch.object(norm,'_normalize_image',wraps=norm._normalize_image) as legacy:
                self.assertFalse(norm._normalized_icon(icon_theme._ICON_DIR/name,{}).isNull())
                legacy.assert_called_once()

    def test_exact_hash_and_bundled_path_required(self):
        for name in ACTIVE_READY:
            with self.subTest(icon=name):
                p=icon_theme._ICON_DIR/name;data=p.read_bytes()
                self.assertTrue(norm._is_validated_masked_source(p,data))
                self.assertFalse(norm._is_validated_masked_source(p,data+b'changed'))
                self.assertFalse(norm._is_validated_masked_source(FIX/name,data))

    def test_cache_hits_neither_read_nor_reprocess(self):
        for name in ACTIVE_READY:
            path=icon_theme._ICON_DIR/name;cache={};first=norm._normalized_icon(path,cache)
            with self.subTest(icon=name),patch.object(Path,'read_bytes',side_effect=AssertionError('reread')),patch.object(norm,'_present_preserved_source',side_effect=AssertionError('reprocess')):
                self.assertIs(first,norm._normalized_icon(path,cache))

    def test_source_unchanged_by_presentation_and_safe_padding(self):
        for name in ACTIVE_READY:
            with self.subTest(icon=name):
                source=QImage(str(icon_theme._ICON_DIR/name));before=rgba(source)
                result=norm._present_preserved_source(source);bounds=norm._preserved_source_bounds(result)
                self.assertTrue(np.array_equal(before,rgba(source)))
                self.assertEqual((256,256),(result.width(),result.height()))
                self.assertGreaterEqual(min(bounds.left(),bounds.top(),255-bounds.right(),255-bounds.bottom()),20)
                self.assertLessEqual(abs(bounds.left()+bounds.right()-255),1)
                self.assertLessEqual(abs(bounds.top()+bounds.bottom()-255),1)

if __name__=='__main__': unittest.main()
