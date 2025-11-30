"""Helper utilities for AI model selection and configuration"""

import google.generativeai as genai
from typing import Optional, Tuple
from app.config import settings


def get_gemini_model_with_fallback(use_fast: bool = True) -> Tuple[Optional[genai.GenerativeModel], Optional[str]]:
    """
    Get a Gemini model with automatic fallback chain
    
    Args:
        use_fast: If True, prefer fast models. If False, use quality model.
        
    Returns:
        Tuple of (model, model_name) or (None, None) if all models fail
    """
    if not settings.gemini_api_key:
        return None, None
    
    try:
        genai.configure(api_key=settings.gemini_api_key)
    except Exception as e:
        print(f"Failed to configure Gemini API: {e}")
        return None, None
    
    # Model selection order based on preference
    # Include all available Gemini models for comprehensive fallback
    if use_fast:
        # Fast models in order of preference (fastest first)
        fast_chain = getattr(settings, 'gemini_models_fast_chain', 'gemini-2.5-flash,gemini-2.5-flash-lite,gemini-2.0-flash,gemini-2.0-flash-lite,gemini-1.5-flash')
        fast_models = [m.strip() for m in fast_chain.split(',') if m.strip()]
        model_names = [
            getattr(settings, 'gemini_model_fast', 'gemini-2.5-flash'),
            getattr(settings, 'gemini_model_standard', 'gemini-2.5-flash'),
        ] + fast_models + [
            getattr(settings, 'gemini_model_quality', 'gemini-3.0-pro'),
        ]
        # Remove duplicates while preserving order
        seen = set()
        model_names = [x for x in model_names if not (x in seen or seen.add(x))]
    else:
        # Quality models in order of preference (highest quality first)
        quality_chain = getattr(settings, 'gemini_models_quality_chain', 'gemini-3.0-pro,gemini-2.5-pro,gemini-1.5-pro')
        quality_models = [m.strip() for m in quality_chain.split(',') if m.strip()]
        model_names = [
            getattr(settings, 'gemini_model_quality', 'gemini-3.0-pro'),
        ] + quality_models + [
            getattr(settings, 'gemini_model_standard', 'gemini-2.5-flash'),
            getattr(settings, 'gemini_model_fast', 'gemini-2.5-flash'),
        ]
        # Remove duplicates while preserving order
        seen = set()
        model_names = [x for x in model_names if not (x in seen or seen.add(x))]
    
    for model_name in model_names:
        try:
            model = genai.GenerativeModel(model_name)
            return model, model_name
        except Exception as e:
            print(f"Failed to load model {model_name}: {e}")
            continue
    
    return None, None


def get_embedding_model_name() -> str:
    """Get the configured embedding model name"""
    return getattr(settings, 'vertex_ai_embedding_model', 'text-embedding-005')


def get_embedding_batch_size() -> int:
    """Get the configured embedding batch size"""
    return getattr(settings, 'embedding_batch_size', 50)


