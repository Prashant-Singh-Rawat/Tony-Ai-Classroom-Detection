"""
backend/app/agents/memory/agent_memory.py — Persistent Engineering Memory & Knowledge Base
============================================================================================
Combines structured SQLite memory records with semantic ChromaDB vector embeddings.
Enables agents to retrieve architectural rules, conventions, and previous bug fixes.
"""

from __future__ import annotations
import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.app.core.config import REPO_ROOT
from backend.app.database.db import SessionLocal
from backend.app.database.models import AgentMemoryRecord

CHROMA_AGENT_PERSIST = REPO_ROOT / "data" / "chroma"


class AgentMemorySystem:
    """Persistent project memory and semantic retrieval engine for engineering agents."""

    def __init__(self) -> None:
        self.persist_dir = CHROMA_AGENT_PERSIST
        self._collection = None
        self._embedder = None
        self._ensure_baseline_memory()

    def _get_embedder(self):
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedder = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
            except Exception:
                pass
        return self._embedder

    def _get_collection(self):
        if self._collection is None:
            try:
                import chromadb
                self.persist_dir.mkdir(parents=True, exist_ok=True)
                client = chromadb.PersistentClient(path=str(self.persist_dir))
                self._collection = client.get_or_create_collection(
                    name="agent_engineering_memory",
                    metadata={"hnsw:space": "cosine"},
                )
            except Exception:
                pass
        return self._collection

    def store(
        self,
        category: str,
        key: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Stores structured knowledge in SQLite and ChromaDB."""
        meta = metadata or {}
        now = datetime.datetime.now(datetime.timezone.utc)

        # 1. SQLite Storage
        try:
            with SessionLocal() as db:
                rec = db.query(AgentMemoryRecord).filter(
                    AgentMemoryRecord.category == category,
                    AgentMemoryRecord.key == key,
                ).first()

                if rec:
                    rec.content = content
                    rec.metadata_json = meta
                    rec.updated_at = now
                else:
                    rec = AgentMemoryRecord(
                        category=category,
                        key=key,
                        content=content,
                        metadata_json=meta,
                        updated_at=now,
                    )
                    db.add(rec)
                db.commit()
        except Exception:
            pass

        # 2. ChromaDB Semantic Vector Storage
        try:
            coll = self._get_collection()
            embedder = self._get_embedder()
            if coll and embedder:
                emb = embedder.encode(f"{category} | {key} | {content}").tolist()
                coll.upsert(
                    ids=[f"{category}_{key}"],
                    documents=[content],
                    embeddings=[emb],
                    metadatas=[{"category": category, "key": key, **meta}],
                )
        except Exception:
            pass

    def retrieve(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 3,
    ) -> List[Dict[str, Any]]:
        """Semantic retrieval across engineering memory passages."""
        results: List[Dict[str, Any]] = []

        # Vector search
        try:
            coll = self._get_collection()
            embedder = self._get_embedder()
            if coll and embedder and coll.count() > 0:
                q_emb = embedder.encode(query).tolist()
                where_filter = {"category": category} if category else None
                search_res = coll.query(
                    query_embeddings=[q_emb],
                    n_results=min(limit, coll.count()),
                    where=where_filter,
                )
                docs = search_res.get("documents", [[]])[0]
                metas = search_res.get("metadatas", [[]])[0]
                distances = search_res.get("distances", [[]])[0]

                for doc, m, dist in zip(docs, metas, distances):
                    results.append({
                        "category": m.get("category", "GENERAL"),
                        "key": m.get("key", ""),
                        "content": doc,
                        "similarity": max(0.0, round(1.0 - dist, 3)),
                    })
                return results
        except Exception:
            pass

        # Fallback to SQLite text search
        try:
            with SessionLocal() as db:
                q = db.query(AgentMemoryRecord)
                if category:
                    q = q.filter(AgentMemoryRecord.category == category)
                records = q.all()
                for r in records:
                    if query.lower() in r.content.lower() or query.lower() in r.key.lower():
                        results.append({
                            "category": r.category,
                            "key": r.key,
                            "content": r.content,
                            "similarity": 0.8,
                        })
                        if len(results) >= limit:
                            break
        except Exception:
            pass

        return results

    def _ensure_baseline_memory(self) -> None:
        """Seeds initial architectural rules and engineering guidelines."""
        baselines = [
            (
                "ARCHITECTURE",
                "system_overview",
                "ClassVision AI comprises a FastAPI backend and React 19 + TypeScript + Tailwind v4 frontend. "
                "AI modules include YOLOv8n (person detection), YOLOv8n-pose (keypoints), Faster-Whisper, EasyOCR, and Sentence Transformers.",
            ),
            (
                "CONVENTION",
                "hardware_constraints",
                "Target hardware: NVIDIA GTX 1650 (4 GB VRAM) on Windows with automatic CPU fallback. "
                "Inference batch size MUST be 1. Video files must be read sequentially without buffering into RAM.",
            ),
            (
                "TECHNICAL_DECISION",
                "dataset_policy",
                "Strict project requirement: 50% Kaggle datasets, 50% synthetic datasets, 0% real classroom recordings. "
                "Do not collect or depend on real classroom footage. Track students with anonymous IDs only (anon_001).",
            ),
            (
                "TECHNICAL_DECISION",
                "model_integrity",
                "Never claim a model is trained when only pretrained COCO weights are loaded. "
                "Do not invent model accuracy metrics. Report ground-truth execution results.",
            ),
        ]

        for cat, k, text in baselines:
            self.store(cat, k, text)


agent_memory = AgentMemorySystem()

