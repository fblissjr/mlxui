from fastapi import APIRouter, HTTPException, Depends, status
import logging
from typing import List, Optional
from mlxui.backend.core.mlx_adapter import MLXAdapter, get_mlx_adapter
from mlxui.backend.api.schemas import GenerationRequest, TokenChunk, CacheSaveRequest, CacheLoadRequest, TrimCacheRequest, CacheResponse
from mlxui.backend.api.schemas import ModelInfo, ModelLoadRequest, ModelLoadResponse

router = APIRouter()
logger = logging.getLogger("mlxui.backend.api.models")

@router.get("/", response_model=List[ModelInfo])
async def list_models(adapter: MLXAdapter = Depends(get_mlx_adapter)): # Type hint with imported MLXAdapter
    logger.info("Request received: List available local models.")
    if not adapter.is_available():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="MLX-LM library not available.")
    try:
        models = await adapter.list_local_models()
        # Update is_loaded status based on current adapter state
        current_loaded_id = adapter.current_identifier
        for model_data in models:
            if isinstance(model_data, dict): # Ensure it's a dict before modifying
                 model_data['is_loaded'] = (model_data.get('id') == current_loaded_id)
            elif isinstance(model_data, ModelInfo): # If it's already a Pydantic model
                 model_data.is_loaded = (model_data.id == current_loaded_id)

        return models
    except Exception as e:
        logger.exception("Failed to list local models:")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list models: {str(e)}")

@router.post("/load", response_model=ModelLoadResponse)
async def load_model_endpoint(
    request: ModelLoadRequest,
    adapter: MLXAdapter = Depends(get_mlx_adapter)
):
    logger.info(f"Request received: Load model identifier='{request.identifier}', adapter='{request.adapter_path}'")
    if not adapter.is_available():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="MLX-LM library not available.")
    try:
        result = await adapter.load_model(request.identifier, request.adapter_path)
        if result.get("success"):
            loaded_model_info = await adapter.get_current_model_info()
            return ModelLoadResponse(success=True, message=result.get("message", "Model loaded."), model_info=loaded_model_info)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("message", "Failed to load model."))
    except FileNotFoundError as e: # Specifically catch this from adapter
        logger.error(f"Model not found during load: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Model or adapter not found: {e}")
    except RuntimeError as e: # Catch runtime errors from adapter (e.g., load failure)
        logger.error(f"Runtime error loading model: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error loading model '{request.identifier}':")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error: {str(e)}")

@router.post("/unload", response_model=ModelLoadResponse)
async def unload_model_endpoint(adapter: MLXAdapter = Depends(get_mlx_adapter)):
    logger.info("Request received: Unload current model.")
    if not adapter.is_available():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="MLX-LM library not available.")
    if not adapter.is_model_loaded():
        return ModelLoadResponse(success=True, message="No model currently loaded.", model_info=None)
    
    unloaded_model_name = adapter.current_identifier or "Unknown"
    success = await adapter.unload_model()
    if success:
        return ModelLoadResponse(success=True, message=f"Model '{unloaded_model_name}' unloaded successfully.", model_info=None)
    else:
        # Adapter's unload_model logs specifics, return a general error here
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to unload model.")

@router.get("/current", response_model=Optional[ModelInfo])
async def get_current_model_endpoint(adapter: MLXAdapter = Depends(get_mlx_adapter)):
    logger.debug("Request received: Get current model info.")
    if not adapter.is_available():
        # Don't raise 503 if just checking, client might want to know if service is up but mlx-lm missing
        logger.warning("Attempted to get current model info, but mlx-lm library is not available.")
        return None
    
    model_info_dict = await adapter.get_current_model_info()
    if model_info_dict:
        return ModelInfo(**model_info_dict) # Convert dict from adapter to Pydantic model
    return None