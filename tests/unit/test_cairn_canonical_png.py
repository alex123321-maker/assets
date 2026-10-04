"""Pixel-stream preservation and rejection of damaged PNG evidence."""
import importlib.util
from pathlib import Path
import struct
import unittest
import zlib

SPEC=importlib.util.spec_from_file_location('canonical_png',Path(__file__).resolve().parents[2]/'tools/cairn/canonical_png.py')
MODULE=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MODULE)


def chunk(kind,payload):
    return struct.pack('>I',len(payload))+kind+payload+struct.pack('>I',zlib.crc32(kind+payload))


class CanonicalPngTests(unittest.TestCase):
    def test_volatile_annotations_leave_compressed_pixels_and_color_unchanged(self):
        header=chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,2,0,0,0))
        color=chunk(b'sRGB',b'\0')
        pixels=chunk(b'IDAT',zlib.compress(b'\0\x80\x90\xa0'))
        ending=chunk(b'IEND',b'')
        clean=MODULE.SIGNATURE+header+color+pixels+ending
        annotated=MODULE.SIGNATURE+header+chunk(b'tEXt',b'Date\0variable')+color+pixels+chunk(b'eXIf',b'variable')+ending
        self.assertEqual(MODULE.canonical_bytes(annotated),clean)
        self.assertEqual(MODULE.canonical_bytes(clean),clean)

    def test_damaged_evidence_is_rejected(self):
        valid=MODULE.SIGNATURE+chunk(b'IDAT',b'pixels')+chunk(b'IEND',b'')
        with self.assertRaises(ValueError): MODULE.canonical_bytes(valid[:-1])
        damaged=bytearray(valid); damaged[18]^=1
        with self.assertRaises(ValueError): MODULE.canonical_bytes(bytes(damaged))


if __name__=='__main__': unittest.main()
