"""ONNX Runtime CPU-only patching to force CPU execution."""

import os
import logging

logger = logging.getLogger(__name__)


def apply_cpu_patches():
    """Apply patches to force ONNX Runtime to use CPU only.
    
    This must be called before importing pix2text or any ONNX-dependent libraries.
    """
    # Set environment variables early to force CPU usage for ONNX Runtime
    os.environ['ONNXRUNTIME_EXECUTION_PROVIDER'] = 'CPUExecutionProvider'
    os.environ['CUDA_VISIBLE_DEVICES'] = ''  # Hide CUDA devices to force CPU
    
    # Patch ONNX Runtime BEFORE importing pix2text to force CPU usage
    try:
        import onnxruntime as ort
        
        # Store original functions
        _original_get_available_providers = ort.get_available_providers
        _original_InferenceSession = ort.InferenceSession
        
        def _get_available_providers_cpu_only():
            """Return only CPU-compatible providers."""
            providers = _original_get_available_providers()
            # Filter to only CPU and Azure providers (both work on CPU)
            cpu_providers = [p for p in providers if 'CPU' in p or 'Azure' in p]
            # Always include CPUExecutionProvider as first choice
            if 'CPUExecutionProvider' not in cpu_providers:
                cpu_providers.insert(0, 'CPUExecutionProvider')
            return cpu_providers
        
        def _InferenceSession_cpu_only(model_path, sess_options=None, providers=None, provider_options=None, **kwargs):
            """Create InferenceSession with CPU providers only."""
            # Force CPU providers
            if providers is None:
                providers = _get_available_providers_cpu_only()
            else:
                # Filter providers to only CPU-compatible ones
                providers = [p for p in providers if 'CPU' in p or 'Azure' in p]
                if not providers:
                    providers = ['CPUExecutionProvider']
            
            # Remove CUDA from providers if somehow it got in
            providers = [p for p in providers if 'CUDA' not in p]
            
            try:
                return _original_InferenceSession(
                    model_path,
                    sess_options=sess_options,
                    providers=providers,
                    provider_options=provider_options,
                    **kwargs
                )
            except ValueError as e:
                # If still fails, try with only CPUExecutionProvider
                if 'CUDAExecutionProvider' in str(e):
                    providers = ['CPUExecutionProvider']
                    return _original_InferenceSession(
                        model_path,
                        sess_options=sess_options,
                        providers=providers,
                        provider_options=provider_options,
                        **kwargs
                    )
                raise
        
        # Apply patches immediately
        ort.get_available_providers = _get_available_providers_cpu_only
        ort.InferenceSession = _InferenceSession_cpu_only
        
        logger.debug("ONNX Runtime CPU patches applied successfully")
        return True
    except ImportError:
        # onnxruntime not available yet, will patch later
        logger.debug("ONNX Runtime not available, skipping patches")
        return False


def ensure_cpu_patches():
    """Ensure CPU patches are applied, applying them if needed."""
    try:
        import onnxruntime as ort
        
        # Check if patches are already applied
        if hasattr(ort, '_original_get_available_providers'):
            return True
        
        # Apply patches inline if module-level ones don't exist
        ort._original_get_available_providers = ort.get_available_providers
        ort._original_InferenceSession = ort.InferenceSession
        
        def get_cpu_providers():
            """Return only CPU providers."""
            providers = ort._original_get_available_providers()
            cpu_providers = [p for p in providers if 'CPU' in p or 'Azure' in p]
            if not cpu_providers:
                cpu_providers = ['CPUExecutionProvider']
            return cpu_providers
        
        def create_cpu_session(model_path, sess_options=None, providers=None, provider_options=None, **kwargs):
            """Create InferenceSession with CPU providers only."""
            if providers is None:
                providers = get_cpu_providers()
            else:
                # Filter to only CPU-compatible providers
                providers = [p for p in providers if 'CPU' in p or 'Azure' in p]
                if not providers:
                    providers = ['CPUExecutionProvider']
            
            # Remove any CUDA providers
            providers = [p for p in providers if 'CUDA' not in p]
            
            try:
                return ort._original_InferenceSession(
                    model_path,
                    sess_options=sess_options,
                    providers=providers,
                    provider_options=provider_options,
                    **kwargs
                )
            except ValueError as e:
                # If still fails, try with only CPUExecutionProvider
                if 'CUDA' in str(e) or 'cuda' in str(e):
                    providers = ['CPUExecutionProvider']
                    return ort._original_InferenceSession(
                        model_path,
                        sess_options=sess_options,
                        providers=providers,
                        provider_options=provider_options,
                        **kwargs
                    )
                raise
        
        ort.get_available_providers = get_cpu_providers
        ort.InferenceSession = create_cpu_session
        
        logger.debug("ONNX Runtime CPU patches applied inline")
        return True
    except Exception as e:
        logger.debug(f"Error applying CPU patches: {e}")
        return False
