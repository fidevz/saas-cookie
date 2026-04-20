import { api } from "@/lib/api";

/** WebSocket() only accepts ws: or wss: — http(s) is a common .env mistake and throws "Invalid URL". */
function normalizeWebSocketBase(raw: string): string {
  const t = raw.trim();
  if (!t) return "ws://localhost:8000";
  if (t.startsWith("https://")) return "wss://" + t.slice(8).replace(/\/+$/, "");
  if (t.startsWith("http://")) return "ws://" + t.slice(7).replace(/\/+$/, "");
  return t.replace(/\/+$/, "");
}

const _wsUrl = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";
const WS_BASE = normalizeWebSocketBase(_wsUrl);

// Enforce encrypted WebSocket connections in production.
if (process.env.NODE_ENV === "production" && WS_BASE.startsWith("ws://")) {
  throw new Error(
    `NEXT_PUBLIC_WS_URL must use wss:// in production (got: ${WS_BASE}). ` +
      "Unencrypted WebSocket connections are not allowed."
  );
}

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
      const wsUrl = `${WS_BASE}/ws/notifications/?ticket=${encodeURIComponent(ticket)}`;
      this.ws = new WebSocket(wsUrl);

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

      this.ws.onclose = (event: CloseEvent) => {
        // Permanent failure codes — do not reconnect
        if (event.code === 4001 || event.code === 4008 || event.code === 4029) {
          console.warn(`WebSocket closed permanently (code ${event.code}). Not reconnecting.`);
          return;
        }
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
