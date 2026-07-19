import sys
import os
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QFileDialog, QMessageBox, QFrame, QButtonGroup
)
from PyQt6.QtGui import QIcon

# QFluentWidgets imports
from qfluentwidgets import (
    FluentWindow, SubtitleLabel, BodyLabel, PushButton, PrimaryPushButton,
    LineEdit, SwitchButton, CardWidget, RadioButton, FluentIcon as FIF,
    setTheme, Theme
)

# Business logic
from pdf_processor import PDFProcessor
import fitz

class MergeInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.pdf_list = []  # List of absolute file paths
        self.pdf_metadata = {}  # Map: abs_path -> {"pages": count, "exclude_str": ""}
        self.current_selection_path = None
        
        self._init_ui()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # ================= LEFT PANEL: File List & Sorting =================
        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)
        
        # Subtitle Label
        lbl_list_title = SubtitleLabel("병합 파일 목록 (PDF Files to Merge)", self)
        left_panel.addWidget(lbl_list_title)
        
        # File list
        self.file_list_widget = QListWidget(self)
        self.file_list_widget.setStyleSheet(
            "QListWidget { border: 1px solid #d2d2d2; border-radius: 6px; background-color: #fafafa; padding: 5px; }"
            "QListWidget::item { padding: 10px; border-radius: 4px; margin-bottom: 2px; }"
            "QListWidget::item:hover { background-color: #f0f0f0; }"
            "QListWidget::item:selected { background-color: #005fb8; color: white; }"
        )
        self.file_list_widget.itemSelectionChanged.connect(self._on_item_selection_changed)
        left_panel.addWidget(self.file_list_widget)
        
        # List control buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        self.btn_add = PushButton("파일 추가 (Add PDF)", self, FIF.ADD)
        self.btn_add.clicked.connect(self._add_files)
        btn_layout.addWidget(self.btn_add)
        
        self.btn_remove = PushButton("제거 (Remove)", self, FIF.DELETE)
        self.btn_remove.clicked.connect(self._remove_file)
        btn_layout.addWidget(self.btn_remove)
        
        btn_layout.addStretch(1)
        
        self.btn_up = PushButton("위로 이동", self, FIF.UP)
        self.btn_up.clicked.connect(self._move_up)
        btn_layout.addWidget(self.btn_up)
        
        self.btn_down = PushButton("아래로 이동", self, FIF.DOWN)
        self.btn_down.clicked.connect(self._move_down)
        btn_layout.addWidget(self.btn_down)
        
        left_panel.addLayout(btn_layout)
        main_layout.addLayout(left_panel, 3)  # Left panel takes larger space
        
        # ================= RIGHT PANEL: Configurations =================
        right_panel = QVBoxLayout()
        right_panel.setSpacing(15)
        
        # Card 1: Selected File Exclusions
        self.card_exclusion = CardWidget(self)
        card_ex_layout = QVBoxLayout(self.card_exclusion)
        card_ex_layout.setSpacing(10)
        card_ex_layout.setContentsMargins(15, 15, 15, 15)
        
        self.lbl_selected_title = SubtitleLabel("No PDF selected", self.card_exclusion)
        card_ex_layout.addWidget(self.lbl_selected_title)
        
        self.lbl_page_count = BodyLabel("Total Pages: -", self.card_exclusion)
        self.lbl_page_count.setStyleSheet("color: gray;")
        card_ex_layout.addWidget(self.lbl_page_count)
        
        lbl_exclude_prompt = BodyLabel("제외할 페이지 범위 (Exclude Pages):", self.card_exclusion)
        lbl_exclude_prompt.setStyleSheet("font-weight: bold;")
        card_ex_layout.addWidget(lbl_exclude_prompt)
        
        self.exclude_entry = LineEdit(self.card_exclusion)
        self.exclude_entry.setPlaceholderText("예: 1, 3-5")
        self.exclude_entry.setEnabled(False)
        self.exclude_entry.textChanged.connect(self._on_exclude_text_changed)
        card_ex_layout.addWidget(self.exclude_entry)
        
        lbl_hint = BodyLabel(
            "쉼표(,)와 대시(-)로 범위를 설정할 수 있습니다.\n설정 후 입력창 바깥을 누르거나 다른 파일을 선택하면 자동 저장됩니다.", 
            self.card_exclusion
        )
        lbl_hint.setStyleSheet("color: #7f7f7f; font-size: 11px;")
        card_ex_layout.addWidget(lbl_hint)
        
        self.btn_apply_ex = PushButton("Exclusion 적용", self.card_exclusion, FIF.SAVE)
        self.btn_apply_ex.setEnabled(False)
        self.btn_apply_ex.clicked.connect(self._apply_exclusions)
        card_ex_layout.addWidget(self.btn_apply_ex)
        
        right_panel.addWidget(self.card_exclusion)
        
        # Card 2: Common & Merge Execution Options
        card_merge = CardWidget(self)
        card_merge_layout = QVBoxLayout(card_merge)
        card_merge_layout.setSpacing(15)
        card_merge_layout.setContentsMargins(15, 15, 15, 15)
        
        lbl_option_title = SubtitleLabel("공통 병합 설정", card_merge)
        card_merge_layout.addWidget(lbl_option_title)
        
        self.switch_dedup = SwitchButton("중복 페이지 자동 감지 및 제거", card_merge)
        self.switch_dedup.setChecked(True)
        card_merge_layout.addWidget(self.switch_dedup)
        
        self.btn_merge_execute = PrimaryPushButton("PDF 병합 실행 (Merge PDFs)", card_merge, FIF.COMPLETED)
        self.btn_merge_execute.clicked.connect(self._execute_merge)
        card_merge_layout.addWidget(self.btn_merge_execute)
        
        self.lbl_status = BodyLabel("파일을 추가하여 병합을 시작해 주세요.", card_merge)
        self.lbl_status.setStyleSheet("color: #005fb8; font-style: italic;")
        card_merge_layout.addWidget(self.lbl_status)
        
        right_panel.addWidget(card_merge)
        right_panel.addStretch(1)
        
        main_layout.addLayout(right_panel, 2)

    def _update_list_ui(self):
        self.file_list_widget.clear()
        for path in self.pdf_list:
            filename = os.path.basename(path)
            meta = self.pdf_metadata.get(path, {"pages": 0, "exclude_str": ""})
            exclude_text = f" [제외: {meta['exclude_str']}]" if meta['exclude_str'] else ""
            
            item = QListWidgetItem(f"{filename} ({meta['pages']} pgs){exclude_text}")
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.file_list_widget.addItem(item)

    def _add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select PDF Files", "", "PDF Files (*.pdf);;All Files (*)"
        )
        if not files:
            return
            
        for file in files:
            abs_path = os.path.abspath(file)
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
                QMessageBox.critical(self, "Error", f"Failed to load {os.path.basename(file)}:\n{str(e)}")
                
        self._update_list_ui()
        self.lbl_status.setText(f"총 {len(self.pdf_list)}개의 파일이 로드되었습니다.")

    def _remove_file(self):
        selected_items = self.file_list_widget.selectedItems()
        if not selected_items:
            return
            
        item = selected_items[0]
        path = item.data(Qt.ItemDataRole.UserRole)
        
        self.pdf_list.remove(path)
        self.pdf_metadata.pop(path, None)
        
        self._update_list_ui()
        self._clear_details()
        self.lbl_status.setText("파일이 제거되었습니다.")

    def _move_up(self):
        row = self.file_list_widget.currentRow()
        if row <= 0:
            return
        # Swap in list
        self.pdf_list[row], self.pdf_list[row-1] = self.pdf_list[row-1], self.pdf_list[row]
        self._update_list_ui()
        self.file_list_widget.setCurrentRow(row - 1)

    def _move_down(self):
        row = self.file_list_widget.currentRow()
        if row < 0 or row >= len(self.pdf_list) - 1:
            return
        # Swap in list
        self.pdf_list[row], self.pdf_list[row+1] = self.pdf_list[row+1], self.pdf_list[row]
        self._update_list_ui()
        self.file_list_widget.setCurrentRow(row + 1)

    def _on_item_selection_changed(self):
        selected_items = self.file_list_widget.selectedItems()
        if not selected_items:
            self._clear_details()
            return
            
        item = selected_items[0]
        path = item.data(Qt.ItemDataRole.UserRole)
        
        # Save previous exclusions first
        if self.current_selection_path and self.current_selection_path in self.pdf_metadata:
            self._save_exclusions(self.current_selection_path, self.exclude_entry.text().strip())
            
        self.current_selection_path = path
        filename = os.path.basename(path)
        meta = self.pdf_metadata[path]
        
        self.lbl_selected_title.setText(filename)
        self.lbl_page_count.setText(f"Total Pages: {meta['pages']}")
        
        self.exclude_entry.setEnabled(True)
        self.exclude_entry.setText(meta["exclude_str"])
        self.btn_apply_ex.setEnabled(True)

    def _clear_details(self):
        self.current_selection_path = None
        self.lbl_selected_title.setText("No PDF selected")
        self.lbl_page_count.setText("Total Pages: -")
        self.exclude_entry.clear()
        self.exclude_entry.setEnabled(False)
        self.btn_apply_ex.setEnabled(False)

    def _on_exclude_text_changed(self, text):
        # Automatically update metadata list presentation on change
        if self.current_selection_path:
            self.pdf_metadata[self.current_selection_path]["exclude_str"] = text.strip()

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

    def _save_exclusions(self, path, exclude_str):
        meta = self.pdf_metadata[path]
        if exclude_str == meta["exclude_str"]:
            return True
            
        excluded, err = self._parse_exclude_string(exclude_str, meta["pages"])
        if err:
            return False
            
        meta["exclude_str"] = exclude_str
        return True

    def _apply_exclusions(self):
        if not self.current_selection_path:
            return
        val = self.exclude_entry.text().strip()
        meta = self.pdf_metadata[self.current_selection_path]
        
        excluded, err = self._parse_exclude_string(val, meta["pages"])
        if err:
            QMessageBox.warning(self, "Validation Error", f"Failed to apply exclusions:\n{err}")
            return
            
        meta["exclude_str"] = val
        self._update_list_ui()
        # Reselect
        for i in range(self.file_list_widget.count()):
            item = self.file_list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == self.current_selection_path:
                self.file_list_widget.setCurrentItem(item)
                break
                
        self.lbl_status.setText("Exclusion settings applied.")

    def _execute_merge(self):
        if not self.pdf_list:
            QMessageBox.warning(self, "Warning", "Please add at least one PDF file.")
            return
            
        # Verify exclusions for all files
        for path in self.pdf_list:
            meta = self.pdf_metadata[path]
            _, err = self._parse_exclude_string(meta["exclude_str"], meta["pages"])
            if err:
                QMessageBox.critical(
                    self, "Error", 
                    f"Invalid exclusions in file: {os.path.basename(path)}\n{err}"
                )
                return
                
        output_file, _ = QFileDialog.getSaveFileName(
            self, "Save Merged PDF As", "", "PDF Files (*.pdf)"
        )
        if not output_file:
            return
            
        self.lbl_status.setText("PDF 병합 중... 잠시만 기다려 주세요.")
        
        # Prepare page exclusions
        exclude_pages = {}
        for path in self.pdf_list:
            meta = self.pdf_metadata[path]
            if meta["exclude_str"]:
                excluded_set, _ = self._parse_exclude_string(meta["exclude_str"], meta["pages"])
                exclude_pages[path] = excluded_set
                
        # Perform merge
        remove_dups = self.switch_dedup.isChecked()
        success, msg = PDFProcessor.merge_pdfs(
            pdf_paths=self.pdf_list,
            output_path=output_file,
            exclude_pages=exclude_pages,
            remove_duplicates=remove_dups
        )
        
        if success:
            self.lbl_status.setText("병합 성공!")
            QMessageBox.information(self, "Success", f"PDFs successfully merged and saved to:\n{output_file}")
        else:
            self.lbl_status.setText("병합 실패.")
            QMessageBox.critical(self, "Error", f"Failed to merge PDFs:\n{msg}")


class SplitInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.split_source_path = ""
        self.split_source_pages = 0
        self.split_output_dir = ""
        
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title_label = SubtitleLabel("PDF Connection - Split", self)
        layout.addWidget(title_label)
        
        # Card 1: Source Selection
        self.card_source = CardWidget(self)
        src_layout = QHBoxLayout(self.card_source)
        src_layout.setContentsMargins(15, 15, 15, 15)
        
        self.lbl_split_file_path = BodyLabel("분할할 원본 PDF 파일을 선택해 주세요. (Select PDF to Split)", self.card_source)
        src_layout.addWidget(self.lbl_split_file_path, 1)
        
        self.btn_select_src = PushButton("PDF 선택", self.card_source, FIF.FOLDER)
        self.btn_select_src.clicked.connect(self._select_split_source)
        src_layout.addWidget(self.btn_select_src)
        
        layout.addWidget(self.card_source)
        
        # Card 2: Split Options
        self.card_options = CardWidget(self)
        opt_layout = QVBoxLayout(self.card_options)
        opt_layout.setSpacing(15)
        opt_layout.setContentsMargins(15, 15, 15, 15)
        
        lbl_opt_title = SubtitleLabel("분할 방식 설정 (Split Mode)", self.card_options)
        opt_layout.addWidget(lbl_opt_title)
        
        # Mode button group
        self.btn_group = QButtonGroup(self)
        
        # Mode 1: Every page
        self.rad_every = RadioButton("낱장 분할 (Extract every page as a single PDF)", self.card_options)
        self.rad_every.setChecked(True)
        self.btn_group.addButton(self.rad_every, 0)
        opt_layout.addWidget(self.rad_every)
        
        # Mode 2: Split at Page X
        mode2_layout = QHBoxLayout()
        self.rad_at_page = RadioButton("지정 페이지 기준 이분할 (Split into 2 files at page index):", self.card_options)
        self.btn_group.addButton(self.rad_at_page, 1)
        mode2_layout.addWidget(self.rad_at_page)
        
        self.split_at_entry = LineEdit(self.card_options)
        self.split_at_entry.setFixedWidth(80)
        self.split_at_entry.setEnabled(False)
        mode2_layout.addWidget(self.split_at_entry)
        
        lbl_hint_at = BodyLabel("(예: 4 -> 1-4페이지 파일 1개, 5-마지막페이지 파일 1개 생성)", self.card_options)
        lbl_hint_at.setStyleSheet("color: gray; font-size: 11px;")
        mode2_layout.addWidget(lbl_hint_at)
        mode2_layout.addStretch(1)
        opt_layout.addLayout(mode2_layout)
        
        # Mode 3: Custom Ranges
        mode3_layout = QHBoxLayout()
        self.rad_ranges = RadioButton("범위 지정 분할 (Split by custom ranges):", self.card_options)
        self.btn_group.addButton(self.rad_ranges, 2)
        mode3_layout.addWidget(self.rad_ranges)
        
        self.split_ranges_entry = LineEdit(self.card_options)
        self.split_ranges_entry.setFixedWidth(150)
        self.split_ranges_entry.setEnabled(False)
        mode3_layout.addWidget(self.split_ranges_entry)
        
        lbl_hint_ranges = BodyLabel("(예: 1-3, 4-5)", self.card_options)
        lbl_hint_ranges.setStyleSheet("color: gray; font-size: 11px;")
        mode3_layout.addWidget(lbl_hint_ranges)
        mode3_layout.addStretch(1)
        opt_layout.addLayout(mode3_layout)
        
        self.btn_group.idClicked.connect(self._on_split_mode_changed)
        layout.addWidget(self.card_options)
        
        # Card 3: Output Selection
        self.card_output = CardWidget(self)
        out_layout = QHBoxLayout(self.card_output)
        out_layout.setContentsMargins(15, 15, 15, 15)
        
        self.lbl_split_output_dir = BodyLabel("저장 폴더: 원본 파일 위치와 동일 (Default: Same as Source Folder)", self.card_output)
        out_layout.addWidget(self.lbl_split_output_dir, 1)
        
        self.btn_select_out = PushButton("폴더 선택", self.card_output, FIF.FOLDER)
        self.btn_select_out.clicked.connect(self._select_split_output_dir)
        out_layout.addWidget(self.btn_select_out)
        
        layout.addWidget(self.card_output)
        
        # Action Row
        action_layout = QHBoxLayout()
        self.lbl_split_status = BodyLabel("분할할 원본 PDF 파일을 선택해 주세요.", self)
        self.lbl_split_status.setStyleSheet("color: gray; font-style: italic;")
        action_layout.addWidget(self.lbl_split_status)
        
        self.btn_split_execute = PrimaryPushButton("PDF 분할 실행 (Split PDF)", self, FIF.COMPLETED)
        self.btn_split_execute.setEnabled(False)
        self.btn_split_execute.clicked.connect(self._execute_split)
        action_layout.addWidget(self.btn_split_execute)
        
        layout.addLayout(action_layout)
        layout.addStretch(1)

    def _select_split_source(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Select PDF to Split", "", "PDF Files (*.pdf)"
        )
        if not file:
            return
            
        abs_path = os.path.abspath(file)
        try:
            doc = fitz.open(abs_path)
            self.split_source_pages = len(doc)
            doc.close()
            
            self.split_source_path = abs_path
            self.lbl_split_file_path.setText(f"선택된 파일: {abs_path} (총 {self.split_source_pages} 페이지)")
            
            self.btn_split_execute.setEnabled(True)
            self.lbl_split_status.setText("원하는 분할 방식을 설정한 후 실행해 주세요.")
            
            if not self.split_output_dir:
                self.split_output_dir = os.path.dirname(abs_path)
                self.lbl_split_output_dir.setText(f"저장 폴더: {self.split_output_dir}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load PDF:\n{str(e)}")
            self.btn_split_execute.setEnabled(False)

    def _select_split_output_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.split_output_dir = os.path.abspath(folder)
            self.lbl_split_output_dir.setText(f"저장 폴더: {self.split_output_dir}")

    def _on_split_mode_changed(self, id):
        self.split_at_entry.setEnabled(id == 1)
        self.split_ranges_entry.setEnabled(id == 2)

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
            return
            
        mode_id = self.btn_group.checkedId()
        mode = "every"
        parameter = None
        
        if mode_id == 0:
            mode = "every"
        elif mode_id == 1:
            mode = "at_page"
            val = self.split_at_entry.text().strip()
            if not val:
                QMessageBox.warning(self, "Warning", "Please enter a split page index.")
                return
            try:
                split_idx = int(val)
                if split_idx < 1 or split_idx >= self.split_source_pages:
                    QMessageBox.warning(
                        self, "Warning", 
                        f"Split index must be between 1 and {self.split_source_pages - 1}."
                    )
                    return
                parameter = split_idx
            except ValueError:
                QMessageBox.warning(self, "Warning", "Split index must be an integer.")
                return
        elif mode_id == 2:
            mode = "ranges"
            val = self.split_ranges_entry.text().strip()
            ranges, err = self._parse_split_ranges(val, self.split_source_pages)
            if err:
                QMessageBox.warning(self, "Error", f"Failed to parse ranges:\n{err}")
                return
            parameter = ranges
            
        out_dir = self.split_output_dir if self.split_output_dir else os.path.dirname(self.split_source_path)
        self.lbl_split_status.setText("PDF 분할 작업 중... 잠시만 기다려 주세요.")
        
        success, msg = PDFProcessor.split_pdf(
            pdf_path=self.split_source_path,
            output_dir=out_dir,
            mode=mode,
            parameter=parameter
        )
        
        if success:
            self.lbl_split_status.setText("분할 성공!")
            QMessageBox.information(self, "Success", f"PDF successfully split and saved to:\n{out_dir}")
        else:
            self.lbl_split_status.setText("분할 실패.")
            QMessageBox.critical(self, "Error", f"Failed to split PDF:\n{msg}")


class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Connection")
        self.resize(850, 650)
        self.setMinimumSize(800, 600)
        
        # Force Light Theme for consistent elegant look (or can use system theme)
        setTheme(Theme.LIGHT)
        
        self.merge_interface = MergeInterface(self)
        self.split_interface = SplitInterface(self)
        
        self._init_navigation()

    def _init_navigation(self):
        self.addSubInterface(self.merge_interface, FIF.ALBUM, "PDF 병합 (Merge)")
        self.addSubInterface(self.split_interface, FIF.CUT, "PDF 분할 (Split)")
        
        # Position navigation bar elegantly
        self.navigationInterface.setMinimumExpandWidth(180)
        self.navigationInterface.setExpand(True)
