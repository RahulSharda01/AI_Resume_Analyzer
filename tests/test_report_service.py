import unittest
from types import SimpleNamespace

from app.resume.report_service import ResumeReportService


class ReportServiceTests(unittest.TestCase):
    def test_generate_report_returns_pdf_bytes(self):
        service = ResumeReportService()
        resume = SimpleNamespace(
            original_filename="sample.pdf",
            upload_time=__import__("datetime").datetime(2024, 1, 1, 12, 0, 0),
        )

        buffer = service.generate_report(
            resume,
            ats_analysis={"scores": {"experience": 0.9}, "overall_score": 90},
            match_result={"similarity_percent": 85, "matched_skills": ["Python"], "missing_skills": ["Flask"], "suggested_skills": ["SQLAlchemy"]},
        )

        self.assertTrue(buffer.getvalue().startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
