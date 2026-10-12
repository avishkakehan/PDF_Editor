import pymupdf


class PDFDocument:
    def __init__(self):
        self.document = None

    def open(self, file_path):
        self.document = pymupdf.open(file_path)

    def page_count(self):
        return len(self.document)

    def get_page(self, page_number):
        return self.document[page_number]

    def render_page(self, page_number):
        page = self.get_page(page_number)
        return page.get_pixmap()

    def rotate_page(self, page_number, angle):
        """Rotate a page by the given angle (90, 180, 270)."""
        page = self.get_page(page_number)
        page.set_rotation(angle)

    def reorder_page(self, from_index, to_index):
        """Move a page from one position to another."""
        self.document.move_page(from_index, to_index)

    def save(self, output_path):
        """Save the document to the given path."""
        self.document.save(output_path)
