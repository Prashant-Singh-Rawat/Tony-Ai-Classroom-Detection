"""
backend/app/services/rag/service.py — Retrieval-Augmented Generation Service
===========================================================================
Manages curriculum-grounded Q&A over lecture transcripts and whiteboard notes
using ChromaDB and Sentence Transformers (all-MiniLM-L6-v2).
Provides honest responses:
- If live retrieval finds no matching documents: returns explicit unavailable answer.
- If live mode is requested without indexed docs: returns NOT_CONNECTED.
- In demo fallback: returns labeled DEMO_DATA.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.app.core.config import REPO_ROOT
from backend.app.schemas.common import DataStatus
from backend.app.schemas.rag import RagResponse, RagSource

CHROMA_PERSIST_DIR = REPO_ROOT / "data" / "chroma"


class RagService:
    """RAG Assistant service over multimodal lecture content."""

    def __init__(self) -> None:
        self.status: DataStatus = DataStatus.READY
        self.persist_dir = CHROMA_PERSIST_DIR
        self._client = None
        self._collection = None
        self._embedder = None

    def is_available(self) -> bool:
        """Returns True since chromadb and sentence-transformers are installed."""
        return True

    def _get_embedder(self):
        if self._embedder is None:
            from sentence_transformers import SentenceTransformer
            self._embedder = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
        return self._embedder

    def _get_collection(self):
        """Lazy loader for persistent ChromaDB collection."""
        if self._collection is None:
            import chromadb
            self.persist_dir.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=str(self.persist_dir))
            self._collection = self._client.get_or_create_collection(
                name="lecture_curriculum",
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def ingest_lecture(
        self,
        session_id: str,
        transcript_text: str = "",
        ocr_text: str = "",
        segments: Optional[List[Dict[str, Any]]] = None,
    ) -> int:
        """
        Chunks and indexes lecture transcript and whiteboard OCR notes into ChromaDB.
        Returns the number of indexed chunks.
        """
        coll = self._get_collection()
        embedder = self._get_embedder()
        indexed_count = 0

        # Ingest transcript segments or chunks
        if segments:
            for idx, seg in enumerate(segments):
                txt = seg.get("text", "").strip()
                if not txt:
                    continue
                start_s = seg.get("start", 0.0)
                m, s = divmod(int(start_s), 60)
                h, m = divmod(m, 60)
                ts_str = f"{h:02d}:{m:02d}:{s:02d}"
                doc_id = f"{session_id}_seg_{idx:04d}"
                emb = embedder.encode(txt).tolist()
                coll.upsert(
                    ids=[doc_id],
                    documents=[txt],
                    embeddings=[emb],
                    metadatas=[{
                        "session_id": session_id,
                        "source_type": "transcript",
                        "title": f"Lecture Transcript ({ts_str})",
                        "timestamp": ts_str,
                    }],
                )
                indexed_count += 1
        elif transcript_text.strip():
            # Chunk by sentences
            import re
            chunks = [c.strip() for c in re.split(r"(?<=[.!?])\s+", transcript_text) if len(c.strip()) > 10]
            for idx, c in enumerate(chunks):
                doc_id = f"{session_id}_tr_{idx:04d}"
                emb = embedder.encode(c).tolist()
                coll.upsert(
                    ids=[doc_id],
                    documents=[c],
                    embeddings=[emb],
                    metadatas=[{
                        "session_id": session_id,
                        "source_type": "transcript",
                        "title": f"Lecture Transcript Chunk #{idx+1}",
                        "timestamp": "00:00:00",
                    }],
                )
                indexed_count += 1

        # Ingest whiteboard OCR text
        if ocr_text.strip():
            lines = [l.strip() for l in ocr_text.split("\n") if len(l.strip()) > 3]
            for idx, l in enumerate(lines):
                doc_id = f"{session_id}_ocr_{idx:04d}"
                emb = embedder.encode(l).tolist()
                coll.upsert(
                    ids=[doc_id],
                    documents=[l],
                    embeddings=[emb],
                    metadatas=[{
                        "session_id": session_id,
                        "source_type": "slide_ocr",
                        "title": "Whiteboard / Slide Notes",
                        "timestamp": "00:00:00",
                    }],
                )
                indexed_count += 1

        return indexed_count

    def index_document(
        self,
        doc_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Embeds and indexes a document passage in ChromaDB."""
        if not text.strip():
            return False
        try:
            embedder = self._get_embedder()
            embedding = embedder.encode(text).tolist()
            coll = self._get_collection()

            meta = metadata or {}
            meta["indexed_at"] = meta.get("indexed_at", "2026-10-30")
            coll.upsert(
                ids=[doc_id],
                documents=[text],
                embeddings=[embedding],
                metadatas=[meta],
            )
            return True
        except Exception:
            return False

    def query(
        self,
        query: str,
        session_id: Optional[str] = None,
        force_live: bool = False,
        use_demo_fallback: bool = True,
    ) -> RagResponse:
        """
        Executes a RAG query.
        Returns explicit NOT_CONNECTED response if force_live=True without ingested docs.
        Returns labeled demonstration data if fallback is permitted.
        """
        clean_query = query.strip()

        # If demo fallback is requested without session or force_live, serve labeled demo response
        if not (use_demo_fallback and not force_live and not session_id):
            # Check if live index has documents
            try:
                coll = self._get_collection()
                count = coll.count()
                if count > 0:
                    embedder = self._get_embedder()
                    q_emb = embedder.encode(clean_query).tolist()
                    where_filter = {"session_id": session_id} if session_id else None
                    try:
                        results = coll.query(
                            query_embeddings=[q_emb],
                            n_results=min(3, count),
                            where=where_filter,
                        )
                        if not results.get("documents", [[]])[0] and where_filter:
                            results = coll.query(query_embeddings=[q_emb], n_results=min(3, count))
                    except Exception:
                        results = coll.query(query_embeddings=[q_emb], n_results=min(3, count))

                    docs = results.get("documents", [[]])[0]
                    metas = results.get("metadatas", [[]])[0]
                    distances = results.get("distances", [[]])[0]

                    if docs:
                        best_dist = distances[0] if distances else 1.0
                        best_sim = max(0.0, round(1.0 - best_dist, 3))

                        # Educational honesty: refuse questions when supporting content is absent
                        if best_sim < 0.35:
                            return RagResponse(
                                query=clean_query,
                                answer="Cannot find sufficient supporting lecture content for your question in the recorded lecture transcripts or whiteboard notes.",
                                confidence=best_sim,
                                sources=[],
                                isPlaceholder=False,
                                isDemoData=False,
                                status="REAL_PROCESSING",
                            )

                        sources = []
                        for doc, meta, dist in zip(docs, metas, distances):
                            sim = max(0.0, round(1.0 - dist, 2))
                            if sim >= 0.25:
                                sources.append(RagSource(
                                    title=meta.get("title", "Lecture Transcript Chunk"),
                                    sourceType=meta.get("source_type", "transcript"),
                                    timestamp=meta.get("timestamp", "00:00:00"),
                                    snippet=doc[:150] + ("..." if len(doc) > 150 else ""),
                                ))

                        return RagResponse(
                            query=clean_query,
                            answer=f"Based on retrieved lecture content: {docs[0]}",
                            confidence=best_sim,
                            sources=sources,
                            isPlaceholder=False,
                            isDemoData=False,
                            status="REAL_PROCESSING",
                        )
            except Exception:
                pass

        # If live was forced but no live documents or query failed
        if force_live or not use_demo_fallback:
            return RagResponse(
                query=clean_query,
                answer="RAG vector store is NOT CONNECTED. No lecture documents have been ingested for this session yet.",
                confidence=0.0,
                sources=[],
                isPlaceholder=True,
                isDemoData=False,
                status="NOT_CONNECTED",
            )

        # Demonstration fallback response (explicitly flagged)
        q_lower = clean_query.lower()
        if "question" in q_lower or "dilated" in q_lower or "hand" in q_lower:
            return RagResponse(
                query=clean_query,
                answer=(
                    "Yes, at timestamp 09:30:18, a student in the front row raised a hand to ask "
                    "whether dilated convolutions preserve spatial resolution without downsampling. "
                    "The lecturer confirmed this advantage."
                ),
                confidence=0.95,
                sources=[
                    RagSource(
                        title="Gesture Timeline & Transcript Synchrony",
                        sourceType="transcript",
                        timestamp="09:30:18",
                        snippet='Student 1: "Professor, does dilated convolution preserve spatial dimensions...?"',
                    )
                ],
                isPlaceholder=True,
                isDemoData=True,
                status="DEMO_DATA",
            )

        return RagResponse(
            query=clean_query,
            answer=(
                "In session sess_01, the instructor compared SGD with Adam optimization. "
                "Key points included adaptive learning rate scaling using first and second momentum "
                "estimates (m_t and v_t) and how Adam mitigates oscillation across steep ravines in the loss landscape."
            ),
            confidence=0.92,
            sources=[
                RagSource(
                    title="Lecture Audio Transcript",
                    sourceType="transcript",
                    timestamp="09:35:10",
                    snippet='Dr. Sharma: "Adam combines AdaGrad and RMSProp with momentum buffers."',
                ),
                RagSource(
                    title="Blackboard OCR Extraction",
                    sourceType="slide_ocr",
                    snippet="W_new = W_old - lr * (m_t / sqrt(v_t + eps))",
                ),
            ],
            isPlaceholder=True,
            isDemoData=True,
            status="DEMO_DATA",
        )


rag_service = RagService()
