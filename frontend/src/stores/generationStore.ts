import { defineStore } from 'pinia';
import { ref, watch } from 'vue';
import type { GenerationParams, TokenChunk, CacheResponse, KVCacheOptions, GenerationRequest as ApiGenerationRequest, ChatMessage } from '@/api/types'; // Added ChatMessage
import { GenerationStreamManager, saveKVCache, loadKVCache, trimKVCache } from '@/api/generation';
import { useAppStore } from './appStore';
import { useModelStore } from './modelStore';

export const DEFAULT_GENERATION_PARAMS: GenerationParams = {
  max_tokens: 4096,
  temperature: 1.0,
  top_p: 0.95,
  top_k: 0,
  min_p: 0.0,
  min_tokens_to_keep: 1,
  repetition_penalty: 1.0,
  repetition_context_size: 20,
  xtc_probability: 0.0,     // Added
  xtc_threshold: 0.0,       // Added
  extra_eos_tokens: [],     // Added
  seed: undefined,
  ignore_chat_template: false, // Added
  use_speculative: false,
  draft_model_identifier: null,
  num_draft_tokens: 3,
  kv_cache_options: {
      bits: undefined,
      group_size: 64,
      quantized_kv_start: 5000,
      max_size: undefined, // Added (primarily for make_prompt_cache, but can be here for consistency)
  },
  logit_bias: {},
  // 'prompt' and 'messages' are not part of default params saved in store
};


export const useGenerationStore = defineStore('generation', () => {
  const generationParams = ref<GenerationParams>({ ...DEFAULT_GENERATION_PARAMS });
  const isGenerating = ref(false);
  const currentOutputStream = ref<string>('');
  const lastChunk = ref<TokenChunk | null>(null);

  const cacheOperationStatus = ref<{ message: string; type: 'success' | 'error' | 'info' | ''; isLoading: boolean, cache_size?: number | null }>({
    message: '', type: '', isLoading: false
  });

  const appStore = useAppStore();
  const modelStore = useModelStore();
  let streamManager: GenerationStreamManager | null = null;

  watch(() => modelStore.currentModel, (newModel, oldModel) => {
    if (newModel?.id !== oldModel?.id || newModel?.adapter_path !== oldModel?.adapter_path) {
      if (isGenerating.value) stopGenerationStream("Model changed");
      currentOutputStream.value = "";
      lastChunk.value = null;
    }
  });

  function updateGenerationParams(params: Partial<GenerationParams>) {
    if (params.kv_cache_options) {
        const defaultKvOpts = DEFAULT_GENERATION_PARAMS.kv_cache_options || {};
        generationParams.value.kv_cache_options = {
            ...(generationParams.value.kv_cache_options || defaultKvOpts),
            ...params.kv_cache_options
        };
        delete params.kv_cache_options;
    }
    generationParams.value = { ...generationParams.value, ...params };
  }

  function resetGenerationParams() {
    generationParams.value = { ...DEFAULT_GENERATION_PARAMS };
  }

  // Modified startGenerationStream
  function startGenerationStream(
    // Takes an object that can have EITHER prompt OR messages
    payload: { prompt?: string; messages?: ChatMessage[] },
    onTokenUpdate: (chunkText: string) => void,
    onStreamComplete: () => void,
    onStreamError: (errorMessage: string) => void
  ) {
    if (isGenerating.value) {
      onStreamError("Another generation is already in progress.");
      return;
    }
    if (!modelStore.currentModel) {
      onStreamError("No model is loaded. Please select and load a model first.");
      return;
    }
    if (appStore.backendStatus !== 'online') {
        onStreamError("Backend is offline. Cannot start generation.");
        return;
    }

    isGenerating.value = true;
    currentOutputStream.value = "";
    lastChunk.value = null;
    appStore.clearError();

    const baseParams = { ...generationParams.value };
    // Remove prompt/messages from baseParams as they are in payload
    delete (baseParams as any).prompt;
    delete (baseParams as any).messages;

    const request: ApiGenerationRequest = {
      ...payload, // This will include either prompt or messages from the `payload` argument
      ...baseParams,
    };
    
    if (request.kv_cache_options === undefined || request.kv_cache_options === null) {
        request.kv_cache_options = {};
    }


    streamManager = new GenerationStreamManager(
      (chunk: TokenChunk) => {
        if (chunk.text) currentOutputStream.value += chunk.text;
        lastChunk.value = chunk;
        onTokenUpdate(chunk.text);
      },
      (error: Error) => {
        isGenerating.value = false;
        appStore.setLastError(`Generation Error: ${error.message}`);
        onStreamError(`Stream Error: ${error.message}`);
        streamManager = null;
      },
      () => {
        isGenerating.value = false;
        onStreamComplete();
        streamManager = null;
      }
    );
    streamManager.startStream(request);
  }

  function stopGenerationStream(reason: string = "User requested stop") {
    if (streamManager) {
      streamManager.closeStream(reason);
      streamManager = null;
    }
    if (isGenerating.value) {
        isGenerating.value = false;
    }
  }

  async function performCacheOperation(
    operation: 'save' | 'load' | 'trim',
    filenameOrTokens: string | number
  ) {
    if (cacheOperationStatus.value.isLoading) return;
    if (!modelStore.currentModel) {
        appStore.setLastError("No model loaded for cache operation.");
        cacheOperationStatus.value = { message: "No model loaded.", type: 'error', isLoading: false };
        return;
    }

    cacheOperationStatus.value = { message: `Performing ${operation}...`, type: 'info', isLoading: true };
    appStore.clearError();
    let result: CacheResponse;

    try {
        if (operation === 'save') {
            result = await saveKVCache(filenameOrTokens as string);
        } else if (operation === 'load') {
            result = await loadKVCache(filenameOrTokens as string);
        } else {
            result = await trimKVCache(filenameOrTokens as number);
        }

        if (result.success) {
            cacheOperationStatus.value = { message: result.message, type: 'success', isLoading: false, cache_size: result.cache_size };
        } else {
            const errorMsg = result.message || `Failed to ${operation} cache.`;
            cacheOperationStatus.value = { message: errorMsg, type: 'error', isLoading: false };
            appStore.setLastError(errorMsg);
        }
    } catch (error) {
        const errorMsg = error instanceof Error ? error.message : 'Unknown error during cache operation.';
        cacheOperationStatus.value = { message: errorMsg, type: 'error', isLoading: false };
        appStore.setLastError(errorMsg);
    }
  }

  return {
    generationParams,
    isGenerating,
    currentOutputStream,
    lastChunk,
    cacheOperationStatus,
    updateGenerationParams,
    resetGenerationParams,
    startGenerationStream,
    stopGenerationStream,
    saveCache: (filename: string) => performCacheOperation('save', filename),
    loadCache: (filename: string) => performCacheOperation('load', filename),
    trimCache: (numTokens: number) => performCacheOperation('trim', numTokens),
  };
});