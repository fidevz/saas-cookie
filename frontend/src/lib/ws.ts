import { api } from "@/lib/api";

const _wsUrl = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";
// Enforce encrypted WebSocket connections in production.
if (process.env.NODE_ENV === "production" && _wsUrl.startsWith("ws://")) {
  throw new Error(
    `NEXT_PUBLIC_WS_URL must use wss:// in production (got: ${_wsUrl}). ` +
      "Unencrypted WebSocket connections are not allowed."
  );
}
const WS_BASE = _wsUrl;

class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private onMessageCallback: ((data: unknown) => void) | null = null;

  async connect(onMessage: (data: unknown) => void): Promise<void> {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    this.onMessageCallback = onMessage;
    this.reconnectAttempts = 0;
    await this.createConnection(onMessage);
  }

  private async createConnection(onMessage: (data: unknown) => void): Promise<void> {
    try {
      const { ticket } = await api.post<{ ticket: string }>("/notifications/ws-ticket/");
      this.ws = new WebSocket(`${WS_BASE}/ws/notifications/?ticket=${ticket}`);

      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data as string);
          onMessage(data);
        } catch {
          // Ignore invalid JSON messages
        }
      };

      this.ws.onerror = () => {
        // Error handled by onclose
      };

      this.ws.onclose = () => {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnect(onMessage);
        }
      };
    } catch {
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnect(onMessage);
      }
    }
  }

  private reconnect(onMessage: (data: unknown) => void): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }
    this.reconnectAttempts += 1;
    const delay = Math.min(1000 * 2 ** this.reconnectAttempts, 30000);
    this.reconnectTimer = setTimeout(() => {
      // Each reconnect fetches a fresh ticket (tickets are single-use)
      void this.createConnection(onMessage);
    }, delay);
  }

  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent auto-reconnect
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.onMessageCallback = null;
  }

  send(data: unknown): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export const wsClient = new WebSocketClient();
