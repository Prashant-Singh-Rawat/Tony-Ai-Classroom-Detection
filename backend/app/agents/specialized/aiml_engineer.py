"""
backend/app/agents/specialized/aiml_engineer.py — AI/ML Engineer Agent (Agent 5)
================================================================================
Integrates pretrained models, manages YOLOv8n and YOLOv8n-pose inference pipelines,
handles Faster-Whisper, EasyOCR, and Sentence Transformers, and reports honest execution metrics.
"""

from __future__ import annotations
from typing import Any, Dict

from backend.app.agents.core.base_agent import BaseAgent
from backend.app.agents.core.types import AgentRole, AgentStatus, ToolPermissionLevel
from backend.app.agents.providers.provider_manager import provider_manager
from backend.app.agents.tools.project_tools import inspect_model_status


class AIMLEngineerAgent(BaseAgent):
    """Agent 5: AI/ML Engineer — Multimodal AI inference pipelines, hardware optimization, honesty enforcement."""

    def __init__(self) -> None:
        super().__init__(
            agent_id="aiml_engineer",
            role=AgentRole.AIML_ENGINEER,
            name="AI/ML Engineer Agent",
            responsibility="Integrates and optimizes pretrained CV, Speech, OCR, and RAG pipelines. Enforces ground-truth reporting.",
            capabilities=[
                "yolo_inference_optimization",
                "pose_keypoint_analysis",
                "speech_recognition_pipeline",
                "ocr_formula_extraction",
                "rag_vector_search",
                "hardware_vram_profiling",
            ],
            permission_level=ToolPermissionLevel.SAFE_WRITE,
            system_prompt=(
                "You are the AI/ML Engineer Agent for ClassVision AI. You optimize and verify multimodal AI pipelines "
                "(YOLOv8n, Faster-Whisper, EasyOCR, Sentence Transformers, ChromaDB). You NEVER invent accuracy metrics "
                "and NEVER claim models are trained when using pretrained COCO weights."
            ),
        )

    def execute_step(
        self,
        task_id: str,
        instruction: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        self.set_status(AgentStatus.EXECUTING, f"Evaluating AI/ML pipeline: {instruction[:60]}")

        model_status = inspect_model_status()

        prompt = (
            f"Instruction: {instruction}\n"
            f"Current Model Status: {model_status}\n"
            "Hardware Constraints: HP Victus (NVIDIA GTX 1650 4GB VRAM / CPU Fallback, batch size 1).\n"
            "Produce AI engineering evaluation and inference verification summary."
        )

        response = provider_manager.generate(
            prompt=prompt,
            system_prompt=self.system_prompt,
        )

        self.record_success("AI/ML pipeline evaluated successfully.")
        return {
            "agent": self.agent_id,
            "instruction": instruction,
            "aiml_output": response.content,
            "model_status": model_status,
            "status": "COMPLETED",
        }

