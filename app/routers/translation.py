"""Translation endpoints for multilingual support"""

from fastapi import APIRouter, HTTPException, status
from app.models.ai_features import TranslationRequest, BatchTranslationRequest
from app.services.translation_service import TranslationService
from app.utils.exceptions import APIException

router = APIRouter(prefix="/translation", tags=["Translation"])

# Lazy initialization - will be created on first use
_translation_service = None

def get_translation_service():
    """Get or create translation service instance"""
    global _translation_service
    if _translation_service is None:
        try:
            _translation_service = TranslationService()
        except Exception as e:
            # If translation service fails to initialize, raise error
            raise APIException(
                code="TRANSLATION_SERVICE_UNAVAILABLE",
                message=f"Translation service is not available: {str(e)}",
                status_code=503
            )
    return _translation_service


@router.post("/translate")
async def translate_text(request: TranslationRequest):
    """
    Translate text to target language
    
    Args:
        request: Translation request with text and target language
    
    Returns:
        Translated text
    """
    try:
        service = get_translation_service()
        translated_text = service.translate_text(
            text=request.text,
            target_language=request.target_language,
            source_language=request.source_language
        )
        return {
            "success": True,
            "original_text": request.text,
            "translated_text": translated_text,
            "target_language": request.target_language,
            "source_language": request.source_language
        }
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation failed: {str(e)}"
        )


@router.post("/translate/batch")
async def translate_batch(request: BatchTranslationRequest):
    """
    Translate multiple texts to target language
    
    Args:
        request: Batch translation request
    
    Returns:
        List of translated texts
    """
    try:
        service = get_translation_service()
        translated_texts = service.translate_batch(
            texts=request.texts,
            target_language=request.target_language,
            source_language=request.source_language
        )
        return {
            "success": True,
            "original_texts": request.texts,
            "translated_texts": translated_texts,
            "target_language": request.target_language,
            "source_language": request.source_language
        }
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch translation failed: {str(e)}"
        )


@router.post("/detect")
async def detect_language(text: str):
    """
    Detect the language of text
    
    Args:
        text: Text to detect language for
    
    Returns:
        Detected language and confidence
    """
    try:
        service = get_translation_service()
        result = service.detect_language(text)
        return {
            "success": True,
            "text": text,
            "detected_language": result['language'],
            "confidence": result['confidence']
        }
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Language detection failed: {str(e)}"
        )


@router.get("/languages")
async def get_supported_languages():
    """
    Get list of supported languages
    
    Returns:
        List of supported languages
    """
    try:
        service = get_translation_service()
        languages = service.get_supported_languages()
        return {
            "success": True,
            "languages": languages
        }
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch languages: {str(e)}"
        )

