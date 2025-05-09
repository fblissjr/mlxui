import { WS_BASE_URL, API_URL, ENDPOINTS } from './constants';
import type { GenerationRequest, TokenChunk, CacheSaveRequest, CacheLoadRequest, TrimCacheRequest, CacheResponse } from './types';

export class GenerationStreamManager {
  private ws: WebSocket | null = null;
  private request: GenerationRequest | null = null;
  private onTokenCallback: (chunk: TokenChunk) => void;
  private onErrorCallback: (error: Error) => void;
  private onCompleteCallback: () => void;
  private receivedFinalChunk: boolean = false;
  private connectionTimeout: NodeJS.Timeout | null = null;
  private explicitlyClosed: boolean = false;

  constructor(
    onToken: (chunk: TokenChunk) => void,
    onError: (error: Error) => void,
    onComplete: () => void
  ) {
    this.onTokenCallback = onToken;
    this.onErrorCallback = onError;
    this.onCompleteCallback = onComplete;
  }

  public startStream(request: GenerationRequest): void {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      this.closeStream("Starting new stream");
    }
    this.request = request;
    this.receivedFinalChunk = false;
    this.explicitlyClosed = false;

    const wsUrl = ENDPOINTS.GENERATION.STREAM_WS;

    try {
        this.ws = new WebSocket(wsUrl);
    } catch (error) {
        this.onErrorCallback(new Error(`Failed to establish WebSocket: ${error instanceof Error ? error.message : String(error)}`));
        return;
    }

    this.connectionTimeout = setTimeout(() => {
        if (this.ws && this.ws.readyState !== WebSocket.OPEN) {
            this.onErrorCallback(new Error("WebSocket connection timed out."));
            this.ws.close();
        }
    }, 10000);


    this.ws.onopen = () => {
      if (this.connectionTimeout) clearTimeout(this.connectionTimeout);
      if (this.ws && this.request) {
        try {
          this.ws.send(JSON.stringify(this.request));
        } catch (error) {
          this.onErrorCallback(new Error(`Failed to send request: ${error instanceof Error ? error.message : String(error)}`));
          this.ws.close();
        }
      }
    };

    this.ws.onmessage = (event) => {
      try {
        const chunk = JSON.parse(event.data as string) as TokenChunk;
        if (chunk.error) {
          this.onErrorCallback(new Error(chunk.error));
          this.receivedFinalChunk = true;
          this.closeStream("Error received from backend");
          return;
        }
        this.onTokenCallback(chunk);
        if (chunk.is_finished) {
          this.receivedFinalChunk = true;
          this.onCompleteCallback();
        }
      } catch (error) {
        this.onErrorCallback(new Error(`Failed to parse server response: ${error instanceof Error ? error.message : String(error)}`));
        this.closeStream("Message parsing error");
      }
    };

    this.ws.onerror = (_event) => {
      if (this.connectionTimeout) clearTimeout(this.connectionTimeout);
    };

    this.ws.onclose = (event) => {
      if (this.connectionTimeout) clearTimeout(this.connectionTimeout);
      if (!this.explicitlyClosed && !this.receivedFinalChunk && event.code !== 1000) {
        this.onErrorCallback(new Error(`WebSocket closed unexpectedly. Code: ${event.code}, Reason: ${event.reason || 'N/A'}`));
      } else if (!this.receivedFinalChunk && event.code === 1000) {
        this.onCompleteCallback();
      }
      this.ws = null;
    };
  }

  public closeStream(reason: string = "Client requested close"): void {
    this.explicitlyClosed = true;
    if (this.connectionTimeout) clearTimeout(this.connectionTimeout);
    if (this.ws) {
      if (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING) {
        this.ws.close(1000, reason);
      }
      this.ws = null;
    }
  }
}

export const saveKVCache = async (filename: string): Promise<CacheResponse> => {
    try {
        const requestBody: CacheSaveRequest = { filename };
        const response = await fetch(ENDPOINTS.GENERATION.CACHE_SAVE, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody),
        });
        const data: CacheResponse = await response.json();
        if (!response.ok) {
            throw new Error(data.message || `HTTP error saving cache: ${response.status}`);
        }
        return data;
    } catch (error) {
        return { success: false, message: error instanceof Error ? error.message : 'Unknown error saving cache', cache_size: null };
    }
};

export const loadKVCache = async (filename: string): Promise<CacheResponse> => {
    try {
        const requestBody: CacheLoadRequest = { filename };
        const response = await fetch(ENDPOINTS.GENERATION.CACHE_LOAD, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody),
        });
        const data: CacheResponse = await response.json();
        if (!response.ok) {
            throw new Error(data.message || `HTTP error loading cache: ${response.status}`);
        }
        return data;
    } catch (error) {
        return { success: false, message: error instanceof Error ? error.message : 'Unknown error loading cache', cache_size: null };
    }
};

export const trimKVCache = async (num_tokens: number): Promise<CacheResponse> => {
    try {
        const requestBody: TrimCacheRequest = { num_tokens };
        const response = await fetch(ENDPOINTS.GENERATION.CACHE_TRIM, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody),
        });
        const data: CacheResponse = await response.json();
        if (!response.ok) {
            throw new Error(data.message || `HTTP error trimming cache: ${response.status}`);
        }
        return data;
    } catch (error) {
        return { success: false, message: error instanceof Error ? error.message : 'Unknown error trimming cache', cache_size: null };
    }
};