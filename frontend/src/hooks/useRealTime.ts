import { useEffect, useState } from 'react';

// Build the WebSocket URL from env var, with production fallback
const WS_REALTIME_URL =
  import.meta.env.VITE_WS_URL
    ? import.meta.env.VITE_WS_URL.replace(/\/ws$/, '/api/realtime/ws')
    : 'wss://maritrace.onrender.com/api/realtime/ws';

export function useRealTime() {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [data, setData] = useState<any>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    let socket: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let cancelled = false;

    const connect = () => {
      if (cancelled) return;

      socket = new WebSocket(WS_REALTIME_URL);

      socket.onopen = () => {
        console.log('[useRealTime] WebSocket connected:', WS_REALTIME_URL);
        setConnected(true);
      };

      socket.onmessage = (event) => {
        try {
          setData(JSON.parse(event.data));
        } catch (err) {
          console.warn('[useRealTime] Bad message:', err);
        }
      };

      socket.onerror = (err) => {
        console.warn('[useRealTime] WebSocket error:', err);
      };

      socket.onclose = () => {
        setConnected(false);
        if (!cancelled) {
          reconnectTimer = setTimeout(() => {
            console.log('[useRealTime] Reconnecting...');
            connect();
          }, 3000);
        }
      };

      setWs(socket);
    };

    connect();

    return () => {
      cancelled = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (socket) socket.close();
    };
  }, []);

  return { data, connected };
}