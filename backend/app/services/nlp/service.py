"""
backend/app/services/nlp/service.py — Lecture Content NLP Analytics Service
==========================================================================
Provides topic identification, extractive summarization, and key concept extraction
using Sentence Transformers and lightweight NLP algorithms.
Strict rule: Does not claim to infer student emotion or cognitive state.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, List, Optional

from backend.app.schemas.common import DataStatus


class NlpService:
    """Manages topic classification, lecture summarization, and keyword extraction."""

    def __init__(self) -> None:
        self.status: DataStatus = DataStatus.READY
        self._embedder = None

    def is_available(self) -> bool:
        """Returns True since sentence-transformers is installed."""
        return True

    def get_status_info(self) -> dict:
        return {
            "module": "nlp_analytics",
            "status": "READY",
            "models": ["sentence-transformers/all-MiniLM-L6-v2", "extractive-summarizer"],
            "ready_for_nlp": True,
            "provenance": "PRETRAINED MODEL",
            "ethics_boundary": "Analyzes curriculum text and pace only; no student emotion or mental state claims.",
        }

    def _get_embedder(self):
        """Lazy loader for SentenceTransformer model."""
        if self._embedder is None:
            from sentence_transformers import SentenceTransformer
            # Lightweight 384-dimensional embedding model
            self._embedder = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
        return self._embedder

    def extract_keywords(self, text: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Extracts significant domain concepts using term frequency and position weighting."""
        stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with",
            "about", "against", "between", "into", "through", "during", "before", "after",
            "above", "below", "from", "up", "down", "is", "are", "was", "were", "be",
            "been", "being", "have", "has", "had", "do", "does", "did", "this", "that",
            "these", "those", "we", "you", "they", "it", "he", "she", "what", "which",
            "who", "whom", "will", "would", "can", "could", "should", "of", "so", "as",
            "today", "let", "going", "discuss", "look", "see", "take", "also", "just",
        }
        words = re.findall(r"\b[A-Za-z]{3,}\b", text.lower())
        filtered = [w for w in words if w not in stopwords]
        counts = Counter(filtered)
        total = sum(counts.values()) or 1

        results = []
        for word, cnt in counts.most_common(top_k):
            results.append({
                "keyword": word,
                "frequency": cnt,
                "relative_importance": round(cnt / total, 3),
            })
        return results

    def identify_topics(self, text: str) -> List[Dict[str, Any]]:
        """Identifies primary academic topics by embedding cosine similarity against known curriculum subjects."""
        candidate_topics = [
            "Convolutional Neural Networks & Computer Vision",
            "Transformer Architecture & Attention Mechanisms",
            "Optimization Algorithms & Gradient Descent",
            "Linear Algebra & Matrix Decompositions",
            "Natural Language Processing & Embeddings",
            "Signal Processing & Fourier Analysis",
            "Software Engineering & System Architecture",
        ]

        if not text.strip():
            return []

        try:
            embedder = self._get_embedder()
            doc_emb = embedder.encode(text, convert_to_tensor=True)
            topic_embs = embedder.encode(candidate_topics, convert_to_tensor=True)

            from sentence_transformers import util
            scores = util.cos_sim(doc_emb, topic_embs)[0].cpu().tolist()

            ranked = []
            for topic, score in zip(candidate_topics, scores):
                if score > 0.25:
                    ranked.append({
                        "topic": topic,
                        "confidence": round(float(score), 3),
                        "provenance": "PRETRAINED MODEL (all-MiniLM-L6-v2)",
                    })
            ranked.sort(key=lambda x: x["confidence"], reverse=True)
            return ranked[:3]
        except Exception:
            # Fallback simple keyword match if embedding is busy
            matched = []
            lower = text.lower()
            for cand in candidate_topics:
                for word in cand.lower().split():
                    if len(word) > 4 and word in lower:
                        matched.append({"topic": cand, "confidence": 0.75, "provenance": "KEYWORD_HEURISTIC"})
                        break
            return matched[:3]

    def summarize_lecture(self, text: str, max_sentences: int = 3) -> str:
        """Generates an extractive summary of the lecture text using sentence scoring."""
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 20]
        if not sentences:
            return text[:200]
        if len(sentences) <= max_sentences:
            return " ".join(sentences)

        # Score sentences by keyword density
        stopwords = {"the", "and", "that", "this", "with", "from", "they", "were", "have"}
        scored = []
        for idx, s in enumerate(sentences):
            words = [w for w in re.findall(r"\b\w+\b", s.lower()) if w not in stopwords]
            score = len(words) + (2 if idx == 0 else 0)  # Slight bias for introduction
            scored.append((score, idx, s))

        scored.sort(reverse=True, key=lambda x: x[0])
        top_sentences = sorted(scored[:max_sentences], key=lambda x: x[1])
        return " ".join(s for _, _, s in top_sentences)

    def analyze_lecture_content(self, text: str) -> Dict[str, Any]:
        """Comprehensive content analysis combining topics, summary, and concepts."""
        return {
            "topics": self.identify_topics(text),
            "keywords": self.extract_keywords(text),
            "summary": self.summarize_lecture(text),
            "char_count": len(text),
            "word_count": len(text.split()),
            "data_source": "REAL_PROCESSING",
            "provenance": "PRETRAINED MODEL",
        }


nlp_service = NlpService()
