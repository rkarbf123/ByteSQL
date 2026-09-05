import os


class Pager:
    PAGE_SIZE = 4096

    def __init__(self, filepath):
        self.filepath = filepath
        self.file = open(filepath, "a+b")
        self.file.seek(0, os.SEEK_END)
        file_length = self.file.tell()
        self.num_pages = file_length // self.PAGE_SIZE

        if self.num_pages == 0:
            self.allocate_page()

    def read_page(self, page_id):
        if page_id >= self.num_pages:
            raise IndexError("Page out of bounds")
        self.file.seek(page_id * self.PAGE_SIZE)
        return self.file.read(self.PAGE_SIZE)

    def write_page(self, page_id, data):
        if len(data) > self.PAGE_SIZE:
            raise ValueError("Data exceeds page size")
        data = data.ljust(self.PAGE_SIZE, b"\x00")
        self.file.seek(page_id * self.PAGE_SIZE)
        self.file.write(data)
        self.file.flush()

    def allocate_page(self):
        self.file.seek(self.num_pages * self.PAGE_SIZE)
        self.file.write(b"\x00" * self.PAGE_SIZE)
        self.file.flush()
        page_id = self.num_pages
        self.num_pages += 1
        return page_id

    def close(self):
        self.file.close()
