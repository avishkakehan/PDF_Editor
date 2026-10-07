import sys
import os
from PySide6.QtWidgets import (QApplication,
                                QMainWindow,
                                QWidget,
                                QHBoxLayout,
                                QFrame,
                                QVBoxLayout,
                                QLabel,
                                QPushButton,
                                QFileDialog,
                                QMessageBox,
                                QInputDialog,
                                QListWidget,
                                QListWidgetItem,
                                QAbstractItemView
                                )
from pdf.document import PDFDocument
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt, QSize


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.document = PDFDocument()
        self.pdf_files = []
        self.current_page = 0

        self.setWindowTitle("PDF Editor")
        self.resize(1200, 700)
        self.setMinimumSize(900, 500)

        # ---- Central Widget & Main Layout ----
        central_widget = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ---- Sidebar ----
        sidebar = QFrame()
        sidebar.setFixedWidth(260)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #1e1e2f;
                border-right: 1px solid #2d2d44;
            }
            QLabel#app_title {
                color: #e0e0e0;
                font-size: 20px;
                font-weight: bold;
                padding: 20px 10px 10px 10px;
            }
            QLabel#section_label {
                color: #7a7a9a;
                font-size: 11px;
                font-weight: bold;
                padding: 15px 10px 5px 10px;
            }
            QPushButton {
                background-color: transparent;
                color: #c0c0d0;
                border: none;
                padding: 10px 15px;
                text-align: left;
                font-size: 13px;
                border-radius: 6px;
                margin: 2px 8px;
            }
            QPushButton:hover {
                background-color: #2d2d44;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #3d3d5c;
            }
            QPushButton#action_btn {
                background-color: #4a4a8a;
                color: #ffffff;
                font-weight: bold;
                text-align: center;
                padding: 12px 15px;
                margin: 4px 8px;
            }
            QPushButton#action_btn:hover {
                background-color: #5a5a9a;
            }
            QPushButton#action_btn:pressed {
                background-color: #3a3a7a;
            }
            QPushButton#small_btn {
                background-color: #2d2d44;
                color: #c0c0d0;
                border: none;
                padding: 6px 10px;
                text-align: center;
                font-size: 11px;
                border-radius: 4px;
                margin: 2px 4px;
            }
            QPushButton#small_btn:hover {
                background-color: #3d3d5c;
                color: #ffffff;
            }
            QListWidget {
                background-color: #16162a;
                border: 1px solid #2d2d44;
                border-radius: 6px;
                margin: 4px 8px;
                padding: 4px;
                color: #c0c0d0;
                font-size: 12px;
                outline: none;
            }
            QListWidget::item {
                padding: 6px 8px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #4a4a8a;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #2d2d44;
            }
        """)

        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # App Title
        title = QLabel("PDF Editor")
        title.setObjectName("app_title")
        sidebar_layout.addWidget(title)

        # --- File Section ---
        file_label = QLabel("FILE")
        file_label.setObjectName("section_label")
        sidebar_layout.addWidget(file_label)

        open_btn = QPushButton("Open PDF")
        open_btn.clicked.connect(self.open_pdf)
        sidebar_layout.addWidget(open_btn)

        # --- Selected PDFs List ---
        list_label = QLabel("SELECTED PDFs")
        list_label.setObjectName("section_label")
        sidebar_layout.addWidget(list_label)

        # List widget to show selected PDFs
        self.pdf_list = QListWidget()
        self.pdf_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.pdf_list.setMinimumHeight(120)
        self.pdf_list.setMaximumHeight(200)
        sidebar_layout.addWidget(self.pdf_list)

        # Add/Remove buttons row
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)

        add_btn = QPushButton("+ Add")
        add_btn.setObjectName("small_btn")
        add_btn.clicked.connect(self.add_pdf_to_list)
        btn_row.addWidget(add_btn)

        remove_btn = QPushButton("- Remove")
        remove_btn.setObjectName("small_btn")
        remove_btn.clicked.connect(self.remove_pdf_from_list)
        btn_row.addWidget(remove_btn)

        clear_btn = QPushButton("Clear All")
        clear_btn.setObjectName("small_btn")
        clear_btn.clicked.connect(self.clear_pdf_list)
        btn_row.addWidget(clear_btn)

        sidebar_layout.addLayout(btn_row)

        # --- Tools Section ---
        tools_label = QLabel("TOOLS")
        tools_label.setObjectName("section_label")
        sidebar_layout.addWidget(tools_label)

        merge_btn = QPushButton("Merge PDFs")
        merge_btn.clicked.connect(self.merge_pdfs)
        sidebar_layout.addWidget(merge_btn)

        split_btn = QPushButton("Split PDF")
        split_btn.clicked.connect(self.split_pdf)
        sidebar_layout.addWidget(split_btn)

        # --- Save Section ---
        save_label = QLabel("EXPORT")
        save_label.setObjectName("section_label")
        sidebar_layout.addWidget(save_label)

        save_btn = QPushButton("Save PDF")
        save_btn.setObjectName("action_btn")
        save_btn.clicked.connect(self.save_pdf)
        sidebar_layout.addWidget(save_btn)

        sidebar_layout.addStretch()

        sidebar.setLayout(sidebar_layout)

        # ---- Workspace ----
        workspace = QFrame()
        workspace.setStyleSheet("background-color: #f5f5fa;")

        workspace_layout = QVBoxLayout()
        workspace_layout.setContentsMargins(20, 20, 20, 20)
        workspace_layout.setSpacing(10)

        # Toolbar for navigation
        toolbar = QFrame()
        toolbar.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 8px;
                border: 1px solid #e0e0e8;
            }
            QPushButton {
                background-color: #eeeeF5;
                border: 1px solid #d0d0e0;
                border-radius: 5px;
                padding: 6px 14px;
                font-size: 12px;
                color: #333;
            }
            QPushButton:hover {
                background-color: #e0e0f0;
            }
            QPushButton:pressed {
                background-color: #d0d0e8;
            }
            QLabel {
                font-size: 13px;
                color: #555;
                padding: 0 10px;
            }
        """)
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(10, 8, 10, 8)

        self.prev_btn = QPushButton("Prev")
        self.prev_btn.clicked.connect(self.prev_page)
        self.prev_btn.setEnabled(False)

        self.page_label = QLabel("No PDF loaded")
        self.page_label.setAlignment(Qt.AlignCenter)

        self.next_btn = QPushButton("Next")
        self.next_btn.clicked.connect(self.next_page)
        self.next_btn.setEnabled(False)

        toolbar_layout.addWidget(self.prev_btn)
        toolbar_layout.addWidget(self.page_label, 1)
        toolbar_layout.addWidget(self.next_btn)
        toolbar.setLayout(toolbar_layout)

        # Preview area
        preview_frame = QFrame()
        preview_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 8px;
                border: 1px solid #e0e0e8;
            }
        """)
        preview_layout = QVBoxLayout()
        preview_layout.setContentsMargins(10, 10, 10, 10)

        self.preview_label = QLabel("Open a PDF to start editing")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("""
            color: #999;
            font-size: 16px;
        """)

        preview_layout.addWidget(self.preview_label)
        preview_frame.setLayout(preview_layout)

        workspace_layout.addWidget(toolbar)
        workspace_layout.addWidget(preview_frame, 1)

        workspace.setLayout(workspace_layout)

        # ---- Assemble Main Layout ----
        main_layout.addWidget(sidebar)
        main_layout.addWidget(workspace, 1)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    # ==================== FILE OPERATIONS ====================

    def open_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open PDF",
            "",
            "PDF Files (*.pdf)"
        )
        if file_path:
            self.document.open(file_path)
            self.current_page = 0
            self.pdf_files = [file_path]
            self.refresh_pdf_list()
            self.update_preview()
            self.update_navigation()

    def add_pdf_to_list(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Add PDFs to List",
            "",
            "PDF Files (*.pdf)"
        )
        if file_paths:
            for path in file_paths:
                if path not in self.pdf_files:
                    self.pdf_files.append(path)
            self.refresh_pdf_list()

    def remove_pdf_from_list(self):
        selected_items = self.pdf_list.selectedItems()
        if not selected_items:
            QMessageBox.information(
                self,
                "Remove PDF",
                "Please select a PDF from the list to remove."
            )
            return

        for item in selected_items:
            row = self.pdf_list.row(item)
            self.pdf_list.takeItem(row)
            if row < len(self.pdf_files):
                self.pdf_files.pop(row)

        # If no PDFs remain in the list, clear the preview and document
        if not self.pdf_files:
            self.clear_preview()

    def clear_pdf_list(self):
        self.pdf_list.clear()
        self.pdf_files = []
        self.clear_preview()

    def clear_preview(self):
        """Clear the preview area and reset the loaded document."""
        self.document = PDFDocument()
        self.current_page = 0
        self.preview_label.setPixmap(QPixmap())
        self.preview_label.setText("Open a PDF to start editing")
        self.preview_label.setStyleSheet("""
            color: #999;
            font-size: 16px;
        """)
        self.update_navigation()

    def refresh_pdf_list(self):
        self.pdf_list.clear()
        for path in self.pdf_files:
            filename = os.path.basename(path)
            item = QListWidgetItem(filename)
            item.setToolTip(path)
            self.pdf_list.addItem(item)

    # ==================== TOOLS ====================

    def merge_pdfs(self):
        if len(self.pdf_files) < 2:
            QMessageBox.warning(
                self,
                "Merge PDFs",
                "Please add at least 2 PDFs to the list using '+ Add' button."
            )
            return

        # Show which files will be merged
        file_list = "\n".join([f"  {i+1}. {os.path.basename(f)}" for i, f in enumerate(self.pdf_files)])
        confirm = QMessageBox.question(
            self,
            "Confirm Merge",
            f"The following {len(self.pdf_files)} PDFs will be merged in order:\n\n{file_list}\n\nContinue?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Merged PDF",
            "merged.pdf",
            "PDF Files (*.pdf)"
        )
        if not output_path:
            return

        try:
            import pymupdf
            merged = pymupdf.open()
            for pdf_path in self.pdf_files:
                src = pymupdf.open(pdf_path)
                merged.insert_pdf(src)
                src.close()
            merged.save(output_path)
            merged.close()

            QMessageBox.information(
                self,
                "Success",
                f"Merged {len(self.pdf_files)} PDFs successfully!\nSaved to: {output_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Merge failed: {str(e)}")

    def split_pdf(self):
        if not self.document.document:
            QMessageBox.warning(
                self,
                "Split PDF",
                "Please open a PDF first."
            )
            return

        page_count = self.document.page_count()
        if page_count <= 1:
            QMessageBox.warning(
                self,
                "Split PDF",
                "PDF must have more than 1 page to split."
            )
            return

        text, ok = QInputDialog.getText(
            self,
            "Split PDF",
            f"Enter page ranges to extract (e.g., 1-3, 5, 7-{page_count}):"
        )
        if not ok or not text.strip():
            return

        try:
            import pymupdf
            output_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Split PDF",
                "split.pdf",
                "PDF Files (*.pdf)"
            )
            if not output_path:
                return

            new_doc = pymupdf.open()
            ranges = text.strip().split(",")
            for r in ranges:
                r = r.strip()
                if "-" in r:
                    parts = r.split("-")
                    start = int(parts[0].strip()) - 1
                    end = int(parts[1].strip()) - 1
                else:
                    start = int(r.strip()) - 1
                    end = start

                for i in range(start, end + 1):
                    if 0 <= i < page_count:
                        new_doc.insert_pdf(self.document.document, from_page=i, to_page=i)

            new_doc.save(output_path)
            new_doc.close()

            QMessageBox.information(
                self,
                "Success",
                f"Split PDF saved to: {output_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Split failed: {str(e)}")

    # ==================== SAVE ====================

    def save_pdf(self):
        if not self.document.document:
            QMessageBox.warning(
                self,
                "Save PDF",
                "No PDF is currently loaded."
            )
            return

        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save PDF As",
            "output.pdf",
            "PDF Files (*.pdf)"
        )
        if output_path:
            try:
                self.document.document.save(output_path)
                QMessageBox.information(
                    self,
                    "Success",
                    f"PDF saved to: {output_path}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Save failed: {str(e)}")

    # ==================== NAVIGATION & PREVIEW ====================

    def update_preview(self):
        if not self.document.document:
            return

        page_count = self.document.page_count()
        if self.current_page >= page_count:
            self.current_page = 0

        pixmap = self.document.render_page(self.current_page)
        img = QImage(pixmap.samples, pixmap.width, pixmap.height,
                     pixmap.stride, QImage.Format_RGB888)
        qpixmap = QPixmap.fromImage(img)

        label_size = self.preview_label.size()
        scaled = qpixmap.scaled(label_size - QSize(40, 40),
                                Qt.KeepAspectRatio,
                                Qt.SmoothTransformation)
        self.preview_label.setPixmap(scaled)
        self.preview_label.setStyleSheet("")

    def update_navigation(self):
        if not self.document.document:
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            self.page_label.setText("No PDF loaded")
            return

        page_count = self.document.page_count()
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page < page_count - 1)
        self.page_label.setText(f"Page {self.current_page + 1} of {page_count}")

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_preview()
            self.update_navigation()

    def next_page(self):
        if self.document.document and self.current_page < self.document.page_count() - 1:
            self.current_page += 1
            self.update_preview()
            self.update_navigation()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_preview()


app = QApplication(sys.argv)
app.setStyle("Fusion")

window = MainWindow()
window.show()

sys.exit(app.exec())
