import { useEffect, useState } from "react";
import { api } from "../api/client";
import { spillStore } from "../lib/store";

export function useSpills() {
  const [state, setState] = useState({ ...spillStore.state });

  useEffect(() => {
    const unsubscribe = spillStore.subscribe(() => {
      setState({ ...spillStore.state });
    });

    if (spillStore.isStale() && !spillStore.state.loading) {
      spillStore.setLoading(true);
      api
        .recentSpills()
        .then((r: any) => {
          spillStore.setData(r.spills || [], r.regions || {});
        })
        .catch((e: any) => {
          spillStore.setError(e.message);
        });
    }

    return () => {
      unsubscribe();
    };
  }, []);

  return state;
}