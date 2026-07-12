import random
import re
from typing import Dict, List

from app.models import JobDescriptionMatch


class InterviewQuestionService:
    """Rule-based interview question generator based on resume, ATS insights, and job description."""

    def __init__(self):
        self.technical_templates = {
            "python": [
                "Explain how you would design a Python solution for a scalable backend service.",
                "How do you ensure code quality and maintainability in Python projects?",
                "Describe a Python library or framework you rely on and why.",
            ],
            "flask": [
                "How do you structure a Flask application with blueprints and modular components?",
                "How would you handle authentication and error management in a Flask app?",
                "Describe how you would optimize request performance in a Flask endpoint.",
            ],
            "sql": [
                "How would you optimize a slow SQL query in a production application?",
                "Explain the difference between INNER JOIN and LEFT JOIN in SQL.",
                "How do you choose between normalized and denormalized database schema designs?",
            ],
            "database": [
                "Describe the ACID properties in a DBMS and why they matter.",
                "How would you design a database schema for high read and write throughput?",
                "What strategies do you use to avoid database deadlocks?",
            ],
            "oop": [
                "How do you apply OOP principles such as encapsulation and inheritance in your work?",
                "Describe a time when you refactored code to improve object design.",
                "How do you balance inheritance and composition in application design?",
            ],
            "data structures": [
                "Describe a data structure you regularly use and explain its trade-offs.",
                "How do you choose between arrays, linked lists, and hash tables for a data problem?",
            ],
            "machine learning": [
                "How would you evaluate a machine learning model for production readiness?",
                "Describe how you would collect and prepare training data for a model.",
            ],
        }
        self.project_templates = [
            "Tell me about a project you are most proud of and what your role was.",
            "What challenges did you face in the project and how did you resolve them?",
            "How did you measure the impact of your project on users or business goals?",
            "What would you improve if you had to rebuild that project today?",
            "How did you collaborate with others while delivering that project?",
            "Describe a project where you applied your strongest technical skill.",
            "What was your contribution to a recent project you worked on?",
            "How did you handle scope changes during a project lifecycle?",
            "What trade-offs did you make during project implementation?",
            "How did you ensure the project met its delivery goals?",
        ]
        self.hr_templates = [
            "What are your strengths?",
            "What is one weakness you are working to improve?",
            "Describe a time you worked effectively in a team.",
            "How do you approach problem solving?",
            "What are your career goals?",
            "Why should we hire you?",
            "What steps do you take to keep improving your skill set?",
            "How would you approach learning the suggested skills for this role?",
            "What motivates you to stay engaged in your work?",
            "How do you adapt to changing priorities at work?",
        ]

    def generate_questions(self, resume_text: str, ats_analysis: Dict[str, object], job_match: JobDescriptionMatch | None = None) -> Dict[str, List[str]]:
        """Generate technical, project, and HR interview questions."""
        resume_text = resume_text or ""
        normalized = re.sub(r"\s+", " ", resume_text.lower()).strip()

        technical = self._generate_technical_questions(normalized, job_match)
        project = self._generate_project_questions(normalized)
        hr = self._generate_hr_questions(normalized, job_match)

        return {
            "technical": technical[:10],
            "project": project[:5],
            "hr": hr[:5],
        }

    def _select_unique(self, candidates: List[str], max_items: int) -> List[str]:
        unique = []
        pool = list(dict.fromkeys(candidates))
        random.shuffle(pool)
        for question in pool:
            if question not in unique:
                unique.append(question)
            if len(unique) >= max_items:
                break
        return unique

    def _generate_technical_questions(self, resume_text: str, job_match: JobDescriptionMatch | None) -> List[str]:
        questions = []
        seen_categories = set()

        def add_topic(topic: str, phrase: str):
            if phrase not in questions:
                questions.extend(self.technical_templates.get(topic, []))
                seen_categories.add(topic)

        for topic in self.technical_templates:
            if topic in resume_text or (job_match and topic in (job_match.job_description or "").lower()):
                add_topic(topic, topic)

        if not questions:
            questions.extend(
                [
                    "How do you approach debugging a production issue under time pressure?",
                    "Describe how you test your code before deployment.",
                    "How do you document technical work and handoffs to other engineers?",
                    "What metrics do you use to evaluate the quality of a software solution?",
                    "How do you stay current with modern software engineering practices?",
                ]
            )

        return self._select_unique(questions, 10)

    def _generate_project_questions(self, resume_text: str) -> List[str]:
        questions = []
        if "project" in resume_text:
            questions.extend(self.project_templates[:7])
        else:
            questions.extend(self.project_templates[5:])

        return self._select_unique(questions, 5)

    def _generate_hr_questions(self, resume_text: str, job_match: JobDescriptionMatch | None) -> List[str]:
        questions = list(self.hr_templates)
        if job_match and job_match.suggested_skills:
            questions.append("How would you approach learning the suggested skills for this role?")
        if "team" in resume_text:
            questions.append("Describe a time you collaborated successfully with a teammate on a challenging task.")
        if "lead" in resume_text or "manager" in resume_text:
            questions.append("How do you approach leadership and mentoring in a team setting?")

        return self._select_unique(questions, 5)
