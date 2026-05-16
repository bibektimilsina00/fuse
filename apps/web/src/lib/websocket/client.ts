import type { ExecutionEvent } from '@fuse/workflow-schema';
import { logger } from '@/lib/logger';

export type { ExecutionEvent };

export interface WebSocketOptions {
  onEvent: (event: ExecutionEvent) => void;
  onClose?: () => void;
  reconnect?: boolean;
  maxRetries?: number;
}

/**
 * Robust WebSocket Manager for execution streaming.
 * Handles heartbeats, reconnection, and basic event routing.
 */
export class ExecutionWebSocket {
  private ws: WebSocket | null = null;
  private retryCount = 0;
  private maxRetries: number;
  private reconnect: boolean;
  private executionId: string;
  private token: string;
  private onEvent: (event: ExecutionEvent) => void;
  private onClose?: () => void;
  private heartbeatInterval: any;
  private receivedTerminalEvent = false;

  constructor(executionId: string, token: string, options: WebSocketOptions) {
    this.executionId = executionId;
    this.token = token;
    this.onEvent = options.onEvent;
    this.onClose = options.onClose;
    this.reconnect = options.reconnect ?? true;
    this.maxRetries = options.maxRetries ?? 5;

    this.connect();
  }

  private connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // In production, this would use the actual API URL from config
    const baseUrl = window.location.hostname === 'localhost' ? 'localhost:8000' : window.location.host;
    const wsUrl = `${protocol}//${baseUrl}/api/v1/ws/executions/${this.executionId}?token=${this.token}`;

    logger.info('[WS] Connecting', { executionId: this.executionId });
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      logger.info('[WS] Connected', { executionId: this.executionId });
      this.retryCount = 0;
      this.startHeartbeat();
    };

    this.ws.onmessage = (event) => {
      try {
        if (event.data === 'pong') return;
        const data = JSON.parse(event.data) as ExecutionEvent;
        this.onEvent(data);
        if (data.type === 'execution_completed' || data.type === 'execution_failed') {
          this.receivedTerminalEvent = true;
        }
      } catch (err) {
        logger.error('[WS] Failed to parse event:', err);
      }
    };

    this.ws.onclose = () => {
      logger.info('[WS] Disconnected', { executionId: this.executionId });
      this.stopHeartbeat();

      if (this.reconnect && !this.receivedTerminalEvent && this.retryCount < this.maxRetries) {
        const delay = Math.min(1000 * Math.pow(2, this.retryCount), 10000);
        logger.info('[WS] Reconnecting', {
          executionId: this.executionId,
          delay,
          attempt: this.retryCount + 1,
          maxRetries: this.maxRetries,
        });
        setTimeout(() => {
          this.retryCount++;
          this.connect();
        }, delay);
      } else {
        if (this.onClose) this.onClose();
      }
    };

    this.ws.onerror = (err) => {
      logger.error('[WS] Error:', err);
    };
  }

  private startHeartbeat() {
    this.stopHeartbeat();
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send('ping');
      }
    }, 30000); // 30s heartbeat
  }

  private stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  public close() {
    this.reconnect = false; // Prevent auto-reconnect
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

/**
 * Shorthand helper to connect.
 */
export function connectExecutionWebSocket(
  executionId: string,
  token: string,
  options: WebSocketOptions
): ExecutionWebSocket {
  return new ExecutionWebSocket(executionId, token, options);
}
