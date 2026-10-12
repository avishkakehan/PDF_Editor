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
                                QAbstractItemView,
                                QScrollArea,
                                QSizePolicy
                                )
from pdf.document import PDFDocument
from PySide6.QtGui import QImage, QPixmap, QDrag, QPainter
from PySide6.QtCore import Qt, QSize, QMimeData, QUrl


class DraggableThumbnail(QLabel):
    """A thumbnail label that supports drag-and-drop reordering."""

    def __init__(self, page_num, parent=None):
        super().__init__(parent)
        self.page_num = page_num
        self.parent_window = None
        self.drag_start_position = None
        self.is_dragging = False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
            self.is_dragging = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        if self.drag_start_position is None:
            return
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return

        # Start drag operation
        self.is_dragging = True
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(str(self.page_num))
        drag.setMimeData(mime_data)

        # Create a pixmap for the drag cursor
        pixmap = QPixmap(self.size())
        self.render(pixmap)
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos())

        drag.exec(Qt.MoveAction)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not self.is_dragging and self.parent_window:
                # This was a click, not a drag — toggle selection
                self.parent_window.on_thumbnail_click(self.page_num)
            self.drag_start_position = None
            self.is_dragging = False
        super().mouseReleaseEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            from_page = int(event.mimeData().text())
            to_page = self.page_num
            if from_page != to_page and self.parent_window:
                self.parent_window.document.reorder_page(from_page, to_page)
                self.parent_window.generate_thumbnails()
                self.parent_window.update_preview()
                self.parent_window.update_navigation()
            event.acceptProposedAction()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.document = PDFDocument()
        self.pdf_files = []
        self.current_page = 0
        self.selected_pages = set()  # Set of selected page indices
        self.thumbnails = []  # List of QLabels for thumbnails

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

        self.pdf_list = QListWidget()
        self.pdf_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.pdf_list.setMinimumHeight(100)
        self.pdf_list.setMaximumHeight(160)
        self.pdf_list.itemClicked.connect(self.on_pdf_list_item_clicked)
        sidebar_layout.addWidget(self.pdf_list)

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

        # --- Page Edit Section ---
        page_edit_label = QLabel("PAGE EDIT")
        page_edit_label.setObjectName("section_label")
        sidebar_layout.addWidget(page_edit_label)

        rotate_left_btn = QPushButton("Rotate Left")
        rotate_left_btn.clicked.connect(lambda: self.rotate_selected(-90))
        sidebar_layout.addWidget(rotate_left_btn)

        rotate_right_btn = QPushButton("Rotate Right")
        rotate_right_btn.clicked.connect(lambda: self.rotate_selected(90))
        sidebar_layout.addWidget(rotate_right_btn)

        move_left_btn = QPushButton("Move Left")
        move_left_btn.clicked.connect(lambda: self.move_selected(-1))
        sidebar_layout.addWidget(move_left_btn)

        move_right_btn = QPushButton("Move Right")
        move_right_btn.clicked.connect(lambda: self.move_selected(1))
        sidebar_layout.addWidget(move_right_btn)

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

        # --- Thumbnail Strip ---
        thumbnail_container = QFrame()
        thumbnail_container.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 8px;
                border: 1px solid #e0e0e8;
            }
        """)
        thumbnail_layout = QVBoxLayout()
        thumbnail_layout.setContentsMargins(10, 5, 10, 5)
        thumbnail_layout.setSpacing(2)

        thumbnail_header = QLabel("Pages (click to select)")
        thumbnail_header.setStyleSheet("color: #777; font-size: 11px; padding: 2px;")
        thumbnail_layout.addWidget(thumbnail_header)

        # Scroll area for thumbnails
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(120)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:horizontal {
                height: 8px;
                background: #f0f0f5;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal {
                background: #c0c0d0;
                border-radius: 4px;
            }
        """)

        self.thumbnail_widget = QWidget()
        self.thumbnail_layout = QHBoxLayout()
        self.thumbnail_layout.setContentsMargins(0, 0, 0, 0)
        self.thumbnail_layout.setSpacing(6)
        self.thumbnail_widget.setLayout(self.thumbnail_layout)
        scroll.setWidget(self.thumbnail_widget)

        thumbnail_layout.addWidget(scroll)
        thumbnail_container.setLayout(thumbnail_layout)

        workspace_layout.addWidget(toolbar)
        workspace_layout.addWidget(preview_frame, 1)
        workspace_layout.addWidget(thumbnail_container)

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
            self._current_file_path = file_path
            self.document.open(file_path)
            self.current_page = 0
            self.pdf_files = [file_path]
            self.selected_pages = set()
            self.refresh_pdf_list()
            self.update_preview()
            self.update_navigation()
            self.generate_thumbnails()

    def load_pdf_from_path(self, file_path):
        """Load a PDF from the given path into the preview."""
        self._current_file_path = file_path
        self.document.open(file_path)
        self.current_page = 0
        self.selected_pages = set()
        self.update_preview()
        self.update_navigation()
        self.generate_thumbnails()

    def on_pdf_list_item_clicked(self, item):
        """When user clicks a PDF in the list, display it in the preview."""
        row = self.pdf_list.row(item)
        if 0 <= row < len(self.pdf_files):
            file_path = self.pdf_files[row]
            self.load_pdf_from_path(file_path)

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

        # Track if we're removing the currently displayed document
        removed_paths = []
        for item in selected_items:
            row = self.pdf_list.row(item)
            if row < len(self.pdf_files):
                removed_paths.append(self.pdf_files[row])
            self.pdf_list.takeItem(row)
            if row < len(self.pdf_files):
                self.pdf_files.pop(row)

        # Check if the currently displayed PDF was removed
        current_file = self.pdf_files[0] if self.pdf_files else None
        display_cleared = False

        # If the document being displayed was removed, clear it
        if hasattr(self, '_current_file_path') and self._current_file_path in removed_paths:
            self.clear_preview()
            display_cleared = True
        elif not self.pdf_files:
            self.clear_preview()
            display_cleared = True
        elif self.pdf_files and hasattr(self, '_current_file_path') and self._current_file_path not in self.pdf_files:
            # The displayed file was removed, show the first remaining file
            self.load_pdf_from_path(self.pdf_files[0])

    def clear_pdf_list(self):
        self.pdf_list.clear()
        self.pdf_files = []
        self.clear_preview()

    def clear_preview(self):
        """Clear the preview area and reset the loaded document."""
        self.document = PDFDocument()
        self.current_page = 0
        self.selected_pages = set()
        self.preview_label.setPixmap(QPixmap())
        self.preview_label.setText("Open a PDF to start editing")
        self.preview_label.setStyleSheet("""
            color: #999;
            font-size: 16px;
        """)
        self.clear_thumbnails()
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

    # ==================== PAGE EDIT: ROTATE & REORDER ====================

    def rotate_selected(self, angle):
        """Rotate all selected pages by the given angle."""
        if not self.document.document:
            QMessageBox.warning(self, "Rotate", "Please open a PDF first.")
            return

        if not self.selected_pages:
            QMessageBox.information(
                self,
                "Rotate",
                "Please select one or more pages from the thumbnail strip first."
            )
            return

        for page_num in self.selected_pages:
            page = self.document.get_page(page_num)
            current_rotation = page.rotation
            new_rotation = (current_rotation + angle) % 360
            page.set_rotation(new_rotation)

        self.generate_thumbnails()
        self.update_preview()
        QMessageBox.information(
            self,
            "Rotated",
            f"Rotated {len(self.selected_pages)} page(s) by {angle} degrees."
        )

    def move_selected(self, direction):
        """Move selected pages left (-1) or right (+1)."""
        if not self.document.document:
            QMessageBox.warning(self, "Move", "Please open a PDF first.")
            return

        if not self.selected_pages:
            QMessageBox.information(
                self,
                "Move",
                "Please select one or more pages from the thumbnail strip first."
            )
            return

        page_count = self.document.page_count()
        sorted_pages = sorted(self.selected_pages)

        if direction < 0:
            # Moving left: can't move the first page further left
            if sorted_pages[0] == 0:
                QMessageBox.information(self, "Move", "Already at the first position.")
                return
            for page_num in sorted_pages:
                self.document.reorder_page(page_num, page_num - 1)
            self.selected_pages = {p - 1 for p in self.selected_pages}
        else:
            # Moving right: can't move the last page further right
            if sorted_pages[-1] == page_count - 1:
                QMessageBox.information(self, "Move", "Already at the last position.")
                return
            for page_num in reversed(sorted_pages):
                self.document.reorder_page(page_num, page_num + 1)
            self.selected_pages = {p + 1 for p in self.selected_pages}

        self.generate_thumbnails()
        self.update_preview()
        self.update_navigation()

    # ==================== THUMBNAILS ====================

    def generate_thumbnails(self):
        """Generate thumbnail images for all pages."""
        self.clear_thumbnails()

        if not self.document.document:
            return

        page_count = self.document.page_count()
        for i in range(page_count):
            # Create draggable thumbnail
            thumb = DraggableThumbnail(i)
            thumb.parent_window = self
            thumb.setFixedSize(70, 90)
            thumb.setAcceptDrops(True)
            thumb.setStyleSheet("""
                QLabel {
                    border: 2px solid #d0d0e0;
                    border-radius: 4px;
                    background-color: #fafafa;
                }
            """)
            thumb.setAlignment(Qt.AlignCenter)
            thumb.setScaledContents(False)

            # Render the page as a small thumbnail
            try:
                pixmap = self.document.render_page(i)
                img = QImage(pixmap.samples, pixmap.width, pixmap.height,
                             pixmap.stride, QImage.Format_RGB888)
                qpixmap = QPixmap.fromImage(img)
                scaled = qpixmap.scaled(QSize(64, 84), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                thumb.setPixmap(scaled)
            except Exception:
                thumb.setText(f"Page {i+1}")

            # Store reference
            self.thumbnails.append(thumb)
            self.thumbnail_layout.addWidget(thumb)

        self.highlight_selected_thumbnails()

    def clear_thumbnails(self):
        """Remove all thumbnail widgets."""
        for thumb in self.thumbnails:
            self.thumbnail_layout.removeWidget(thumb)
            thumb.deleteLater()
        self.thumbnails = []

    def on_thumbnail_click(self, page_num):
        """Handle thumbnail click to select/deselect pages."""
        if page_num in self.selected_pages:
            self.selected_pages.discard(page_num)
        else:
            self.selected_pages.add(page_num)

        self.current_page = page_num
        self.highlight_selected_thumbnails()
        self.update_preview()
        self.update_navigation()

    def highlight_selected_thumbnails(self):
        """Update thumbnail borders to show selection."""
        for i, thumb in enumerate(self.thumbnails):
            if i in self.selected_pages:
                thumb.setStyleSheet("""
                    QLabel {
                        border: 3px solid #4a4a8a;
                        border-radius: 4px;
                        background-color: #e8e8ff;
                    }
                """)
            else:
                thumb.setStyleSheet("""
                    QLabel {
                        border: 2px solid #d0d0e0;
                        border-radius: 4px;
                        background-color: #fafafa;
                    }
                """)

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
                self.document.save(output_path)
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
