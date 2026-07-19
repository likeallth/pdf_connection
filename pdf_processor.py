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

    @staticmethod
    def split_pdf(pdf_path, output_dir, mode, parameter=None):
        """
        Split a single PDF file into multiple PDFs based on the chosen mode.
        
        :param pdf_path: Absolute path to the source PDF.
        :param output_dir: Directory where split PDFs will be saved.
        :param mode: 'every', 'at_page', or 'ranges'
        :param parameter: 
            - For 'every': None
            - For 'at_page': int (1-based split index, e.g. 4 means split into 1-4 and 5-end)
            - For 'ranges': list of tuples [(start, end), ...] (0-based page indices)
        :return: (bool, str) True and message on success, False and error message on failure.
        """
        if not pdf_path or not os.path.exists(pdf_path):
            return False, f"Source file not found: {pdf_path}"
        
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except Exception as e:
                return False, f"Failed to create output directory: {str(e)}"
                
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        
        try:
            src_doc = fitz.open(pdf_path)
            total_pages = len(src_doc)
            
            if total_pages == 0:
                src_doc.close()
                return False, "The PDF file has 0 pages."
                
            if mode == 'every':
                for i in range(total_pages):
                    out_doc = fitz.open()
                    out_doc.insert_pdf(src_doc, from_page=i, to_page=i)
                    out_path = os.path.join(output_dir, f"{base_name}_page_{i+1}.pdf")
                    out_doc.save(out_path)
                    out_doc.close()
                src_doc.close()
                return True, f"Successfully split into {total_pages} individual pages."
                
            elif mode == 'at_page':
                try:
                    split_idx = int(parameter)
                except (ValueError, TypeError):
                    src_doc.close()
                    return False, f"Invalid split page parameter: {parameter}"
                    
                if split_idx < 1 or split_idx >= total_pages:
                    src_doc.close()
                    return False, f"Split index {split_idx} out of valid range (1 to {total_pages - 1})."
                
                # Part 1 (1 to X)
                out1 = fitz.open()
                out1.insert_pdf(src_doc, from_page=0, to_page=split_idx - 1)
                out1.save(os.path.join(output_dir, f"{base_name}_part_1_1-{split_idx}.pdf"))
                out1.close()
                
                # Part 2 (X+1 to total_pages)
                out2 = fitz.open()
                out2.insert_pdf(src_doc, from_page=split_idx, to_page=total_pages - 1)
                out2.save(os.path.join(output_dir, f"{base_name}_part_2_{split_idx + 1}-{total_pages}.pdf"))
                out2.close()
                
                src_doc.close()
                return True, f"Successfully split into 2 files at page {split_idx}."
                
            elif mode == 'ranges':
                if not isinstance(parameter, list):
                    src_doc.close()
                    return False, "Ranges parameter must be a list of tuples."
                    
                created_files = 0
                for start, end in parameter:
                    if start < 0 or end >= total_pages or start > end:
                        src_doc.close()
                        return False, f"Invalid range: {start+1}-{end+1} (Total pages: {total_pages})"
                    
                    out_doc = fitz.open()
                    out_doc.insert_pdf(src_doc, from_page=start, to_page=end)
                    out_path = os.path.join(output_dir, f"{base_name}_range_{start+1}-{end+1}.pdf")
                    out_doc.save(out_path)
                    out_doc.close()
                    created_files += 1
                    
                src_doc.close()
                return True, f"Successfully split into {created_files} range-based files."
                
            else:
                src_doc.close()
                return False, f"Unknown split mode: {mode}"
                
        except Exception as e:
            return False, f"Error during split: {str(e)}"
