import pymupdf

class PDFDocument:
    def __init__(self):
        self.document = None

    def open(self, file_path):
        self.document = pymupdf.open(file_path)

    def page_count(self):
        return len(self.document)

    def get_page(self,page_number):
        return self.document[page_number]

    def render_page(self, page_number):
        page = self.get_page(page_number)
        return page.get_pixmap()