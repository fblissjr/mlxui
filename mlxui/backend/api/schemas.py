"""
Pydantic models (schemas) for API request and response validation.
These models define the data structures expected by the API endpoints.
"""
from pydantic import (
    BaseModel,
    Field,
    root_validator,
    field_validator,
)  # Add root_validator
from typing import List, Dict, Any, Optional, Union, Literal
from datetime import datetime

class ModelInfo(BaseModel):
    id: str = Field(..., description="Unique identifier (local path or Hub ID)")
    name: str = Field(..., description="Display name (e.g., directory basename)")
    path: Optional[str] = Field(None, description="Full local path if source is 'local'")
    source: Literal["local", "hub"] = Field(..., description="Origin of the model")
    config: Optional[Dict[str, Any]] = Field(None, description="Snippet of relevant model config (e.g., type, quantization)")
    is_loaded: bool = Field(False, description="Indicates if the model is currently loaded in the backend") # Default to False
    adapter_path: Optional[str] = Field(None, description="Path to loaded adapter, if any")

class ModelLoadRequest(BaseModel):
    identifier: str = Field(..., description="Local path or Hugging Face Hub repository ID to load")
    adapter_path: Optional[str] = Field(None, description="Optional path to LoRA adapter weights")

class ModelLoadResponse(BaseModel):
    success: bool
    message: str
    model_info: Optional[ModelInfo] = Field(None, description="Info of the model after the operation")

class KVCacheOptions(BaseModel):
    bits: Optional[int] = Field(None, ge=1, le=8, description="Bits for KV cache quantization (e.g., 2, 4, 8). None or 0 disables.")
    group_size: Optional[int] = Field(64, ge=1, description="Group size for KV cache quantization.")
    quantized_kv_start: Optional[int] = Field(5000, ge=0, description="Token position to start quantizing KV cache.")
    # Added from mlx_lm CLI, though this is more a cache creation time param for make_prompt_cache
    max_size: Optional[int] = Field(
        None,
        ge=1,
        description="Max tokens for rotating KV cache (make_prompt_cache arg).",
    )
    # Note: --prompt-cache-file is handled by separate API endpoints, not per-generation request

class GenerationRequest(BaseModel):
    # Make prompt optional, but we'll validate that either prompt or messages exists
    prompt: Optional[str] = Field(
        None, description="The input prompt text. Used if 'messages' is not provided."
    )
    messages: Optional[List[Dict[str, str]]] = Field(
        None,
        description="List of messages for chat templating. Takes precedence over 'prompt' if provided.",
    )

    # Core Sampling Parameters
    max_tokens: int = Field(default=4096, ge=1, le=16384)
    temperature: float = Field(default=1.0, ge=0.0, le=5.0)
    top_p: Optional[float] = Field(default=0.95, ge=0.0, le=1.0)
    top_k: Optional[int] = Field(default=0, ge=0)
    min_p: Optional[float] = Field(default=0.0, ge=0.0, le=1.0)
    min_tokens_to_keep: Optional[int] = Field(default=1, ge=1)

    repetition_penalty: Optional[float] = Field(default=1.0, ge=0.0)
    repetition_context_size: Optional[int] = Field(default=20, ge=0)

    xtc_probability: Optional[float] = Field(default=0.0, ge=0.0, le=1.0)
    xtc_threshold: Optional[float] = Field(default=0.0, ge=0.0, le=0.5)

    extra_eos_tokens: Optional[List[str]] = Field(default_factory=list)
    seed: Optional[int] = Field(None)

    ignore_chat_template: Optional[bool] = Field(default=False)

    use_speculative: Optional[bool] = Field(default=False)
    draft_model_identifier: Optional[str] = Field(None)
    num_draft_tokens: Optional[int] = Field(default=3, ge=1)

    kv_cache_options: Optional[KVCacheOptions] = Field(None)
    logit_bias: Optional[Dict[str, float]] = Field(None)

    # Why: Root validator to ensure at least prompt or messages is provided.
    @root_validator(
        pre=False, skip_on_failure=True
    )  # Pydantic v1 style, use model_validator for v2
    @classmethod
    def check_prompt_or_messages_present(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        prompt, messages = values.get("prompt"), values.get("messages")
        if not prompt and not messages:
            raise ValueError("Either 'prompt' or 'messages' must be provided.")
        if prompt and messages:
            # As per current logic, messages will override prompt if ignore_chat_template is False
            # This is fine, adapter will handle which one to use.
            pass
        return values

    # Why: Pydantic validator for logit_bias keys
    @field_validator('logit_bias', mode='before')
    @classmethod
    def validate_logit_bias_keys(cls, v: Any) -> Optional[Dict[str, float]]:
        if v is None:
            return None
        if not isinstance(v, dict):
            raise ValueError("logit_bias must be a dictionary.")
        validated_bias: Dict[str, float] = {}
        for key, value in v.items():
            try:
                str_key = str(key)
                float_value = float(value)
                validated_bias[str_key] = float_value
            except ValueError:
                raise ValueError(f"Invalid logit_bias: '{key}': '{value}'.")
        return validated_bias

class TokenChunk(BaseModel):
    text: str = Field(..., description="The generated text segment in this chunk")
    is_finished: bool = Field(False, description="Indicates if this is the last chunk")
    finish_reason: Optional[Literal["length", "stop", "error"]] = Field(None, description="Reason for generation ending")
    error: Optional[str] = Field(None, description="Error message if generation failed")
    from_draft: Optional[bool] = Field(None, description="True if token(s) came from the draft model")
    token_count: Optional[int] = Field(None, description="Number of new tokens generated in this chunk (usually 1)")
    token: Optional[int] = Field(None, description="The token ID generated (from mlx-lm)")
    prompt_tokens: Optional[int] = Field(None, description="Number of prompt tokens processed")
    generation_tokens: Optional[int] = Field(None, description="Cumulative number of tokens generated so far in this stream")
    generation_tps: Optional[float] = Field(
        None, description="Overall generation tokens-per-second (from mlx-lm)"
    )

class CacheSaveRequest(BaseModel):
    filename: str = Field(..., min_length=1, description="Filename (without path) for the cache file. '.safetensors' will be appended.")

class CacheLoadRequest(BaseModel):
    filename: str = Field(..., min_length=1, description="Filename (without path) of the cache file to load.")

class TrimCacheRequest(BaseModel):
    num_tokens: int = Field(..., ge=1, description="Number of tokens to trim from the start of the cache")

class CacheResponse(BaseModel):
    success: bool
    message: str
    cache_size: Optional[int] = Field(None, description="Number of tokens in the cache after operation, if applicable")

class MemoryUsage(BaseModel):
    rss_mb: float = Field(..., description="Resident Set Size in MB")
    # gpu_active_mb: Optional[float] = Field(None, description="Estimated active GPU memory (if available)") # Future

class PerformanceMetrics(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the metrics snapshot")
    tokens_per_second: Optional[float] = Field(None, description="Generation speed (tokens/sec) from last generation")
    memory_usage: Optional[MemoryUsage] = Field(None, description="Current memory usage of the backend process")
    cpu_usage_percent: Optional[float] = Field(None, description="Current system CPU usage percentage")

class ConfigUpdateRequest(BaseModel):
    key: str = Field(..., description="Configuration key (dot notation, e.g., 'models.scan_directories')")
    value: Any = Field(..., description="New value for the configuration key")

class ConfigUpdateResponse(BaseModel):
    success: bool
    message: Optional[str] = None