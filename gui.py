import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from pdf_processor import PDFProcessor
import fitz

class PDFConnectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Connection")
        self.root.geometry("800x600")
        self.root.minsize(750, 550)
        
        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use('vista' if 'vista' in self.style.theme_names() else 'default')
        
        # Setup Notebook (Tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Merge Tab Frame
        self.merge_tab = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(self.merge_tab, text=" Merge PDFs (병합) ")
        
        # Split Tab Frame
        self.split_tab = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(self.split_tab, text=" Split PDF (분할) ")
        
        # Build UI for both tabs
        self._build_merge_ui()
        self._build_split_ui()

    # ==================== MERGE TAB LOGIC & UI ====================
    def _build_merge_ui(self):
        # Data structures for merge
        self.pdf_list = []  # List of absolute file paths
        self.pdf_metadata = {}  # Map: abs_path -> {"pages": count, "exclude_str": ""}
        self.current_selection_idx = -1
        
        # Title Banner
        title_label = ttk.Label(
            self.merge_tab, 
            text="PDF Connection - Merge", 
            font=("Segoe UI", 16, "bold"),
            foreground="#1a5f7a"
        )
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Middle Area (Split into Left and Right)
        middle_frame = ttk.Frame(self.merge_tab)
        middle_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Left Panel (File List & Controls)
        left_frame = ttk.LabelFrame(middle_frame, text=" PDF Files to Merge (Order from top to bottom) ", padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # File listbox with scrollbar
        list_scroll_frame = ttk.Frame(left_frame)
        list_scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        self.file_listbox = tk.Listbox(
            list_scroll_frame, 
            selectmode=tk.SINGLE, 
            font=("Segoe UI", 10),
            bg="#fcfcfc",
            selectbackground="#1a5f7a",
            selectforeground="white",
            activestyle="none",
            borderwidth=1,
            relief=tk.SOLID
        )
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_scroll_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=scrollbar.set)
        
        # File List Controls (Buttons)
        btn_frame = ttk.Frame(left_frame, padding="5")
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.btn_add = ttk.Button(btn_frame, text="Add PDF", command=self._add_files)
        self.btn_add.pack(side=tk.LEFT, padx=2)
        
        self.btn_remove = ttk.Button(btn_frame, text="Remove", command=self._remove_file)
        self.btn_remove.pack(side=tk.LEFT, padx=2)
        
        self.btn_up = ttk.Button(btn_frame, text="Move Up", command=self._move_up)
        self.btn_up.pack(side=tk.RIGHT, padx=2)
        
        self.btn_down = ttk.Button(btn_frame, text="Move Down", command=self._move_down)
        self.btn_down.pack(side=tk.RIGHT, padx=2)
        
        # Right Panel (Properties and Exclude options)
        right_frame = ttk.LabelFrame(middle_frame, text=" Page Exclusion Settings ", padding="15", width=280)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        right_frame.pack_propagate(False)  # Keep fixed width
        
        # Selected File details
        self.lbl_selected_title = ttk.Label(right_frame, text="No PDF selected", font=("Segoe UI", 10, "bold"), wraplength=230)
        self.lbl_selected_title.pack(anchor=tk.W, pady=(0, 5))
        
        self.lbl_page_count = ttk.Label(right_frame, text="Total Pages: -", font=("Segoe UI", 9))
        self.lbl_page_count.pack(anchor=tk.W, pady=(0, 20))
        
        # Exclude input
        lbl_exclude = ttk.Label(right_frame, text="Exclude Pages:", font=("Segoe UI", 9, "bold"))
        lbl_exclude.pack(anchor=tk.W, pady=(0, 5))
        
        self.exclude_entry = ttk.Entry(right_frame, font=("Segoe UI", 10))
        self.exclude_entry.pack(fill=tk.X, pady=(0, 5))
        
        lbl_hint = ttk.Label(
            right_frame, 
            text="Specify pages/ranges to exclude.\nExample: 1, 3-5\n(Leave blank to keep all pages)", 
            font=("Segoe UI", 8), 
            foreground="gray",
            justify=tk.LEFT
        )
        lbl_hint.pack(anchor=tk.W, pady=(0, 15))
        
        # Live status check of exclude entry
        self.btn_save_settings = ttk.Button(right_frame, text="Apply Exclusions", command=self._save_current_exclusions)
        self.btn_save_settings.pack(fill=tk.X, pady=(10, 0))
        self.btn_save_settings.state(['disabled'])
        self.exclude_entry.state(['disabled'])
        
        # Bottom Area (Global Options & Run)
        bottom_frame = ttk.LabelFrame(self.merge_tab, text=" Merge & Output Settings ", padding="15")
        bottom_frame.pack(fill=tk.X)
        
        # Options
        self.dedup_var = tk.BooleanVar(value=True)
        chk_dedup = ttk.Checkbutton(
            bottom_frame, 
            text="Remove duplicate pages (Auto-detect visually identical content)", 
            variable=self.dedup_var
        )
        chk_dedup.pack(anchor=tk.W, pady=(0, 10))
        
        # Action row
        action_row = ttk.Frame(bottom_frame)
        action_row.pack(fill=tk.X)
        
        self.btn_merge = ttk.Button(action_row, text="Merge PDFs", command=self._execute_merge)
        self.btn_merge.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Status Label
        self.lbl_status = ttk.Label(action_row, text="Ready. Add PDF files to start.", font=("Segoe UI", 9, "italic"), foreground="gray")
        self.lbl_status.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Setup bindings for Merge Tab
        self.file_listbox.bind('<<ListboxSelect>>', self._on_listbox_select)
        self.exclude_entry.bind("<FocusOut>", lambda e: self._save_current_exclusions(silent=True))

    def _update_listbox(self):
        self.file_listbox.delete(0, tk.END)
        for path in self.pdf_list:
            filename = os.path.basename(path)
            meta = self.pdf_metadata.get(path, {"pages": 0, "exclude_str": ""})
            exclude_text = f" [Excludes: {meta['exclude_str']}]" if meta['exclude_str'] else ""
            self.file_listbox.insert(tk.END, f"{filename} ({meta['pages']} pgs){exclude_text}")

    def _add_files(self):
        files = filedialog.askopenfilenames(
            title="Select PDF Files",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if not files:
            return
            
        for filepath in files:
            abs_path = os.path.abspath(filepath)
            if abs_path in self.pdf_list:
                continue
                
            try:
                doc = fitz.open(abs_path)
                page_count = len(doc)
                doc.close()
                
                self.pdf_list.append(abs_path)
                self.pdf_metadata[abs_path] = {
                    "pages": page_count,
                    "exclude_str": ""
                }
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load PDF file: {os.path.basename(filepath)}\n{str(e)}")
                
        self._update_listbox()
        self.lbl_status.config(text=f"Loaded {len(self.pdf_list)} file(s).")

    def _remove_file(self):
        sel = self.file_listbox.curselection()
        if not sel:
            return
            
        idx = sel[0]
        path = self.pdf_list[idx]
        
        self.pdf_list.pop(idx)
        self.pdf_metadata.pop(path, None)
        
        self._update_listbox()
        self._clear_details()
        self.lbl_status.config(text="File removed.")

    def _move_up(self):
        sel = self.file_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx == 0:
            return
        self.pdf_list[idx], self.pdf_list[idx-1] = self.pdf_list[idx-1], self.pdf_list[idx]
        self._update_listbox()
        self.file_listbox.select_set(idx-1)
        self.file_listbox.event_generate("<<ListboxSelect>>")

    def _move_down(self):
        sel = self.file_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx == len(self.pdf_list) - 1:
            return
        self.pdf_list[idx], self.pdf_list[idx+1] = self.pdf_list[idx+1], self.pdf_list[idx]
        self._update_listbox()
        self.file_listbox.select_set(idx+1)
        self.file_listbox.event_generate("<<ListboxSelect>>")

    def _on_listbox_select(self, event):
        sel = self.file_listbox.curselection()
        if not sel:
            return
            
        idx = sel[0]
        path = self.pdf_list[idx]
        self.current_selection_idx = idx
        
        filename = os.path.basename(path)
        meta = self.pdf_metadata[path]
        
        self.lbl_selected_title.config(text=filename)
        self.lbl_page_count.config(text=f"Total Pages: {meta['pages']}")
        
        self.exclude_entry.state(['!disabled'])
        self.btn_save_settings.state(['!disabled'])
        
        self.exclude_entry.delete(0, tk.END)
        self.exclude_entry.insert(0, meta["exclude_str"])

    def _clear_details(self):
        self.current_selection_idx = -1
        self.lbl_selected_title.config(text="No PDF selected")
        self.lbl_page_count.config(text="Total Pages: -")
        self.exclude_entry.delete(0, tk.END)
        self.exclude_entry.state(['disabled'])
        self.btn_save_settings.state(['disabled'])

    def _parse_exclude_string(self, pages_str, max_pages):
        if not pages_str.strip():
            return set(), None
            
        excluded = set()
        parts = [p.strip() for p in pages_str.split(',')]
        
        for part in parts:
            if not part:
                continue
            if '-' in part:
                subparts = part.split('-')
                if len(subparts) != 2:
                    return set(), f"Invalid range format: '{part}'"
                try:
                    start = int(subparts[0].strip())
                    end = int(subparts[1].strip())
                    if start > end:
                        return set(), f"Invalid range: '{part}' (start > end)"
                    if start < 1 or end > max_pages:
                        return set(), f"Page out of range: '{part}' (valid range: 1-{max_pages})"
                    for p in range(start, end + 1):
                        excluded.add(p - 1)
                except ValueError:
                    return set(), f"Invalid numbers in range: '{part}'"
            else:
                try:
                    p = int(part)
                    if p < 1 or p > max_pages:
                        return set(), f"Page out of range: {p} (valid range: 1-{max_pages})"
                    excluded.add(p - 1)
                except ValueError:
                    return set(), f"Invalid page number: '{part}'"
                    
        return excluded, None

    def _save_current_exclusions(self, silent=False):
        if self.current_selection_idx == -1:
            return False
            
        path = self.pdf_list[self.current_selection_idx]
        meta = self.pdf_metadata[path]
        exclude_str = self.exclude_entry.get().strip()
        
        if exclude_str == meta["exclude_str"]:
            return True
            
        excluded, err = self._parse_exclude_string(exclude_str, meta["pages"])
        if err:
            if not silent:
                messagebox.showerror("Validation Error", f"Failed to apply exclusions:\n{err}")
            return False
            
        meta["exclude_str"] = exclude_str
        self._update_listbox()
        self.file_listbox.select_set(self.current_selection_idx)
        
        if not silent:
            self.lbl_status.config(text=f"Exclusions applied to {os.path.basename(path)}.")
        return True

    def _execute_merge(self):
        if not self.pdf_list:
            messagebox.showwarning("Warning", "Please add at least one PDF file.")
            return
            
        if not self._save_current_exclusions(silent=False):
            return
            
        output_file = filedialog.asksaveasfilename(
            title="Save Merged PDF As",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")]
        )
        if not output_file:
            return
            
        self.lbl_status.config(text="Processing PDFs... Please wait.")
        self.root.update_idletasks()
        
        exclude_pages = {}
        for path in self.pdf_list:
            meta = self.pdf_metadata[path]
            if meta["exclude_str"]:
                excluded_set, _ = self._parse_exclude_string(meta["exclude_str"], meta["pages"])
                exclude_pages[path] = excluded_set
                
        remove_dups = self.dedup_var.get()
        success, msg = PDFProcessor.merge_pdfs(
            pdf_paths=self.pdf_list,
            output_path=output_file,
            exclude_pages=exclude_pages,
            remove_duplicates=remove_dups
        )
        
        if success:
            self.lbl_status.config(text="Merge completed successfully!")
            messagebox.showinfo("Success", f"PDFs successfully merged and saved to:\n{output_file}")
        else:
            self.lbl_status.config(text="Merge failed.")
            messagebox.showerror("Error", f"Failed to merge PDFs:\n{msg}")


    # ==================== SPLIT TAB LOGIC & UI ====================
    def _build_split_ui(self):
        # State variables for split
        self.split_source_path = ""
        self.split_source_pages = 0
        self.split_output_dir = ""
        
        # Title Banner
        title_label = ttk.Label(
            self.split_tab, 
            text="PDF Connection - Split", 
            font=("Segoe UI", 16, "bold"),
            foreground="#1a5f7a"
        )
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        # File selector frame
        file_frame = ttk.LabelFrame(self.split_tab, text=" Source PDF File ", padding="10")
        file_frame.pack(fill=tk.X, pady=(0, 15))
        
        file_row = ttk.Frame(file_frame)
        file_row.pack(fill=tk.X)
        
        self.lbl_split_file_path = ttk.Label(file_row, text="No PDF file selected", font=("Segoe UI", 10), wraplength=500)
        self.lbl_split_file_path.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        btn_select_split_file = ttk.Button(file_row, text="Select PDF", command=self._select_split_source)
        btn_select_split_file.pack(side=tk.RIGHT)
        
        self.lbl_split_page_count = ttk.Label(file_frame, text="Total Pages: -", font=("Segoe UI", 9, "italic"), foreground="gray")
        self.lbl_split_page_count.pack(anchor=tk.W, pady=(5, 0))
        
        # Split options frame
        self.opt_frame = ttk.LabelFrame(self.split_tab, text=" Split Settings ", padding="15")
        self.opt_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Radio variables
        self.split_mode_var = tk.StringVar(value="every")
        
        # Mode 1: Every page
        self.rad_every = ttk.Radiobutton(
            self.opt_frame, 
            text="Extract every page as a single PDF (낱장 분할)", 
            value="every", 
            variable=self.split_mode_var,
            command=self._on_split_mode_change
        )
        self.rad_every.pack(anchor=tk.W, pady=5)
        
        # Mode 2: Split at Page X
        mode2_row = ttk.Frame(self.opt_frame)
        mode2_row.pack(fill=tk.X, anchor=tk.W, pady=5)
        
        self.rad_at_page = ttk.Radiobutton(
            mode2_row, 
            text="Split into 2 files at page index (지정 페이지 이분할):", 
            value="at_page", 
            variable=self.split_mode_var,
            command=self._on_split_mode_change
        )
        self.rad_at_page.pack(side=tk.LEFT)
        
        self.split_at_entry = ttk.Entry(mode2_row, width=8, font=("Segoe UI", 10))
        self.split_at_entry.pack(side=tk.LEFT, padx=10)
        self.split_at_entry.state(['disabled'])
        
        self.lbl_at_hint = ttk.Label(mode2_row, text="(e.g., 4: splits into pages 1-4 and 5-end)", font=("Segoe UI", 8), foreground="gray")
        self.lbl_at_hint.pack(side=tk.LEFT)
        
        # Mode 3: Custom Ranges
        mode3_row = ttk.Frame(self.opt_frame)
        mode3_row.pack(fill=tk.X, anchor=tk.W, pady=5)
        
        self.rad_ranges = ttk.Radiobutton(
            mode3_row, 
            text="Split by custom ranges (범위 지정 분할):", 
            value="ranges", 
            variable=self.split_mode_var,
            command=self._on_split_mode_change
        )
        self.rad_ranges.pack(side=tk.LEFT)
        
        self.split_ranges_entry = ttk.Entry(mode3_row, width=20, font=("Segoe UI", 10))
        self.split_ranges_entry.pack(side=tk.LEFT, padx=10)
        self.split_ranges_entry.state(['disabled'])
        
        self.lbl_ranges_hint = ttk.Label(mode3_row, text="(e.g., 1-3, 4-5)", font=("Segoe UI", 8), foreground="gray")
        self.lbl_ranges_hint.pack(side=tk.LEFT)
        
        # Disable all inputs initially
        self._disable_split_settings()
        
        # Output directory frame
        out_frame = ttk.LabelFrame(self.split_tab, text=" Output Settings ", padding="10")
        out_frame.pack(fill=tk.X, pady=(0, 15))
        
        out_row = ttk.Frame(out_frame)
        out_row.pack(fill=tk.X)
        
        self.lbl_split_output_dir = ttk.Label(out_row, text="No output folder selected (Will default to source PDF folder)", font=("Segoe UI", 10), wraplength=500)
        self.lbl_split_output_dir.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        btn_select_out_dir = ttk.Button(out_row, text="Select Folder", command=self._select_split_output_dir)
        btn_select_out_dir.pack(side=tk.RIGHT)
        
        # Split execution bar
        split_action_row = ttk.Frame(self.split_tab)
        split_action_row.pack(fill=tk.X)
        
        self.btn_split_execute = ttk.Button(split_action_row, text="Split PDF", command=self._execute_split)
        self.btn_split_execute.pack(side=tk.RIGHT)
        self.btn_split_execute.state(['disabled'])
        
        self.lbl_split_status = ttk.Label(split_action_row, text="Please select a source PDF file.", font=("Segoe UI", 9, "italic"), foreground="gray")
        self.lbl_split_status.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _select_split_source(self):
        file = filedialog.askopenfilename(
            title="Select PDF to Split",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if not file:
            return
            
        abs_path = os.path.abspath(file)
        try:
            doc = fitz.open(abs_path)
            self.split_source_pages = len(doc)
            doc.close()
            
            self.split_source_path = abs_path
            self.lbl_split_file_path.config(text=abs_path)
            self.lbl_split_page_count.config(text=f"Total Pages: {self.split_source_pages}")
            
            # Enable split settings & execution
            self._enable_split_settings()
            self.btn_split_execute.state(['!disabled'])
            self.lbl_split_status.config(text="Ready. Select split mode and execute.")
            
            # Default output directory to source directory
            if not self.split_output_dir:
                self.lbl_split_output_dir.config(text=os.path.dirname(abs_path))
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load PDF file:\n{str(e)}")
            self._disable_split_settings()
            self.btn_split_execute.state(['disabled'])

    def _select_split_output_dir(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.split_output_dir = os.path.abspath(folder)
            self.lbl_split_output_dir.config(text=self.split_output_dir)

    def _on_split_mode_change(self):
        mode = self.split_mode_var.get()
        if mode == "every":
            self.split_at_entry.state(['disabled'])
            self.split_ranges_entry.state(['disabled'])
        elif mode == "at_page":
            self.split_at_entry.state(['!disabled'])
            self.split_ranges_entry.state(['disabled'])
        elif mode == "ranges":
            self.split_at_entry.state(['disabled'])
            self.split_ranges_entry.state(['!disabled'])

    def _disable_split_settings(self):
        self.rad_every.state(['disabled'])
        self.rad_at_page.state(['disabled'])
        self.rad_ranges.state(['disabled'])
        self.split_at_entry.state(['disabled'])
        self.split_ranges_entry.state(['disabled'])

    def _enable_split_settings(self):
        self.rad_every.state(['!disabled'])
        self.rad_at_page.state(['!disabled'])
        self.rad_ranges.state(['!disabled'])
        self._on_split_mode_change()

    def _parse_split_ranges(self, ranges_str, max_pages):
        if not ranges_str.strip():
            return None, "Please specify range parameters (e.g. 1-3, 4-5)"
            
        ranges = []
        parts = [p.strip() for p in ranges_str.split(',')]
        for part in parts:
            if not part:
                continue
            if '-' not in part:
                try:
                    p = int(part)
                    if p < 1 or p > max_pages:
                        return None, f"Page number {p} out of range (1-{max_pages})"
                    ranges.append((p - 1, p - 1))
                except ValueError:
                    return None, f"Invalid format: '{part}'"
            else:
                subparts = part.split('-')
                if len(subparts) != 2:
                    return None, f"Invalid range format: '{part}'"
                try:
                    start = int(subparts[0].strip())
                    end = int(subparts[1].strip())
                    if start > end:
                        return None, f"Invalid range: '{part}' (start > end)"
                    if start < 1 or end > max_pages:
                        return None, f"Page out of range: '{part}' (valid range: 1-{max_pages})"
                    ranges.append((start - 1, end - 1))
                except ValueError:
                    return None, f"Invalid numbers in range: '{part}'"
        return ranges, None

    def _execute_split(self):
        if not self.split_source_path:
            messagebox.showwarning("Warning", "Please select a source PDF file.")
            return
            
        mode = self.split_mode_var.get()
        parameter = None
        
        # Validate inputs based on mode
        if mode == "at_page":
            val = self.split_at_entry.get().strip()
            if not val:
                messagebox.showerror("Error", "Please enter a split page index.")
                return
            try:
                split_idx = int(val)
                if split_idx < 1 or split_idx >= self.split_source_pages:
                    messagebox.showerror("Error", f"Split page index must be between 1 and {self.split_source_pages - 1}.")
                    return
                parameter = split_idx
            except ValueError:
                messagebox.showerror("Error", "Split page index must be a valid integer.")
                return
                
        elif mode == "ranges":
            val = self.split_ranges_entry.get().strip()
            ranges, err = self._parse_split_ranges(val, self.split_source_pages)
            if err:
                messagebox.showerror("Error", f"Failed to parse ranges:\n{err}")
                return
            parameter = ranges
            
        # Determine output directory
        out_dir = self.split_output_dir if self.split_output_dir else os.path.dirname(self.split_source_path)
        
        self.lbl_split_status.config(text="Splitting PDF... Please wait.")
        self.root.update_idletasks()
        
        success, msg = PDFProcessor.split_pdf(
            pdf_path=self.split_source_path,
            output_dir=out_dir,
            mode=mode,
            parameter=parameter
        )
        
        if success:
            self.lbl_split_status.config(text="Split completed successfully!")
            messagebox.showinfo("Success", f"PDF successfully split and saved to:\n{out_dir}")
        else:
            self.lbl_split_status.config(text="Split failed.")
            messagebox.showerror("Error", f"Failed to split PDF:\n{msg}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFConnectionApp(root)
    root.mainloop()
