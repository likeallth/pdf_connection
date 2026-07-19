import fitz  # PyMuPDF
import hashlib
import os

class PDFProcessor:
    @staticmethod
    def get_page_hash(page) -> str:
        """
        Render the page at a low resolution (72 DPI) and compute MD5 of its pixels.
        This provides a robust way to identify visually identical pages.
        """
        pix = page.get_pixmap(dpi=72)
        return hashlib.md5(pix.samples).hexdigest()

    @staticmethod
    def merge_pdfs(pdf_paths, output_path, exclude_pages=None, remove_duplicates=True):
        """
        Merge multiple PDFs in the specified order.
        
        :param pdf_paths: List of file paths to the input PDFs.
        :param output_path: Destination file path for the merged PDF.
        :param exclude_pages: Dict mapping input PDF path to a set/list of 0-based page indices to exclude.
                              e.g., {"C:/path/to/file1.pdf": {0, 2}}
        :param remove_duplicates: If True, filters out duplicate pages based on visual content hash.
        :return: (bool, str) True and message on success, False and error message on failure.
        """
        if not pdf_paths:
            return False, "No PDF files provided."
        
        if exclude_pages is None:
            exclude_pages = {}

        # Normalise paths to ensure dict lookup works consistently
        exclude_pages_norm = {os.path.abspath(p): set(pages) for p, pages in exclude_pages.items()}

        out_doc = fitz.open()
        seen_hashes = set()
        
        try:
            for path in pdf_paths:
                abs_path = os.path.abspath(path)
                if not os.path.exists(abs_path):
                    return False, f"File not found: {path}"
                
                # Open current PDF
                src_doc = fitz.open(abs_path)
                pages_to_skip = exclude_pages_norm.get(abs_path, set())
                
                for page_idx in range(len(src_doc)):
                    # Check if this page is excluded by user
                    if page_idx in pages_to_skip:
                        continue
                    
                    page = src_doc[page_idx]
                    
                    # Check duplicates if enabled
                    if remove_duplicates:
                        page_hash = PDFProcessor.get_page_hash(page)
                        if page_hash in seen_hashes:
                            # Skip duplicate page
                            continue
                        seen_hashes.add(page_hash)
                    
                    # Insert page into output document
                    out_doc.insert_pdf(src_doc, from_page=page_idx, to_page=page_idx)
                
                src_doc.close()
            
            # Save output PDF
            out_dir = os.path.dirname(os.path.abspath(output_path))
            if out_dir and not os.path.exists(out_dir):
                os.makedirs(out_dir, exist_ok=True)
                
            out_doc.save(output_path)
            out_doc.close()
            return True, f"Successfully merged to {output_path}"
            
        except Exception as e:
            if 'out_doc' in locals() and out_doc:
                try:
                    out_doc.close()
                except Exception:
                    pass
            return False, f"Error processing PDF: {str(e)}"
