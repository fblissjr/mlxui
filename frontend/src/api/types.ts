// ties to pydantic data model
// note for future: is there a way to sync the two data models?

export interface ModelInfo {
    id: string;
    name: string;
    path?: string | null;
    source: "local" | "hub";
    config?: Record<string, any> | null;
    is_loaded: boolean;
    adapter_path?: string | null;
}

export interface ModelLoadRequest {
    identifier: string;
    adapter_path?: string | null;
}

export interface ModelLoadResponse {
    success: boolean;
    message: string;
    model_info?: ModelInfo | null;
}


export interface KVCacheOptions {
    bits?: number | null;
    group_size?: number;
    quantized_kv_start?: number;
    max_size?: number | null; // Added
}

export interface GenerationParams {
    prompt?: string; // This might be sent by Notebook, or constructed by chat
    messages?: Array<{role: string, content: string}> | null; // For chat mode

    max_tokens: number;
    temperature: number;
    top_p?: number | null;
    top_k?: number | null;
    min_p?: number | null;
    min_tokens_to_keep?: number | null;
    
    repetition_penalty?: number | null;
    repetition_context_size?: number | null;
    
    xtc_probability?: number | null; // Added
    xtc_threshold?: number | null;   // Added
    
    // stopping_strings?: string[] | null; // Handled client-side or by adapter if mlx-lm supports
    extra_eos_tokens?: string[] | null; // Added

    seed?: number | null | undefined;
    
    ignore_chat_template?: boolean | null; // Added
    // use_default_chat_template?: boolean | null; // Defer for now

    use_speculative?: boolean | null;
    draft_model_identifier?: string | null;
    num_draft_tokens?: number | null;
    
    kv_cache_options?: KVCacheOptions | null;
    logit_bias?: Record<string, number> | null;
}

// GenerationRequest to backend will require either prompt or messages
export interface GenerationRequest extends Omit<GenerationParams, 'prompt' | 'messages'> {
    prompt?: string; // For non-chat or direct prompt input
    messages?: Array<{role: string, content: string}> | null; // For chat mode
}


export interface TokenChunk {
    text: string;
    is_finished: boolean;
    finish_reason?: "length" | "stop" | "error" | null;
    error?: string | null;
    from_draft?: boolean | null;
    token_count?: number | null;
    token?: number | null;
    prompt_tokens?: number | null;
    generation_tokens?: number | null;
    generation_tps?: number | null;
}

export interface CacheSaveRequest {
    filename: string;
}

export interface CacheLoadRequest {
    filename: string;
}

export interface TrimCacheRequest {
    num_tokens: number;
}

export interface CacheResponse {
    success: boolean;
    message: string;
    cache_size?: number | null;
}

export interface MemoryUsage {
    rss_mb: number;
}

export interface PerformanceMetrics {
    timestamp: Date; // Will be string from JSON, convert to Date on frontend
    tokens_per_second?: number | null;
    memory_usage?: MemoryUsage | null;
    cpu_usage_percent?: number | null;
}

export interface ConfigUpdateRequest {
    key: string
    value: any;
}

export interface ConfigUpdateResponse {
    success: boolean;
    message?: string | null;
}

// For frontend chat display
export interface ChatMessage {
    id: string;
    role: 'user' | 'assistant' | 'system' | 'error'; // Added 'error' role
    content: string;
    timestamp: number; // Unix timestamp
}