"""OCR model initialization and management."""

import os
import warnings
import logging
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

from pix2text import Pix2Text

from ..ocr.cpu_patch import ensure_cpu_patches

logger = logging.getLogger(__name__)


async def initialize_ocr_model() -> tuple[Optional[Pix2Text], Optional[ThreadPoolExecutor]]:
    """Initialize the OCR model for math problem recognition - CPU only.
    
    Returns:
        Tuple of (ocr_model, ocr_executor) or (None, None) if initialization fails
    """
    # Suppress ALL warnings
    warnings.filterwarnings('ignore')
    
    # Force CPU mode - ensure environment variables are set
    os.environ['ONNXRUNTIME_EXECUTION_PROVIDER'] = 'CPUExecutionProvider'
    os.environ['CUDA_VISIBLE_DEVICES'] = ''  # Hide CUDA devices
    
    # Ensure CPU patches are applied
    ensure_cpu_patches()
    
    # Initialize OCR model with CPU only
    logger.info("Initializing OCR model with CPU only...")
    
    # Try different initialization methods
    initialization_methods = [
        # Method 1: Try with formula recognition model
        lambda: Pix2Text.from_config(dict(
            formula=dict(model_name='breezedeus/pix2text-mfr')
        )),
        # Method 2: Simple initialization
        lambda: Pix2Text(),
    ]
    
    for i, init_method in enumerate(initialization_methods, 1):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                logger.info(f"Trying OCR initialization method {i}...")
                ocr_model = init_method()
                ocr_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="ocr")
                logger.info("OCR model initialized successfully - Running on CPU")
                return ocr_model, ocr_executor
        except Exception as e:
            logger.warning(f"OCR initialization method {i} failed: {e}")
            if i == len(initialization_methods):
                # Last method failed, log the error
                logger.error(f"All OCR initialization methods failed. Last error: {e}")
                logger.warning("OCR initialization failed. Math challenge processing disabled.")
                return None, None
            continue
    
    # Should not reach here, but just in case
    logger.warning("OCR initialization failed. Math challenge processing disabled.")
    return None, None
