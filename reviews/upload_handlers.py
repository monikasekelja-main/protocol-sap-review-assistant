from django.core.exceptions import RequestDataTooBig
from django.core.files.uploadhandler import FileUploadHandler, StopUpload


class BoundedUploadHandler(FileUploadHandler):
    """Stop oversized multipart uploads before they fill temporary storage."""

    def __init__(self, request=None):
        super().__init__(request)
        self.total_bytes = self.file_bytes = self.file_count = 0

    def handle_raw_input(self, input_data, META, content_length, boundary, encoding=None):
        if content_length and content_length > 52 * 1024 * 1024:
            raise RequestDataTooBig("Upload request exceeds 52 MB.")

    def new_file(self, *args, **kwargs):
        super().new_file(*args, **kwargs)
        self.file_bytes = 0
        self.file_count += 1
        if self.file_count > 2:
            raise StopUpload(connection_reset=True)

    def receive_data_chunk(self, raw_data, start):
        self.file_bytes += len(raw_data)
        self.total_bytes += len(raw_data)
        if self.file_bytes > 25 * 1024 * 1024 or self.total_bytes > 50 * 1024 * 1024:
            raise StopUpload(connection_reset=True)
        return raw_data

    def file_complete(self, file_size):
        return None
