import re
from typing import Dict, List, Tuple


class ATSScoringService:
    """Heuristic ATS scoring engine for resume text analysis."""

    def __init__(self):
        self.category_weights = {
            "contact_information": 0.12,
            "skills": 0.18,
            "education": 0.12,
            "projects": 0.10,
            "experience": 0.20,
            "formatting": 0.10,
            "keywords": 0.18,
        }

        self.contact_patterns = [
            r"\b(?:email|e-mail)\b",
            r"\b(?:phone|mobile|contact)\b",
            r"\b(?:linkedin|github|portfolio)\b",
        ]

        self.skill_keywords = {
            "python",
            "java",
            "javascript",
            "typescript",
            "sql",
            "mysql",
            "postgresql",
            "mongodb",
            "flask",
            "django",
            "fastapi",
            "react",
            "node",
            "docker",
            "kubernetes",
            "aws",
            "azure",
            "git",
            "linux",
            "machine learning",
            "ai",
            "data analysis",
            "api",
            "rest",
        }

        self.education_keywords = ["bachelor", "master", "phd", "degree", "university", "college", "school"]
        self.project_keywords = ["project", "built", "developed", "implemented", "designed", "created"]
        self.experience_keywords = ["experience", "worked", "engineer", "developer", "manager", "intern", "lead"]
        self.formatting_markers = ["summary", "skills", "experience", "education", "projects", "contact"]

    def analyze(self, text: str) -> Dict[str, object]:
        """Analyze resume text and return category results and overall score."""
        if not text or not text.strip():
            return {
                "scores": {
                    "contact_information": 0,
                    "skills": 0,
                    "education": 0,
                    "projects": 0,
                    "experience": 0,
                    "formatting": 0,
                    "keywords": 0,
                },
                "overall_score": 0,
                "missing_skills": [],
                "suggestions": ["Add resume content to generate ATS insights."],
            }

        normalized = re.sub(r"\s+", " ", text.lower()).strip()
        scores = {}

        scores["contact_information"] = self._score_contact_information(normalized)
        scores["skills"] = self._score_skills(normalized)
        scores["education"] = self._score_education(normalized)
        scores["projects"] = self._score_projects(normalized)
        scores["experience"] = self._score_experience(normalized)
        scores["formatting"] = self._score_formatting(text)
        scores["keywords"] = self._score_keywords(normalized)

        overall_score = round(
            sum(scores[name] * self.category_weights[name] for name in scores) * 100,
            2,
        )

        missing_skills = [skill for skill in sorted(self.skill_keywords) if skill not in normalized]
        suggestions = self._build_suggestions(scores, missing_skills)

        return {
            "scores": scores,
            "overall_score": overall_score,
            "missing_skills": missing_skills[:8],
            "suggestions": suggestions,
        }

    def _score_contact_information(self, text: str) -> float:
        hits = sum(1 for pattern in self.contact_patterns if re.search(pattern, text))
        return min(1.0, hits / 3.0)

    def _score_skills(self, text: str) -> float:
        found = sum(1 for skill in self.skill_keywords if skill in text)
        return min(1.0, found / 6.0)

    def _score_education(self, text: str) -> float:
        if any(keyword in text for keyword in self.education_keywords):
            return 1.0
        return 0.0

    def _score_projects(self, text: str) -> float:
        if any(keyword in text for keyword in self.project_keywords):
            return 1.0
        return 0.0

    def _score_experience(self, text: str) -> float:
        if any(keyword in text for keyword in self.experience_keywords):
            return 1.0
        return 0.0

    def _score_formatting(self, text: str) -> float:
        headings = sum(1 for marker in self.formatting_markers if marker.lower() in text.lower())
        return min(1.0, headings / 4.0)

    def _score_keywords(self, text: str) -> float:
        found = sum(1 for skill in self.skill_keywords if skill in text)
        return min(1.0, found / 8.0)

    def _build_suggestions(self, scores: Dict[str, float], missing_skills: List[str]) -> List[str]:
        suggestions = []
        if scores["contact_information"] < 1.0:
            suggestions.append("Add clear contact details such as email, phone, and LinkedIn/GitHub links.")
        if scores["skills"] < 0.7:
            suggestions.append("Expand the skills section with relevant technical competencies.")
        if scores["education"] < 1.0:
            suggestions.append("Include your education details, degree, and institution name.")
        if scores["projects"] < 1.0:
            suggestions.append("Highlight your projects with concrete outcomes and implementation details.")
        if scores["experience"] < 1.0:
            suggestions.append("Add experience details with job titles, responsibilities, and achievements.")
        if scores["formatting"] < 0.7:
            suggestions.append("Use clearer section headings such as Summary, Skills, Experience, and Education.")
        if missing_skills:
            suggestions.append("Consider adding missing skills: " + ", ".join(missing_skills[:5]))
        if not suggestions:
            suggestions.append("Your resume looks well-structured and keyword-rich.")
        return suggestions
