import re
from typing import Dict, List, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class JobDescriptionService:
    """TF-IDF and cosine similarity-based job description matcher."""

    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))

    def compare(self, resume_text: str, job_description: str) -> Dict[str, object]:
        """Compare resume text with a job description and return match details."""
        if not resume_text.strip() or not job_description.strip():
            raise ValueError("Both resume text and job description are required.")

        documents = [self._normalize_text(resume_text), self._normalize_text(job_description)]
        matrix = self.vectorizer.fit_transform(documents)
        similarity = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
        similarity_percent = round(float(similarity) * 100, 2)

        resume_tokens = self._tokenize(resume_text)
        jd_tokens = self._tokenize(job_description)
        matched_skills = sorted(set(resume_tokens) & set(jd_tokens))
        missing_skills = sorted(set(jd_tokens) - set(resume_tokens))
        suggested_skills = self._suggest_skills(missing_skills, resume_tokens, jd_tokens)

        return {
            "similarity_percent": similarity_percent,
            "matched_skills": matched_skills[:15],
            "missing_skills": missing_skills[:15],
            "suggested_skills": suggested_skills[:10],
        }

    def _normalize_text(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _tokenize(self, text: str) -> set:
        normalized = self._normalize_text(text).lower()
        return {token for token in re.findall(r"[a-zA-Z0-9#+.]+", normalized) if len(token) > 2}

    def _suggest_skills(self, missing_skills: List[str], resume_tokens: set, jd_tokens: set) -> List[str]:
        if not missing_skills:
            return []

        # Suggest the most relevant missing skills from the job description.
        ranked = sorted(missing_skills, key=lambda skill: (skill not in resume_tokens, len(skill)))
        return ranked[:10]
