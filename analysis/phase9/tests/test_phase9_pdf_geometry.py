import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('trim',Path(__file__).resolve().parents[1]/'scripts/trim_pdf_pages.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class PDFPageBounds(unittest.TestCase):
    """SYNTHETIC_METHOD_TEST: page geometry, no scientific data production."""
    def ppm(self,w=50,h=50,dark=True):
        pixels=bytearray([255]*(w*h*3))
        if dark:pixels[(25*w+25)*3:(25*w+25)*3+3]=b'\0\0\0'
        return b'P6\n50 50\n255\n'+bytes(pixels)
    def test_bounded_geometry_keeps_padding(self):self.assertEqual(m.ppm_bounds(self.ppm()),(50,50,(9,9,42,42)))
    def test_empty_page_rejected(self):
        with self.assertRaises(ValueError):m.ppm_bounds(self.ppm(dark=False))
    def test_incomplete_render_rejected(self):
        with self.assertRaises(ValueError):m.ppm_bounds(self.ppm()[:-1])
    def test_wrong_colour_format_rejected(self):
        with self.assertRaises(ValueError):m.ppm_bounds(self.ppm().replace(b'P6',b'P5',1))
if __name__=='__main__':unittest.main()