from io import BytesIO
from datetime import datetime
from html import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


class ResumeReportService:
    """Generate a professional PDF report for a resume analysis summary."""

    def generate_report(self, resume, ats_analysis=None, match_result=None, interview_questions=None):
        """Create a PDF buffer containing the resume summary and analysis data."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=54,
        )

        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph("AI Resume Analyzer Report", styles["Title"]))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Resume:</b> {escape(resume.original_filename)}", styles["Heading2"]))
        story.append(Paragraph(
            f"<b>Uploaded:</b> {resume.upload_time.strftime('%Y-%m-%d %H:%M') if resume.upload_time else 'Not Available'}",
            styles["Normal"],
        ))
        story.append(Paragraph(
            f"<b>Generated:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            styles["Normal"],
        ))
        story.append(Spacer(1, 18))

        story.append(Paragraph("ATS Analysis", styles["Heading3"]))
        if ats_analysis:
            story.append(Paragraph(
                f"<b>Overall ATS Score:</b> {ats_analysis.get('overall_score', 'Not Available')}",
                styles["Normal"],
            ))
            story.append(Spacer(1, 6))

            scores = ats_analysis.get("scores", {})
            if scores:
                table_data = [["Category", "Score"]]
                for key, value in scores.items():
                    table_data.append([key.replace("_", " ").title(), f"{round(value * 100, 1)}%"])
                table = Table(table_data, repeatRows=1)
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d6efd")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                            ("PADDING", (0, 0), (-1, -1), 6),
                        ]
                    )
                )
                story.append(table)
                story.append(Spacer(1, 6))

            missing_skills = ats_analysis.get("missing_skills", [])
            suggestions = ats_analysis.get("suggestions", [])
            story.append(Paragraph(
                f"<b>Missing Skills:</b> {escape(', '.join(missing_skills)) if missing_skills else 'Not Available'}",
                styles["Normal"],
            ))
            story.append(Spacer(1, 6))
            story.append(Paragraph("<b>ATS Suggestions:</b>", styles["Normal"]))
            if suggestions:
                for suggestion in suggestions:
                    story.append(Paragraph(escape(suggestion), styles["Normal"]))
            else:
                story.append(Paragraph("Not Available", styles["Normal"]))
        else:
            story.append(Paragraph("Not Available", styles["Normal"]))
        story.append(Spacer(1, 18))

        story.append(Paragraph("Job Description Matching", styles["Heading3"]))
        if match_result:
            story.append(Paragraph(
                f"<b>Match Percentage:</b> {match_result.get('similarity_percent', 'Not Available')}%",
                styles["Normal"],
            ))
            story.append(Paragraph(
                f"<b>Matched Skills:</b> {escape(', '.join(match_result.get('matched_skills', []))) if match_result.get('matched_skills') else 'Not Available'}",
                styles["Normal"],
            ))
            story.append(Paragraph(
                f"<b>Missing Skills:</b> {escape(', '.join(match_result.get('missing_skills', []))) if match_result.get('missing_skills') else 'Not Available'}",
                styles["Normal"],
            ))
            story.append(Paragraph(
                f"<b>Suggested Skills to Learn:</b> {escape(', '.join(match_result.get('suggested_skills', []))) if match_result.get('suggested_skills') else 'Not Available'}",
                styles["Normal"],
            ))
        else:
            story.append(Paragraph("Not Available", styles["Normal"]))
        story.append(Spacer(1, 18))

        story.append(Paragraph("Interview Questions", styles["Heading3"]))
        if interview_questions:
            story.append(Paragraph("<b>Technical Questions:</b>", styles["Normal"]))
            for question in interview_questions.get("technical", []):
                story.append(Paragraph(escape(question), styles["Normal"]))
            story.append(Spacer(1, 6))
            story.append(Paragraph("<b>Project Questions:</b>", styles["Normal"]))
            for question in interview_questions.get("project", []):
                story.append(Paragraph(escape(question), styles["Normal"]))
            story.append(Spacer(1, 6))
            story.append(Paragraph("<b>HR Questions:</b>", styles["Normal"]))
            for question in interview_questions.get("hr", []):
                story.append(Paragraph(escape(question), styles["Normal"]))
        else:
            story.append(Paragraph("Not Available", styles["Normal"]))
        story.append(Spacer(1, 18))

        story.append(Paragraph("Resume Summary", styles["Heading3"]))
        story.append(Paragraph(self._build_summary(getattr(resume, "extracted_text", None)), styles["Normal"]))
        story.append(Spacer(1, 24))

        story.append(Paragraph("Generated by AI Resume Analyzer", styles["Italic"]))

        doc.build(story, onFirstPage=self._add_footer, onLaterPages=self._add_footer)
        buffer.seek(0)
        return buffer

    def _build_summary(self, text):
        if not text or not text.strip():
            return "Not Available"

        normalized = text.replace("\r\n", "\n").strip()
        paragraphs = [paragraph.strip() for paragraph in normalized.split("\n\n") if paragraph.strip()]
        summary_text = "\n\n".join(paragraphs[:3]) if paragraphs else normalized
        if len(summary_text) > 1400:
            summary_text = summary_text[:1400].rsplit(" ", 1)[0] + "..."

        return escape(summary_text).replace("\n", "<br/>")

    def _add_footer(self, canvas, doc):
        canvas.saveState()
        footer_text = f"Generated by AI Resume Analyzer • {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(36, 20, footer_text)
        canvas.drawRightString(letter[0] - 36, 20, f"Page {doc.page}")
        canvas.restoreState()
