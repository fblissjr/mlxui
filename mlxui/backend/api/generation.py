from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, status
import logging
import json
from typing import AsyncIterator  # Ensure this is imported

from mlxui.backend.core.mlx_adapter import MLXAdapter, get_mlx_adapter
from mlxui.backend.api.schemas import (
    GenerationRequest,
    TokenChunk,
    CacheSaveRequest,
    CacheLoadRequest,
    TrimCacheRequest,
    CacheResponse,
)

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
        error_chunk = TokenChunk(
            text="",
            is_finished=True,
            error="mlx-lm library not available.",
            finish_reason="error",
        )
        await websocket.send_text(error_chunk.model_dump_json())
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return
    if not adapter.is_model_loaded():
        error_chunk = TokenChunk(text="", is_finished=True, error="No model loaded. Please load a model first.", finish_reason="error")
        await websocket.send_text(error_chunk.model_dump_json())
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return

    try:
        request_data_str = await websocket.receive_text()
        request_data_dict = json.loads(request_data_str)
        generation_request = GenerationRequest(**request_data_dict)

        prompt_start_for_log = "N/A"
        if generation_request.prompt:
            prompt_start_for_log = generation_request.prompt[:50] + "..."
        elif generation_request.messages:
            first_user_message_content = "N/A"
            for msg_dict in generation_request.messages:  # Iterate over list of dicts
                # Pydantic model_dump might be better if messages are complex models
                # but if they are simple dicts from JSON, .get() is fine.
                if (
                    isinstance(msg_dict, dict)
                    and msg_dict.get("role") == "user"
                    and msg_dict.get("content")
                ):
                    first_user_message_content = (
                        str(msg_dict.get("content", ""))[:50] + "..."
                    )
                    break
            prompt_start_for_log = (
                f"Messages (first user: {first_user_message_content})"
            )
        logger.info(
            f"Generation request received via WebSocket. Input starts: '{prompt_start_for_log}'"
        )

        async for chunk in adapter.stream_generate(generation_request):
            await websocket.send_text(chunk.model_dump_json())
            if chunk.is_finished and chunk.error:
                logger.error(f"Error during generation stream: {chunk.error}")
            elif chunk.is_finished:
                logger.info(f"Generation stream finished successfully. Reason: {chunk.finish_reason}")

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected by client during generation stream.")
    except json.JSONDecodeError:
        logger.error("Invalid JSON received for generation request via WebSocket.")
        error_chunk = TokenChunk(
            text="",
            is_finished=True,
            error="Invalid JSON request.",
            finish_reason="error",
        )
        await websocket.send_text(error_chunk.model_dump_json())
    except Exception as e:
        logger.exception("Unexpected error during WebSocket generation stream:")
        error_chunk = TokenChunk(
            text="",
            is_finished=True,
            error=f"Internal server error: {str(e)}",
            finish_reason="error",
        )
        try:
            await websocket.send_text(error_chunk.model_dump_json())
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
            logger.info("WebSocket connection closed.")
        except RuntimeError:
            pass


@router.post("/cache/save", response_model=CacheResponse)
async def save_cache_endpoint(
    request: CacheSaveRequest,
    adapter: MLXAdapter = Depends(get_mlx_adapter)
):
    logger.info(f"Request to save KV cache to file: {request.filename}")
    if not adapter.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="mlx-lm library not available.",
        )
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