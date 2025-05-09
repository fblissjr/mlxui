import asyncio
import gc
import json
import logging
import time
import sys
from functools import partial
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Literal, Optional, Tuple, Union

import mlx.core as mx
import mlx.nn as nn

try:
    from mlx_lm.generate import GenerationResponse as MLXInternalGenerationResponse
    from mlx_lm.generate import stream_generate
    from mlx_lm.models.cache import (can_trim_prompt_cache, load_prompt_cache,
                                     make_prompt_cache, save_prompt_cache,
                                     trim_prompt_cache)
    from mlx_lm.sample_utils import make_logits_processors, make_sampler
    from mlx_lm.tokenizer_utils import TokenizerWrapper
    from mlx_lm.utils import get_model_path, load, load_config
    MLX_LM_AVAILABLE = True
except ImportError as e:
    print(f"CRITICAL: Failed to import mlx-lm components: {e}", file=sys.stderr)
    print("Please ensure mlx-lm is installed correctly (`pip install mlx-lm`). mlxui will not function.", file=sys.stderr)
    MLX_LM_AVAILABLE = False
    class MLXInternalGenerationResponse: pass
    class TokenizerWrapper: pass
    class KVCache: pass
    _err_msg = "mlx-lm library not installed or failed to import."
    def load(*args, **kwargs): raise ImportError(_err_msg)
    def stream_generate(*args, **kwargs): raise ImportError(_err_msg)
    def make_prompt_cache(*args, **kwargs): raise ImportError(_err_msg)
    def save_prompt_cache(*args, **kwargs): raise ImportError(_err_msg)
    def load_prompt_cache(*args, **kwargs): raise ImportError(_err_msg)
    def trim_prompt_cache(*args, **kwargs): raise ImportError(_err_msg)
    def can_trim_prompt_cache(*args, **kwargs): return False
    def make_sampler(*args, **kwargs): raise ImportError(_err_msg)
    def make_logits_processors(*args, **kwargs): raise ImportError(_err_msg)
    def get_model_path(*args, **kwargs) -> Path: raise ImportError(_err_msg) # type: ignore
    def load_config(*args, **kwargs): raise ImportError(_err_msg)


from ..config import config as app_config
from ..config import DEFAULT_CONFIG_DIR, DEFAULT_MODELS_SCAN_DIR, DEFAULT_KV_CACHE_DIR
from ..api.schemas import GenerationRequest, TokenChunk, ModelInfo

logger = logging.getLogger("mlxui.backend.core.adapter")

_adapter_instance: Optional['MLXAdapter'] = None
_adapter_lock = asyncio.Lock()

async def get_mlx_adapter() -> 'MLXAdapter':
    global _adapter_instance
    if _adapter_instance is None:
        async with _adapter_lock:
            if _adapter_instance is None:
                logger.info("Creating MLXAdapter singleton instance.")
                _adapter_instance = MLXAdapter()
    return _adapter_instance

class MLXAdapter:
    def __init__(self):
        if not MLX_LM_AVAILABLE:
            logger.error("mlx-lm library is NOT available. MLXAdapter will be non-functional.")
        self._set_initial_state()
        self.last_generation_tps: Optional[float] = None
        logger.info("MLXAdapter initialized." if MLX_LM_AVAILABLE else "MLXAdapter initialized (NON-FUNCTIONAL).")

    def _set_initial_state(self):
        self.model: Optional[nn.Module] = None
        self.tokenizer: Optional[TokenizerWrapper] = None
        self.prompt_cache: Optional[List[Any]] = None
        self.prompt_cache_tokens: List[int] = []
        self.draft_model: Optional[nn.Module] = None
        self.draft_tokenizer: Optional[TokenizerWrapper] = None
        self.current_config: Optional[dict] = None
        self.current_identifier: Optional[str] = None
        self.current_adapter_path: Optional[str] = None
        self.current_draft_identifier: Optional[str] = None
        self.last_generation_tps = None

    def is_available(self) -> bool:
        return MLX_LM_AVAILABLE

    def _raise_if_unavailable(self):
        if not self.is_available():
            raise RuntimeError("mlx-lm library is required but not installed or failed to import.")

    def is_model_loaded(self) -> bool:
        return self.is_available() and self.model is not None and self.tokenizer is not None

    def _clear_state(self):
        logger.info("Clearing MLXAdapter state...")
        old_identifier = self.current_identifier
        self._set_initial_state()
        if self.is_available():
            gc.collect()
            try:
                mx.clear_cache()
                logger.debug("Cleared MLX cache.")
            except Exception as e:
                logger.warning(f"Could not clear MLX cache during state clear for '{old_identifier}': {e}")

    async def load_model(
        self,
        identifier: str,
        adapter_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        self._raise_if_unavailable()

        if self.current_identifier == identifier and \
           self.current_adapter_path == adapter_path and \
           self.model:
             logger.info(f"Model '{identifier}' with adapter '{adapter_path}' is already loaded.")
             return {"success": True, "message": "Model already loaded."}

        logger.info(f"Load request: identifier='{identifier}', adapter='{adapter_path}'")

        if self.is_model_loaded():
            logger.info(f"Unloading current model '{self.current_identifier}' before loading new one.")
            await self.unload_model()

        try:
            logger.info(f"Starting load of model '{identifier}'...")
            loop = asyncio.get_running_loop()
            
            load_fn_with_kwargs = partial(load, adapter_path=adapter_path, lazy=False)
            model_instance, tokenizer_instance = await loop.run_in_executor(
                None, load_fn_with_kwargs, identifier
            )
            logger.info(f"Model and tokenizer for '{identifier}' loaded in memory.")

            try:
                model_path_obj = await loop.run_in_executor(None, get_model_path, identifier)
                config_dict = await loop.run_in_executor(None, load_config, model_path_obj)
            except Exception: # If identifier is Hub ID and not downloaded yet, get_model_path might handle it, or load_config fails
                config_dict = model_instance.args.to_dict() if hasattr(model_instance, 'args') and hasattr(model_instance.args, 'to_dict') else {}


            self.model = model_instance
            self.tokenizer = tokenizer_instance # type: ignore
            self.current_config = config_dict
            self.current_identifier = identifier
            self.current_adapter_path = adapter_path
            self.prompt_cache = None
            self.prompt_cache_tokens = []
            if self.draft_model:
                self.draft_model = None
                self.current_draft_identifier = None
                logger.info("Unloaded previous draft model due to main model change.")

            logger.info(f"Successfully assigned model '{identifier}' to adapter state.")
            return {"success": True, "message": f"Model '{identifier}' loaded successfully."}

        except FileNotFoundError as e:
             logger.error(f"Model file not found for '{identifier}': {e}")
             self._clear_state()
             raise
        except Exception as e:
            logger.exception(f"Failed to load model '{identifier}':")
            self._clear_state()
            raise RuntimeError(f"Failed to load model '{identifier}': {str(e)}")

    async def unload_model(self) -> bool:
        self._raise_if_unavailable()
        if not self.is_model_loaded():
            logger.info("No model currently loaded, nothing to unload.")
            return True
        identifier = self.current_identifier
        logger.info(f"Unloading model '{identifier}'...")
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._clear_state)
            logger.info(f"Model '{identifier}' unloaded successfully.")
            return True
        except Exception as e:
            logger.exception(f"Error during model unload for '{identifier}':")
            return False

    async def get_current_model_info(self) -> Optional[ModelInfo]:
        self._raise_if_unavailable()
        if not self.is_model_loaded() or not self.current_identifier or self.current_config is None:
            return None

        is_local_path = Path(self.current_identifier).is_dir()
        
        path_str: Optional[str] = None
        source_type: Literal["local", "hub"]

        if is_local_path:
            path_str = str(Path(self.current_identifier).resolve())
            source_type = "local"
            model_name = Path(self.current_identifier).name
        else: # Assumed Hub ID
            path_str = None # For Hub ID, local path after download is managed by HF cache
            source_type = "hub"
            model_name = self.current_identifier


        config_snippet = {
            key: self.current_config.get(key)
            for key in ["model_type", "hidden_size", "num_hidden_layers", "vocab_size", "quantization"]
            if self.current_config and key in self.current_config
        }

        return ModelInfo(
            id=self.current_identifier,
            name=model_name,
            path=path_str,
            source=source_type,
            is_loaded=True,
            adapter_path=self.current_adapter_path,
            config=config_snippet
        )

    async def list_local_models(self) -> List[ModelInfo]:
        self._raise_if_unavailable()
        local_models_list: List[ModelInfo] = []
        scan_dirs_str = app_config.get("models.scan_directories", [str(DEFAULT_MODELS_SCAN_DIR)])
        loop = asyncio.get_running_loop()

        for dir_str in scan_dirs_str:
            scan_dir = await loop.run_in_executor(None, lambda: Path(dir_str).expanduser().resolve())
            if not await loop.run_in_executor(None, scan_dir.is_dir):
                logger.warning(f"Model scan directory not found or not a directory: {scan_dir}")
                continue
            logger.info(f"Scanning for models in: {scan_dir}")
            try:
                items_in_dir = await loop.run_in_executor(None, list, scan_dir.iterdir())
                for item_path_obj in items_in_dir: # item_path_obj is a Path object
                    if await loop.run_in_executor(None, item_path_obj.is_dir):
                        has_config = await loop.run_in_executor(None, (item_path_obj / "config.json").is_file)
                        weight_files = await loop.run_in_executor(None, list, item_path_obj.glob("*.safetensors"))
                        has_weights = bool(weight_files)
                        has_tokenizer_json = await loop.run_in_executor(None, (item_path_obj / "tokenizer.json").is_file)
                        has_tokenizer_model = await loop.run_in_executor(None, (item_path_obj / "tokenizer.model").is_file)

                        if has_config and has_weights and (has_tokenizer_json or has_tokenizer_model):
                            model_full_path = str(item_path_obj.resolve())
                            model_display_name = item_path_obj.name
                            logger.debug(f"Found potential local model: {model_display_name} at {model_full_path}")

                            model_config_snippet = {}
                            try:
                                config_content = await loop.run_in_executor(None, load_config, item_path_obj)
                                model_config_snippet = {
                                    "model_type": config_content.get("model_type"),
                                    "quantization": config_content.get("quantization"),
                                    "hidden_size": config_content.get("hidden_size"),
                                    "num_hidden_layers": config_content.get("num_hidden_layers"),
                                }
                            except Exception: pass
                            
                            is_currently_loaded = (self.current_identifier == model_full_path and self.is_model_loaded())

                            if not any(m.id == model_full_path for m in local_models_list):
                                local_models_list.append(ModelInfo(
                                    id=model_full_path, # Use full path as the ID for local models
                                    name=model_display_name,
                                    path=model_full_path,
                                    source="local",
                                    config=model_config_snippet,
                                    is_loaded=is_currently_loaded,
                                    adapter_path=self.current_adapter_path if is_currently_loaded else None
                                ))
            except OSError as e: logger.error(f"Error scanning directory {scan_dir}: {e}")
        logger.info(f"Finished scanning. Found {len(local_models_list)} potential local models.")
        return local_models_list

    async def _update_prompt_cache(self, new_prompt_tokens_list: List[int]) -> List[int]:
        self._raise_if_unavailable()
        loop = asyncio.get_running_loop()
        def _blocking_make_cache():
            new_cache = make_prompt_cache(self.model)
            if self.draft_model: new_cache += make_prompt_cache(self.draft_model)
            return new_cache
        if self.prompt_cache is None:
             self.prompt_cache = await loop.run_in_executor(None, _blocking_make_cache)
             self.prompt_cache_tokens = list(new_prompt_tokens_list)
             return new_prompt_tokens_list
        cache_len = len(self.prompt_cache_tokens)
        prompt_len = len(new_prompt_tokens_list)
        common_prefix_len = 0
        while common_prefix_len < min(cache_len, prompt_len) and \
              self.prompt_cache_tokens[common_prefix_len] == new_prompt_tokens_list[common_prefix_len]:
            common_prefix_len += 1
        if common_prefix_len == cache_len:
            if cache_len == prompt_len: return []
            else:
                suffix_tokens = new_prompt_tokens_list[common_prefix_len:]
                self.prompt_cache_tokens.extend(suffix_tokens)
                return suffix_tokens
        else:
            tokens_to_trim = cache_len - common_prefix_len
            if tokens_to_trim > 0:
                can_trim = await loop.run_in_executor(None, can_trim_prompt_cache, self.prompt_cache)
                if can_trim:
                    try:
                        trimmed_count = await loop.run_in_executor(None, trim_prompt_cache, self.prompt_cache, tokens_to_trim)
                        if trimmed_count == tokens_to_trim:
                            self.prompt_cache_tokens = self.prompt_cache_tokens[:common_prefix_len]
                            suffix_tokens = new_prompt_tokens_list[common_prefix_len:]
                            self.prompt_cache_tokens.extend(suffix_tokens)
                            return suffix_tokens
                        else: logger.warning(f"Cache trim reported {trimmed_count}, expected {tokens_to_trim}. Resetting cache.")
                    except Exception as trim_err: logger.error(f"Error trimming cache: {trim_err}. Resetting cache.")
                else: logger.debug("Current cache type cannot be trimmed. Resetting cache.")
            self.prompt_cache = await loop.run_in_executor(None, _blocking_make_cache)
            self.prompt_cache_tokens = list(new_prompt_tokens_list)
            return new_prompt_tokens_list

    async def save_kv_cache(self, filename_base: str) -> Tuple[bool, str, Optional[int]]:
        self._raise_if_unavailable()
        if not self.is_model_loaded() or self.prompt_cache is None:
            return False, "No model or active cache loaded to save.", None
        
        cache_dir_str = app_config.get("models.cache_directory", str(DEFAULT_KV_CACHE_DIR))
        cache_dir = Path(cache_dir_str).expanduser().resolve()
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, cache_dir.mkdir, True, True)
        save_path = cache_dir / f"{Path(filename_base).stem}.safetensors"
        logger.info(f"Saving KV cache state ({len(self.prompt_cache_tokens)} tokens) to {save_path}")
        try:
            metadata = {
                 "model_identifier": self.current_identifier,
                 "adapter_path": self.current_adapter_path,
                 "token_count": len(self.prompt_cache_tokens),
                 "mlxui_version": __import__('mlxui').__version__, # type: ignore
                 "creation_timestamp": time.time(),
            }
            await loop.run_in_executor(None, save_prompt_cache, str(save_path), self.prompt_cache, metadata)
            cache_size = len(self.prompt_cache_tokens)
            logger.info(f"KV cache saved successfully to {save_path}.")
            return True, f"Cache saved to {save_path.name}.", cache_size
        except Exception as e:
            logger.exception(f"Failed to save KV cache to {save_path}:")
            return False, f"Failed to save cache: {str(e)}", None

    async def load_kv_cache(self, filename_base: str) -> Tuple[bool, str, Optional[int]]:
        self._raise_if_unavailable()
        if not self.is_model_loaded():
             return False, "Load a model before loading a KV cache.", None
        cache_dir_str = app_config.get("models.cache_directory", str(DEFAULT_KV_CACHE_DIR))
        cache_dir = Path(cache_dir_str).expanduser().resolve()
        load_path = cache_dir / f"{Path(filename_base).stem}.safetensors"
        logger.info(f"Attempting to load KV cache state from {load_path}")
        if not await asyncio.get_running_loop().run_in_executor(None, load_path.is_file):
             logger.error(f"Cache file not found: {load_path}")
             return False, "Cache file not found.", None
        try:
            loop = asyncio.get_running_loop()
            loaded_cache, metadata = await loop.run_in_executor(None, load_prompt_cache, str(load_path), True)
            loaded_model_id = metadata.get("model_identifier")
            if loaded_model_id and loaded_model_id != self.current_identifier:
                 msg = (f"Cache model mismatch (Cache: '{loaded_model_id}', Current: '{self.current_identifier}'). Loading anyway.")
                 logger.warning(msg)
            if not isinstance(loaded_cache, list): raise ValueError("Loaded cache data is not in the expected list format.")
            self.prompt_cache = loaded_cache
            self.prompt_cache_tokens = [0] * metadata.get("token_count", 0)
            cache_size = len(self.prompt_cache_tokens)
            logger.info(f"KV cache ({cache_size} tokens) loaded successfully from {load_path}.")
            return True, "Cache loaded successfully.", cache_size
        except Exception as e:
            logger.exception(f"Failed to load KV cache from {load_path}:")
            self.prompt_cache = None; self.prompt_cache_tokens = []
            return False, f"Failed to load cache: {str(e)}", None

    async def trim_kv_cache(self, num_tokens: int) -> Tuple[bool, str, Optional[int]]:
        self._raise_if_unavailable()
        if not self.is_model_loaded() or self.prompt_cache is None:
            return False, "No model or active cache loaded to trim.", None
        logger.info(f"Trimming {num_tokens} tokens from the start of the KV cache.")
        try:
            loop = asyncio.get_running_loop()
            can_trim = await loop.run_in_executor(None, can_trim_prompt_cache, self.prompt_cache)
            if not can_trim:
                msg = "Current cache type does not support trimming."
                logger.warning(msg); return False, msg, len(self.prompt_cache_tokens)
            trimmed_count = await loop.run_in_executor(None, trim_prompt_cache, self.prompt_cache, num_tokens)
            if trimmed_count >= 0:
                self.prompt_cache_tokens = self.prompt_cache_tokens[trimmed_count:]
                cache_size = len(self.prompt_cache_tokens)
                logger.info(f"Successfully trimmed {trimmed_count} tokens. Cache size now: {cache_size} tokens.")
                return True, f"Trimmed {trimmed_count} tokens.", cache_size
            else:
                msg = "Failed to trim cache (operation not supported or error)."
                logger.error(msg); return False, msg, len(self.prompt_cache_tokens)
        except Exception as e:
            logger.exception("Failed to trim KV cache:")
            current_size = len(self.prompt_cache_tokens) if self.prompt_cache_tokens else 0
            return False, f"Failed to trim cache: {str(e)}", current_size


    async def stream_generate(self, request: GenerationRequest) -> AsyncIterator[TokenChunk]:
        self._raise_if_unavailable()
        if not self.is_model_loaded():
            yield TokenChunk(text="", is_finished=True, error="No model loaded.", finish_reason="error")
            return

        logger.info(f"Generation stream requested for prompt: '{request.prompt[:70]}...'")
        overall_start_time = time.perf_counter()
        generation_tokens_count = 0
        num_prompt_tokens_for_model = 0 

        try:
            loop = asyncio.get_running_loop()
            try:
                prompt_tokens_list: List[int] = await loop.run_in_executor(None, self.tokenizer.encode, request.prompt) # type: ignore
            except Exception as e: raise ValueError(f"Prompt encoding failed: {e}")
            initial_prompt_token_count = len(prompt_tokens_list)

            tokens_to_process_list = await self._update_prompt_cache(prompt_tokens_list)
            tokens_to_process_mx = mx.array(tokens_to_process_list)
            num_prompt_tokens_for_model = len(tokens_to_process_list)

            sampler = make_sampler(
                temp=request.temperature, top_p=request.top_p or 1.0,
                min_p=request.min_p or 0.0, min_tokens_to_keep=request.min_tokens_to_keep or 1,
                top_k=request.top_k or 0
            )
            logit_bias_int_keys: Optional[Dict[int, float]] = None
            if request.logit_bias:
                try: logit_bias_int_keys = {int(k): float(v) for k, v in request.logit_bias.items()}
                except ValueError: logger.warning("Invalid logit_bias format. Ignoring.")
            logits_processors = make_logits_processors(
                logit_bias=logit_bias_int_keys, repetition_penalty=request.repetition_penalty,
                repetition_context_size=request.repetition_context_size,
            )

            active_draft_model = None
            if request.use_speculative and request.draft_model_identifier:
                if self.current_draft_identifier != request.draft_model_identifier or self.draft_model is None:
                    logger.info(f"Loading draft model for speculative decoding: {request.draft_model_identifier}")
                    try:
                        load_draft_fn_with_kwargs = partial(load, lazy=False) # Ensure draft is loaded
                        draft_model_instance, draft_tokenizer_instance = await loop.run_in_executor(
                            None, load_draft_fn_with_kwargs, request.draft_model_identifier
                        )
                        if draft_tokenizer_instance.vocab_size != self.tokenizer.vocab_size: # type: ignore
                             logger.warning("Draft model tokenizer vocab size mismatch!")
                        self.draft_model = draft_model_instance
                        self.draft_tokenizer = draft_tokenizer_instance
                        self.current_draft_identifier = request.draft_model_identifier
                        self.prompt_cache = None
                        tokens_to_process_list = await self._update_prompt_cache(prompt_tokens_list)
                        tokens_to_process_mx = mx.array(tokens_to_process_list)
                        num_prompt_tokens_for_model = len(tokens_to_process_list)
                    except Exception as e:
                         logger.error(f"Failed to load draft model '{request.draft_model_identifier}': {e}. Disabling spec decoding.")
                         self.draft_model = None; self.current_draft_identifier = None
                active_draft_model = self.draft_model
            elif not request.use_speculative and self.draft_model is not None: active_draft_model = None

            kv_bits: Optional[int] = None; kv_group_size: int = 64; kv_quantized_start: int = 5000
            if request.kv_cache_options:
                kv_bits = request.kv_cache_options.bits
                if request.kv_cache_options.group_size is not None: kv_group_size = request.kv_cache_options.group_size
                if request.kv_cache_options.quantized_kv_start is not None: kv_quantized_start = request.kv_cache_options.quantized_kv_start
            
            logger.info(f"Calling mlx_lm.stream_generate with {num_prompt_tokens_for_model} effective prompt tokens.")
            
            partial_stream_generate = partial(
                stream_generate,
                self.model, self.tokenizer, tokens_to_process_mx, # type: ignore
                max_tokens=request.max_tokens,
                prompt_cache=self.prompt_cache,
                sampler=sampler,
                logits_processors=logits_processors,
                draft_model=active_draft_model if request.use_speculative else None,
                num_draft_tokens=request.num_draft_tokens if request.use_speculative and active_draft_model else 0,
                kv_bits=kv_bits,
                kv_group_size=kv_group_size,
                quantized_kv_start=kv_quantized_start,
            )
            generation_iterator = await loop.run_in_executor(None, partial_stream_generate) # type: ignore
            
            last_chunk_for_final_yield: Optional[TokenChunk] = None

            for mlx_response in generation_iterator: 
                if not isinstance(mlx_response, MLXInternalGenerationResponse):
                    logger.warning(f"Unexpected type from stream_generate: {type(mlx_response)}"); continue
                
                self.prompt_cache_tokens.append(mlx_response.token)
                generation_tokens_count += 1
                self.last_generation_tps = mlx_response.generation_tps

                chunk = TokenChunk(
                    text=mlx_response.text,
                    is_finished=(mlx_response.finish_reason is not None),
                    finish_reason=mlx_response.finish_reason, # type: ignore
                    token_count=1, token=mlx_response.token,
                    from_draft=getattr(mlx_response, 'from_draft', False),
                    prompt_tokens=initial_prompt_token_count,
                    generation_tokens=generation_tokens_count,
                    generation_tps=mlx_response.generation_tps
                )
                last_chunk_for_final_yield = chunk
                yield chunk
                if chunk.is_finished: logger.info(f"Gen stream finished by model. Reason: {chunk.finish_reason}"); break
            else:
                if generation_tokens_count >= request.max_tokens:
                     logger.info(f"Gen finished: max_tokens ({request.max_tokens}) reached.")
                     if not (last_chunk_for_final_yield and last_chunk_for_final_yield.is_finished):
                          yield TokenChunk(text="", is_finished=True, finish_reason="length",
                                           prompt_tokens=initial_prompt_token_count,
                                           generation_tokens=generation_tokens_count,
                                           generation_tps=self.last_generation_tps)
        except ValueError as e:
             logger.error(f"Config error during generation: {e}")
             yield TokenChunk(text="", is_finished=True, error=str(e), finish_reason="error")
        except Exception as e:
            logger.exception("Unhandled error during generation stream:")
            yield TokenChunk(text="", is_finished=True, error=f"Generation failed: {str(e)}", finish_reason="error")
        finally:
            total_duration = time.perf_counter() - overall_start_time
            logger.info(f"Stream generation took {total_duration:.2f}s. Processed {num_prompt_tokens_for_model} prompt tokens, Generated {generation_tokens_count} tokens.")