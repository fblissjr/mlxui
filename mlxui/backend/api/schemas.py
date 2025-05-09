"""
Pydantic models (schemas) for API request and response validation.
These models define the data structures expected by the API endpoints.
"""
from pydantic import BaseModel, Field, field_validator
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
    max_size: Optional[int] = Field(None, ge=1, description="Max tokens for rotating KV cache.")

class GenerationRequest(BaseModel):
    prompt: str = Field(..., description="The input prompt text")
    max_tokens: int = Field(default=512, ge=1, le=16384, description="Maximum number of new tokens to generate")
    temperature: float = Field(default=0.6, ge=0.0, le=2.0, description="Sampling temperature. 0.0 means greedy.")
    top_p: Optional[float] = Field(default=0.9, ge=0.0, le=1.0, description="Nucleus sampling probability threshold")
    top_k: Optional[int] = Field(default=50, ge=0, description="Top-k sampling threshold (0 disables)")
    min_p: Optional[float] = Field(default=0.0, ge=0.0, le=1.0, description="Min-p sampling threshold (0 disables)")
    min_tokens_to_keep: Optional[int] = Field(default=1, ge=1, description="Min tokens to keep for min-p")
    repetition_penalty: Optional[float] = Field(default=1.1, ge=0.0, description="Penalty for repeating tokens (1.0 means no penalty)")
    repetition_context_size: Optional[int] = Field(default=25, ge=0, description="Context window size for repetition penalty")
    stopping_strings: Optional[List[str]] = Field(default_factory=list, description="Sequences that stop generation")
    seed: Optional[int] = Field(None, description="PRNG seed for reproducible generation. None or -1 for random.")
    use_speculative: Optional[bool] = Field(default=False, description="Whether to use speculative decoding")
    draft_model_identifier: Optional[str] = Field(None, description="Identifier (path/Hub ID) for the draft model")
    num_draft_tokens: Optional[int] = Field(default=3, ge=1, description="Number of draft tokens for speculative decoding")
    kv_cache_options: Optional[KVCacheOptions] = Field(None, description="Options for KV cache quantization")
    logit_bias: Optional[Dict[str, float]] = Field(None, description="Bias added to specific token logits (token_id as string key)")

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
                raise ValueError(f"Invalid logit_bias key-value pair: '{key}': '{value}'. Key must be string, value convertible to float.")
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
    generation_tps: Optional[float] = Field(None, description="Generation tokens-per-second (from mlx-lm)")

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