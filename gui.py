import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from pdf_processor import PDFProcessor
import fitz  # To read page counts directly in GUI

class PDFConnectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Connection")
        self.root.geometry("750x550")
        self.root.minsize(700, 500)
        
        # Data structures
        self.pdf_list = []  # List of absolute file paths
        self.pdf_metadata = {}  # Map: abs_path -> {"pages": count, "exclude_str": ""}
        self.current_selection_idx = -1
        
        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use('vista' if 'vista' in self.style.theme_names() else 'default')
        
        # Create Layout
        self._create_widgets()
        self._setup_bindings()

    def _create_widgets(self):
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title Banner
        title_label = ttk.Label(
            main_frame, 
            text="PDF Connection", 
            font=("Segoe UI", 18, "bold"),
            foreground="#1a5f7a"
        )
        title_label.pack(anchor=tk.W, pady=(0, 15))
        
        # Middle Area (Split into Left and Right)
        middle_frame = ttk.Frame(main_frame)
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
        bottom_frame = ttk.LabelFrame(main_frame, text=" Merge & Output Settings ", padding="15")
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
        
        self.btn_merge = ttk.Button(action_row, text="Merge PDFs", style="Accent.TButton", command=self._execute_merge)
        self.btn_merge.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Status Label
        self.lbl_status = ttk.Label(action_row, text="Ready. Add PDF files to start.", font=("Segoe UI", 9, "italic"), foreground="gray")
        self.lbl_status.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _setup_bindings(self):
        # Update details when selection changes in listbox
        self.file_listbox.bind('<<ListboxSelect>>', self._on_listbox_select)
        
        # Register a validator or save on focus out/key release
        self.exclude_entry.bind("<FocusOut>", lambda e: self._save_current_exclusions(silent=True))

    def _update_listbox(self):
        self.file_listbox.delete(0, tk.END)
        for path in self.pdf_list:
            # Display filename and total pages
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
                # Get page count using fitz
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
            
        # Swap
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
            
        # Swap
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
        
        # Load details
        filename = os.path.basename(path)
        meta = self.pdf_metadata[path]
        
        self.lbl_selected_title.config(text=filename)
        self.lbl_page_count.config(text=f"Total Pages: {meta['pages']}")
        
        # Enable entries
        self.exclude_entry.state(['!disabled'])
        self.btn_save_settings.state(['!disabled'])
        
        # Load exclude string
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
        """
        Parse user input string to 0-based page index set.
        """
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
            return True  # No change
            
        # Validate input
        excluded, err = self._parse_exclude_string(exclude_str, meta["pages"])
        if err:
            if not silent:
                messagebox.showerror("Validation Error", f"Failed to apply exclusions:\n{err}")
            return False
            
        # Update metadata
        meta["exclude_str"] = exclude_str
        self._update_listbox()
        # Keep selection
        self.file_listbox.select_set(self.current_selection_idx)
        
        if not silent:
            self.lbl_status.config(text=f"Exclusions applied to {os.path.basename(path)}.")
        return True

    def _execute_merge(self):
        if not self.pdf_list:
            messagebox.showwarning("Warning", "Please add at least one PDF file.")
            return
            
        # Ensure any pending input in exclude entry is saved
        if not self._save_current_exclusions(silent=False):
            return  # Validation failed
            
        # Choose output file
        output_file = filedialog.asksaveasfilename(
            title="Save Merged PDF As",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")]
        )
        if not output_file:
            return
            
        self.lbl_status.config(text="Processing PDFs... Please wait.")
        self.root.update_idletasks()
        
        # Prepare page exclusions
        exclude_pages = {}
        for path in self.pdf_list:
            meta = self.pdf_metadata[path]
            if meta["exclude_str"]:
                excluded_set, _ = self._parse_exclude_string(meta["exclude_str"], meta["pages"])
                exclude_pages[path] = excluded_set
                
        # Merge
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

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFConnectionApp(root)
    root.mainloop()
