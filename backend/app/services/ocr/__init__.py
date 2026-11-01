"""OCR Service Package."""
from backend.app.services.ocr.service import ocr_service, OcrService
from backend.app.services.ocr.character_service import character_service, CharacterRecognitionService

__all__ = ["ocr_service", "OcrService", "character_service", "CharacterRecognitionService"]

