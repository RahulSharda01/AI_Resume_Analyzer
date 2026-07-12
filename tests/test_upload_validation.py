import unittest
from io import BytesIO
from types import SimpleNamespace

from app.resume.services import validate_resume_upload


class UploadValidationTests(unittest.TestCase):
    def test_validate_resume_upload_accepts_valid_pdf(self):
        file_storage = SimpleNamespace(
            filename="My Resume.pdf",
            stream=BytesIO(b"%PDF-1.4\n%test"),
            content_type="application/pdf",
        )

        filename, file_size = validate_resume_upload(file_storage, max_content_length=1024 * 1024)

        self.assertEqual(filename, "My Resume.pdf")
        self.assertEqual(file_size, len(b"%PDF-1.4\n%test"))

    def test_validate_resume_upload_rejects_invalid_extension(self):
        file_storage = SimpleNamespace(
            filename="resume.txt",
            stream=BytesIO(b"not a resume"),
            content_type="text/plain",
        )

        with self.assertRaises(ValueError):
            validate_resume_upload(file_storage, max_content_length=1024 * 1024)


if __name__ == "__main__":
    unittest.main()
