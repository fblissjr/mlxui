import { WS_BASE_URL, API_URL, ENDPOINTS } from './constants';
import type { PerformanceMetrics } from './types';

export const fetchPerformanceStats = async (): Promise<PerformanceMetrics | null> => {
  try {
    const response = await fetch(ENDPOINTS.PERFORMANCE.STATS, { cache: 'no-store' });
    if (!response.ok) {
      console.error(`HTTP error fetching performance stats: ${response.status}`);
      return null;
    }
    const data = await response.json();
    return { ...data, timestamp: new Date(data.timestamp) } as PerformanceMetrics;
  } catch (error) {
    console.error('Error fetching performance stats:', error);
    return null;
  }
};

export class PerformanceStreamManager {
  private ws: WebSocket | null = null;
  private onMetricsCallback: (metrics: PerformanceMetrics) => void;
  private onErrorCallback: (error: Error) => void;
  private onCompleteCallback?: () => void;
  private reconnectAttempts: number = 0;
  private readonly maxReconnectAttempts: number = 5;
  private readonly initialReconnectDelay: number = 3000;
  private reconnectTimeoutId: NodeJS.Timeout | null = null;
  private explicitlyClosed: boolean = false;

  constructor(
    onMetrics: (metrics: PerformanceMetrics) => void,
    onError: (error: Error) => void,
    onComplete?: () => void
  ) {
    this.onMetricsCallback = onMetrics;
    this.onErrorCallback = onError;
    this.onCompleteCallback = onComplete;
    this.connect();
  }

  private connect(): void {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
        return;
    }
    this.explicitlyClosed = false;
    const wsUrl = ENDPOINTS.PERFORMANCE.STREAM_WS;

    try {
        this.ws = new WebSocket(wsUrl);
    } catch (error) {
        this.handleConnectionError(new Error(`Failed to create WebSocket: ${error instanceof Error ? error.message : String(error)}`));
        return;
    }

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data as string);
        if (data && data.timestamp) {
          const metrics: PerformanceMetrics = { ...data, timestamp: new Date(data.timestamp) };
          this.onMetricsCallback(metrics);
        } else if (data && data.error) {
            this.onErrorCallback(new Error(data.error));
        }
      } catch (error) {
        // Log, but don't always call global error handler for single bad message
      }
    };

    this.ws.onerror = (_event) => {
      // Error event often precedes onclose
    };

    this.ws.onclose = (event) => {
      this.ws = null;
      if (!this.explicitlyClosed) {
        this.handleConnectionError(new Error(`Performance WebSocket closed unexpectedly (Code: ${event.code}).`));
      } else if (this.onCompleteCallback) {
        this.onCompleteCallback();
      }
    };
  }

  private handleConnectionError(error: Error): void {
    this.onErrorCallback(error);
    this.scheduleReconnect();
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts && !this.explicitlyClosed) {
      this.reconnectAttempts++;
      const delay = Math.min(this.initialReconnectDelay * Math.pow(2, this.reconnectAttempts -1), 30000);
      if (this.reconnectTimeoutId) clearTimeout(this.reconnectTimeoutId);
      this.reconnectTimeoutId = setTimeout(() => this.connect(), delay);
    } else if (!this.explicitlyClosed) {
      this.onErrorCallback(new Error("Failed to reconnect to performance WebSocket after multiple attempts."));
    }
  }

  public closeStream(reason: string = "Client requested close"): void {
    this.explicitlyClosed = true;
    if (this.reconnectTimeoutId) clearTimeout(this.reconnectTimeoutId);
    if (this.ws) {
      if (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING) {
        this.ws.close(1000, reason);
      }
      this.ws = null;
    }
  }
}