from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
import asyncio
import logging
import psutil # For system metrics
from mlxui.backend.core.mlx_adapter import MLXAdapter, get_mlx_adapter
from mlxui.backend.api.schemas import PerformanceMetrics, MemoryUsage 
from mlxui.backend.config import config as app_config 
from datetime import datetime

router = APIRouter()
logger = logging.getLogger("mlxui.backend.api.performance")

process = psutil.Process() # Get current process for memory usage

def get_current_performance_metrics(adapter: MLXAdapter) -> PerformanceMetrics:
    """Helper function to gather current performance metrics."""
    mem_info = process.memory_info()
    rss_mb = mem_info.rss / (1024 * 1024)
    
    # TODO (Phase 3+): Explore more detailed MLX memory (if API exists)
    # For now, process RSS is a good start.
    # gpu_active_mb = mx.metal.get_active_memory() / (1024 * 1024) if hasattr(mx, 'metal') else None

    memory_usage = MemoryUsage(rss_mb=rss_mb)
    cpu_percent = psutil.cpu_percent(interval=None) # Non-blocking

    return PerformanceMetrics(
        timestamp=datetime.utcnow(),
        tokens_per_second=adapter.last_generation_tps,
        memory_usage=memory_usage,
        cpu_usage_percent=cpu_percent,
    )

@router.get("/stats", response_model=PerformanceMetrics)
async def get_performance_stats_endpoint(adapter: MLXAdapter = Depends(get_mlx_adapter)):
    logger.debug("Request received: Get current performance stats.")
    if not adapter.is_available(): # Check if mlx-lm is usable
        # Return basic stats even if mlx-lm is down, just no TPS
        adapter.last_generation_tps = None # Ensure TPS is None
    return get_current_performance_metrics(adapter)


@router.websocket("/ws")
async def websocket_performance_stream(
    websocket: WebSocket,
    adapter: MLXAdapter = Depends(get_mlx_adapter)
):
    await websocket.accept()
    logger.info("Performance WebSocket connection established.")
    
    update_interval_ms = app_config.get("performance.update_interval_ms", 2000)
    update_interval_s = max(0.5, update_interval_ms / 1000.0) # Ensure at least 0.5s

    try:
        while True:
            if not adapter.is_available(): # Check periodically
                 adapter.last_generation_tps = None
            
            metrics = get_current_performance_metrics(adapter)
            await websocket.send_text(metrics.model_dump_json())
            await asyncio.sleep(update_interval_s)
            
    except WebSocketDisconnect:
        logger.info("Performance WebSocket disconnected by client.")
    except Exception as e:
        logger.exception("Error in performance WebSocket stream:")
        try:
            await websocket.send_text(json.dumps({"error": str(e)}))
        except:
            pass # Ignore if sending error fails
    finally:
        try:
            await websocket.close()
            logger.info("Performance WebSocket connection closed.")
        except RuntimeError: # Already closed
            pass