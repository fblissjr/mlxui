from fastapi import APIRouter, HTTPException, Depends, status
import logging
from typing import Dict, Any

from mlxui.backend.config import config as app_config
from mlxui.backend.api.schemas import ConfigUpdateRequest, ConfigUpdateResponse

router = APIRouter()
logger = logging.getLogger("mlxui.backend.api.config_router") # Router specific logger

@router.get("/", response_model=Dict[str, Any])
async def get_app_configuration():
    logger.info("Request received: Get application configuration.")
    # Return a copy to prevent direct modification of the internal config dict via reference
    return app_config.get()

@router.post("/", response_model=ConfigUpdateResponse)
async def update_app_configuration(request: ConfigUpdateRequest):
    logger.info(f"Request received: Update configuration for key '{request.key}'.")
    
    # Basic validation (more complex validation could be added in Config.set)
    if not request.key or not isinstance(request.key, str):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid configuration key provided.")

    # Attempt to set the configuration
    success = app_config.set(request.key, request.value)

    if success:
        return ConfigUpdateResponse(success=True, message=f"Configuration key '{request.key}' updated successfully.")
    else:
        # Config.set should log the specific error.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update configuration for key '{request.key}'. Check server logs.")