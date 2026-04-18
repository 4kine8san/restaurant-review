import { useState, useCallback } from "react";
import type { DisplayMode } from "../constants";
import type { ListParams } from "../api/restaurants";

const STORAGE_KEY = "restaurant_list_state";

interface ListState {
  params: ListParams;
  displayMode: DisplayMode;
}

function loadState(): ListState {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw) as ListState;
  } catch {
    // ignore
  }
  return { params: { page: 1, order: "created_at_desc" }, displayMode: "medium" };
}

export function useListState() {
  const [state, setState] = useState<ListState>(loadState);

  const update = useCallback((patch: Partial<ListState>) => {
    setState((prev) => {
      const next = { ...prev, ...patch };
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  return { state, update };
}
