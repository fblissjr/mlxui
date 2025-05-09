from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, status
import logging
import json
from typing import AsyncIterator

from ..core.mlx_adapter import MLXAdapter, get_mlx_adapter
from .schemas import GenerationRequest, TokenChunk, CacheSaveRequest, CacheLoadRequest, TrimCacheRequest, CacheResponse

router = APIRouter()
logger = logging.getLogger("mlxui.backend.api.generation")

@router.websocket("/ws")
async def websocket_generate_stream(
    websocket: WebSocket,
    adapter: MLXAdapter = Depends(get_mlx_adapter)
):
    await websocket.accept()
    logger.info("WebSocket connection established for generation stream.")

    if not adapter.is_available():
        error_chunk = TokenChunk(text="", is_finished=True, error="mlx-lmlibrary not available.", finish_reason="error")
        await websocket.send_text(error_chunk.model_dump_json())
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return
    if not adapter.is_model_loaded():
        error_chunk = TokenChunk(text="", is_finished=True, error="No model loaded. Please load a model first.", finish_reason="error")
        await websocket.send_text(error_chunk.model_dump_json())
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR) # Using internal error as client needs to fix this
        return

    try:
        # Receive the generation request (once)
        request_data_str = await websocket.receive_text()
        request_data_dict = json.loads(request_data_str)
        generation_request = GenerationRequest(**request_data_dict)
        logger.info(f"Generation request received via WebSocket: {generation_request.prompt[:50]}...")

        # Stream generated tokens
        async for chunk in adapter.stream_generate(generation_request):
            await websocket.send_text(chunk.model_dump_json())
            if chunk.is_finished and chunk.error:
                logger.error(f"Error during generation stream: {chunk.error}")
                # Error already sent in chunk, client should handle
            elif chunk.is_finished:
                logger.info(f"Generation stream finished successfully. Reason: {chunk.finish_reason}")

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected by client during generation stream.")
    except json.JSONDecodeError:
        logger.error("Invalid JSON received for generation request via WebSocket.")
        error_chunk = TokenChunk(text="", is_finished=True, error="Invalid JSON request.", finish_reason="error")
        await websocket.send_text(error_chunk.model_dump_json())
    except Exception as e:
        logger.exception("Unexpected error during WebSocket generation stream:")
        error_chunk = TokenChunk(text="", is_finished=True, error=f"Internal server error: {str(e)}", finish_reason="error")
        try: # Attempt to send error before closing
            await websocket.send_text(error_chunk.model_dump_json())
        except Exception:
            pass # Ignore if send fails on already broken socket
    finally:
        # Ensure connection is closed from server side if not already
        try:
            await websocket.close()
            logger.info("WebSocket connection closed.")
        except RuntimeError: # Already closed
            pass


@router.post("/cache/save", response_model=CacheResponse)
async def save_cache_endpoint(
    request: CacheSaveRequest,
    adapter: MLXAdapter = Depends(get_mlx_adapter)
):
    logger.info(f"Request to save KV cache to file: {request.filename}")
    if not adapter.is_available():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="MLX-LM library not available.")
    if not adapter.is_model_loaded() or adapter.prompt_cache is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active model or cache to save.")
    
    success, message, cache_size = await adapter.save_kv_cache(request.filename)
    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)
    return CacheResponse(success=True, message=message, cache_size=cache_size)


@router.post("/cache/load", response_model=CacheResponse)
async def load_cache_endpoint(
    request: CacheLoadRequest,
    adapter: MLXAdapter = Depends(get_mlx_adapter)
):
    logger.info(f"Request to load KV cache from file: {request.filename}")
    if not adapter.is_available():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="mlx-lm library not available.")
    if not adapter.is_model_loaded():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Load a model before loading a cache.")

    success, message, cache_size = await adapter.load_kv_cache(request.filename)
    if not success:
        if "not found" in message.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)
    return CacheResponse(success=True, message=message, cache_size=cache_size)

@router.post("/cache/trim", response_model=CacheResponse)
async def trim_cache_endpoint(
    request: TrimCacheRequest,
    adapter: MLXAdapter = Depends(get_mlx_adapter)
):
    logger.info(f"Request to trim {request.num_tokens} tokens from KV cache.")
    if not adapter.is_available():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="mlx-lm library not available.")
    if not adapter.is_model_loaded() or adapter.prompt_cache is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active model or cache to trim.")

    success, message, cache_size = await adapter.trim_kv_cache(request.num_tokens)
    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)
    return CacheResponse(success=True, message=message, cache_size=cache_size)