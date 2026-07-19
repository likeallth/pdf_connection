import unittest
import os
import tempfile
import fitz  # PyMuPDF
from pdf_processor import PDFProcessor

class TestPDFProcessor(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test files
        self.test_dir = tempfile.TemporaryDirectory()
        self.pdf1_path = os.path.join(self.test_dir.name, "test1.pdf")
        self.pdf2_path = os.path.join(self.test_dir.name, "test2.pdf")
        self.output_path = os.path.join(self.test_dir.name, "merged.pdf")
        
        # Create PDF 1: 3 pages (Page A, Page B, Page A) -> Page A is duplicated
        self.create_test_pdf(self.pdf1_path, ["Page A", "Page B", "Page A"])
        
        # Create PDF 2: 2 pages (Page C, Page B) -> Page B is duplicated from PDF 1
        self.create_test_pdf(self.pdf2_path, ["Page C", "Page B"])

    def tearDown(self):
        # Clean up temporary directory
        self.test_dir.cleanup()

    def create_test_pdf(self, filename, pages_content):
        doc = fitz.open()
        for text in pages_content:
            page = doc.new_page()
            # Insert text at a fixed coordinate
            page.insert_text((50, 50), text)
        doc.save(filename)
        doc.close()

    def test_basic_merge_without_dedup_and_exclude(self):
        # Merge PDF 1 (3 pages) and PDF 2 (2 pages) without deduplication or exclusions
        success, msg = PDFProcessor.merge_pdfs(
            [self.pdf1_path, self.pdf2_path],
            self.output_path,
            exclude_pages=None,
            remove_duplicates=False
        )
        self.assertTrue(success)
        
        # Verify the output PDF has 5 pages
        doc = fitz.open(self.output_path)
        self.assertEqual(len(doc), 5)
        
        # Verify page contents
        texts = [page.get_text().strip() for page in doc]
        self.assertEqual(texts, ["Page A", "Page B", "Page A", "Page C", "Page B"])
        doc.close()

    def test_merge_with_exclusions(self):
        # Exclude the 2nd page (index 1: "Page B") of PDF 1
        # Exclude the 1st page (index 0: "Page C") of PDF 2
        exclusions = {
            self.pdf1_path: [1],
            self.pdf2_path: [0]
        }
        success, msg = PDFProcessor.merge_pdfs(
            [self.pdf1_path, self.pdf2_path],
            self.output_path,
            exclude_pages=exclusions,
            remove_duplicates=False
        )
        self.assertTrue(success)
        
        # Verify page count and contents
        # PDF1 should have: Page A (0), Page A (2)
        # PDF2 should have: Page B (1)
        # Total: 3 pages
        doc = fitz.open(self.output_path)
        self.assertEqual(len(doc), 3)
        texts = [page.get_text().strip() for page in doc]
        self.assertEqual(texts, ["Page A", "Page A", "Page B"])
        doc.close()

    def test_merge_with_duplicate_removal(self):
        # Merge PDFs with duplicate removal enabled
        # Input sequence:
        # PDF 1: Page A, Page B, Page A (duplicate)
        # PDF 2: Page C, Page B (duplicate)
        # Expected sequence: Page A, Page B, Page C
        success, msg = PDFProcessor.merge_pdfs(
            [self.pdf1_path, self.pdf2_path],
            self.output_path,
            exclude_pages=None,
            remove_duplicates=True
        )
        self.assertTrue(success)
        
        # Verify page count and unique contents
        doc = fitz.open(self.output_path)
        self.assertEqual(len(doc), 3)
        texts = [page.get_text().strip() for page in doc]
        self.assertEqual(texts, ["Page A", "Page B", "Page C"])
        doc.close()

    def test_merge_with_both_dedup_and_exclude(self):
        # Exclude index 0 of PDF 1 ("Page A")
        # Deduplication enabled.
        # PDF1 remaining: Page B, Page A
        # PDF2 remaining: Page C, Page B (duplicate of PDF1 Page B)
        # Expected after merge & dedup: Page B, Page A, Page C
        exclusions = {
            self.pdf1_path: [0]
        }
        success, msg = PDFProcessor.merge_pdfs(
            [self.pdf1_path, self.pdf2_path],
            self.output_path,
            exclude_pages=exclusions,
            remove_duplicates=True
        )
        self.assertTrue(success)
        
        doc = fitz.open(self.output_path)
        self.assertEqual(len(doc), 3)
        texts = [page.get_text().strip() for page in doc]
        self.assertEqual(texts, ["Page B", "Page A", "Page C"])
        doc.close()

if __name__ == '__main__':
    unittest.main()
