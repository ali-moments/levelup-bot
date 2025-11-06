"""Logging configuration for LevelUp Bot."""

import logging


def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Suppress verbose warnings from RapidOCR and other libraries
    logging.getLogger('RapidOCR').setLevel(logging.ERROR)
    logging.getLogger('cnstd').setLevel(logging.ERROR)
    logging.getLogger('transformers').setLevel(logging.ERROR)  # Suppress use_fast warnings
    logging.getLogger('optimum').setLevel(logging.ERROR)  # Suppress ONNX warnings
    logging.getLogger('optimum.onnxruntime').setLevel(logging.ERROR)
    
    return logging.getLogger(__name__)
