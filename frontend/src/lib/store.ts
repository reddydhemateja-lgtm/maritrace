type Listener = () => void;

interface SpillCache {
  data: any[];
  regions: Record<string, any>;
  lastFetch: number;
  loading: boolean;
  error: string | null;
}

const TTL_MS = 60_000;

export const spillStore = {
  state: {
    data: [],
    regions: {},
    lastFetch: 0,
    loading: false,
    error: null,
  } as SpillCache,

  listeners: new Set<Listener>(),

  subscribe(fn: Listener) {
    this.listeners.add(fn);
    return () => {
      this.listeners.delete(fn);
    };
  },

  notify() {
    this.listeners.forEach((l) => l());
  },

  isStale() {
    return Date.now() - this.state.lastFetch > TTL_MS;
  },

  setLoading(v: boolean) {
    this.state.loading = v;
    this.notify();
  },

  setData(data: any[], regions: Record<string, any>) {
    this.state.data = data;
    this.state.regions = regions;
    this.state.lastFetch = Date.now();
    this.state.loading = false;
    this.state.error = null;
    this.notify();
  },

  setError(err: string) {
    this.state.error = err;
    this.state.loading = false;
    this.notify();
  },
};