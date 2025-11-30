"""Translation service using Google Cloud Translation API"""

from typing import List, Optional
from google.cloud import translate
from app.config import settings
from app.utils.exceptions import APIException


class TranslationService:
    """Service for multilingual support using Google Cloud Translation API"""
    
    def __init__(self):
        """Initialize translation service"""
        try:
            # Use v3 API (TranslationServiceClient)
            # Only initialize if credentials are available
            import os
            if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS') and not settings.google_application_credentials:
                raise Exception("Google Cloud credentials not configured. Set GOOGLE_APPLICATION_CREDENTIALS environment variable.")
            
            self.client = translate.TranslationServiceClient()
            self.project_id = settings.google_cloud_project
            self.parent = f"projects/{self.project_id}/locations/global"
        except Exception as e:
            raise APIException(
                code="TRANSLATION_INIT_ERROR",
                message=f"Failed to initialize translation service: {str(e)}",
                status_code=500
            )
    
    def translate_text(
        self,
        text: str,
        target_language: str = "en",
        source_language: Optional[str] = None
    ) -> str:
        """
        Translate text to target language
        
        Args:
            text: Text to translate
            target_language: Target language code (e.g., 'hi', 'en', 'es')
            source_language: Source language code (auto-detect if None)
        
        Returns:
            Translated text
        """
        try:
            request_params = {
                "parent": self.parent,
                "contents": [text],
                "mime_type": "text/plain",
                "target_language_code": target_language,
            }
            
            if source_language:
                request_params["source_language_code"] = source_language
            
            response = self.client.translate_text(request=request_params)
            return response.translations[0].translated_text
        except Exception as e:
            raise APIException(
                code="TRANSLATION_ERROR",
                message=f"Translation failed: {str(e)}",
                status_code=500
            )
    
    def translate_batch(
        self,
        texts: List[str],
        target_language: str = "en",
        source_language: Optional[str] = None
    ) -> List[str]:
        """
        Translate multiple texts to target language
        
        Args:
            texts: List of texts to translate
            target_language: Target language code
            source_language: Source language code (auto-detect if None)
        
        Returns:
            List of translated texts
        """
        try:
            request_params = {
                "parent": self.parent,
                "contents": texts,
                "mime_type": "text/plain",
                "target_language_code": target_language,
            }
            
            if source_language:
                request_params["source_language_code"] = source_language
            
            response = self.client.translate_text(request=request_params)
            return [translation.translated_text for translation in response.translations]
        except Exception as e:
            raise APIException(
                code="TRANSLATION_ERROR",
                message=f"Batch translation failed: {str(e)}",
                status_code=500
            )
    
    def detect_language(self, text: str) -> dict:
        """
        Detect the language of text
        
        Args:
            text: Text to detect language for
        
        Returns:
            Dictionary with 'language' and 'confidence' keys
        """
        try:
            response = self.client.detect_language(
                request={
                    "parent": self.parent,
                    "content": text,
                    "mime_type": "text/plain",
                }
            )
            return {
                'language': response.languages[0].language_code,
                'confidence': response.languages[0].confidence
            }
        except Exception as e:
            raise APIException(
                code="LANGUAGE_DETECTION_ERROR",
                message=f"Language detection failed: {str(e)}",
                status_code=500
            )
    
    def get_supported_languages(self) -> List[dict]:
        """
        Get list of supported languages
        
        Returns:
            List of dictionaries with language codes and names
        """
        try:
            response = self.client.get_supported_languages(parent=self.parent)
            return [
                {
                    'language': lang.language_code,
                    'name': lang.display_name
                }
                for lang in response.languages
            ]
        except Exception as e:
            # Fallback to common languages if API fails
            return [
                {'language': 'en', 'name': 'English'},
                {'language': 'hi', 'name': 'Hindi'},
                {'language': 'es', 'name': 'Spanish'},
                {'language': 'fr', 'name': 'French'},
                {'language': 'de', 'name': 'German'},
                {'language': 'zh', 'name': 'Chinese'},
                {'language': 'ja', 'name': 'Japanese'},
                {'language': 'ar', 'name': 'Arabic'},
            ]

