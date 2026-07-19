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

    def test_split_every_page(self):
        split_dir = os.path.join(self.test_dir.name, "split_every")
        success, msg = PDFProcessor.split_pdf(self.pdf1_path, split_dir, 'every')
        self.assertTrue(success)
        
        files = sorted(os.listdir(split_dir))
        self.assertEqual(len(files), 3)
        self.assertEqual(files, ["test1_page_1.pdf", "test1_page_2.pdf", "test1_page_3.pdf"])
        
        expected_texts = ["Page A", "Page B", "Page A"]
        for filename, expected in zip(files, expected_texts):
            path = os.path.join(split_dir, filename)
            doc = fitz.open(path)
            self.assertEqual(len(doc), 1)
            self.assertEqual(doc[0].get_text().strip(), expected)
            doc.close()

    def test_split_at_page(self):
        split_dir = os.path.join(self.test_dir.name, "split_at")
        success, msg = PDFProcessor.split_pdf(self.pdf1_path, split_dir, 'at_page', parameter=2)
        self.assertTrue(success)
        
        files = sorted(os.listdir(split_dir))
        self.assertEqual(len(files), 2)
        self.assertEqual(files, ["test1_part_1_1-2.pdf", "test1_part_2_3-3.pdf"])
        
        doc1 = fitz.open(os.path.join(split_dir, "test1_part_1_1-2.pdf"))
        self.assertEqual(len(doc1), 2)
        self.assertEqual([p.get_text().strip() for p in doc1], ["Page A", "Page B"])
        doc1.close()
        
        doc2 = fitz.open(os.path.join(split_dir, "test1_part_2_3-3.pdf"))
        self.assertEqual(len(doc2), 1)
        self.assertEqual([p.get_text().strip() for p in doc2], ["Page A"])
        doc2.close()

    def test_split_ranges(self):
        split_dir = os.path.join(self.test_dir.name, "split_ranges")
        ranges = [(0, 1), (1, 2)]
        success, msg = PDFProcessor.split_pdf(self.pdf1_path, split_dir, 'ranges', parameter=ranges)
        self.assertTrue(success)
        
        files = sorted(os.listdir(split_dir))
        self.assertEqual(len(files), 2)
        self.assertEqual(files, ["test1_range_1-2.pdf", "test1_range_2-3.pdf"])
        
        doc1 = fitz.open(os.path.join(split_dir, "test1_range_1-2.pdf"))
        self.assertEqual(len(doc1), 2)
        self.assertEqual([p.get_text().strip() for p in doc1], ["Page A", "Page B"])
        doc1.close()
        
        doc2 = fitz.open(os.path.join(split_dir, "test1_range_2-3.pdf"))
        self.assertEqual(len(doc2), 2)
        self.assertEqual([p.get_text().strip() for p in doc2], ["Page B", "Page A"])
        doc2.close()

if __name__ == '__main__':
    unittest.main()
